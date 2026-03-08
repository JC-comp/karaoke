import os
from flask import Blueprint, Response

web_bp = Blueprint('web', __name__)
web_bp.static_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'static')

@web_bp.route('/', methods=['GET'])
def index() -> Response:
    """
    Serve the index.html file.
    """
    return web_bp.send_static_file('index.html')

@web_bp.route('/<path>', methods=['GET'])
def static_proxy(path: str) -> Response:
    """
    Serve static files from the static folder.
    """
    if web_bp.static_folder and os.path.exists(os.path.join(web_bp.static_folder, path + '.html')):
        return web_bp.send_static_file(path + '.html')
    return web_bp.send_static_file(path)
