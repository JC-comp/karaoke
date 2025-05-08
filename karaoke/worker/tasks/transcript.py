import json
import os

from .task import Task, Execution, ArtifactType
from ..job import RemoteJob
from ...utils.translate import convert_simplified_to_traditional

def convert_timestamps(segments: list[dict], time: float):
    """
    Convert the time in VAD results to the time in original audio.
    """
    min_diff = float('inf')
    closest_segment = None
    for segment in segments:
        if time >= segment['start'] and time <= segment['end']:
            return segment['original_start'] + (time - segment['start'])
        diff = min(abs(segment['start'] - time), abs(segment['end'] - time))
        if diff < min_diff:
            min_diff = diff
            closest_segment = segment
    
    if closest_segment is None:
        raise ValueError("No closest segment found")
    return closest_segment['original_start'] + time - closest_segment['start']

class TranscriptLyricsExecution(Execution):
    def _preload(self) -> bool:
        """
        Preload any resources needed for the task.
        """
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

    def _set_result(self, vad_vocal_path: str, transcription_cache_path: str, segments: list[dict]) -> None:
        """
        Set the result of the transcription task.
        """
        self.passing_args['transcription_cache_path'] = transcription_cache_path
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
                'artifact': vad_vocal_path
            }]
        )
        
    def _external_long_running_task(self, args) -> None:
        """
        Run the transcription in a separate process to capture the progress in real-time.
        """
        vad_vocal_path, vad_segments = args
        
        transcription_cache_path = os.path.join(vad_vocal_path + '.transcript')
        if os.path.exists(transcription_cache_path):
            with open(transcription_cache_path, 'r') as f:
                segments = json.load(f)
                self._set_result(vad_vocal_path, transcription_cache_path, segments)
                self.update(message='Found transcription in cache')
                return

        self.update(message="Starting transcription")
        
        initial_prompt = self.config.whisper_initial_prompt
        result = self.model.transcribe(
            vad_vocal_path, language="zh", initial_prompt=initial_prompt, 
            word_timestamps=True,
            verbose=False
        )
        self.update(message="Collecting transcription results")
        segments = [
            {
                "start": convert_timestamps(vad_segments, words["start"]),
                "end": convert_timestamps(vad_segments, words["end"]),
                "original_start": words["start"],
                "original_end": words["end"],
                "text": convert_simplified_to_traditional(words["word"]),
                "no_speech_prob": segment["no_speech_prob"],
            }
            for segment in result['segments']
            for words in segment['words']
        ]
        with open(transcription_cache_path, 'w') as f:
            json.dump(segments, f, ensure_ascii=False)
        self._set_result(vad_vocal_path, transcription_cache_path, segments)
        self.update(message='Transcription completed')
    
    def _start(self, args):
        """
        Transcribe the lyrics using whisper.
        See https://github.com/openai/whisper for more details.
        """
        self.update(message='Transcribing lyrics with whisper')
        vad_vocal_path = args['vad_vocal_path']
        vad_segments = args['vad_segments']
        
        self._start_external_long_running_task((vad_vocal_path, vad_segments))


class TranscriptLyrics(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Lyrics Transcription', job=job,
            execution_class=TranscriptLyricsExecution,
        )