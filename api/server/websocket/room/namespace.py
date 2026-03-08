from flask import request
from flask_socketio import join_room, leave_room
from redis import Redis
from ..base import LoggingNamespace, get_sid
from .manager import RoomManager

class RoomNamespace(LoggingNamespace):
    def __init__(self, manager: RoomManager) -> None:
        super().__init__(namespace="/ktv")
        self.manager = manager
    
    def on_connect(self):
        sid = get_sid(request)
        self.logger.debug(f"Client connected: {sid}")
    
    def on_disconnect(self, reason) -> None:
        sid = get_sid(request)
        self.logger.debug(f'Client {sid} disconnected')
    
    def sync(self, room_id: str, room: str) -> None:
        data = self.manager.get_room(room_id)
        self.logger.debug(f'Emitting {data} to {room}')
        self.emit('update', data, room=room)

    def on_join(self, room_id: str | None) -> None:
        """
        Handle the join event from the socketio client.
        """
        sid = get_sid(request)
        if room_id is None:
            room_id = 'Default'
        try:
            self.sync(room_id=room_id, room=sid)
        except:
            self.logger.error(f'Failed to get sync data', exc_info=True)
            self.emit('error', {'message': 'Failed to join room'}, room=sid)
            return

        join_room(room_id)
        self.logger.debug(f'Client {sid} joined room {room_id}')

    def on_sync(self, room_id: str | None) -> None:
        """
        Handle the sync event from the socketio client.
        """
        sid = get_sid(request)
        if room_id is None:
            room_id = 'Default'
        try:
            self.sync(room_id=room_id, room=sid)
        except:
            self.logger.error(f'Failed to get sync data', exc_info=True)
            self.emit('error', {'message': 'Failed to sync data'}, room=sid)
            return

    def on_leave(self, room_id: str) -> None:
        """
        Handle the leave event from the socketio client.
        """
        sid = get_sid(request)
        if room_id is None:
            self.emit('error', {'message': 'Room ID is required'}, room=sid)
            self.logger.warning(f'Client {sid} tried to leave without a room ID')
            return
        
        leave_room(room_id)
        self.logger.debug(f'Client {sid} left room {room_id}')

    def on_action(self, data):
        """
        Consolidated dispatcher for all room mutations.
        Expected data format: 
        { "room_id": "...", "type": "SET_VOLUME", "payload": {...} }
        """
        sid = get_sid(request)
        
        room_id = data.get("room_id")
        action_type = data.get("type")
        payload = data.get("payload", {})
        request_id = data.get("request_id")

        if not all([room_id, action_type, request_id]):
            error_msg = 'Room ID, Type, and Request ID are required'
            self.emit('action_response', {
                'request_id': request_id,
                'status': 'error',
                'message': error_msg
            }, room=sid)
            self.logger.warning(f"Invalid action attempt by {sid}: {error_msg}")
            return
        
        try:
            if action_type == "UPDATE_METADATA":
                result = self.manager.set_metadata(room_id, payload)
            elif action_type == "PLAY_NEXT":
                result = self.manager.move_item_to_top(room_id, payload.get("item_id"))
            elif action_type == "SKIP_TO":
                result = self.manager.move_to_item(room_id, payload.get("item_id"))
            elif action_type == "REMOVE_SONG":
                result = self.manager.remove_song(room_id, payload.get("item_id"))
            else:
                raise ValueError(f"Unknown action type: {action_type}")

            self.emit('action_response', {
                'request_id': request_id,
                'status': 'ok'
            }, room=sid)
            self.emit('update', result, room=room_id)

        except Exception as e:
            self.logger.error(f"Action {action_type} failed for room {room_id}", exc_info=True)
            self.emit('action_response', {
                'request_id': request_id,
                'status': 'error',
                'message': str(e)
            }, room=sid)