from gevent import monkey
monkey.patch_all()

import logging.config
from .config import config
logging.config.dictConfig({
    "version": 1,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        "detailed": {"format": "%(asctime)s [%(levelname)s] %(module)s.%(funcName)s:%(lineno)d: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": config.log_level,
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": config.log_level,
        },
    }
})

import json
from flask import Response
from werkzeug.exceptions import HTTPException
from .blueprints import BLUEPRINTS
from .config import config
from .websocket import prepare_room_environment, prepare_artifact_environment, prepare_job_environment
from .datatype import MyFlaskApp

logger = logging.getLogger(__name__)

app = MyFlaskApp(__name__, static_url_path='/')

@app.errorhandler(Exception)
def handle_exception(e: Exception):
    if isinstance(e, HTTPException):
        return e
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return str(e), 500

@app.after_request
def success_response(response: Response):
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
    if 200 <= response.status_code < 300:
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

if config.server.web:
    app.register_blueprint(**BLUEPRINTS['web'])
if config.server.yt:
    app.register_blueprint(**BLUEPRINTS['yt'])
if config.server.room:
    app.register_blueprint(**BLUEPRINTS['room'])
    prepare_room_environment(app)
if config.server.artifact:
    app.register_blueprint(**BLUEPRINTS['artifact'])
    prepare_artifact_environment(app)
if config.server.job:
    app.register_blueprint(**BLUEPRINTS['job'])
    prepare_job_environment(app)


if __name__ == '__main__':
    app.run()
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(config.log_level)