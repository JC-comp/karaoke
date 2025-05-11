import json
import requests
import re
import logging

from .base import BaseLyricsProvider, compare

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
    
    final_name = final_artist = final_lyrics = None
    for result in results:
        try:
            name = result['name']
            logger.info(f"Found result: {name}")
            url = result['url']
            has_lyrics = result['has_lyrics']
            if not has_lyrics:
                raise Exception("No lyrics found")
            lyrics = get_lyrics(url)

            artist_roles = result.get('artist_roles', [])
            if artist_roles:
                artist = artist_roles[0].get('name', None)
            else:
                artist = None

            if compare(q, name):
                final_name = name
                final_artist = artist
                final_lyrics = lyrics
                if compare(q_artist, artist):
                    logger.info(f"Perfect match found: {name} by {artist}")
                    return name, artist, lyrics                
        except Exception as e:
            logger.error(f"Error processing result: {e}")

    if final_lyrics:
        return final_name, final_artist, final_lyrics
    raise Exception("No matching results found")

class KKBox(BaseLyricsProvider):
    name="KKBox"
    """
    Search for the lyrics using KKBox API.
    """
    def search(self, title: str, artist:str) -> tuple[str, str, str]:
        title, artist, lyrics = macro_search(title, artist, self.logger)
        self.logger.info(f"Found lyrics: {title} by {artist}")
        return title, artist, lyrics