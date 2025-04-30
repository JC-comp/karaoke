import json

from auditok import split, make_silence
from .task import Task, Execution, ArtifactType
from ..job import RemoteJob

class VoiceActivityExecution(Execution):
    def _start(self, args: dict) -> None:
        """
        Detects voice activity with auditok.
        See https://github.com/amsehili/auditok for more details.
        """
        vocal_path = args['Vocals_only']
        vad_vocal_path = args['Vocals_only'] + '_vad.mp3'
        vad_segments_cache = args['Vocals_only'] + '_vad.seg'

        self.update(message='Detecting voice activity')
        # Split the audio into segments
        voice_segments = list(split(input=vocal_path, max_dur=600))
        # Join the segments into a single audio file with 1 second of silence
        silence_seconds = 1
        first = voice_segments[0]
        silence = make_silence(silence_seconds, first.sr, first.sw, first.ch)
        silence.join(voice_segments).save(vad_vocal_path)
        # Export the segments with their start and end times in original audio
        segments = []
        accum = 0
        for idx, i in enumerate(voice_segments):
            segments.append(
                {
                    "start": accum,
                    "end": accum + i.end - i.start,
                    "duration": i.end - i.start,
                    "original_start": i.start,
                    "original_end": i.end,
                }
            )
            accum += i.end - i.start + 1

        self.passing_args['vad_vocal_path'] = vad_vocal_path
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

        with open(vad_segments_cache, 'w') as f:
            json.dump(segments, f, ensure_ascii=False)
        
        self.update(message="Voice activity detection completed")
        
class VoiceActivity(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Voice activity detection', job=job,
            execution_class=VoiceActivityExecution
        )
        