import json
import os

from flask import Flask, Response
from flask_socketio import SocketIO
from werkzeug.exceptions import HTTPException
from .blueprints import BLUEPRINTS
from .ktv import KTV_BP, KTVNamespace, RoomManager
from .events import JobNamespace
from ..utils.config import get_logger, Config

config = Config()

app = Flask(__name__, static_url_path='/')
app.config['UPLOAD_FOLDER'] = config.media_path
app.static_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')
print(app.static_folder)
socketio = SocketIO(app, path=config.socketio_path, cors_allowed_origins="*", async_mode='threading')

logger = get_logger(__name__, config.log_level)

room_manager = RoomManager(socketio)

app.register_blueprint(KTV_BP.setup(room_manager), url_prefix='/api/ktv')
for blueprint in BLUEPRINTS:
    app.register_blueprint(blueprint['blueprint'], url_prefix=blueprint['url_prefix'])

socketio.on_namespace(JobNamespace(socketio))
socketio.on_namespace(KTVNamespace(room_manager))

@app.errorhandler(Exception)
def handle_exception(e: Exception) -> tuple:
    if isinstance(e, HTTPException):
        return e
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return str(e), 500

@app.after_request
def success_response(response: Response) -> tuple:
    """
    Handle the success response.
    This is called after each request to ensure that the response is successful.
    """
    if response.is_streamed:
        return response
    
    if response.is_json:
        body = response.get_json()
    else:
        body = response.get_data(as_text=True)
    
    response.headers['Content-Type'] = 'application/json'
    if response.status_code == 200:
        response.set_data(json.dumps({
            'success': True,
            'body': body
        }))
    else:
        response.set_data(json.dumps({
            'success': False,
            'message': body
        }))

    return response
    
if __name__ == '__main__':
    socketio.run(app, debug=True, port=5328)