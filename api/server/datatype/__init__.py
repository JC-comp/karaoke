import typing

from flask import Flask
from redis import Redis
from flask_socketio import SocketIO

from .queue import QueueItem, QueueType
if typing.TYPE_CHECKING:
    from ..websocket.room import RoomManager
    from ..websocket.job import JobManager
    from ..airflow import Storage

class MyFlaskApp(Flask):
    redis: Redis
    socketio: SocketIO
    roomManager: "RoomManager"
    jobManager: "JobManager"
    storage: "Storage"

__all__ = [
    'QueueItem',
    'QueueType',
    'MyFlaskApp'
]