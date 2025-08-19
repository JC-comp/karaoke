from .playlist_item import PlaylistItem

class Room:
    def __init__(self, room_name: str):
        self.room_name = room_name
        self.playlist: list[PlaylistItem] = []
        self.is_fullscreen = True
        self.is_playing = False
        self.is_vocal_on = False
        self.volume = 100

        self.version = 0
        self.clients = set()

    def add_client(self, sid: str) -> None:
        """
        Add a client to the room.
        """
        if sid in self.clients:
            raise ValueError(f"Client {sid} is already in the room.")
        self.clients.add(sid)

    def remove_client(self, sid: str) -> None:
        """
        Remove a client from the room.
        """
        if sid not in self.clients:
            raise ValueError(f"Client {sid} is not in the room.")
        self.clients.discard(sid)

    def set_fullscreen(self, is_fullscreen: bool) -> None:
        """
        Set the fullscreen mode for the room.
        """
        self.is_fullscreen = is_fullscreen
    
    def set_playing(self, is_playing: bool) -> None:
        """
        Set the playing state for the room.
        """
        self.is_playing = is_playing

    def add_item(self, item: PlaylistItem) -> None:
        """
        Add an item to the playlist.
        """
        self.playlist.append(item)

    def remove_item(self, item_id: str) -> None:
        """
        Remove an item from the playlist.
        """
        for item in self.playlist:
            if item.item_id == item_id:
                self.playlist.remove(item)
                return
        raise ValueError(f"Item {item_id} not found in the playlist.")

    def move_item_to_top(self, item_id: str) -> None:
        """
        Move an item to the top of the playlist and remove the original first item.
        """
        for i, item in enumerate(self.playlist):
            if item.item_id == item_id:
                self.playlist.insert(0, self.playlist.pop(i))
                if len(self.playlist) > 1:
                    self.playlist.pop(1)
                return
        raise ValueError(f"Item {item_id} not found in the playlist.")
    
    def move_to_item(self, item_id: str) -> None:
        """
        Pop the item above the target item to set it as the first item.
        """
        target_index = None
        for i, item in enumerate(self.playlist):
            if item.item_id == item_id:
                target_index = i
                break
        if target_index is None:
            raise ValueError(f"Item {item_id} not found in the playlist.")
        self.playlist = self.playlist[target_index:]

    def serialize(self) -> dict:
        """
        Serialize the room object to a dictionary.
        """
        return {
            'room_name': self.room_name,
            'playlist': [item.serialize() for item in self.playlist],
            'is_fullscreen': self.is_fullscreen,
            'is_playing': self.is_playing,
            'is_vocal_on': self.is_vocal_on,
            'volume': self.volume,
            'version': self.version
        }