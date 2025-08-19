import logging
import threading

from flask import request
from flask_socketio import Namespace, SocketIO, join_room, leave_room
from ..scheduler import SchedulerBinder

class BinderManager:
    """
    BinderManager manages the monitoring of jobs and the clients connected to them.
    """
    def __init__(self, namespace: str, socketio: SocketIO, logger: logging.Logger) -> None:
        self.logger = logger
        self.namespace = namespace
        self.socketio = socketio

        self.operation_lock = threading.RLock()
        self.job_monitor_map: dict[str, SchedulerBinder] = {}
        self.rooms: dict[str, list[str]] = {}

    def ensure_lock_acquired(func) -> callable:
        """
        Decorator to ensure that the operation lock is acquired before executing the function.
        """
        def wrapper(*args, **kwargs):
            self: BinderManager = args[0]
            with self.operation_lock:
                return func(*args, **kwargs)
        return wrapper
    
    def _send_latest_progress(self, scheduler: SchedulerBinder, sid: str) -> None:
        """
        Send the latest progress to connected clients if binding already exists.
        """
        raise NotImplementedError("This method should be overridden")
    
    def _serving_progress_update(self, scheduler: SchedulerBinder, job_id: str) -> None:
        """
        Start a background task to serve progress updates to connected clients.
        """
        raise NotImplementedError("This method should be overridden")
    
    @ensure_lock_acquired
    def add_member(self, sid: str, job_id: str) -> None:
        """
        Handle the join event from the socketio client.
            1. Check if the client is already in the room.
            2. Check if the job monitor already exists.
            3. If not, create a new SchedulerBinder and add it to the job monitor map.
        """
        if job_id is None:
            self.logger.debug(f'Job ID is None for client {sid}')
            self.socketio.emit('error', {'message': 'Job ID is None'}, room=sid, namespace=self.namespace)
            return
        if job_id not in self.rooms:
            self.rooms[job_id] = []
        if sid in self.rooms[job_id]:
            self.logger.debug(f'Client already connected {sid}')
            self.socketio.emit('error', {'message': 'Client already connected'}, room=sid, namespace=self.namespace)
            # Client already in the room
            return
        
        self.rooms[job_id].append(sid)
        join_room(job_id, sid, namespace=self.namespace)
        self.logger.info(f'# of clients monitored for job {job_id}: {len(self.rooms[job_id])}')

        if job_id in self.job_monitor_map:
            # Job monitor already exists
            scheduler = self.job_monitor_map[job_id]
            self._send_latest_progress(scheduler, sid)
            return
        
        scheduler = SchedulerBinder()
        self.job_monitor_map[job_id] = scheduler
        try:    
            scheduler.bind()
        except Exception as e:
            self.logger.error(f"Failed to bind scheduler: {e}")
            self.socketio.emit('error', {'message': 'Scheduler is not connected'}, room=sid, namespace=self.namespace)
            return

        self.socketio.start_background_task(self._serving_progress_update, scheduler, job_id)
      
    @ensure_lock_acquired
    def leave_member(self, sid: str, job_id: str) -> None:
        """
        Handle the leave event from the socketio client.
        """
        if job_id not in self.rooms:
            return
        
        if sid in self.rooms[job_id]:
            self.rooms[job_id].remove(sid)
            leave_room(job_id, sid, namespace=self.namespace)
        
        self.logger.info(f'(del) # of clients monitored for job {job_id}: {len(self.rooms[job_id])}')
        if len(self.rooms[job_id]) > 0:
            return
        # No more members in the room, close the scheduler
        scheduler = self.job_monitor_map.get(job_id)
        if not scheduler:
            return
        scheduler.close()
        del self.job_monitor_map[job_id]
    
    @ensure_lock_acquired
    def disconnect_member(self, sid: str) -> None:
        """
        Handle the disconnect event from the socketio client.
        """
        for job_id in self.rooms:
            if sid in self.rooms[job_id]:
                self.leave_member(sid, job_id)

class SchedulerNamespace(Namespace):
    def __init__(self, namespace: str, manager: BinderManager, logger: logging.Logger) -> None:
        super().__init__(namespace)
        self.manager = manager
        self.logger = logger

    def on_join(self, job_id: str) -> None:
        """
        Handle the join event from the socketio client.
        """
        sid = request.sid
        self.manager.add_member(sid, job_id)

    def on_leave(self, job_id: str) -> None:
        """
        Handle the leave event from the socketio client.
        """
        sid = request.sid
        self.logger.info(f'Client {sid} left job {job_id}')
        self.manager.leave_member(sid, job_id)

    def on_disconnect(self, reason) -> None:
        """
        Handle the disconnect event from the socketio client.
        """
        sid = request.sid
        self.logger.info(f'Client {sid} disconnected')
        self.manager.disconnect_member(sid)
