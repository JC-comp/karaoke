import os
import json
import socket
import logging
import logging.config
import torch
import stable_whisper
from config import config

logging.config.dictConfig({
            "version": 1,
            "formatters": {
                "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
                "detailed": {"format": "%(asctime)s [%(levelname)s] %(module)s.%(funcName)s:%(lineno)d: %(message)s"},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": config.log_level,
                },
            },
            "loggers": {
                "": {
                    "handlers": ["console"],
                    "level": config.log_level,
                },
            }
        })

logger = logging.getLogger("transcribe")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 5000))
server.listen(1)

logger.info("GPU transcription worker started")

logger.info("Loading whisper model")
        
if torch.cuda.is_available():
    model_name = config.transcription.gpu_model
else:
    model_name = config.transcription.cpu_model
model = stable_whisper.load_model(
    model_name,
    download_root=os.path.join(config.model_dir, 'whisper')
)
logger.info("Whisper model loaded")

def transcribe(vocal_path: str, vad_segments_path: str, lyrics: str) -> None:
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
    initial_prompt = config.transcription.initial_prompt

    result = None
    if lyrics:
        logger.info("Starting transcription with lyrics")
        result = model.align(
            vocal_path, lyrics, language="zh",
            verbose=False
        )
    if result is None:
        logger.info("Starting transcription without lyrics")
        with open(vad_segments_path) as f:
            vad_segments = json.loads(f.read())
        clip_timestamps = [
            float(ts)
            for segment in vad_segments
            for ts in [segment['start'], segment['start'] + segment['duration']]
        ]
        result = model.transcribe(
            vocal_path, language="zh", initial_prompt=initial_prompt, 
            clip_timestamps=clip_timestamps,
            condition_on_previous_text=False,
            word_timestamps=True,
            verbose=False
        )
    result = result.to_dict()
    return result

while True:
    conn, addr = server.accept()
    try:
        logger.info(f"Connected to {addr}")

        data_len = conn.recv(4)
        data_len = int.from_bytes(data_len, "big")
        logger.info(f"Received data length: {data_len}")
        data = conn.recv(data_len)
        data = data.decode("utf-8")
        data = json.loads(data)
        logger.info(f"Received data: {json.dumps(list(data.keys()), indent=4)}")
        vocal_path = data["vocal_path"]
        lyrics = data["lyrics"]
        vad_segments_path = data["vad_segments_path"]
        
        result = transcribe(vocal_path, vad_segments_path, lyrics)

        send_data = json.dumps(result).encode("utf-8")
        conn.sendall(len(send_data).to_bytes(4, "big"))
        conn.sendall(send_data)
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        conn.close()