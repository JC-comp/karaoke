import enum
import os
import threading
import json

from .task import BaseTask, Artifact
from ..utils.config import Config

class JobType(str, enum.Enum):
    YOUTUBE = "youtube"
    LOCAL = "local"

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    CREATED = "created"
    RUNNING = "running"
    INTERRUPTING = "interrupting"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

class Media:
    def __init__(self, source: str, metadata: dict[str, str]):
        self.source = source
        self.metadata = metadata

    def update(self, **kwargs: dict):
        """
        Updates the media with partial support.
        """
        for key, value in kwargs.items():
            if key == "metadata":
                self.update_metadata(value)
            else:
                setattr(self, key, value)

    def update_metadata(self, metadata: dict[str, str]) -> bool:
        """
        Updates the metadata of the media.
        Returns True if any metadata was updated, False otherwise.
        """
        if self.metadata is None:
            self.metadata = metadata
            return True
        updated = False
        for key, value in metadata.items():
            if value != self.metadata.get(key):
                self.metadata[key] = value
                updated = True
        return updated
    
    def serialize(self) -> dict:
        """
        Serializes the media to a dictionary format.
        This is used for sending media information over the network.
        """
        return {
            "source": self.source,
            "metadata": self.metadata
        }
    
    def __str__(self):
        return f"Media(source={self.source}, metadata={self.metadata})"
    
class BaseJob:
    def __init__(self,
        jid: str, created_at: float, started_at: float, finished_at: float,
        job_type: str, media: dict[str, str],
        status: str, message: str, isProcessExited: bool, last_update: float, 
        tasks: dict[dict], result_artifact_index: int, artifacts: list[str] | None = None
    ):
        """
        Initializes a BaseJob instance from the client request 
        or for a worker to initiate jobs using arguments received from the scheduler.
        """
        self.config = Config()
        self.jid = jid
        self.created_at = created_at
        self.started_at = started_at
        self.finished_at = finished_at
        self.job_type: JobType = job_type
        self.media: Media = media
        
        self.status: JobStatus = status
        self.message: str = message
        self.isProcessExited = isProcessExited
        self.last_update = last_update

        self.operation_lock = threading.RLock()
        self.tasks: dict[str, BaseTask] = {tid: BaseTask(**task) for tid, task in tasks.items()}
        self.artifacts: list[str] = artifacts if artifacts is not None else []
        self.result_artifact_index: int = result_artifact_index

    def add_task(self, task: BaseTask) -> None:
        """
        Adds a task to the job.
        """
        self.tasks[task.tid] = task

    def add_artifact(self, artifact: str) -> int:
        """
        Adds an artifact to the job and returns the index of the artifact.
        """
        with self.operation_lock:
            self.artifacts.append(artifact)
            aid = len(self.artifacts) - 1
        self.update(artifacts=self.artifacts)
        return aid
    
    def get_artifact(self, index: int) -> Artifact:
        """
        Gets an artifact from the job by index.
        """
        if index >= len(self.artifacts):
            return None
        return self.artifacts[index]

    def done(self) -> None:
        """
        Marks the job as done and updates the status of all tasks.
        """
        for task in self.tasks.values():
            task.done()

    def update(self, **progress: dict) -> None:
        """
        Updates the job with the given progress.
        """
        raise NotImplementedError("update() method must be implemented in subclasses")
    
    def __setattr__(self, name, value):
        """
        Converts specific attributes received from the client to their respective types.
        """
        if name == "job_type":
            value = JobType(value)
        elif name == "status":
            value = JobStatus(value)
        elif name == "media":
            if isinstance(value, dict):
                value = Media(**value)
        elif name == "status":
            value = JobStatus(value)
        elif name == "tasks":
            converted = {}
            for tid, task in value.items():
                if isinstance(task, dict):
                    task = BaseTask(**task)
                converted[tid] = task
            value = converted
        super().__setattr__(name, value)

    def serialize(self) -> dict:
        """
        Serializes the job to a dictionary format.
        This is used for sending job information over the network.
        """
        return {
            "jid": self.jid,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "job_type": self.job_type.value,
            "media": self.media.serialize(),
            "status": self.status.value,
            "message": self.message,
            "isProcessExited": self.isProcessExited,
            "last_update": self.last_update,
            "tasks": {task_id: task.serialize() for task_id, task in self.tasks.items()},
            "result_artifact_index": self.result_artifact_index
        }

    def dump_serialize(self) -> str:
        """
        Serializes the job to a dictionary format with all attributes.
        This is used for dumping the job to a file.
        """
        result = self.serialize()
        result.update({
            "artifacts": self.artifacts,
        })
        return result

    def dump(self):
        """
        Dumps the job to a file.
        """
        location = os.path.join(self.config.media_path, self.jid + '.json')
        with open(location, 'w') as f:
            json.dump(self.dump_serialize(), f)