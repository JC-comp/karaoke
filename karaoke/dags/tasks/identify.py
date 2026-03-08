from .cli import CLI
from .base import Task
from .providers.utils import NotEnabledException
from .providers.identify import PROVIDERS
from .utils.translate import convert_simplified_to_traditional
from .utils.artifact import ArtifactType

class IdentifyMusic(Task):
    task_method_name = "identify_music"
    def __init__(self, run_id: str):
        super().__init__("Music identification", run_id, arglist=['source_audio'])
   
    def identify_music(self, audio_path: str) -> None:
        """
        Identify music using available providers.

        Output:
            - title? (str): cleaned title
            - artist? (str): cleaned artist
        """
        title, artist = None, None
        for provider_type in PROVIDERS:
            provider = provider_type(self.config)
            try:
                title, artist = provider.identify(audio_path)
                break
            except NotEnabledException as e:
                self.logger.info(f"{e}")
            except Exception as e:
                self.logger.error(f"{e}", exc_info=True)

        if title is None:
            self.logger.warning("No identification results found")
            return
        
        self.add_result(
            key='title',
            name='Title',
            value=convert_simplified_to_traditional(title),
            type=ArtifactType.TEXT,
            attached=True
        )
        self.add_result(
            key='artist',
            name='Artist',
            value=convert_simplified_to_traditional(artist),
            type=ArtifactType.TEXT,
            attached=True
        )
        
        self.logger.info("Music identification successful")

if __name__ == "__main__":
    cli = CLI(
        description='Identify song name from audio.',
        actionDesc='Identify audio'
    )
    cli.add_local_arg(
        '--source_audio', required=True, help='Path to target audio'
    )
    cli.parse_args()
    
    task = IdentifyMusic(run_id=cli.get_run_id())
    cli.execute(task)