import io
import enum

class TaskStatus(str, enum.Enum):
    PENDING = 'pending'
    QUEUED = 'queued'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SOFT_FAILED = 'soft_failed'
    CANCELED = 'canceled'
    SKIPPED = 'skipped'
    INTERRUPTING = 'interrupting'
    INTERRUPTED = 'interrupted'

class ArtifactType(str, enum.Enum):
    VIDEO = 'video'
    AUDIO = 'audio'
    JSON = 'json'
    TEXT = 'text'
    SEGMENTS = 'segments'

class Artifact:
    def __init__(self, aid: int, name: str, artifact_type: ArtifactType, is_attached: bool):
        """
        Initializes an Artifact instance.
        """
        self.aid = aid
        self.name = name
        self.mType = ArtifactType(artifact_type)
        self.is_attached = is_attached

    def serialize(self) -> dict:
        """
        Serializes the artifact to a dictionary format.
        This is used for sending artifacts over the network.
        """
        return {
            "aid": self.aid,
            "name": self.name,
            "artifact_type": self.mType.value,
            "is_attached": self.is_attached
        }

class BaseTask:
    def __init__(self, tid: str, name: str, message: str, output: io.StringIO, status: str, artifacts: list[str]):
        """
        Initializes a BaseTask instance for a worker to run, 
        or for a scheduler to initiate, using arguments received from the worker.
        """
        self.tid = tid
        self.name = name
        self.message = message
        self.output = output
        self.status = TaskStatus(status)
        self.artifacts = [Artifact(**artifact) for artifact in artifacts]

    def __setattr__(self, name, value):
        if name == "output":
            if isinstance(value, str):
                value = io.StringIO(value)
        elif name == "status":
            value = TaskStatus(value)
        super().__setattr__(name, value)

    def is_pending(self) -> bool:
        """
        Checks if the task is pending.
        """
        return self.status == TaskStatus.PENDING

    def is_running(self) -> bool:
        """
        Checks if the task is currently running.
        """
        return self.status in (TaskStatus.RUNNING, TaskStatus.QUEUED, TaskStatus.INTERRUPTING)
    
    def is_success(self) -> bool:
        """
        Checks if the task has completed successfully.
        """
        return self.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED, TaskStatus.SOFT_FAILED)
    
    def is_interrupting(self) -> bool:
        """
        Checks if the task is in the process of being interrupted.
        """
        return self.status == TaskStatus.INTERRUPTING

    def is_interrupted(self) -> bool:
        """
        Checks if the task has been interrupted.
        """
        return self.status == TaskStatus.INTERRUPTED

    def update(self, **kwargs) -> None:
        """
        Updates the task attributes.
        """
        for key, value in kwargs.items():
            if key == "artifacts":
                parsed = [Artifact(**artifact) for artifact in value]
                value = parsed
            setattr(self, key, value)

    def done(self) -> None:
        """
        Marks the task as done and updates the status accordingly.
        """
        if self.status in (TaskStatus.PENDING, TaskStatus.QUEUED):
            self.status = TaskStatus.CANCELED
            self.message = "Job canceled due to process exit"
        elif self.status == TaskStatus.RUNNING:
            self.status = TaskStatus.INTERRUPTED
            self.message = "Job interrupted due to process exit"
        elif self.status == TaskStatus.INTERRUPTING:
            self.status = TaskStatus.INTERRUPTED
            self.message = "Job interrupted due to process exit"
    
    def serialize(self) -> dict:
        """
        Serializes the task to a dictionary format.
        This is used for sending updates to the client.
        """
        return {
            "tid": self.tid,
            "name": self.name,
            "message": self.message,
            "output": self.output.getvalue(),
            "status": self.status.value,
            "artifacts": [artifact.serialize() for artifact in self.artifacts]
        }