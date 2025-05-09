import json
import time
import threading
import uuid

from .slave.process import Process
from ...utils.config import get_logger
from ...utils.connection import Connection as Client
from ...utils.job import BaseJob, JobStatus
from ...utils.task import BaseTask

class CacheJob(BaseJob):
    def __init__(self, jid: str, created_at: float, started_at: float, finished_at: float,
        job_type: str, media: dict[str, str], status: str, message: str, 
        isProcessExited: bool, last_update: float, 
        artifact_tags: dict[str, int], 
        tasks: dict[dict], artifacts: list
    ):
        """
        Initializes a job loaded from the cache.
        """
        super().__init__(
            jid=jid, created_at=created_at, started_at=started_at, finished_at=finished_at,
            job_type=job_type, media=media, status=status, message=message, 
            isProcessExited=isProcessExited, last_update=last_update,
            artifact_tags=artifact_tags,
            tasks=tasks, artifacts=artifacts
        )
        self.process: Process = None
        self.listeners: list[Client] = []
        self.logger = get_logger(__name__, self.config.log_level)
        self.process_guard_thread = None
        self.operation_event = threading.Event()
    
    def attach(self, process: Process) -> None:
        """
        Attaches a subprocess to the job.
        """
        with self.operation_lock:
            if self.process is not None:
                raise RuntimeError("Process already attached to job")
            self.process = process
            self.logger.info(f"Process {self.process.pid} attached to job {self.jid}")
            self.update(status=JobStatus.CREATED, started_at=time.time())
            self.process_guard_thread = threading.Thread(target=self.process_guard)
            self.process_guard_thread.daemon = True
            self.process_guard_thread.start()

    def process_guard(self) -> None:
        """
        Monitors the process to ensure it is responsive.
        If the process does not respond within a certain time frame, it is interrupted.
        This is a separate thread that runs in the background.
        """
        self.logger.info(f"Starting process guard for job {self.jid}")
        min_response_time = self.config.min_job_response_time
        while self.process and self.process.poll() is None:
            now = time.time()
            if now - self.last_update > min_response_time:
                self.logger.warning("Process exceeded minimum response time, interrupting...")
                self.interrupt()
                continue
            self.operation_event.wait(60)
        self.logger.info(f"Process guard for job {self.jid} finished")

    def interrupt(self) -> None:
        """
        Interrupts the process attached to the job.
        """
        with self.operation_lock:
            if self.process is None:
                raise RuntimeError("No process attached to job")
            self.logger.info("Terminating process...")
            self.update(status=JobStatus.INTERRUPTING)
            self.process.terminate()
            self.process.wait()
            self.update(status=JobStatus.INTERRUPTED, isProcessExited=True)

    def is_finished(self) -> bool:
        if self.status in (JobStatus.QUEUED, JobStatus.CREATED, JobStatus.PENDING):
            return False
        if self.process is None:
            return True
        if self.process.poll() is not None:
            return True
        return False
    
    def done(self) -> None:
        """
        This method is called when the process attached to the job is exited.
        It performs the following actions:
            1. Raises an exception if the process is still running.
            2. Waiting for the guard thread to finish.
            3. Marks the job as done and updates the status accordingly.
        """
        super().done()
        self.logger.debug(f"Checking if process is still running for job {self.jid}")
        if self.process is not None:
            if self.process.poll() is None:
                raise RuntimeError("Process is still running")
            self.process = None
        self.logger.debug(f"Waiting for process guard thread to finish for job {self.jid}")
        self.operation_event.set()
        if self.process_guard_thread is not None:
            self.process_guard_thread.join()
        
        with self.operation_lock:
            if not self.isProcessExited:
                self.logger.error("Job failed due to process exit abnormality")
                self.update(status=JobStatus.FAILED, isProcessExited=True)
            self.update(finished_at=time.time())
            self.dump()
    
    def push(self, listener: Client, progress: dict) -> bool:
        try:
            listener.send(json.dumps(progress))
            return True
        except Exception as e:
            self.logger.error(f"Error sending progress to listener: {e}")
        return False

    def broadcast(self) -> None:
        """
        Broadcasts the job progress to all listeners.
        """
        failed_listeners = []
        for listener in self.listeners:
            if not self.push(listener, self.serialize()):
                failed_listeners.append(listener)
        for listener in failed_listeners:
            self.remove_listener(listener)

    def add_listener(self, listener: Client) -> None:
        """
        Adds a listener to the job.
        This is used for sending updates to the client.
        """
        self.logger.debug(f'Length of listeners: {len(self.listeners)}')
        with self.operation_lock:
            self.listeners.append(listener)
        if not self.push(listener, self.serialize()):
            self.logger.error(f"Failed to send initial data to listener {listener}")
            self.remove_listener(listener)

    def remove_listener(self, listener: Client) -> None:
        """
        Removes a listener from the job.
        """
        with self.operation_lock:
            if listener in self.listeners:
                listener.close()
                self.logger.debug(f'Length of listeners: {len(self.listeners)}')
                self.listeners.remove(listener)
    
    def update(self, **kwargs: dict) -> None:
        """
        Updates the job with the provided progress updates from the worker
        """
        self.last_update = time.time()
        for key, value in kwargs.items():
            partial_update = False
            if key == 'media':
                self.media.update(**value)
                partial_update = True
            elif key == 'tasks':
                partial_update = True
                for tid, task in value.items():
                    target = self.tasks.get(tid)
                    if target is None:
                        self.tasks[tid] = BaseTask(**task)
                    else:
                        target.update(**task)
            if not partial_update:
                setattr(self, key, value)
        self.broadcast()

class Job(CacheJob):
    def __init__(self, job_type: str, media: dict):
        """
        Initializes a Job instance from the client request.
        This is used for creating a job from the client.
        """
        if 'metadata' not in media:
            media['metadata'] = {}
        super().__init__(
            jid=str(uuid.uuid4()), created_at=time.time(), started_at=None, finished_at=None,
            job_type=job_type, media=media,
            status=JobStatus.PENDING, message='Waiting for scheduler...', isProcessExited=False, 
            last_update=time.time(), 
            artifact_tags={},
            tasks={}, artifacts=None
        )
