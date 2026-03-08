import json
import requests
import re
import logging

from typing import Optional
from .base import BaseLyricsProvider, compare
from ..utils import NotEnabledException

QUERY_URL = "https://www.kkbox.com/api/search/song?q={}&terr=tw&lang=tc"

def get_lyrics(url: str) -> str:
    """
    Fetch the lyrics from the given URL.
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"{response.status_code} {response.reason}")
    body = response.text
    regex = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)
    matches = regex.findall(body)
    if not matches:
        raise Exception("Unable to find lyrics section")
    for match in matches:
        data = json.loads(match)
        if 'recordingOf' in data:
            recording_of = data['recordingOf']
            if 'lyrics' in recording_of:
                lyrics = recording_of['lyrics']
                if 'text' in lyrics:
                    return lyrics['text'].strip()
    raise Exception("No lyrics found in sections")

def macro_search(q: str, q_artist: str, logger: logging.Logger) -> tuple[str, str, str]:
    """
    Perform a search using the KKBox API.
    """
    url = QUERY_URL.format(q)
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"{response.status_code} {response.reason}")
    data = response.json()
    results = data.get('data', {}).get('result', [])
    if not results:
        raise Exception("No results found")
    
    for result in results:
        try:
            url = result['url']
            name = result['name']
            has_lyrics = result['has_lyrics']

            logger.info(f"Found result: {name}")
            if not has_lyrics:
                logger.info(f"- Skipping as no lyrics or URL available")
                continue
            
            if not compare(q, name):
                logger.info(f"- Skipping as name mismatch")
                continue

            artist_roles = result.get('artist_roles', [])
            if not artist_roles:
                logger.info(f"- Skipping as Artist info missing")
                continue

            artist = artist_roles[0].get('name')
            if not compare(q_artist, artist):
                logger.info(f"- Artist mismatch: {q_artist} != {artist}")
                continue
            
            lyrics = get_lyrics(url)
            return name, artist, lyrics
        except Exception as e:
            logger.error(f"Error processing result: {e}")

    raise Exception("No matching results found")

class KKBox(BaseLyricsProvider):
    """
    Search for the lyrics using KKBox API.
    """
    @property
    def name(self) -> str:
        return "KKBox"
    
    def search(self, title: str, artist:str) -> tuple[str, str, str]:
        if not self.config.provider.kkbox:
            raise NotEnabledException("KKBOX is not enabled")
        
        title, artist, lyrics = macro_search(title, artist, self.logger)
        self.logger.info(f"Found lyrics: {title} by {artist}")
        return title, artist, lyrics