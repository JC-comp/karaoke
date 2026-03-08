import logging

from typing import Protocol, TYPE_CHECKING
from flask_socketio import Namespace
from flask import Request

class SocketRequest(Protocol):
    sid: str

def get_sid(request: Request) -> str:
    from typing import cast
    r = cast(SocketRequest, request)
    return r.sid
    
class LoggingNamespace(Namespace):
    def __init__(self, namespace: str):
        super().__init__(namespace)
        self.logger = logging.getLogger("Namespace" + namespace)