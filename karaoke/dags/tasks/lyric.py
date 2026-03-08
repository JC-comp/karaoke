from typing import Optional
from .base import Task
from .providers.lyrics import PROVIDERS, compare
from .utils.translate import convert_simplified_to_traditional
from .cli import CLI
from .utils.artifact import ArtifactType

class FetchLyrics(Task):
    task_method_name = "search"

    def __init__(self, run_id: str):
        super().__init__(name="Lyrics retrieval", run_id=run_id, arglist=['title', 'artist', 'metadata'])
    
    def search(self, title: Optional[str], artist: Optional[str], metadata: dict) -> None:
        """
        Search for lyrics using the MusixMatch API.
        See https://www.musixmatch.com/search for more details.

        Output:
            - lyrics (str): The cleaned lyrics of the song.
        """
        title = title or metadata.get('title')
        artist = artist or metadata.get('channel')
        
        if title is None or artist is None:
            self.logger.warning("No title/artist found to search for lyrics")
            return
        
        lyrics = None
        for provider_type in PROVIDERS:
            provider = provider_type(self.config)
            try:
                found_title, found_artist, lyrics = provider.search(title, artist)
                if not compare(artist, found_artist):
                    self.logger.warning(f"Artist mismatch: {artist} != {found_artist}")
                    if not compare(title, found_title):
                        raise ValueError(f"Title mismatch: {title} != {found_title}")
                break
            except Exception as e:
                self.logger.error(f"{e}")
                lyrics = None
        
        if lyrics is None:
            self.logger.warning("Failed to find lyrics")
            return
        
        lyrics = convert_simplified_to_traditional(lyrics)
        self.add_result(
            key='lyrics',
            name='Lyrics',
            value=lyrics,
            type=ArtifactType.TEXT,
            attached=True
        )
        self.logger.info('Lyrics retrieval completed')

if __name__ == "__main__":
    cli = CLI(
        description='Retrive song lyrics from metadata.',
        actionDesc='Retrive song lyrics'
    )
    cli.add_local_arg(
        '--title', required=True, help='Title of the song'
    )
    cli.add_local_arg(
        '--artist', required=True, help='Artist of the song'
    )
    cli.add_local_json_arg(
        'metadata', '--metadata', required=True, help='Metada of the song in json format'
    )
    task = FetchLyrics(run_id=cli.get_run_id())
    cli.execute(task)
    