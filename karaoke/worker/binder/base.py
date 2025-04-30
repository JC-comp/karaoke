from ...utils.job import BaseJob
from ...utils.config import Config, get_logger


class Binder:
    def __init__(self):
        self.logger = get_logger(__name__, Config().log_level)

    def get_job_info(self) -> BaseJob:
        """
        Retrieves job information from the job provider.
        """
        raise NotImplementedError()
    
    def bind(self) -> None:
        """
        Binds the worker to the job provider.
        """
        raise NotImplementedError()
    
    def update(self, **kwargs) -> None:
        """
        Updates the job status to the job provider.
        """
        raise NotImplementedError()
    
    def close(self) -> None:
        """
        Closes the connection to the job provider.
        """
        raise NotImplementedError()