import threading

from ...utils.job import BaseJob, JobAction
from ...utils.config import Config, get_logger


class Binder:
    action: JobAction | None
    listen_thread: threading.Thread | None
    def __init__(self):
        self.logger = get_logger(__name__, Config().log_level)
        self.action = None
        self.listen_thread = None

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
    
    def listen_thread_func(self) -> None:
        """
        Thread function to listen for actions from the job provider.
        """
        raise NotImplementedError()
    
    def listen(self) -> None:
        """
        Listens for actions from the job provider.
        """
        self.listen_thread = threading.Thread(target=self.listen_thread_func)
        self.listen_thread.start()
    
    def update(self, **kwargs) -> None:
        """
        Updates the job status to the job provider.
        """
        raise NotImplementedError()
    
    def close(self) -> None:
        """
        Closes the connection to the job provider.
        """
        if self.listen_thread:
            self.listen_thread.join()