import os

from .execution import SoftFailure
from .task import Task, Execution, ArtifactType
from .providers.lyrics import PROVIDERS
from ..job import RemoteJob

def compare_artist(artist: str, found_artist: str) -> bool:
    """
    Compare the artist names.
    """
    if not artist or not found_artist:
        return False
    cleaned_artist = artist.lower().replace(' ', '')
    cleaned_found_artist = found_artist.lower().replace(' ', '')
    if cleaned_artist in cleaned_found_artist or cleaned_found_artist in cleaned_artist:
        return True
    return False

def validate_title(title: str, found_title: str) -> bool:
    """
    Validate if the title matches the found title.
    """
    if title.replace(' ', '').lower() == found_title.replace(' ', '').lower():
        return True
    raise ValueError(f"Title mismatch: {title} != {found_title}")

class FetchLyricsExecution(Execution):
    def check_cache(self, lyrics_cache_path: str) -> bool:
        """
        Check if the lyrics are already cached.
        """
        if os.path.exists(lyrics_cache_path):
            with open(lyrics_cache_path, 'r', encoding='utf-8') as f:
                lyrics = f.read()
                self.passing_args['lyrics'] = lyrics
                return True
        return False

    def _set_result(self, lyrics_cache_path: str) -> None:
        """
        Set the result of the lyrics retrieval task.
        """
        self.passing_args['lyrics_cache_path'] = lyrics_cache_path
        self.add_artifact(
            name='Lyrics found',
            artifact_type=ArtifactType.TEXT,
            artifact=self.passing_args['lyrics']
        )

    def _start(self, args: dict) -> None:
        """
        Search for lyrics using the MusixMatch API.
        See https://www.musixmatch.com/search for more details.
        """
        # Check if the lyrics are already cached
        lyrics_cache_path = os.path.join(self.config.media_path, args['source_audio'] + '.lib')
        if self.check_cache(lyrics_cache_path):
            self._set_result(lyrics_cache_path)
            self.update(message='Using cached lyrics')
            return

        media = args['media']
        # Check if the title is provided for lyrics search
        # If identify task is not able to find the title, 
        # use the title from the media metadata
        title = args.get('title') or media.metadata.get('title')
        artist = args.get('artist') or media.metadata.get('channel')
        if title is None:
            raise SoftFailure("No title found to search for lyrics")
        
        lyrics = None
        for provider_type in PROVIDERS:
            provider = provider_type(self)
            try:
                found_title, found_artist, lyrics = provider.search(title, artist)
                if not compare_artist(artist, found_artist):
                    self.logger.warning(f"Artist mismatch: {artist} != {found_artist}")
                    validate_title(title, found_title)
                break
            except Exception as e:
                provider.logger.error(f"{e}", exc_info=True)
                lyrics = None
        
        if lyrics is None:
            raise SoftFailure("Failed to fetch lyrics")

        self.passing_args['lyrics'] = lyrics
        # Save the lyrics to the cache
        with open(lyrics_cache_path, 'w', encoding='utf-8') as f:
            f.write(lyrics)
        self._set_result(lyrics_cache_path)
        self.update(message='Lyrics retrieval completed')

class FetchLyrics(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name="Lyrics retrieval", job=job, 
            execution_class=FetchLyricsExecution
        )
    
    