import multiprocessing
import time

from .job import DaemonJob
from .tasks.task import Task
from .tasks.seprate import SeperateVocal, SeperateInstrument
from .tasks.transcript import TranscriptLyrics
from .tasks.align import AlignLyrics
from ..utils.config import get_logger, Config

DAEMON_LIST: list[type[Task]] = [SeperateVocal, SeperateInstrument, TranscriptLyrics, AlignLyrics]


def start_execution(task_cls: type[Task]) -> None:    
    fake_job = DaemonJob()
    task = task_cls(fake_job)
    execution = task.execution
    execution.start_daemon_server()

def stop_daemon() -> None:
    fake_job = DaemonJob()
    for task_cls in DAEMON_LIST:
        task = task_cls(fake_job)
        execution = task.execution
        execution.stop_daemon_server()
    
def run_daemon() -> None:
    config = Config()
    logger = get_logger(__name__, config.log_level)
    process_list: list[multiprocessing.Process] = []
    for task_cls in DAEMON_LIST:
        logger.info(f"Starting daemon for task {task_cls.__name__}")
        process = multiprocessing.Process(
            target=start_execution, args=(task_cls,)
        )
        process.start()
        process_list.append(process)

    logger.info("Daemon processes started")
    print("Press Ctrl+C to stop the daemon processes")
    while True:
        try:
            for process in process_list:
                process.join()
                logger.info(f"Daemon for task {process.name} has exited")
            break
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, exiting...")
            stop_daemon()
