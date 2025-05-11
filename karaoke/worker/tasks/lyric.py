import os

from .execution import SoftFailure
from .task import Task, Execution, ArtifactType
from .providers.lyrics import PROVIDERS, compare
from ..job import RemoteJob
from ...utils.translate import convert_simplified_to_traditional

class FetchLyricsExecution(Execution):
    def _set_result(self, lyrics: str) -> None:
        """
        Set the result of the lyrics retrieval task.
        """
        self.passing_args['lyrics'] = lyrics
        self.add_artifact(
            name='Lyrics found',
            artifact_type=ArtifactType.TEXT,
            artifact=lyrics,
        )

    def _start(self, args: dict) -> None:
        """
        Search for lyrics using the MusixMatch API.
        See https://www.musixmatch.com/search for more details.

        Output:
            - lyrics (str): The cleaned lyrics of the song.
        """
        # Check if the lyrics are already cached
        lyrics_cache_path = os.path.join(self.config.media_path, args['source_audio'] + '.lib')
        if os.path.exists(lyrics_cache_path):
            with open(lyrics_cache_path, 'r', encoding='utf-8') as f:
                lyrics = f.read()
            self._set_result(lyrics)
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
                if not compare(artist, found_artist):
                    self.logger.warning(f"Artist mismatch: {artist} != {found_artist}")
                    if not compare(title, found_title):
                        raise ValueError(f"Title mismatch: {title} != {found_title}")
                break
            except Exception as e:
                provider.logger.error(f"{e}", exc_info=True)
                lyrics = None
        
        if lyrics is None:
            raise SoftFailure("Failed to fetch lyrics")
        
        lyrics = convert_simplified_to_traditional(lyrics)

        # Save the lyrics to the cache
        with open(lyrics_cache_path, 'w', encoding='utf-8') as f:
            f.write(lyrics)
        self._set_result(lyrics)
        self.update(message='Lyrics retrieval completed')

class FetchLyrics(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name="Lyrics retrieval", job=job, 
            execution_class=FetchLyricsExecution
        )
    
    