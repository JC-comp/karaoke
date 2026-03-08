from flask import request
from flask_socketio import join_room, leave_room
from ..base import LoggingNamespace, get_sid
from .manager import JobManager

def get_job_room(job_id: str) -> str:
    return 'job-' + job_id

def get_task_room(job_id: str) -> str:
    return 'task-' + job_id

class JobNamespace(LoggingNamespace):
    def __init__(self, manager: JobManager) -> None:
        super().__init__(namespace="/job")
        self.manager = manager
    
    def on_connect(self):
        sid = get_sid(request)
        self.logger.debug(f"Client connected: {sid}")
    
    def on_disconnect(self, reason) -> None:
        sid = get_sid(request)
        self.logger.debug(f'Client {sid} disconnected')

    def sync_jobs(self, room: str) -> None:
        try:
            dag_runs = self.manager.get_dag_runs()
            while True:
                try:
                    dag_run = next(dag_runs)
                    self.logger.debug(f'Emitting {dag_run} to {room}')
                    self.emit('update_job', dag_run, room=room)
                except StopIteration:
                    break
                except Exception as e:
                    self.logger.error(f'Error processing a DAG run: {e}', exc_info=True)
                    continue
            self.emit('updated_job')
        except:
            self.logger.error('Failed to send sync jobs', exc_info=True)
            self.emit('error', {'type': 'updated_job'}, room=room)

    def sync_job(self, job_id: str, room: str) -> None:
        try:
            dag_id, dag_run_id = job_id.split('|')
            dag_run = self.manager.get_dag_run(dag_id, dag_run_id)
            self.logger.debug(f'Emitting {dag_run} to {room}')
            self.emit('update_job', dag_run, room=room)
        except:
            self.logger.error('Failed to send sync job', exc_info=True)
            self.emit('error', {'type': 'updated_job'}, room=room)

    def on_sync_job(self, job_id: str) -> None:
        if job_id is None:
            self.logger.debug(f'Job ID is None for client {sid}')
            self.emit('error', {'type': 'sync', 'message': 'Job ID is None'}, room=sid)
            return
        
        sid = get_sid(request)
        if job_id == '*':
            self.sync_jobs(sid)
        else:
            self.sync_job(job_id, sid)

    def on_join_job(self, job_id: str) -> None:
        """
        Handle the join event from the socketio client.
        """
        if job_id is None:
            self.logger.debug(f'Job ID is None for client {sid}')
            self.emit('error', {'type': 'join', 'message': 'Job ID is None'}, room=sid)
            return
        self.on_sync_job(job_id)
        join_room(get_job_room(job_id))

        sid = get_sid(request)
        self.logger.debug(f'Client {sid} joined {get_job_room(job_id)}')

    def on_leave_job(self, job_id: str) -> None:
        """
        Handle the leave event from the socketio client.
        """
        sid = get_sid(request)
        if job_id is None:
            self.emit('error', {'message': 'Job ID is required'}, room=sid)
            self.logger.warning(f'Client {sid} tried to leave without a Job ID')
            return
        
        leave_room(get_job_room(job_id))
        self.logger.debug(f'Client {sid} left job {job_id}')

    def sync_task(self, job_id: str, room: str) -> None:
        try:
            dag_id, dag_run_id = job_id.split('|')
            task_instances = self.manager.get_task_instances(dag_id, dag_run_id)
            for task_instance in task_instances:
                self.logger.debug(f'Emitting {task_instance} to {room}')
                self.emit('update_task', task_instance, room=room)
        except:
            self.logger.error('Failed to send sync task', exc_info=True)
            self.emit('error', {'type': 'update_task'}, room=room)
    
    def on_sync_task(self, job_id: str) -> None:
        if job_id is None:
            self.logger.debug(f'Job ID is None for client {sid}')
            self.emit('error', {'type': 'sync', 'message': 'Job ID is None'}, room=sid)
            return
        
        sid = get_sid(request)
        self.sync_task(job_id, sid)

    def on_join_task(self, job_id: str) -> None:
        """
        Handle the join event from the socketio client.
        """
        if job_id is None:
            self.logger.debug(f'Job ID is None for client {sid}')
            self.emit('error', {'type': 'join', 'message': 'Job ID is None'}, room=sid)
            return
        
        self.on_sync_task(job_id)
        sid = get_sid(request)
        join_room(get_task_room(job_id))
        self.logger.debug(f'Client {sid} joined {get_task_room(job_id)}')
    
    def on_leave_task(self, job_id: str) -> None:
        """
        Handle the leave event from the socketio client.
        """
        sid = get_sid(request)
        if job_id is None:
            self.emit('error', {'message': 'Job ID is required'}, room=sid)
            self.logger.warning(f'Client {sid} tried to leave without a Job ID')
            return
        
        leave_room(get_task_room(job_id))
        self.logger.debug(f'Client {sid} left task {job_id}')
