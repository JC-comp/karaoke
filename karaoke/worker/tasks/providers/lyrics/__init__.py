from .base import BaseLyricsProvider, compare
from .musicmatch import MusixMatch
from .kkbox import KKBox

PROVIDERS: list[type[BaseLyricsProvider]] = [KKBox, MusixMatch]

__all__ = [
    'PROVIDERS',
    'compare',
]