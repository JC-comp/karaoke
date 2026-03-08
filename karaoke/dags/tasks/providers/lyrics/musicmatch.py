from musicxmatch_api import MusixMatchAPI
from .base import BaseLyricsProvider
from ..utils import NotEnabledException

class MusixMatch(BaseLyricsProvider):
    """
    Search for the lyrics using the MusixMatch API.
    """
    @property
    def name(self) -> str:
        return "MusixMatch"
    
    def search(self, title: str, artist:str) -> tuple[str, str, str]:
        if not self.config.provider.musixmatch:
            raise NotEnabledException("KKBOX is not enabled")
        
        api = MusixMatchAPI()
        # Search for the lyrics using the title
        best_match, found_title, found_artist = self.search_track(api, title, artist)
        
        # Fetch the lyrics for the track
        track_id = best_match['track_id']
        lyrics = self.get_lyrics(api, track_id)
        return found_title, found_artist, lyrics
    
    def search_track(self, api: MusixMatchAPI, title: str, artist: str) -> tuple[dict, str, str]:
        """
        Search for the track with the given title and artist using the MusixMatch API.
        """
        self.logger.info(f"Searching lyrics for {title} by {artist}")
        search_result = api.search_tracks(title)
        status_code = search_result['message']['header']['status_code']
        if status_code != 200:
            raise Exception(f"Failed to fetch search results: {status_code}")
        
        
        track_list = search_result['message']['body']['track_list']
        if len(track_list) == 0:
            raise Exception(f"No results found")
        best_match = track_list[0]['track']
        found_title = best_match['track_name']
        found_artist = best_match['artist_name']
        self.logger.info(f"Found track: {found_title} by {found_artist}")
        return best_match, found_title, found_artist
    
    def get_lyrics(self, api: MusixMatchAPI, track_id: str) -> str:
        """
        Fetch the lyrics for the track found using the MusixMatch API.
        """
        lyrics_result = api.get_track_lyrics(track_id)
        status_code = lyrics_result['message']['header']['status_code']
        if status_code != 200:
            raise Exception(f"Failed to fetch lyrics: {status_code}")
        
        # Check if the lyrics exist
        lyrics_json = lyrics_result['message']['body']['lyrics']
        if lyrics_json['instrumental'] == 1:
            raise Exception("Lyrics are instrumental")
        if lyrics_json['restricted'] == 1:
            raise Exception("Lyrics are restricted")
        if lyrics_json['lyrics_body'] == '':
            raise Exception(f"Lyrics are empty: {lyrics_json}")
        
        lyrics = lyrics_json['lyrics_body']
        return lyrics
    