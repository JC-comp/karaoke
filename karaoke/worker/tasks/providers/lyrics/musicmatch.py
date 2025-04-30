import urllib.parse

from musicxmatch_api import MusixMatchAPI
from .base import BaseLyricsProvider

def macro_search(api: MusixMatchAPI, q: str) -> dict:
    """
    Perform a search using the MusixMatch API.
    """
    q = urllib.parse.quote(q)
    url = f'macro.search?app_id=mxm-com-v1.0&format=json&part=track_artist%2Cartist_image&q={q}&page_size=20&track_fields_set=community_track_search&artist_fields_set=community_artist_search'
    api.headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36'
    return api.make_request(url.format(q))

class MusixMatch(BaseLyricsProvider):
    name="MusixMatch"
    """
    Search for the lyrics using the MusixMatch API.
    """
    def search(self, title: str, artist:str) -> str:
        api = MusixMatchAPI()
        # Search for the lyrics using the title
        best_match = self.search_track(api, title, artist)
        if best_match['type'] != 'track':
            raise ValueError(f"Best match is not a track: {best_match['type']}")
        
        # Fetch the lyrics for the track
        track_id = best_match["id"]
        lyrics = self.get_lyrics(api, track_id)
        return lyrics
    
    def search_track(self, api: MusixMatchAPI, title: str, artist: str) -> dict:
        """
        Search for the track with the given title and artist using the MusixMatch API.
        """
        self.update(message=f"Searching lyrics for {title} by {artist}")
        search_result = macro_search(api, title)
        status_code = search_result['message']['header']['status_code']
        if status_code != 200:
            raise Exception(f"Failed to fetch search results: {status_code}")
        
        best_match = search_result['message']['body']['macro_result_list']['best_match']
        track_id = best_match["id"]
        self.logger.info(f"Best match: {best_match}")
        
        track_list = search_result['message']['body']['macro_result_list']['track_list']
        for track in track_list:
            if track['track']['track_id'] == track_id:
                found_title = track['track']['track_name']
                found_artist = track['track']['artist_name']
                self.logger.info(f"Found track: {found_title} by {found_artist}")
                if not self.compare_artist(artist, found_artist):
                    self.validate_title(title, found_title)
                break
        return best_match

    def compare_artist(self, artist: str, found_artist: str) -> bool:
        """
        Compare the artist names.
        """
        cleaned_artist = artist.lower().replace(' ', '')
        cleaned_found_artist = found_artist.lower().replace(' ', '')
        if cleaned_artist in cleaned_found_artist or cleaned_found_artist in cleaned_artist:
            return True
        return False
    
    def validate_title(self, title: str, found_title: str) -> bool:
        """
        Validate if the title matches the found title.
        """
        if title.lower() == found_title.lower():
            return True
        raise ValueError(f"Title mismatch: {title} != {found_title}")

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
    