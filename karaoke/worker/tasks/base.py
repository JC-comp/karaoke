import multiprocessing

from ...utils.job import JobAction
class ExecuteJob:
    def update(self, **kwargs) -> None:
        raise NotImplementedError("This method should be overridden in subclasses.")
    
    def push(self, target: str, **kwargs) -> None:
        raise NotImplementedError("This method should be overridden in subclasses.")

class ExecuteTask:
    def __init__(self, job: ExecuteJob) -> None:
        super().__init__()
        self.job = job

    def update(self, **kwargs) -> None:
        self.push('update', **kwargs)
    
    def set_passing_args(self, args: dict) -> None:
        self.push('passing_args', args=args)

    def passive_update(self, **kwargs) -> None:
        self.push('passive_update', **kwargs)

    def add_artifact(self, **kwargs) -> None:
        self.push('artifact', **kwargs)

    def push(self, target: str, **kwargs) -> None:
        self.job.push(target, **kwargs)

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