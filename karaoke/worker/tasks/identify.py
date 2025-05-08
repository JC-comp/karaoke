from .execution import SoftFailure
from .task import Task, Execution,ArtifactType
from .providers.utils import NotEnabledException
from .providers.identify import PROVIDERS
from ..job import RemoteJob

class IdentifyMusicExecution(Execution):
    def identify_music(self, args: dict) -> tuple[str, str]:
        """
        Identify music using available providers.
        """
        audio_path = args['source_audio']
        media = args['media']
        title = media.metadata.get('title')
        artist = media.metadata.get('artist')
        for provider_type in PROVIDERS:
            provider = provider_type(self)
            try:
                return provider.identify(audio_path, title, artist)
            except NotEnabledException as e:
                provider.logger.info(f"{e}")
            except Exception as e:
                provider.logger.error(f"{e}", exc_info=True)

        return None, None

    def _start(self, args: dict) -> None:
        self.update(message='Identifying music')
        
        title, artist = self.identify_music(args)
        if title is None:
            raise SoftFailure("No music identified")
        
        self.passing_args['title'] = title
        self.passing_args['artist'] = artist
        
        self.add_artifact('Detected result', ArtifactType.JSON, {
            'title': self.passing_args['title'],
            'artist': self.passing_args['artist'],
        })
        self.update(message="Music identification successful")

class IdentifyMusic(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name="Music identification", job=job,
            execution_class=IdentifyMusicExecution,
        )