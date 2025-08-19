import json
import os

from .task import Task, Execution, ArtifactType
from ..job import RemoteJob
from ...utils.translate import convert_simplified_to_traditional
class TranscriptLyricsExecution(Execution):
    def _preload(self) -> bool:
        """
        Preload any resources needed for the task.
        """
        if hasattr(self, 'model'):
            self.logger.info("Whisper model already loaded")
            return True
        self.logger.info("Loading whisper model")
        import whisper
        import torch
        if torch.cuda.is_available():
            model = whisper.load_model(self.config.whisper_gpu_model)
        else:
            model = whisper.load_model(self.config.whisper_cpu_model)
        self.model = model
        self.logger.info("Whisper model loaded")
        return True

    def _set_result(self, vocal_path: str, segments: list[dict]) -> None:
        """
        Set the result of the transcription task.
        """
        self.passing_args['transcription'] = segments
        self.add_artifact(
            name='Transcription results', 
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
        
    def _external_long_running_task(self, args) -> None:
        """
        Run the transcription in a separate process to capture the progress in real-time.

        Output:
            - transcription (Word[]): List of words with their start and end times.
        
        Word:
            - start (float): Start time of the word in seconds.
            - end (float): End time of the word in seconds.
            - word (str): The word itself.
            - no_speech_prob (float): Probability of no speech in the corresponding segment.
        """
        vocal_path, vad_segments, transcription_cache_path = args
        self.update(message="Starting transcription")

        clip_timestamps = [
            float(ts)
            for segment in vad_segments
            for ts in [segment['start'], segment['end']]
        ]
        initial_prompt = self.config.whisper_initial_prompt

        result = self.model.transcribe(
            vocal_path, language="zh", initial_prompt=initial_prompt, 
            clip_timestamps=clip_timestamps,
            condition_on_previous_text=False,
            word_timestamps=True,
            verbose=False
        )

        self.update(message="Collecting transcription results")
        segments = [
            {
                "start": words["start"],
                "end": words["end"],
                "text": convert_simplified_to_traditional(words["word"]),
                "no_speech_prob": segment["no_speech_prob"],
            }
            for segment in result['segments']
            for words in segment['words']
        ]

        with open(transcription_cache_path, 'w') as f:
            json.dump(segments, f, ensure_ascii=False)
        self._set_result(vocal_path, segments)
        self.update(message='Transcription completed')
    
    def _start(self, args):
        """
        Transcribe the lyrics using whisper.
        See https://github.com/openai/whisper for more details.
        """
        self.update(message='Transcribing lyrics with whisper')
        vocal_path = args['Vocals_only']
        vad_segments = args['vad_segments']

        transcription_cache_path = os.path.join(vocal_path + '.transcript')
        if os.path.exists(transcription_cache_path):
            with open(transcription_cache_path, 'r') as f:
                segments = json.load(f)
            self._set_result(vocal_path, segments)
            self.update(message='Found transcription in cache')
            return
        
        self._start_external_long_running_task((vocal_path, vad_segments, transcription_cache_path))


class TranscriptLyrics(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Lyrics Transcription', job=job,
            execution_class=TranscriptLyricsExecution,
        )