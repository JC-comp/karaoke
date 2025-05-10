import logging
import traceback
import multiprocessing

from ...utils.job import JobAction

class SyncHandler(logging.Handler):
    def __init__(self, message_queue: multiprocessing.Queue, action_queue: multiprocessing.Queue) -> None:
        super().__init__()
        self.message_queue = message_queue
        self.action_queue = action_queue

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

    def get_action(self) -> str:
        action = None
        while not self.action_queue.empty():
            action = self.action_queue.get()
        return action

    def push(self, target: str, ignore_action: bool, **kwargs) -> None:
        self.message_queue.put({
            'target': target,
            'body': kwargs
        })
        action = self.get_action()
        if action == JobAction.STOP:
            if not ignore_action:
                raise RuntimeError("Job interrupted")
            