import logging
import threading
import traceback
import multiprocessing

from .base import ExecuteTask, ExecuteJob
from .task import Task
from ...utils.task import ArtifactType, TaskStatus

class SyncJob(ExecuteJob):
    def __init__(self, message_queue: multiprocessing.Queue) -> None:
        super().__init__()
        self.message_queue = message_queue

    def update(self, **kwargs) -> None:
        self.push('job', **kwargs)
    
    def push(self, target: str, **kwargs) -> None:
        self.message_queue.put({
            'target': target,
            'body': kwargs
        })

class SyncTask(ExecuteTask):
    def __init__(self, message_queue: multiprocessing.Queue) -> None:
        super().__init__()
        self.job = SyncJob(message_queue)

    def update(self, **kwargs) -> None:
        self.push('update', **kwargs)
    
    def set_passing_args(self, args: dict) -> None:
        self.push('passing_args', args=args)

    def passive_update(self, **kwargs) -> None:
        self.push('passive_update', **kwargs)

    def add_artifact(
        self, 
        name: str, artifact_type: ArtifactType, 
        artifact: str | dict,
        attachments: dict | None = None
    ) -> None:
        self.push('artifact', name=name, artifact_type=artifact_type, artifact=artifact, attachments=attachments)

    def push(self, target: str, **kwargs) -> None:
        self.job.push(target, **kwargs)

class SyncHandler(logging.Handler):
    def __init__(self, message_queue: multiprocessing.Queue) -> None:
        super().__init__()
        self.message_queue = message_queue

    def emit(self, record: logging.LogRecord) -> None:
        levelname = record.levelname.lower()
        message = self.format(record)
        exc_info = record.exc_info
        self.push(levelname, message=message)
        if exc_info:
            message = traceback.format_exception(*exc_info)
            for line in message:
                self.push(levelname, message=line)
            
    def push(self, target: str, **kwargs) -> None:
        self.message_queue.put({
            'target': target,
            'body': kwargs
        })

class ProcessRunner:
    def __init__(self, task: Task) -> None:
        self.task = task
        self.message_queue = multiprocessing.Queue()

    def start_capturing(self) -> None:
        """
        Starts capturing the output of the execution.
        """
        while True:
            message = self.message_queue.get()
            if message is None:
                break
            if message['target'] == 'job':
                self.task.job.update(**message['body'])
            elif message['target'] == 'passive_update':
                self.task.passive_update(**message['body'])
            elif message['target'] == 'update':
                self.task.update(**message['body'])
            elif message['target'] == 'error':
                self.task.logger.error(message['body']['message'])
            elif message['target'] == 'info':
                self.task.logger.info(message['body']['message'])
            elif message['target'] == 'debug':
                self.task.logger.debug(message['body']['message'])
            elif message['target'] == 'output':
                self.task.output.write(message['body']['message'])
                self.task.log_listener.flush_output()
            elif message['target'] == 'passing_args':
                self.task.execution.passing_args.update(message['body']['args'])
            elif message['target'] == 'artifact':
                self.task.add_artifact(**message['body'])
            else:
                self.task.logger.warning(f"Unknown message target: {message['target']}")

    def start(self) -> None:
        """
        Starts the task execution in a separate process.
        """
        self.task.logger.info(f"Starting capturing for task {self.task.name}")
        capture_thread = threading.Thread(target=self.start_capturing)
        capture_thread.daemon = True
        capture_thread.start()
        
        self.task.logger.info(f"Starting task {self.task.name} in a separate process")
        
        sync_task = SyncTask(self.message_queue)
        logger = logging.getLogger(self.task.tid)

        logger.handlers.clear()
        handler = SyncHandler(self.message_queue)
        handler.setLevel(self.task.logger.level)
        logger.addHandler(handler)

        process = multiprocessing.Process(
            target=self.task.execution.start, 
            args=(sync_task, logger, self.task.get_running_args())
        )

        process.start()
        self.task.logger.info(f"Waiting for task {self.task.name} / {process.pid} process to finish")
        process.join()
        
        self.task.logger.info(f"Waiting for capture thread to finish for task {self.task.name}")
        self.message_queue.put(None)
        capture_thread.join()
        
        # Check if capture thread process has exited normally
        while not self.message_queue.empty():
            if self.message_queue.get() is None:
                break
            else:
                raise RuntimeError("Capture thread exited unexpectedly")
        
        # Put None in the message queue to signal completion
        self.task.logger.info(f"Task {self.task.name} completed, notifying capture thread")
        
        if process.exitcode != 0:
            self.task.logger.error(f"Task {self.task.name} failed with exit code {process.exitcode}")
            self.task.update(status=TaskStatus.FAILED, message=f"Task failed with exit code {process.exitcode}")
        self.task.done()