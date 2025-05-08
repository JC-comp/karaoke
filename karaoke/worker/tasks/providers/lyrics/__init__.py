from .base import BaseLyricsProvider
from .musicmatch import MusixMatch
from .kkbox import KKBox

PROVIDERS: list[type[BaseLyricsProvider]] = [MusixMatch, KKBox]