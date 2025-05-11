import queue
import threading

from ..tasks.runner import ProcessRunner
from ..job import RemoteJob, JobAction
from ..tasks.task import Task, TaskStatus
from ...utils.config import Config, get_logger
from ...utils.job import JobStatus

class Pipeline:
    runners: dict[str, ProcessRunner]
    def __init__(self, job: RemoteJob):
        self.job = job
        self.tasks: list[Task] = self.build_pipeline()
        self.identifier = None
        self.runners = {}
        self.runner_threads: list[threading.Thread] = []
        self.logger = get_logger(__name__, Config().log_level)
        self.operation_lock = threading.Condition()

    def build_pipeline(self) -> list[Task]:
        """
        Builds the pipeline by creating tasks and setting up their dependencies.
        """
        raise NotImplementedError("You must implement the build_pipeline method")
    
    def run_task(self, runner: ProcessRunner) -> None:
        """
        Runs the task in a separate thread. 
        We will wake up the executor thread when the task is done.
        """
        task = runner.task
        self.logger.info(f"Starting task: {task.name}")
        try:
            runner.start()
        except Exception as e:
            task.update(status=TaskStatus.FAILED, message=str(e))
            self.logger.error(f'Task failed: {task.name}', exc_info=True)
        finally:
            try:
                task.done()
            except Exception as e:
                self.logger.error(f'Task done failed: {task.name}', exc_info=True)
            with self.operation_lock:
                self.operation_lock.notify_all()
    
    def pre_start(self) -> None:
        """
        Builds the runners for each task in the pipeline.
        """
        for task in self.tasks:
            if task.name not in self.runners:
                runner = ProcessRunner(task)
                t = threading.Thread(target=self.run_task, args=(runner,))
                t.start()
                self.runners[task.name] = runner
                self.runner_threads.append(t)

    def post_start(self) -> None:
        """
        Recycles the runners for each task in the pipeline.
        """
        for runner in self.runners.values():
            runner.stop()

    def check_job_action(self) -> None:
        action = self.job.get_action()
        if action == JobAction.STOP:
            self.logger.info('Stopping job execution...')
            for task in self.tasks:
                task.interrupt()
            self.job.update(status=JobStatus.INTERRUPTING)

    def _start(self) -> None:
        """
        Starts the pipeline execution according to the task dependencies.
        """
        self.logger.info(f'Starting pipeline with job ID: {self.job.jid}')
        self.job.update(status=JobStatus.RUNNING)
        
        self.pre_start()

        # Initialize the queue with tasks that have no prerequisites
        pending: queue.Queue[Task] = queue.Queue()
        prerequisite_count: dict[str, int] = {}
        for task in self.tasks:
            prerequisite_count[task.name] = len(task.prerequisites)
            if prerequisite_count[task.name] == 0:
                pending.put(task)
        
        running_tasks: list[Task] = []
        with self.operation_lock:
            while not pending.empty() or running_tasks:
                self.logger.info("Handling task dependencies...")
                # check if any task has finished and update subsequent tasks
                finished_tasks = [
                    task
                    for task in running_tasks
                    if not task.is_running()
                ]
                for task in finished_tasks:
                    if 'identifier' in task.get_passing_args():
                        self.identifier = task.get_passing_args()['identifier']
                    running_tasks.remove(task)
                    for subtask in task.subsequent_tasks:
                        prerequisite_count[subtask.name] -= 1
                        if prerequisite_count[subtask.name] == 0:
                            pending.put(subtask)

                self.check_job_action()

                self.logger.info(f'pending task: {pending.qsize()}')
                self.logger.info(f'running tasks: {len(running_tasks)}')
                # Waiting for running tasks to finish if there are no pending tasks
                if pending.empty():
                    if running_tasks:
                        self.logger.info("Waiting for tasks to finish...")
                        self.operation_lock.wait()
                        continue
                    else:
                        self.logger.info("No tasks to run, exiting...")
                        break
                
                # We have pending tasks, start one of them
                task = pending.get()
                self.logger.info(f"Processing task: {task.name}")
                if task not in running_tasks:
                    running_tasks.append(task)
                if task.is_running():
                    self.logger.info(f"Task {task.name} is already running.")
                    continue
                
                if task.is_prerequisite_fulfilled():
                    if task.is_pending():
                        task.update(status=TaskStatus.QUEUED)
                        task.run(identifier=self.identifier)
                    else:
                        self.logger.info(f"Task {task.name} not in pending state: {task.status}")
                else:
                    task.cancel(reason=f"Task {task.name} prerequisites not fulfilled")
    
    def start(self) -> None:
        """
        Starts the pipeline execution.
        """
        try:
            self._start()
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        
        self.post_start()
        self.logger.info('Waiting for all threads to complete...')
        for thread in self.runner_threads:
            thread.join()
        self.logger.info('All threads have completed.')

        self.job.done()
        self.logger.info('Pipeline execution completed.')