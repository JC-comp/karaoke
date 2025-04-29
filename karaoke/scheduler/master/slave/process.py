import threading
import json

from ....utils.connection import Connection as Client

class Process:
    def __init__(self, jobId: str, pid: int, client: Client):
        self.jobId = jobId
        self.pid = pid
        self.client = client
        self.returncode = None
        self.exit_event = threading.Event()
    
    def poll(self) -> int:
        """ Check if child process has terminated. Set and return returncode
        attribute."""
        return self.returncode

    def terminate(self) -> None:
        """Terminates the process."""
        # Don't terminate a process that we know has already died.
        if self.returncode is not None:
            return
        self.client.send(json.dumps({
            "action": "terminate",
            "jobId": self.jobId
        }))

    def wait(self) -> None:
        """ Wait for child process to terminate; returns self.returncode."""
        self.exit_event.wait()
        return
    
    def update(self, returncode: int) -> None:
        """ Update the process with the return code."""
        self.returncode = returncode
        self.exit_event.set()
