import threading
import multiprocessing

from flask_socketio import SocketIO
from .room import Room
from .playlist_item import PlaylistItem

class RoomManager:
    def __init__(self, socketio: SocketIO) -> None:
        self.operation_lock = threading.RLock()
        self.rooms: dict[str, Room] = {}
        self.socketio = socketio
        self.namespace = '/ktv'

    def ensure_lock_acquired(func):
        """
        Decorator to ensure that the operation lock is acquired before executing the function.
        """
        def wrapper(self: "RoomManager", *args, **kwargs):
            with self.operation_lock:
                return func(self, *args, **kwargs)
        return wrapper
    
    def ensure_room_exists(func):
        """
        Decorator to ensure that the room exists before executing the function.
        """
        def wrapper(self: "RoomManager", room_id: str, *args, **kwargs):
            if room_id not in self.rooms:
                raise ValueError(f"Room {room_id} does not exist.")
            return func(self, room_id, *args, **kwargs)
        return wrapper
    
    @ensure_lock_acquired
    def join_room(self, room_id: str, sid: str) -> None:
        """
        Join a room.
        """
        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id)
        room = self.rooms[room_id]
        room.add_client(sid)
        self.socketio.emit('update', {
            'request_id': 'join',
            'body': room.serialize()
        }, room=room_id, namespace=self.namespace)

    @ensure_lock_acquired
    @ensure_room_exists
    def leave_room(self, room_id: str, sid: str) -> None:
        """
        Leave a room.
        """
        room = self.rooms[room_id]
        room.remove_client(sid)

    def room_operation_wrapper(has_request_id=True):
        """
        Decorator to wrap room operations.
        """
        def decorator(func):
            def wrapper(self: "RoomManager", room_id: str, *args, **kwargs):
                room = self.rooms[room_id]
                op_func = getattr(room, func.__name__)
                if not op_func:
                    raise ValueError(f"Operation {func.__name__} not found in room.")
                if has_request_id:
                    request_id = kwargs.pop('request_id', None)
                    if request_id is None:
                        request_id = args[0] if args else None
                        args = args[1:]
                else:
                    request_id = func.__name__
                op_func(*args, **kwargs)
                self.socketio.emit('update', {
                    'request_id': request_id,
                    'body': room.serialize()
                }, room=room_id, namespace=self.namespace)
            return wrapper
        return decorator
    
    @ensure_lock_acquired
    @ensure_room_exists
    @room_operation_wrapper(has_request_id=False)
    def add_item(self, room_id: str, item: PlaylistItem) -> None:
        """
        Add an item to the queue.
        """
        pass

    @ensure_lock_acquired
    @ensure_room_exists
    @room_operation_wrapper()
    def remove_item(self, room_id: str, request_id: str, item_id: str) -> None:
        """
        Remove an item from the queue.
        """
        pass

    @ensure_lock_acquired
    @ensure_room_exists
    @room_operation_wrapper()
    def move_item_to_top(self, room_id: str, request_id: str, item_id: str) -> None:
        """
        Move an item to the top of the queue.
        """
        pass

    @ensure_lock_acquired
    @ensure_room_exists
    @room_operation_wrapper()
    def set_playing(self, room_id: str, request_id: str, is_playing: bool) -> None:
        """
        Set the playing state for the room.
        """
        pass

    @ensure_lock_acquired
    @ensure_room_exists
    @room_operation_wrapper()
    def move_to_item(self, room_id: str, request_id: str, item_id: str) -> None:
        """
        Move to a specific item in the queue.
        """
        pass