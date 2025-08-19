
from flask import Blueprint, request, g
from .room import playlist_item
from .room.manager import RoomManager

class KTV_BP:
    bp = Blueprint('ktv', __name__)
    manager: RoomManager
    @staticmethod
    def setup(manager: RoomManager) -> Blueprint:
        KTV_BP.manager = manager
        return KTV_BP.bp

    @bp.route('/queue', methods=['POST'])
    def queue():
        """
        Add a song to the queue.
        """
        data = request.get_json()
        room_id = data.get('room_id')
        item_type = data.get('item_type')
        item = data.get('item')
        if not room_id or not item_type or not item:
            return 'Missing required fields', 400
        
        if not hasattr(playlist_item, item_type):
            return 'Item type not found', 400
        item_class = getattr(playlist_item, item_type)
        if not issubclass(item_class, playlist_item.PlaylistItem):
            return 'Invalid item type', 400
        item = item_class(**item)

        KTV_BP.manager.add_item(room_id, item)
        return 'Success', 200
