import io
import json
import logging
import uuid
import threading

from .execution import Execution
from ..job import RemoteJob
from ...utils.task import BaseTask, Artifact, ArtifactType
from ...utils.config import Config, get_task_logger
from ...utils.task import TaskStatus

class LogListener(logging.Handler):
    def __init__(self, task: "Task") -> None:
        super().__init__()
        self.task = task

    def flush_output(self) -> None:
        self.task.job.update(
            tasks={
                self.task.tid: {
                    'output': self.task.output.getvalue(),
                }
            }
        )
    
    def emit(self, _: logging.LogRecord) -> None:
        self.flush_output()

class Task(BaseTask):
    def __init__(self, name: str, job: RemoteJob, execution_class: type[Execution], execution_kargs: dict=None) -> None:
        super().__init__(
            tid=str(uuid.uuid4()),
            name=name,
            message=None,
            output=io.StringIO(),
            status=TaskStatus.PENDING,
            artifacts=[]
        )
        self.job = job
        self.config = Config()
        self.execution = execution_class(self.name, self.config, **(execution_kargs or {}))

        self.prerequisites: list[Task] = []
        self.subsequent_tasks: list[Task] = []

        self.log_listener = LogListener(self)
        self.logger = get_task_logger(
            self.__class__.__module__ + '.' + self.tid, 
            buffer=self.output, event_handler=self.log_listener, 
            level=self.config.log_level
        )
        self.operation_lock = threading.Lock()

        self.job.add_task(self)

    def add_prerequisite(self, prerequisite: "Task") -> None:
        """
        Adds a prerequisite task to the current task.
        """
        self.prerequisites.append(prerequisite)
        prerequisite.subsequent_tasks.append(self)

    def is_prerequisite_fulfilled(self) -> bool:
        """
        Checks if the task can start based on the status of its prerequisites.
        """
        for prerequisite in self.prerequisites:
            if prerequisite.is_success():
                continue
            else:
                self.update(status=TaskStatus.CANCELED, message=f"Task canceled due to incomplete prerequisite: {prerequisite.name}")
                return False
        return True

    def set_passing_args(self, args: dict[str, any]) -> None:
        """
        Sets the passing arguments for the task.
        """
        self.execution.passing_args = args

    def get_running_args(self) -> dict[str, any]:
        """
        Returns a dictionary of arguments from prerequisite tasks.
        """
        args = {
            k: v
            for t in self.prerequisites
            for k, v in t.execution.passing_args.items()
        }
        args['media'] = self.job.media
        return args
    
    def passive_update(self, **kwargs) -> None:
        """
        Updates the task attributes without logging what changes are made.
        This is used when the changes are already logged somewhere else.
        """
        super().update(**kwargs)
        self.job.update(tasks={
            self.tid: kwargs
        })

    def update(self, **kwargs) -> None:
        """
        Updates the task attributes and logs the changes.
        """
        self.logger.info(f"New state: {kwargs}")
        self.passive_update(**kwargs)

    def add_artifact(
        self, name: str, artifact_type: ArtifactType, 
        artifact: str | dict, is_attached: bool = False, 
        attachments: list[dict] | None=None
    ) -> int:
        """
        Add an artifact to the task.
        """
        if artifact_type in (ArtifactType.JSON, ArtifactType.SEGMENTS, ArtifactType.PRODUCT):
            if attachments is not None:
                for attachment in attachments:
                    aid = self.add_artifact(**attachment, is_attached=True)
                    artifact[attachment['name']] = aid
            artifact = json.dumps(artifact)
        elif attachments is not None:
            raise ValueError(f"Attachment is not supported for artifact type {artifact_type}")
        
        aid = self.job.add_artifact(artifact)
        if artifact_type == ArtifactType.PRODUCT:
            self.job.update(result_artifact_index=aid)
        else:
            self.artifacts.append(Artifact(aid=aid, artifact_type=artifact_type, name=name, is_attached=is_attached))
            self.job.update(tasks={
                self.tid: {
                    'artifacts': [a.serialize() for a in self.artifacts]
                }
            })
            self.update(artifacts=[a.serialize() for a in self.artifacts])
        return aid

    def done(self) -> None:
        """
        Cleans up the task.
        """
        super().done()
        self.logger.handlers.clear()