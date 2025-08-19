from flask import request
from flask_socketio import Namespace, join_room, leave_room
from .room.manager import RoomManager
from ...utils.config import get_logger, Config

config = Config()

class KTVNamespace(Namespace):
    def __init__(self, manager: RoomManager) -> None:
        super().__init__(namespace=manager.namespace)
        self.logger = get_logger(__name__, config.log_level)
        self.manager = manager

    def on_join(self, room_id: str | None) -> None:
        """
        Handle the join event from the socketio client.
        """
        sid = request.sid
        if room_id is None:
            room_id = 'Default'

        join_room(room_id)
        self.manager.join_room(room_id, sid)
        self.logger.debug(f'Client {sid} joined room {room_id}')

    def on_leave(self, room_id: str) -> None:
        """
        Handle the leave event from the socketio client.
        """
        sid = request.sid
        if room_id is None:
            self.socketio.emit('error', {'message': 'Room ID is required'}, room=sid)
            self.logger.warning(f'Client {sid} tried to leave without a room ID')
            return
        
        self.manager.leave_room(room_id, sid)
        leave_room(room_id)
        self.logger.debug(f'Client {sid} left room {room_id}')
        
    def on_disconnect(self, reason) -> None:
        """
        Handle the disconnect event from the socketio client.
        """
        sid = request.sid
        self.logger.info(f'Client {sid} disconnected')

    def on_setplay(self, payload: dict) -> None:
        """
        Handle the play event from the socketio client.
        """
        request_id = payload.get('request_id')
        room_id = payload.get('room_id')
        is_playing = payload.get('is_playing')

        self.manager.set_playing(room_id, request_id, is_playing)

    def on_delete(self, payload: dict) -> None:
        """
        Handle the playlist item deletion event from the socketio client.
        """
        request_id = payload.get('request_id')
        room_id = payload.get('room_id')
        item_id = payload.get('item_id')

        self.manager.remove_item(room_id, request_id, item_id)

    def on_first(self, payload: dict) -> None:
        """
        Handle the event to push target item to the top of the playlist.
        """
        request_id = payload.get('request_id')
        room_id = payload.get('room_id')
        item_id = payload.get('item_id')

        self.manager.move_item_to_top(room_id, request_id, item_id)

    def on_moveTo(self, payload: dict) -> None:
        """
        Handle the event to move an item to a specific position in the playlist.
        """
        request_id = payload.get('request_id')
        room_id = payload.get('room_id')
        item_id = payload.get('item_id')

        self.manager.move_to_item(room_id, request_id, item_id)