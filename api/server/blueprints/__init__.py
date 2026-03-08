from .yt import youtube_bp
from .web import web_bp
from .room import room_bp
from .job import job_bp
from .artifact import artifact_bp

BLUEPRINTS = {
    'web': {'blueprint': web_bp, 'url_prefix': '/'},
    'yt': {'blueprint': youtube_bp, 'url_prefix': '/api/youtube'},
    'room': {'blueprint': room_bp, 'url_prefix': '/api/ktv'},
    'job': {'blueprint': job_bp, 'url_prefix': '/api/job'},
    'artifact': {'blueprint': artifact_bp, 'url_prefix': '/artifact'}
}

__all__ = [
    'BLUEPRINTS'
]