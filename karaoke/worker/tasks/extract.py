from .task import Task, Execution, ArtifactType
from ..job import RemoteJob

class ExtractAudioExecution(Execution):
    def _start(self, args: dict) -> None:
        """
        Extract audio from the video file using ffmpeg.
        """
        self.update(message='Extracting audio from youtube video')
        source_path = args['source_audio']
        audio_path = source_path + '.mp3'
        
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-y", '-nostdin',
            "-i", source_path,  # Input file path
            "-vn",  # Only keep the audio
            "-f", "mp3",  # Output format
            audio_path,  # Output file path
        ]
        self.logger.info(f"Running command: {' '.join(cmd)}")
        
        self._start_external_command(cmd)
        self.passing_args['source_path'] = source_path
        self.passing_args['audio_path'] = audio_path
        self.add_artifact('Original Audio', ArtifactType.AUDIO, audio_path)

        self.update(message="Audio extraction completed")
        
class ExtractAudio(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Audio extraction', job=job,
            execution_class=ExtractAudioExecution
        )
        