from auditok import split
from .task import Task, Execution, ArtifactType
from ..job import RemoteJob

class VoiceActivityExecution(Execution):
    def _start(self, args: dict) -> None:
        """
        Detects voice activity with auditok.
        See https://github.com/amsehili/auditok for more details.

        Output:
            - vad_segments (Segments[]): List of segments with start and end times.

        Segments:
            - start (float): Start time of the segment in seconds.
            - end (float): End time of the segment in seconds.
            - duration (float): Duration of the segment in seconds.
        """
        vocal_path = args['Vocals_only']

        self.update(message='Detecting voice activity')
        # Split the audio into segments
        voice_segments = list(split(input=vocal_path, max_dur=600))
        # Export the segments with their start and end times in original audio
        segments = []
        accum = 0
        for i in voice_segments:
            segments.append(
                {
                    "start": i.start,
                    "end": i.end,
                    "duration": i.end - i.start
                }
            )
            accum += i.end - i.start + 1

        self.passing_args['vad_segments'] = segments
        self.add_artifact(
            name='Detected voice activity segments', 
            artifact_type=ArtifactType.SEGMENTS, 
            artifact={
                'segments': segments
            },
            attachments=[{
                'name': 'audio',
                'artifact_type': ArtifactType.AUDIO,
                'artifact': vocal_path
            }]
        )

        self.update(message="Voice activity detection completed")
        
class VoiceActivity(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Voice activity detection', job=job,
            execution_class=VoiceActivityExecution
        )
        