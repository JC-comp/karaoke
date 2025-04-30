from .base import Binder
from ...utils.job import JobType
from ..job import CommandJob

class CommandBinder(Binder):
    def __init__(self, url: str, filepath: str):
        super().__init__()
        self.url = url
        self.filepath = filepath
    
    def bind(self) -> None:
        # We don't need to bind any remote service for command jobs
        return
    
    def get_job_info(self) -> CommandJob:
        if self.url:
            job = CommandJob(job_type=JobType.YOUTUBE, media={'source': self.url})
        else:
            raise NotImplementedError("File input is not implemented yet")
        return job
    
    def close(self) -> None:
        # We don't need to close any remote service for command jobs
        self.logger.debug("Closing CommandBinder")