import logging
import traceback
import multiprocessing

class SyncHandler(logging.Handler):
    def __init__(self, message_queue: multiprocessing.Queue) -> None:
        super().__init__()
        self.message_queue = message_queue

    def emit(self, record: logging.LogRecord) -> None:
        levelname = record.levelname.lower()
        message = self.format(record)
        exc_info = record.exc_info
        self.push(levelname, message=message)
        if exc_info:
            message = traceback.format_exception(*exc_info)
            for line in message:
                self.push(levelname, message=line)
            
    def push(self, target: str, **kwargs) -> None:
        self.message_queue.put({
            'target': target,
            'body': kwargs
        })