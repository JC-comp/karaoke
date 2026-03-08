from auditok import split
from .base import Task
from .cli import CLI
from .utils.artifact import ArtifactType

class VoiceActivity(Task):
    task_method_name = "detect"
    def __init__(self, run_id: str):
        super().__init__(name='Voice activity detection', run_id=run_id, arglist=['Vocals_only'])
    
    def detect(self, vocal_path: str) -> None:
        """
        Detects voice activity with auditok.
        See https://github.com/amsehili/auditok for more details.

        Output:
            - vad_segments (Segments[]): List of segments with start and end times.

        Segments:
            - start (float): Start time of the segment in seconds.
            - duration (float): Duration of the segment in seconds.
        """
        self.logger.info('Detecting voice activity')
        # Split the audio into segments
        voice_segments = list(split(input=vocal_path, max_dur=600))
        # Export the segments with their start and end times in original audio
        segments = []
        for i in voice_segments:
            segments.append(
                {
                    "start": i.start,
                    "duration": getattr(i, 'duration')
                }
            )
        self.add_json_artifact(
            key='vad_segments',
            name='Vad segments',
            value=segments,
            type=ArtifactType.JSON,
            attached=False
        )
        self.add_result(
            key='vad_segment_viewer',
            name='Vad Segments',
            value={
                'segment': 'vad_segments',
                'audio': 'Vocals_only'
            },
            type=ArtifactType.SEGMENT,
            attached=True
        )
        self.logger.info("Voice activity detection completed")

if __name__ == "__main__":
    cli = CLI(
        description='Voice activity detection task.',
        actionDesc='Detect voice'
    )
    cli.add_local_arg(
        '--Vocals_only', required=True, help='Path to separated vocal file'
    )
    task = VoiceActivity(run_id=cli.get_run_id())
    cli.execute(task)