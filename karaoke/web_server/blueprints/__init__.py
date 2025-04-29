from .yt import youtube_bp
from .scheduler import scheduler_bp

BLUEPRINTS = [
    {'blueprint': youtube_bp, 'url_prefix': '/api/youtube'},
    {'blueprint': scheduler_bp, 'url_prefix': '/api'},
]

__all__ = [
    'BLUEPRINTS',
]