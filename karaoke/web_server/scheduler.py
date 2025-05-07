import socket
import json
import os

from flask_socketio import SocketIO
from ..utils.connection import Connection
from ..utils.config import Config, get_logger
from ..utils.job import JobType

class SchedulerBinder(Connection):
    """
    SchedulerBinder is a class that handles the connection to the scheduler.
    It is used by the web server to communicate with the scheduler for client requests.
    """
    def __init__(self):
        mSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        super().__init__(mSocket)
        self.config = Config()
        self.logger = get_logger(__name__, self.config.log_level)
        self.interrupt = False
        self.latest_job: dict[str, str] = {}
        
    def bind(self) -> None:
        """
        Bind the socket to the scheduler.
        """
        self.socket.connect((self.config.scheduler_host, self.config.scheduler_port))

    def index(self) -> list[dict, int]:
        """
        Send a message to the scheduler to retrieve the index info.
        """
        self.logger.debug('Sending index request to scheduler')
        self.send(json.dumps({
            'role': 'user',
            'action': 'index'
        }))
        jobs = self.json()
        return jobs
       
    def get_artifact(self, jobId: str, artifact: int) -> dict:
        """
        Retrieve an artifact from the scheduler.
        Returns the artifact path and type.
        """
        self.logger.debug(f'Getting artifact for job ID: {jobId}, artifact: {artifact}')
        self.send(json.dumps({
            'role': 'user',
            'action': 'artifact',
            'jobId': jobId,
            'artifact': artifact
        }))
        artifact_result = self.json()
        return artifact_result

    def create_by_YT(self, youtube_link: str) -> list[dict, int]:
        """
        Create a job by YouTube link.
        Returns a dictionary with the job information and the status code.
        """
        self.logger.debug(f'Creating job by YouTube link: {youtube_link}')
        self.send(json.dumps({
            'role': 'user',
            'action': 'submit',
            'job': {
                'job_type': JobType.YOUTUBE.value,
                'media': {
                    'source': youtube_link
                }
            }
        }))

        self.logger.debug('Waiting for response from scheduler')
        job = self.json()
        
        return job

    def create_by_file(self, file_path: str) -> list[dict, int]:
        return 'Not implemented yet', 501

    def send_progress_to_sid(self, socketio: SocketIO, sid: str, namespace: str) -> None:
        """
        Send current progress to the new client.
        """
        if self.latest_job:
            for job in self.latest_job.values():
                socketio.emit('progress', job, room=sid, namespace=namespace)

    def listen_progress_by_jobId(self, socketio: SocketIO, jobId: str, namespace: str) -> None:
        """
        Listen for progress updates from the scheduler and emit them to the client.
        """
        try:
            self.logger.debug(f'Getting progress by job ID: {jobId}')
            self.send(json.dumps({
                'role': 'user',
                'action': 'query',
                'jobId': jobId
            }))
            while not self.interrupt:
                latest_progress = self.json()
                self.latest_job[latest_progress.get('jid')] = latest_progress
                socketio.emit('progress', latest_progress, room=jobId, namespace=namespace)
        except Exception as e:
            if not self.interrupt:
                self.logger.error(f'Error getting progress: {str(e)}')
                socketio.emit('error', {'message': str(e)}, room=jobId, namespace=namespace)
        self.logger.debug('Connection interrupted, stopping progress updates')

    def close(self) -> None:
        """
        Close the connection to the scheduler.
        """
        self.interrupt = True
        super().close()
