from redis import Redis
from flask_socketio import SocketIO
from .room import RoomNamespace
from .job import JobNamespace
from ..config import config
from ..datatype import MyFlaskApp
from ..airflow import Storage
from ..websocket.room import RoomManager
from ..websocket.job import JobManager

def prepare_shared_environment(app: MyFlaskApp):
    if not hasattr(app, "redis"):
        app.redis = Redis.from_url(config.server.socketio_message_queue, decode_responses=True)
    
def prepare_websocket_environment(app: MyFlaskApp):
    if not hasattr(app, "socketio"):
        kargs = { }
        if config.server.socketio_cors_allowed_origins:
            kargs['cors_allowed_origins'] = config.server.socketio_cors_allowed_origins
        app.socketio = SocketIO(
            app, path=config.server.socketio_path,
            message_queue=config.server.socketio_message_queue, async_mode='gevent',
            **kargs
        )

def prepare_room_environment(app: MyFlaskApp):
    prepare_shared_environment(app)
    prepare_websocket_environment(app)
    if not hasattr(app, "roomManager"):
        app.roomManager = RoomManager(app.redis)
    app.socketio.on_namespace(RoomNamespace(app.roomManager))


def prepare_job_environment(app: MyFlaskApp):
    prepare_shared_environment(app)
    prepare_websocket_environment(app)
    if not hasattr(app, "jobManager"):
        app.jobManager = JobManager(app.redis)
    app.socketio.on_namespace(JobNamespace(app.jobManager))

def prepare_artifact_environment(app: MyFlaskApp):
    if not hasattr(app, "storage"):
        app.storage = Storage()

                                 
__all__ = [
    "prepare_room_environment",
    "prepare_job_environment",
    "prepare_artifact_environment"
]