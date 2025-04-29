import threading
import json

from .process import Process
from ....utils.config import Config, get_logger
from ....utils.connection import Connection as Client

class SlaveBinder:
    def __init__(self, slave_id: str, config: Config, client: Client):
        self.slave_id = slave_id
        self.client = client
        self.logger = get_logger(__name__, config.log_level)
        self.submit_events: dict[str, threading.Event] = {}
        self.processes: dict[str, Process] = {}
        self.operation_lock = threading.Lock()
        self.working = False
        
    def submit(self, jobId: str) -> Process:
        lock = threading.Event()
        with self.operation_lock:
            self.submit_events[jobId] = lock
        self.client.send(json.dumps({
            "action": "submit",
            "jobId": jobId
        }))
        lock.wait()
        with self.operation_lock:
            del self.submit_events[jobId]
        if jobId not in self.processes:
            raise RuntimeError(f"Failed to submit job {jobId}")
        return self.processes[jobId]

    def serve(self) -> None:
        while True:
            message = self.client.json()
            action = message.get("action")
            if action == "submit":
                jobId = message.get("jobId")
                pid = message.get("pid")
                with self.operation_lock:
                    if jobId not in self.submit_events:
                        raise RuntimeError(f"Job {jobId} is not ready to be submitted")
                    if pid is not None:
                        self.processes[jobId] = Process(jobId, pid, self.client)
                        self.submit_events[jobId].set()
            elif action == "update":
                jobId = message.get("jobId")
                returncode = message.get("returncode")
                with self.operation_lock:
                    if jobId in self.submit_events:
                        self.submit_events[jobId].set()
                        del self.submit_events[jobId]
                        raise RuntimeError(f"Job {jobId} is not running")
                    if jobId not in self.processes:
                        raise RuntimeError(f"Job {jobId} is not running")
                    process = self.processes[jobId]
                    process.update(returncode)
                    del self.processes[jobId]
            elif action == "slave":
                working = message.get("working")
                self.working = working
            else:
                self.logger.error(f"Unknown action: {action}")

    def close(self) -> None:
        with self.operation_lock:
            self.client.close()
            for jobId, event in self.submit_events.items():
                event.set()
            for jobId, process in self.processes.items():
                process.update(-1)
            