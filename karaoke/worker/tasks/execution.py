import io
import multiprocessing
import logging
import subprocess
import socket
import json
import os
import pickle
import base64

from contextlib import redirect_stderr, redirect_stdout
from .base import ExecuteTask, ExecuteJob
from .runner_log import BaseHandler, SyncHandler, DaemonHandler
from .exception import SoftFailure
from ...utils.config import Config, get_logger
from ...utils.task import TaskStatus
from ...utils.connection import Connection

def serialize_args(args: dict) -> str:
    """
    Serializes the arguments to a byte string.
    """
    serialized_bytes = pickle.dumps(args)
    encoded = base64.b64encode(serialized_bytes).decode('utf-8')
    return encoded

def deserialize_args(encoded: str) -> dict:
    """
    Deserializes the arguments from a byte string.
    """
    decoded = base64.b64decode(encoded.encode('utf-8'))
    deserialized_bytes = pickle.loads(decoded)
    return deserialized_bytes

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
            self.execution.push_log_line(target='info', message=line)

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

class DaemonJob(ExecuteJob):
    def __init__(self, connection: Connection) -> None:
        super().__init__()
        self.connection = connection

    def update(self, **kwargs) -> None:
        self.push('job', **kwargs)
    
    def push(self, target: str, **kwargs) -> None:
        self.connection.send(json.dumps({
            'target': target,
            'body': kwargs
        }))

class DaemonTask(ExecuteTask):
    def __init__(self, connection: Connection) -> None:
        super().__init__(DaemonJob(connection))

