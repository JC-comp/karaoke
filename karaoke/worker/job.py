import json
import time
import uuid
import threading

from .binder.base import Binder
from ..utils.job import BaseJob, JobStatus
from ..utils.task import BaseTask
from ..utils.config import get_logger, Config


class CommandJob(BaseJob):
    """
    This class represents a job that is created by a command line.
    """
    def __init__(self, job_type: str, media: dict) -> None:
        if 'metadata' not in media:
            media['metadata'] = {}
        super().__init__(
            jid=str(uuid.uuid4()), created_at=time.time(), started_at=None, finished_at=None,
            job_type=job_type, media=media,
            status=JobStatus.PENDING, message='Waiting for scheduler...',
            isProcessExited=False, last_update=time.time(), 
            artifact_tags={},
            tasks={}, artifacts=None
        )
        self.logger = get_logger(__name__, Config().log_level)

    def update(self, **kwargs: dict) -> None:
        for key, value in kwargs.items():
            partial_update = False
            if key == 'media':
                self.media.update(**value)
                partial_update = True
            elif key == 'tasks':
                # task will handled the update first
                # so we don't need to update again
                # remote scheduler will not update tasks neither
                continue
            if not partial_update:
                setattr(self, key, value)
        tasks = kwargs.get('tasks', {})
        for task in tasks.values():
            message = task.get('message', '')
            if '\r' in message:
                print(message, end='', flush=True)

class RemoteJob(BaseJob):
    """
    This class represents a job that is created by a remote scheduler.
    The remote scheduler is communicating via a Binder.
    """
    def __init__(self, binder: Binder, **kwargs) -> None:
        super().__init__(**kwargs)
        self.binder = binder
        self.logger = get_logger(__name__, Config().log_level)
        self.operation_lock = threading.Lock()

    def add_task(self, task: BaseTask) -> None:
        """
        Adds a task to the job.
        """
        super().add_task(task)
        self.update(tasks={
            task.tid: task.serialize()
        })

    def update(self, **kwargs: dict) -> None:
        """
        Push updates to the remote scheduler.
        """
        with self.operation_lock:
            for key, value in kwargs.items():
                partial_update = False
                if key == 'media':
                    self.media.update(**value)
                    partial_update = True
                elif key == 'tasks':
                    # task will handled the update first
                    # so we don't need to update again
                    # remote scheduler will not update tasks neither
                    continue
                if not partial_update:
                    setattr(self, key, value)
            self.binder.update(**kwargs)

    def done(self) -> None:
        """
        Marks the job as done and updates the status of all tasks.
        Closes the connection to the remote scheduler.
        """
        super().done()
        result = JobStatus.COMPLETED
        for task in self.tasks.values():
            if task.is_interrupted():
                self.logger.error(f'Setting job status to interrupted due to task: {task.name}')
                result = JobStatus.INTERRUPTED
                break
            if not task.is_success():
                self.logger.error(f'Setting job status to failed due to task: {task.name}')
                result = JobStatus.FAILED
                break
        
        self.update(status=result, isProcessExited=True)
        self.binder.close()