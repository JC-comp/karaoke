from .yt import youtube_bp
from .scheduler import scheduler_bp
from .artifact import artifact_bp

WEB_BLUEPRINTS = [
    {'blueprint': youtube_bp, 'url_prefix': '/api/youtube'},
    {'blueprint': scheduler_bp, 'url_prefix': '/api'},
]

ARTIFACT_BLUEPRINTS = [
    {'blueprint': artifact_bp, 'url_prefix': '/api'},
]

WEB_BLUEPRINTS += ARTIFACT_BLUEPRINTS

__all__ = [
    'WEB_BLUEPRINTS',
    'ARTIFACT_BLUEPRINTS',
]