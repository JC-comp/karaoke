import asyncio
import requests
import logging

from shazamio import Shazam, Serialize
from shazamio.schemas.models import ResponseTrack
from .base import BaseIdentifier
from .....utils.translate import convert_simplified_to_traditional

QUERY_URL = 'https://www.shazam.com/services/amapi/v1/catalog/TW/search?types=songs&term={}&limit=3'

async def identify_async(path: str, logger: logging.Logger) -> ResponseTrack:
    """
    Asynchronous function to identify music using Shazam.
    """
    shazam = Shazam(endpoint_country='TW', language='zh-Hant')
    out = await shazam.recognize(path)
    result = Serialize.full_track(data=out)
    track = result.track
    if not track:
        raise Exception("No track found with Shazam")
    
    title = convert_simplified_to_traditional(track.title)
    artist = convert_simplified_to_traditional(track.subtitle)
    
    return title, artist

class ShazamIdentifier(BaseIdentifier):
    name = "ShazamIdentifier"
    """
    Identify music using Shazam.
    """
    def identify(self, audio_path: str, title: str, artist: str) -> tuple[str, str]:
        title, artist = asyncio.run(identify_async(audio_path, self.logger))
        self.logger.info(f"Found music: {title} by {artist}")
        return title, artist
