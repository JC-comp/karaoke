import io
import multiprocessing
import logging
import subprocess
import time
import threading

from contextlib import redirect_stderr, redirect_stdout
from .base import ExecuteTask
from .runner_log import SyncHandler
from .exception import SoftFailure
from ...utils.config import Config
from ...utils.task import ArtifactType
from ...utils.task import TaskStatus

class Execution:
    task: ExecuteTask
    logger: logging.Logger
    def __init__(self, name: str, config: Config) -> None:
        self.passing_args: dict[str, any] = {}
        self.name = name
        self.config = config
        self.thread_exception = None

    def update_job(self, **kwargs) -> None:
        self.task.job.update(**kwargs)

    def update(self, **kwargs) -> None:
        self.task.update(**kwargs)
    
    def set_passing_args(self, args: dict) -> None:
        self.task.set_passing_args(args)

    def passive_update(self, **kwargs) -> None:
        self.task.passive_update(**kwargs)

    def add_artifact(
        self, 
        name: str, artifact_type: ArtifactType, 
        artifact: str | dict,
        attachments: dict | None = None
    ) -> None:
        self.task.add_artifact(name=name, artifact_type=artifact_type, artifact=artifact, attachments=attachments)

    def _start(self, args: dict) -> None:
        raise NotImplementedError("You must implement the _start method")

    def start(self, task: ExecuteTask, logger: logging.Logger, args: dict, handler_args: list[multiprocessing.Queue, int] = None) -> None:
        self.task = task
        self.logger = logger
        if handler_args: 
            message_queue, level = handler_args
            handler = SyncHandler(message_queue)
            logger.setLevel(level)
            logger.addHandler(handler)
        self.logger.info(f"----- {self.name} -----\n")
        self.logger.debug(f"Arguments: {args}")
        self.update(status=TaskStatus.RUNNING)
        try:
            self._start(args)
            self.update(status=TaskStatus.COMPLETED)
            self.set_passing_args(self.passing_args)
        except SoftFailure as e:
            self.logger.info(f"Soft failure in task {self.name}: {str(e)}")
            self.set_passing_args(self.passing_args)
            self.update(status=TaskStatus.SOFT_FAILED, message=str(e))
        except Exception as e:
            self.logger.error(f"Error in task {self.name}", exc_info=True)
            self.update(status=TaskStatus.FAILED, message=str(e))
        self.logger.info(f"----- {self.name} completed -----\n")
    
    def record_buffer_time(self, buffer: str, new_message: str) -> None:
        """
        Records the time taken by the buffer to process.
        """
        buffer += new_message
        lines = buffer.split('\n')
        buffer = lines.pop()
        for line in lines:
            self.logger.info(line)

        return buffer

    def _external_buffer_wrapper(self, target, args) -> None:
        """
        Wrapper for the external task to and capture stdout and stderr.
        """
        progress_buffer = io.StringIO()
        thread = threading.Thread(target=target, args=(progress_buffer, args))
        thread.daemon = True
        thread.start()
        last_pos = 0
        cached_message = None
        buffer = ''
        progress = progress_buffer.getvalue()
        while thread.is_alive() or last_pos != len(progress):
            progress = progress_buffer.getvalue()
            lines = progress.split('\n')
            if len(lines) == 1 or '\r' in lines[-1]:
                lastline = lines[-1]
            else:
                lastline = lines[-2]
            messages = lastline.split('\r')
            if len(messages) == 1:
                message = messages[-1]
            else:
                message = messages[-2]
            
            if cached_message != message:
                cached_message = message
                self.passive_update(message=message)
            
            if last_pos != len(progress):
                new_message = progress[last_pos:]
                buffer = self.record_buffer_time(buffer, new_message)
                last_pos = len(progress)
            time.sleep(0.1)
        if buffer:
            self.record_buffer_time(buffer, '\n')

        if self.thread_exception:
            raise self.thread_exception

    def _execute_external_command_wrapper(self, progress_buffer: io.StringIO, cmd) -> None:
        """
        Wrapper for the external task to handle exceptions. Capture stdout and stderr
        and redirect them to the progress buffer.
        """
        buffer = b''
        try:
            p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
            while p.poll() is None:
                output = p.stdout.read(32)
                try:
                    buffer += output
                    progress_buffer.write(buffer.decode())
                    buffer = b''
                except:
                    self.logger.error(f"Failed to decode buffer: {buffer}", exc_info=True)
            if p.returncode != 0:
                raise subprocess.CalledProcessError(p.returncode, cmd)
        except Exception as e:
            self.thread_exception = e
        finally:
            try:
                progress_buffer.write(buffer.decode())
            except:
                self.logger.error(f"Failed to decode buffer: {buffer}", exc_info=True)
    
    def _start_external_command(self, cmd) -> None:
        """
        Starts an external task in a separate thread and captures its output in real-time.
        """
        self._external_buffer_wrapper(self._execute_external_command_wrapper, cmd)
    
    def _external_long_running_task(self, args):
        """
        Starts an external long-running task in a separate thread.
        """
        raise NotImplementedError("You must implement the _external_long_running_task method")
        
    def _execute_external_long_running_task_wrapper(self, progress_buffer: io.StringIO, args) -> None:
        try:
            with redirect_stdout(progress_buffer), redirect_stderr(progress_buffer):
                self._external_long_running_task(args)
        except Exception as e:
            self.thread_exception = e
        
    def _start_external_long_running_task(self, args) -> None:
        self._external_buffer_wrapper(self._execute_external_long_running_task_wrapper, args)
