import multiprocessing

from ...utils.job import JobAction
class ExecuteJob:
    def update(self, **kwargs) -> None:
        raise NotImplementedError("This method should be overridden in subclasses.")
    
    def push(self, target: str, **kwargs) -> None:
        raise NotImplementedError("This method should be overridden in subclasses.")

class ExecuteTask:
    job: ExecuteJob
    def update(self, **kwargs) -> None:
        raise NotImplementedError("This method should be overridden in subclasses.")

    def passive_update(self, **kwargs) -> None:
        raise NotImplementedError("This method should be overridden in subclasses.")
        
    def set_passing_args(self, args: dict) -> None:
        raise NotImplementedError("This method should be overridden in subclasses.")
        
    def add_artifact(self, **kwargs) -> None:
        raise NotImplementedError("This method should be overridden in subclasses.")
        
class ActionCallback:
    def __init__(self, queue: multiprocessing.Queue) -> None:
        self.queue = queue
    
    def get_action(self) -> str:
        action = None
        while not self.queue.empty():
            action = self.queue.get()
        return action

    def check(self, ignore_action: bool) -> None:
        action = self.get_action()
        if action == JobAction.STOP:
            if not ignore_action:
                raise RuntimeError("Job interrupted")