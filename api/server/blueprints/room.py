from flask import Blueprint, request, current_app
from typing import cast
from ..datatype import MyFlaskApp, QueueItem, QueueType

room_bp = Blueprint('room', __name__)

@room_bp.route('/queue', methods=['POST'])
def queue():
    """
    Add a song to the queue.
    """
    app = cast(MyFlaskApp, current_app)

    data = request.get_json()
    room_id = data.get('room_id')
    item_type_str = data.get('item_type')
    item_data = data.get('item')
    
    if not all([room_id, item_type_str, item_data]):
        return "Missing required fields", 400
    
    if not isinstance(item_data, dict):
        return "Invalid item format", 400
    
    try:
        queue_type = QueueType(item_type_str)
        id = item_data.get('id')
        title = item_data.get('title')
        artist = item_data.get('channel') or item_data.get('artist')
        if not all([id, title, artist]):
            return "Missing required fields", 400
        
        item = QueueItem(queue_type, str(id), str(title), str(artist))
    except:
        return 'Invalid item type', 400
    
    result = app.roomManager.add_song_to_queue(room_id, item)
    app.socketio.emit('update', result, namespace="/ktv", room=room_id) # type: ignore
    return 'Success', 200

