import argparse
import json
import os

from flask import Flask, Response
from flask_socketio import SocketIO
from werkzeug.exceptions import HTTPException
from .blueprints import WEB_BLUEPRINTS, ARTIFACT_BLUEPRINTS
from .ktv import KTV_BP, KTVNamespace, RoomManager
from .events import JobNamespace
from ..utils.config import get_logger, Config

config = Config()
logger = get_logger(__name__, config.log_level)

app = Flask(__name__, static_url_path='/')

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

@app.route('/', methods=['GET'])
def index() -> Response:
    """
    Serve the index.html file.
    """
    return app.send_static_file('index.html')

@app.route('/<path>', methods=['GET'])
def static_proxy(path: str) -> Response:
    """
    Serve static files from the static folder.
    """
    if os.path.exists(os.path.join(app.static_folder, path + '.html')):
        return app.send_static_file(path + '.html')
    return app.send_static_file(path)

def run_web():
    app.static_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static')
    socketio = SocketIO(app, path=config.socketio_path, cors_allowed_origins="*", async_mode='threading')

    room_manager = RoomManager(socketio)

    app.register_blueprint(KTV_BP.setup(room_manager), url_prefix='/api/ktv')
    for blueprint in WEB_BLUEPRINTS:
        app.register_blueprint(blueprint['blueprint'], url_prefix=blueprint['url_prefix'])

    socketio.on_namespace(JobNamespace(socketio))
    socketio.on_namespace(KTVNamespace(room_manager))
    return app

def run_artifact():
    for blueprint in ARTIFACT_BLUEPRINTS:
        app.register_blueprint(blueprint['blueprint'], url_prefix=blueprint['url_prefix'])
    return app

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the web server.')
    parser.add_argument('--artifact', action='store_true', help='Run the artifact server.')
    args = parser.parse_args()
    if args.artifact:
        app = run_artifact()
    else:
        app = run_web()
    app.run()