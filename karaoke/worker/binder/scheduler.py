import socket
import json
import threading

from .base import Binder
from ..job import RemoteJob
from ...utils.job import JobAction
from ...utils.connection import Connection
from ...utils.config import Config

class Scheduler(Connection):
    def __init__(self, socket):
        super().__init__(socket)
        self.lock = threading.Lock()
    
    def send(self, message: str) -> None:
        # prevent concurrent access to the socket
        with self.lock:
            super().send(message)

class SchedulerBinder(Binder):
    def __init__(self, jobId):
        super().__init__()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.scheduler = Scheduler(self.socket)
        self.jobId = jobId
    
    def bind(self) -> None:
        config = Config()
        self.logger.debug('Connecting to scheduler')
        self.socket.connect((config.scheduler_host, config.scheduler_port))
        
    def get_job_info(self) -> RemoteJob:
        self.logger.debug('Requesting job info from scheduler')
        self.scheduler.send(json.dumps({
            'role': 'worker',
            'jobId': self.jobId
        }))
        return RemoteJob(binder=self, **self.scheduler.json())
    
    def listen_thread_func(self) -> None:
        while True:
            try:
                data = self.scheduler.json_idle()
                if 'bye' in data:
                    break
                action = data.get('action')
                self.logger.info(f'Action received: {action}')
                if self.action is None:
                    self.action = JobAction(action)
                else:
                    self.logger.warning(f'Action already set: {self.action}, ignoring new action: {action}')
            except Exception as e:
                self.logger.error(f'Error receiving data from scheduler: {e}', exc_info=True)
                break
    
    def update(self, **kwargs) -> None:
        self.logger.debug('Job progress update received, sending to scheduler')
        self.scheduler.send(json.dumps(kwargs))
        
    def close(self) -> None:
        self.logger.debug('Closing connection to scheduler')
        self.scheduler.close()
        super().close()
