import logging
import traceback
import multiprocessing
import json

from .base import ActionCallback
from ...utils.connection import Connection

class BaseHandler(logging.Handler):
    def push(self, target: str, ignore_action: bool, **kwargs) -> None:
        """
        Pushes a log message to the handler.
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")

class SyncHandler(logging.Handler):
    def __init__(self, message_queue: multiprocessing.Queue, action_queue: multiprocessing.Queue) -> None:
        super().__init__()
        self.message_queue = message_queue
        self.action_callback = ActionCallback(action_queue)

    def emit(self, record: logging.LogRecord) -> None:
        levelname = record.levelname.lower()
        message = self.format(record)
        exc_info = record.exc_info
        if 'ignore_action' in record.__dict__:
            ignore_action = record.ignore_action
        else:
            ignore_action = False
        self.push(levelname, ignore_action=ignore_action, message=message)
        if exc_info:
            message = traceback.format_exception(*exc_info)
            for line in message:
                self.push(levelname, ignore_action=ignore_action, message=line)

    def push(self, target: str, ignore_action: bool, **kwargs) -> None:
        self.message_queue.put({
            'target': target,
            'body': kwargs
        })
        self.action_callback.check(ignore_action=ignore_action)

class DaemonHandler(logging.Handler):
    def __init__(self, connection: Connection) -> None:
        super().__init__()
        self.connection = connection

    def emit(self, record: logging.LogRecord) -> None:
        levelname = record.levelname.lower()
        message = self.format(record)
        exc_info = record.exc_info
        ignore_action = False
        self.push(levelname, ignore_action=ignore_action, message=message)
        if exc_info:
            message = traceback.format_exception(*exc_info)
            for line in message:
                self.push(levelname, ignore_action=ignore_action, message=line)

    def push(self, target: str, ignore_action: bool, **kwargs) -> None:
        try:
            self.connection.send(json.dumps({
                'target': target,
                'body': kwargs
            }))
        except Exception as e:
            if not ignore_action:
                raise e