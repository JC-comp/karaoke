import io
import multiprocessing
import logging
import subprocess

from contextlib import redirect_stderr, redirect_stdout
from .base import ExecuteTask
from .runner_log import SyncHandler
from .exception import SoftFailure
from ...utils.config import Config, get_logger
from ...utils.task import ArtifactType
from ...utils.task import TaskStatus

class ProgressBuffer(io.StringIO):
    def __init__(self, execution: "Execution") -> None:
        super().__init__()
        self.execution = execution
        self.progress_buffer = ''

    def record_buffer_time(self) -> None:
        """
        Records the time taken by the buffer to process.
        """
        buffer = self.progress_buffer
        lines = buffer.split('\n')
        self.progress_buffer = lines.pop()
        for line in lines:
            self.execution.logger.info(line)

    def update_progress(self) -> None:
        lines = self.progress_buffer.split('\n')
        if len(lines) == 1 or '\r' in lines[-1]:
            lastline = lines[-1]
        else:
            lastline = lines[-2]
        messages = lastline.split('\r')
        if len(messages) == 1:
            message = messages[-1]
        else:
            message = messages[-2]
        
        if message.strip():
            if '\r' in lastline:
                message += '\r'
            self.execution.passive_update(message=message)

    def write(self, s: str) -> int:
        self.progress_buffer += s
        self.update_progress()
        self.record_buffer_time()
        return super().write(s)
    
    def flush_progress(self) -> None:
        if self.progress_buffer:
            self.progress_buffer += '\n'
        self.update_progress()
        self.record_buffer_time()
        self.truncate(0)
        self.seek(0)
        
class Execution:
    task: ExecuteTask
    def __init__(self, name: str, config: Config) -> None:
        self.passing_args: dict[str, any] = {}
        self.name = name
        self.config = config
        self.logger = get_logger(__name__, config.log_level)
        self.progress_buffer = ProgressBuffer(self)
        self.thread_exception = None
        self.args_queue = multiprocessing.Queue()

    def update_job(self, **kwargs) -> None:
        self.task.job.update(**kwargs)

    def update(self, **kwargs) -> None:
        self.task.update(**kwargs)
    
    def set_passing_args(self, args: dict) -> None:
        self.task.set_passing_args(args)

    def passive_update(self, **kwargs) -> None:
        self.task.passive_update(**kwargs)

    def add_artifact(self,  **kwargs) -> None:
        self.task.add_artifact(**kwargs)

    def _start(self, args: dict) -> None:
        raise NotImplementedError("You must implement the _start method")
    
    def _preload(self) -> None:
        """
        Preload any resources needed for the task.
        """
        self.logger.info(f"No preloading required for {self.name}")
        return False

    def run(self, args: dict) -> None:
        self.args_queue.put(args)
    
    def cancel(self) -> None:
        self.args_queue.put(None)

    def start(self, task: ExecuteTask, logger: logging.Logger, args: dict = None, handler_args: list[multiprocessing.Queue, multiprocessing.Queue, int] = None) -> None:
        self.task = task
        self.logger = logger
        if handler_args: 
            message_queue, action_queue, level = handler_args
            handler = SyncHandler(message_queue, action_queue)
            logger.setLevel(level)
            logger.addHandler(handler)
        try:
            self.logger.info(f"----- {self.name} -----\n")
            has_preloaded = self._external_buffer_wrapper(self._execute_external_long_running_task_wrapper, (self._preload, None))
            if args is None:
                self.logger.info(f"Task {self.name} waiting for arguments to be queued")
                if has_preloaded and self.args_queue.empty():
                    self.passive_update(message="Preloading completed, waiting for prerequisites")
                args = self.args_queue.get()
            if args is None:
                self.logger.info(f"Task {self.name} stopped without getting arguments")
            else:
                self.update(status=TaskStatus.RUNNING)
                self.logger.debug(f"Arguments: {args}")
                self._start(args)
                self.update(status=TaskStatus.COMPLETED)
                self.set_passing_args(self.passing_args)
        except SoftFailure as e:
            self.logger.info(f"Soft failure in task {self.name}: {str(e)}", extra={'ignore_action': True})
            self.set_passing_args(self.passing_args)
            self.update(status=TaskStatus.SOFT_FAILED, message=str(e))
        except Exception as e:
            self.logger.error(f"Error in task {self.name}", exc_info=True, extra={'ignore_action': True})
            self.update(status=TaskStatus.FAILED, message=str(e))
        self.logger.info(f"----- {self.name} completed -----\n", extra={'ignore_action': True})
    
    def stop(self) -> None:
        self.cancel()

    def _external_buffer_wrapper(self, target, args) -> None:
        """
        Wrapper for the external task to and capture stdout and stderr.
        """
        progress_buffer = self.progress_buffer
        result = target(progress_buffer, args)
        progress_buffer.flush_progress()

        if self.thread_exception:
            raise self.thread_exception
        return result

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
        
    def _execute_external_long_running_task_wrapper(self, progress_buffer: io.StringIO, wrapper_args: list[callable, dict]) -> None:
        target, args = wrapper_args
        try:
            with redirect_stdout(progress_buffer), redirect_stderr(progress_buffer):
                if args is None:
                    result = target()
                else:
                    result = target(args)
            return result
        except Exception as e:
            self.thread_exception = e
        
    def _start_external_long_running_task(self, args) -> None:
        self._external_buffer_wrapper(self._execute_external_long_running_task_wrapper, (self._external_long_running_task, args))
