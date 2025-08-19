import uuid
import socket
import time
import threading
import json
import subprocess

from ..utils.connection import Connection
from ..utils.config import get_logger, Config

class Scheduler(Connection):
    def __init__(self, socket):
        super().__init__(socket)
        self.lock = threading.Lock()
    
    def send(self, message: str) -> None:
        # prevent concurrent access to the socket
        with self.lock:
            super().send(message)

class SchedulerSlave:
    def __init__(self, config: Config) -> None:
        self.slave_id = str(uuid.uuid4())
        self.config = config
        self.logger = get_logger(__name__, config.log_level)
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.scheduler = Scheduler(self.socket)

        self.process_lock = threading.Lock()
        self.processes: dict[str, subprocess.Popen] = {}

    def send_message(self, message: dict) -> None:
        """
        Send a message to the scheduler.
        """
        try:
            self.scheduler.send(json.dumps(message))
        except Exception as e:
            self.logger.error(f"Error sending message to scheduler: {e}", exc_info=True)

    def set_idle(self, is_working: bool) -> None:
        """
        Send an idle message to the scheduler.
        """
        self.send_message({
            'action': 'slave',
            'working': is_working
        })

    def spawn_process(self, jobId: str) -> None:
        """
        Spawn a new process to handle the job.
        We use the lock to ensure that only one process is spawned at a time.
        """
        with self.process_lock:
            try:
                process = subprocess.Popen([
                    'python',
                    '-m',
                    'karaoke.worker.main',
                    '--jobId',
                    jobId,
                ])
                self.logger.info(f'Spawned process {process.pid}')
            except Exception as e:
                self.logger.error(f"Error spawning process: {e}", exc_info=True)
                self.send_message({
                    'action': 'submit',
                    'jobId': jobId,
                    'pid': None,
                })
                self.set_idle(is_working=False)
                return
                
            self.processes[jobId] = process
            self.send_message({
                'action': 'submit',
                'jobId': jobId,
                'pid': process.pid,
            })

            try:
                process.wait()
            except Exception as e:
                self.logger.error(f"Error waiting for process: {e}", exc_info=True)

            # Handle process exit
            del self.processes[jobId]
            self.send_message({
                'action': 'update',
                'jobId': jobId,
                'returncode': process.returncode,
            })
            self.set_idle(is_working=False)

    def terminate_process(self, jobId: str) -> None:
        """
        Terminate the process associated with the jobId.
        """
        process = self.processes.get(jobId)
        if process:
            self.logger.info(f"Terminating process {process.pid} for job {jobId}")
            process.terminate()
        else:
            self.logger.warning(f"No process found for job {jobId}")
    
    def connect(self) -> None:
        """
        Connect to the scheduler and send a registration message.
        """
        self.logger.info(f'Slave {self.slave_id} connecting to scheduler {self.config.scheduler_host}:{self.config.scheduler_port}')
        self.socket.connect((self.config.scheduler_host, self.config.scheduler_port))
        self.scheduler.send(json.dumps({
            'role': 'slave',
            'slaveId': self.slave_id,
        }))

    def handle_message(self, message: dict) -> None:
        action = message.get('action')
        jobId = message.get('jobId')
        if action == 'submit':
            self.set_idle(is_working=True)
            self.spawn_process(jobId)
        elif action == 'terminate':
            self.terminate_process(jobId)
        else:
            self.logger.warning(f"Unknown action: {action}")

    def listen(self) -> None:
        """
        Listen for messages from the scheduler.
        """
        while True:
            try:
                message = self.scheduler.json()
                threading.Thread(target=self.handle_message, args=(message,)).start()
            except Exception as e:
                self.logger.error(f"Error receiving message from scheduler: {e}", exc_info=True)
                break

    def close(self) -> None:
        """
        Close the connection to the scheduler.
        """
        self.logger.info(f'Slave {self.slave_id} closing connection to scheduler')
        self.scheduler.close()

if __name__ == "__main__":
    config = Config()
    slave = None
    terminated = False
    while True:
        try:
            slave = SchedulerSlave(config)
            slave.connect()
            slave.listen()
        except KeyboardInterrupt:
            terminated = True
            break
        except Exception as e:
            if slave:
                slave.logger.error(f"Error connecting to scheduler: {e}", exc_info=True)
            else:
                print(f"Error connecting to scheduler: {e}", exc_info=True)
        finally:
            if slave:
                slave.close()
                if not terminated:
                    slave.logger.info("Retrying in 5 seconds...")
                    time.sleep(5)