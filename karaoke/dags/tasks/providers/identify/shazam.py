import asyncio
import logging

from shazamio import Shazam, Serialize
from shazamio.schemas.models import ResponseTrack
from .base import BaseIdentifier
from ..utils import NotEnabledException

QUERY_URL = 'https://www.shazam.com/services/amapi/v1/catalog/TW/search?types=songs&term={}&limit=3'

async def identify_async(path: str, logger: logging.Logger) -> tuple[str, str]:
    """
    Asynchronous function to identify music using Shazam.
    """
    shazam = Shazam(endpoint_country='TW', language='zh-Hant')
    out = await shazam.recognize(path)
    result = Serialize.full_track(data=out)
    track = result.track
    if not track:
        raise Exception("No track found with Shazam")
    
    title = track.title
    artist = track.subtitle
    
    return title, artist

class ShazamIdentifier(BaseIdentifier):
    """
    Identify music using Shazam.
    """
    @property
    def name(self) -> str:
        return "ShazamIdentifier"
    def identify(self, audio_path: str) -> tuple[str, str]:
        if not self.config.provider.shazam:
            raise NotEnabledException("Shazam is not enabled")
        
        title, artist = asyncio.run(identify_async(audio_path, self.logger))
        self.logger.info(f"Found music: {title} by {artist}")
        return title, artist
