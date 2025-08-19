from flask_socketio import SocketIO
from .scheduler import BinderManager, SchedulerNamespace
from ..scheduler import SchedulerBinder
from ...utils.config import get_logger, Config

config = Config()

class JobBinderManager(BinderManager):
    """
    SchedulerBinderManager manages the monitoring of jobs and the clients connected to them.
    """
    def __init__(self, namespace: str, socketio: SocketIO):
        super().__init__(
            namespace=namespace,
            socketio=socketio,
            logger=get_logger(__name__, config.log_level)
        )

    def _send_latest_progress(self, scheduler: SchedulerBinder, sid: str) -> None:
        scheduler.send_progress_to_sid(self.socketio, sid, self.namespace)
        self.socketio.emit('joined', 'ok', room=sid, namespace=self.namespace)
   
    def _serving_progress_update(self, scheduler: SchedulerBinder, job_id: str) -> None:
        """
        Serve the progress update to the client via socketio.
        """
        self.socketio.emit('joined', 'ok', room=job_id, namespace=self.namespace)
        scheduler.listen_progress_by_jobId(self.socketio, job_id, self.namespace)
        # The only case where the scheduler is closed is when scheduler is gone first or all
        # clients are gone, clients are notified within the scheduler if an error occurs, 
        # so we don't need to notify the clients here

class JobNamespace(SchedulerNamespace):
    def __init__(self, socketio: SocketIO):
        namespace = '/job'
        super().__init__(
            namespace=namespace,
            manager=JobBinderManager(namespace, socketio),
            logger=get_logger(__name__, config.log_level)
        )
