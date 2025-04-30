from ...utils.task import ArtifactType

class ExecuteJob:
    def update(self, **kwargs) -> None:
        raise NotImplementedError("This method should be overridden in subclasses.")
    
    def push(self, target: str, **kwargs) -> None:
        raise NotImplementedError("This method should be overridden in subclasses.")

class ExecuteTask:
    job: ExecuteJob
    def update(self, **kwargs) -> None:
        raise NotImplementedError("This method should be overridden in subclasses.")

    def passive_update(self, **kwargs) -> None:
        raise NotImplementedError("This method should be overridden in subclasses.")
        
    
    def set_passing_args(self, args: dict) -> None:
        raise NotImplementedError("This method should be overridden in subclasses.")
        
    def add_artifact(self, name: str, artifact_type: ArtifactType, artifact: str | dict, attachments: dict | None):
        raise NotImplementedError("This method should be overridden in subclasses.")
        