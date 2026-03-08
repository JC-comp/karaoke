import os
import socket
import json

from typing import Optional
from audio_separator.separator import Separator
from .base import Task
from .cli import CLI
from .utils.artifact import ExportedArtifactTag, ArtifactType

class SeparateAudio(Task):
    task_method_name = "seperate"
    def __init__(self, name: str, run_id: str, model_name: str, output_stem: str):
        super().__init__(name=name, run_id=run_id, arglist=['source_audio'])
        self.model_name = model_name
        self.output_stem = output_stem
        self.output_format = "mp3"
        self.separator: Optional[Separator] = None
    
    def preload(self) -> bool:
        """
        Preload models for the separation task.
        """
        if self.separator is not None:
            self.logger.info("Models already preloaded")
            return True
        self.logger.info("Preloading models for separation task")
        
        self.output_format = "mp3"
        separator = Separator(
            model_file_dir=os.path.join(self.config.model_dir, 'separation'),
            output_format=self.output_format,
            output_single_stem=self.output_stem
        )
        separator.load_model(model_filename=self.model_name)
        self.separator = separator
        self.logger.info("Models preloaded")
        return True
    
    def seperate_api(self, audio_path: str) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.config.separation.host, self.config.separation.port))
            send_data = json.dumps({
                "audio_path": audio_path,
                "output_stem": self.output_stem
            }).encode("utf-8")
            self.logger.info(f"Sending data length: {len(send_data)}")
            s.sendall(len(send_data).to_bytes(4, "big"))
            s.sendall(send_data)

            data_len = s.recv(4)
            data_len = int.from_bytes(data_len, "big")
            data = s.recv(data_len)
            data = data.decode("utf-8")
            data = json.loads(data)
            self.post_process(data)

    def seperate(self, audio_path: str) -> None:
        """
        Separate the audio into primary and secondary stems according to the model used.
        Run in a separate process so that we can capture the output and error streams.
        See https://github.com/nomadkaraoke/python-audio-separator for more details.

        Output:
            - Vocals_only (str): Path to the separated vocals audio file.
            - Instrumental_only (str): Path to the separated instrumental audio file.
        """
        self.preload()
        if self.separator is None or self.separator.model_instance is None:
            raise RuntimeError("Model is not ready")
        self.logger.info('Seperate audio')
        output_dir = self.config.cache_dir
        
        audio_file_base = os.path.splitext(os.path.basename(audio_path))[0]
        primary_stem_name = f"{audio_file_base}_{self.output_stem}"
        custom_output_names = {
            self.output_stem: primary_stem_name,
        }

        # Run the separation 
        self.separator.output_dir = output_dir
        self.separator.model_instance.output_dir = output_dir
        primary_stem_filename, = self.separator.separate(audio_path, custom_output_names=custom_output_names)
        output_filepath = os.path.join(output_dir, primary_stem_filename)
        self.post_process(output_filepath)
        

    def post_process(self, output_filepath: str) -> None:
        self.add_artifact(
            key=self.output_stem + '_only',
            name=f'{self.output_stem} Stem',
            value=output_filepath,
            type=ArtifactType.AUDIO,
            attached=True
        )
        if self.output_stem == 'Instrumental':
            self.add_export(
                result_key=self.output_stem + '_only',
                tag=ExportedArtifactTag.INSTRUMENTAL
            )

        self.logger.info('Separation completed')

if __name__ == "__main__":
    cli = CLI(
        description='Audio separation task.',
        actionDesc='Separate auido'
    )
    cli.add_common_args(
        '--type', choices=['instrument', 'vocal'], required=True, help='Target type'
    )
    cli.add_local_arg(
        '--source_audio', required=True, help='Path to source audio'
    )
    job_type = cli.get('type')
    
    if job_type == 'instrument':
        name = 'Instrument Separation'
        model_name = 'UVR_MDXNET_KARA_2.onnx'
        output_stem = 'Instrumental'
    elif job_type == 'vocal':
        name = 'Vocal Separation'
        model_name = 'Kim_Vocal_2.onnx'
        output_stem = 'Vocals'
    else:
        raise NotImplementedError()
    
    task = SeparateAudio(name=name, run_id=cli.get_run_id(), model_name=model_name, output_stem=output_stem)
    cli.execute(task)