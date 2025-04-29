import threading

from .binder import SlaveBinder
from .process import Process
from ....utils.config import Config, get_logger
from ....utils.connection import Connection as Client

class SlaveManager:
    def __init__(self, config: Config):
        self.operation_lock = threading.Lock()
        self.config = config
        self.logger = get_logger(__name__, config.log_level)
        self.slaves: list[SlaveBinder] = []

    def submit(self, jobId: str) -> Process:
        """
        Submits a job to the slave
        """
        with self.operation_lock:
            if not self.slaves:
                raise RuntimeError("No slaves available")
            target_index = len(self.slaves) - 1
            while target_index > 0:
                if self.slaves[target_index].working:
                    target_index -= 1
                else:
                    break

            slave = self.slaves.pop(target_index)
            self.slaves.append(slave)
            return slave.submit(jobId)

    def add_slave(self, slave_id: str, client: Client) -> None:
        """
        Adds a slave
        """
        slave = SlaveBinder(slave_id, self.config, client)
        with self.operation_lock:
            self.slaves.append(slave)
        try:
            slave.serve()
        except Exception as e:
            self.logger.error(f"Failed to serve slave {slave.slave_id}: {e}", exc_info=True)
        finally:
            self.remove_slave(slave)

    def remove_slave(self, slave: SlaveBinder) -> None:
        """
        Removes a slave
        """
        slave.close()
        with self.operation_lock:
            if slave in self.slaves:
                self.slaves.remove(slave)