class Execution:
    task: ExecuteTask
    logging_handler: BaseHandler
    def __init__(self, name: str, config: Config) -> None:
        self.passing_args: dict[str, any] = {}
        self.name = name
        self.config = config
        self.logger = get_logger(__name__, config.log_level)
        self.logging_handler = None
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

    def push_log_line(self, target: str, **kwargs) -> None:
        if self.logging_handler:
            self.logging_handler.push(target=target, ignore_action=False, **kwargs)

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

    def _start_execution(self, args: dict, daemon_connection: Connection = None):
        try:
            self.logger.info(f"----- {self.name} -----\n")
            has_preloaded = self._external_buffer_wrapper(self._execute_external_long_running_task_wrapper, (self._preload, None))
            if args is None:
                self.logger.info(f"Task {self.name} waiting for arguments to be queued")
                if has_preloaded and self.args_queue.empty():
                    self.passive_update(message="Preloading completed, waiting for prerequisites")
                if daemon_connection:
                    message = daemon_connection.json()
                    args = deserialize_args(message.get('args'))
                else:
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

    def get_daemon_socket(self) -> str:
        return self.__class__.__name__.lower() + '.sock'

    def _start_with_daemon(self, args: dict | None) -> bool:
        """
        Starts the task in daemon mode.
        """
        self.logger.info(f"Trying to connect daemon for task {self.name}")
        daemon_address = self.get_daemon_socket()
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.connect(daemon_address)
            connection = Connection(sock)
            connection.send(json.dumps({
                'action': 'start',
                'log_level': self.config.log_level,
                'args': serialize_args(args)
            }))
            self.logger.info(f"Connected to daemon for task {self.name}")
        except:
            self.logger.info(f"Daemon for task {self.name} not found")
            return False
        
        try:
            if args is None:
                self.logger.info(f"Task {self.name} waiting for arguments to be queued")
                args = self.args_queue.get()
            connection.send(json.dumps({
                'args': serialize_args(args)
            }))
            while True:
                message = connection.json()
                if 'done' in message:
                    self.logger.info(f"Daemon for task {self.name} finished")
                    break
                if message['target'] == 'job':
                    self.update_job(**message['body'])
                elif message['target'] == 'update':
                    self.update(**message['body'])
                elif message['target'] == 'passing_args':
                    self.set_passing_args(message['body']['args'])
                elif message['target'] == 'passive_update':
                    self.passive_update(**message['body'])
                elif message['target'] == 'artifact':
                    self.add_artifact(**message['body'])
                else:
                    if hasattr(self.logger, message['target']):
                        target = getattr(self.logger, message['target'])
                        if callable(target):
                            target(message['body']['message'])
                            continue
                    self.logger.warning(f"Unknown message target: {message['target']}")
        except:
            self.logger.error(f"Error in task {self.name}", exc_info=True, extra={'ignore_action': True})
        finally:
            self.logger.info(f"Closing connection to daemon for task {self.name}")
            connection.close()
        
        return True

    def start(self, task: ExecuteTask, logger: logging.Logger, args: dict = None, handler_args: list[multiprocessing.Queue, multiprocessing.Queue, int] = None) -> None:
        self.task = task
        self.logger = logger
        if handler_args: 
            message_queue, action_queue, level = handler_args
            handler = SyncHandler(message_queue, action_queue)
            self.logging_handler = handler
            logger.setLevel(level)
            logger.addHandler(handler)

        connected = self._start_with_daemon(args)
        if not connected:
            self._start_execution(args)
        
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

    def reset_daemon(self) -> None:
        """
        Resets the task to its initial state.
        """
        self.daemon_logger.info(f"Resetting task {self.name}")
        self.passing_args = {}
        self.thread_exception = None
        self.logger = get_logger(__name__, self.config.log_level)
        self.logger.handlers.clear()
        self.logger = get_logger(__name__, self.config.log_level)
        self.progress_buffer.flush_progress()
        self.args_queue = multiprocessing.Queue()

    def handle_client(self, connection: Connection, data: dict) -> None:
        self.reset_daemon()
        handler = DaemonHandler(connection)
        self.logger.setLevel(data['log_level'])
        self.logger.addHandler(handler)
        self.logging_handler = handler
        self.task = DaemonTask(connection)
        args = deserialize_args(data['args'])
        self._start_execution(args, connection)
        connection.send(json.dumps({
            'done': True
        }))

    def stop_daemon_server(self) -> None:
        self.daemon_logger = get_logger('daemon.' + __name__, self.config.log_level)
        self.daemon_logger.info(f"Sending stop command to daemon server for task {self.name}")
        daemon_address = self.get_daemon_socket()
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        connection = Connection(sock)
        try:
            sock.connect(daemon_address)
            connection.send(json.dumps({
                'action': 'stop'
            }))
            self.daemon_logger.info(f"Stop command sent to daemon server for task {self.name}")
        except Exception as e:
            self.daemon_logger.error(f"Error sending stop command to daemon server: {e}", exc_info=True)
        finally:
            connection.close()

    def start_daemon_server(self) -> None:
        """
        Starts the daemon server for the task.
        """
        self.daemon_logger = get_logger('daemon.' + __name__, self.config.log_level)
        self.daemon_logger.info(f"Starting daemon server for task {self.name}")
        daemon_address = self.get_daemon_socket()
        if os.path.exists(daemon_address):
            os.remove(daemon_address)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(daemon_address)
        sock.listen(1)
        self.daemon_logger.info(f"Daemon server started for task {self.name} at {daemon_address}")
        self._external_buffer_wrapper(self._execute_external_long_running_task_wrapper, (self._preload, None))
        self.daemon_logger.info(f"Daemon server preloaded for task {self.name}")
        
        while True:
            try:
                conn, _ = sock.accept()
            except KeyboardInterrupt:
                self.daemon_logger.info(f"Keyboard interrupt received, stopping daemon server for task {self.name}")
                break
            try:
                connection = Connection(conn)
                data = connection.json()
                if data['action'] == 'start':
                    self.handle_client(connection, data)
                elif data['action'] == 'stop':
                    self.daemon_logger.info(f"Stopping daemon server for task {self.name}")
                    break
                else:
                    connection.error(f"Unknown action: {data['action']}")
            except Exception as e:
                self.daemon_logger.error(f"Error in daemon server: {e}", exc_info=True)
            finally:
                connection.close()
        
        if os.path.exists(daemon_address):
            os.remove(daemon_address)
