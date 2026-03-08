import json
import os
import whisper
import torch
import stable_whisper
import socket

from typing import Optional, cast, Any
from whisper.model import Whisper
from .base import Task
from .utils.translate import convert_simplified_to_traditional
from .cli import CLI
from .utils.artifact import ArtifactType

class TranscriptLyrics(Task):
    task_method_name = 'transcribe_api'
    def __init__(self, run_id: str):
        super().__init__("Lyrics Transcription", run_id, arglist=['Vocals_only', 'vad_segments', 'lyrics'])
        self.model: Optional[Whisper] = None

    def preload(self) -> bool:
        """
        Preload any resources needed for the task.
        """
        if self.model is not None:
            self.logger.info("Whisper model already loaded")
            return True
        self.logger.info("Loading whisper model")
        
        if torch.cuda.is_available():
            model_name = self.config.transcription.gpu_model
        else:
            model_name = self.config.transcription.cpu_model
        model = stable_whisper.load_model(
            model_name,
            download_root=os.path.join(self.config.model_dir, 'whisper')
        )
        self.model = model
        self.logger.info("Whisper model loaded")
        return True
        
    def transcribe(self, vocal_path: str, vad_segments_path: str, lyrics: str) -> None:
        """
        Transcribe the lyrics using whisper.
        See https://github.com/openai/whisper for more details.
        
        Output:
            - transcription (Word[]): List of words with their start and end times.
        
        Word:
            - start (float): Start time of the word in seconds.
            - end (float): End time of the word in seconds.
            - text (str): The word itself.
            - no_speech_prob (float): Probability of no speech in the corresponding segment.
        """
        self.preload()
        if not self.model:
            raise RuntimeError('Model is not ready')
        initial_prompt = self.config.transcription.initial_prompt

        result = None
        if lyrics:
            self.logger.info("Starting transcription with lyrics")
            result = self.model.align(
                vocal_path, lyrics, language="zh",
                verbose=False
            )
        if result is None:
            self.logger.info("Starting transcription without lyrics")
            with open(vad_segments_path) as f:
                vad_segments = json.loads(f.read())
            clip_timestamps = [
                float(ts)
                for segment in vad_segments
                for ts in [segment['start'], segment['start'] + segment['duration']]
            ]
            result = self.model.transcribe(
                vocal_path, language="zh", initial_prompt=initial_prompt, 
                clip_timestamps=clip_timestamps,
                condition_on_previous_text=False,
                word_timestamps=True,
                verbose=False
            )
        result = result.to_dict()
        self.post_process(result)

    def transcribe_api(self, vocal_path: str, vad_segments_path: str, lyrics: str) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.config.transcription.host, self.config.transcription.port))
            send_data = json.dumps({
                "vocal_path": vocal_path,
                "vad_segments_path": vad_segments_path,
                "lyrics": lyrics
            }).encode("utf-8")
            self.logger.info(f"Sending data length: {len(send_data)}")
            s.sendall(len(send_data).to_bytes(4, "big"))
            s.sendall(send_data)

            data_len = s.recv(4)
            data_len = int.from_bytes(data_len, "big")
            data = b''
            while len(data) < data_len:
                data += s.recv(data_len - len(data))
            data = data.decode("utf-8")
            data = json.loads(data)
            self.post_process(data)


    def post_process(self, result: dict) -> None:
        segments_data = cast(list[dict[str, Any]], result.get('segments', []))

        self.logger.info("Collecting transcription results")
        segments = [
            {
                "start": words["start"],
                "end": words["end"],
                "text": convert_simplified_to_traditional(words["word"]),
                "no_speech_prob": segment.get("no_speech_prob"),
            }
            for segment in segments_data
            for words in segment.get('words', [])
        ]

        self.add_json_artifact(
            key='transcription',
            name='Transcription',
            value=segments,
            type=ArtifactType.JSON,
            attached=False
        )
        self.add_result(
            key='transcription_viewer',
            name='Transcription',
            value={
                'segment': 'transcription',
                'audio': 'Vocals_only'
            },
            type=ArtifactType.SEGMENT,
            attached=True
        )
        self.logger.info('Transcription completed')

if __name__ == "__main__":
    cli = CLI(
        description='Audio transcription task.',
        actionDesc='transcribe auido'
    )
    cli.add_local_arg(
        '--Vocals_only', required=True, help='Path to separated vocal file'
    )
    cli.add_local_arg(
        '--vad_segments', required=True, help='Path to vad segment file'
    )
    cli.add_local_arg(
        '--lyrics', required=True, help='Lyric text'
    )
    task = TranscriptLyrics(run_id=cli.get_run_id())
    cli.execute(task)