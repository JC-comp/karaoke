from .base import Binder
from ..job import CommandJob, RemoteJob
from ...utils.job import JobType, JobAction

class CommandBinder(Binder):
    def __init__(self, url: str, filepath: str):
        super().__init__()
        self.url = url
        self.filepath = filepath
        self.closing = False
    
    def bind(self) -> None:
        # We don't need to bind any remote service for command jobs
        return
    
    def get_job_info(self) -> RemoteJob:
        if self.url:
            job = CommandJob(job_type=JobType.YOUTUBE, media={'source': self.url}, binder=self)
        else:
            raise NotImplementedError("File input is not implemented yet")
        return job
    
    def listen_thread_func(self) -> None:
        while not self.closing:
            print("Command: ", end="")
            command = input()
            try:
                command = JobAction(command)
            except ValueError:
                if self.closing:
                    break
                print(f"Invalid command: {command}")
                print("Available commands: ")
                for action in JobAction:
                    print(f" - {action.name}")
                continue
            self.action = command
            print('OK')
            self.logger.info(f"Command received: {command}")
    
    def update(self, **kwargs) -> None:
        tasks = kwargs.get('tasks', {})
        for task in tasks.values():
            message = task.get('message', '')
            if message and '\r' in message:
                print(message, end='', flush=True)

    def close(self) -> None:
        # We don't need to close any remote service for command jobs
        self.logger.debug("Closing CommandBinder")
        self.closing = True
        print()
        print()
        print('Job finished, press enter to exit')
        super().close()