import queue
import threading

from ..tasks.runner import ProcessRunner
from ..job import RemoteJob
from ..tasks.task import Task, TaskStatus
from ...utils.config import Config, get_logger
from ...utils.job import JobStatus

class Pipeline:
    def __init__(self, job: RemoteJob):
        self.job = job
        self.tasks: list[Task] = self.build_pipeline()
        self.logger = get_logger(__name__, Config().log_level)
        self.operation_lock = threading.Lock()
        self.operation_signal = threading.Event()

    def build_pipeline(self) -> list[Task]:
        """
        Builds the pipeline by creating tasks and setting up their dependencies.
        """
        raise NotImplementedError("You must implement the build_pipeline method")
    
    def run_task(self, task: Task) -> None:
        """
        Runs the task in a separate thread. 
        We will wake up the executor thread when the task is done.
        """
        self.logger.info(f"Starting task: {task.name}")
        try:
            ProcessRunner(task).start()
            task.done()
        except Exception as e:
            task.update(status=TaskStatus.FAILED, message=str(e))
            self.logger.error(f'Task failed: {task.name}', exc_info=True)
        finally:
            with self.operation_lock:
                self.operation_signal.set()
            
    def start(self) -> None:
        """
        Starts the pipeline execution according to the task dependencies.
        """
        self.logger.info(f'Starting pipeline with job ID: {self.job.jid}')
        self.job.update(status=JobStatus.RUNNING)
        
        # Initialize the queue with tasks that have no prerequisites
        pending: queue.Queue[Task] = queue.Queue()
        prerequisite_count: dict[str, int] = {}
        for task in self.tasks:
            prerequisite_count[task.name] = len(task.prerequisites)
            if prerequisite_count[task.name] == 0:
                pending.put(task)
        
        running_tasks: list[Task] = []
        while not pending.empty() or running_tasks:
            self.logger.info(f'pending task: {pending.qsize()}')
            self.logger.info(f'running tasks: {len(running_tasks)}')
            if pending.empty() and running_tasks:
                self.logger.info("Waiting for tasks to finish...")
                self.operation_signal.wait()
            
            self.logger.info("Start processing tasks...")
            with self.operation_lock:
                self.operation_signal.clear()
                # check if any task has finished and update subsequent tasks
                finished_tasks = [
                    task
                    for task in running_tasks
                    if not task.is_running()
                ]
                for task in finished_tasks:
                    running_tasks.remove(task)
                    for task in task.subsequent_tasks:
                        prerequisite_count[task.name] -= 1
                        if prerequisite_count[task.name] == 0:
                            pending.put(task)
                # Waiting for running tasks to finish if there are no pending tasks
                if pending.empty():
                    continue
                
                # We have pending tasks, start one of them
                task = pending.get()
                self.logger.info(f"Processing task: {task.name}")
                if task not in running_tasks:
                    running_tasks.append(task)
                if task.is_running():
                    self.logger.info(f"Task {task.name} is already running.")
                    continue
                
                if task.is_prerequisite_fulfilled():
                    task.update(status=TaskStatus.QUEUED)
                    thread = threading.Thread(target=self.run_task, args=(task,))
                    thread.start()
                else:
                    self.operation_signal.set()
                    self.logger.info(f"Task {task.name} failed due to incomplete prerequisites.")

        self.job.done()
        self.logger.info('Pipeline execution completed.')