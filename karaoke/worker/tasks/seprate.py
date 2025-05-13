import os

from .task import Task, Execution, ArtifactType
from ..job import RemoteJob

class SeperateAudioExecution(Execution):
    def __init__(self, name, config, model_name, passing_key):
        super().__init__(name, config)
        self.model_name = model_name
        self.passing_key = passing_key

    def get_daemon_socket(self) -> str:
        return self.__class__.__name__.lower() + '_' + self.model_name.lower() + '.sock'

    def _preload(self) -> bool:
        """
        Preload models for the separation task.
        """
        if hasattr(self, 'separator'):
            self.logger.info("Models already preloaded")
            return True
        self.logger.info("Preloading models for separation task")
        from audio_separator.separator import Separator
        self.output_format = "mp3"
        separator = Separator(
            model_file_dir='model',
            output_format=self.output_format,
            output_single_stem=self.passing_key
        )
        separator.load_model(model_filename=self.model_name)
        self.separator = separator
        self.logger.info("Models preloaded")
        return True

    def _set_result(self, audio_path: str) -> None:
        """
        Set the result of the separation task.
        """
        self.passing_args[self.passing_key + '_only'] = audio_path
        self.add_artifact(
            name=f'Separated {self.passing_key}',
            tag=self.passing_key,
            artifact_type=ArtifactType.AUDIO,
            artifact=audio_path
        )

    def _external_long_running_task(self, args) -> None:
        """
        Separate the audio into primary and secondary stems according to the model used.
        Run in a separate process so that we can capture the output and error streams.
        See https://github.com/nomadkaraoke/python-audio-separator for more details.

        Output:
            - Vocals_only (str): Path to the separated vocals audio file.
            - Instrumental_only (str): Path to the separated instrumental audio file.
        """
        audio_path, output_dir = args
        
        audio_file_base = os.path.splitext(os.path.basename(audio_path))[0]
        primary_stem_name = f"{audio_file_base}_{self.passing_key}"
        primary_stem_path = os.path.join(output_dir, primary_stem_name + '.' + self.output_format)
        custom_output_names = {
            self.passing_key: primary_stem_name,
        }
        # Check if the output targets are already cached
        if os.path.exists(primary_stem_path):
            self.update(message='Found separated audio in cache')
            self._set_result(primary_stem_path)
            return

        # Run the separation 
        self.separator.output_dir = output_dir
        self.separator.model_instance.output_dir = output_dir
        primary_stem_name, = self.separator.separate(audio_path, custom_output_names=custom_output_names)
        self._set_result(os.path.join(output_dir, primary_stem_name))
        self.update(message='Separation completed')
    
    def _start(self, args):
        self.update(message='Seperate audio from video')
        audio_path = args['source_audio']
        output_dir = os.path.dirname(os.path.abspath(audio_path))
        self._start_external_long_running_task((audio_path, output_dir))

class SeperateAudio(Task):
    def __init__(
        self, name: str, job: RemoteJob, 
        passing_key: str, model_name: str
    ):
        super().__init__(
            name=name, job=job, 
            execution_class=SeperateAudioExecution,
            execution_kargs={
                'model_name': model_name,
                'passing_key': passing_key,
            }
        )

class SeperateVocal(SeperateAudio):
    def __init__(
        self, job: RemoteJob
    ):
        super().__init__(
            name='Vocal Separation', job=job, 
            passing_key='Vocals',
            model_name= 'Kim_Vocal_2.onnx',
        )

class SeperateInstrument(SeperateAudio):
    def __init__(
        self, job: RemoteJob
    ):
        super().__init__(
            name='Instrument Separation', job=job, 
            passing_key='Instrumental',
            model_name= 'UVR_MDXNET_KARA_2.onnx'
        )
    
    