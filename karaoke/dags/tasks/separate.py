import os
import torch
from concurrent.futures import ThreadPoolExecutor

from demucs.pretrained import get_model
from demucs.separate import load_track
from demucs.apply import apply_model
from demucs.audio import save_audio
from .base import Task
from .cli import CLI
from .utils.artifact import ExportedArtifactTag, ArtifactType

class SeparateAudio(Task):
    task_method_name = "seperate"
    def __init__(self, run_id: str):
        super().__init__(name='Stem Separation', run_id=run_id, arglist=['source_audio'])
        self.model_name = 'htdemucs'
    
    def seperate(self, audio_path: str) -> None:
        """
        Separate the audio into primary and secondary stems according to the model used.
        Run in a separate process so that we can capture the output and error streams.
        See https://github.com/nomadkaraoke/python-audio-separator for more details.

        Output:
            - Vocals_only (str): Path to the separated vocals audio file.
            - Instrumental_only (str): Path to the separated instrumental audio file.
        """
        self.logger.info('Seperate audio')
        self.logger.info('Loading model')

        model = get_model(name=self.model_name)
        model.cpu()
        model.eval()

        self.logger.info('Model loaded')

        wav = load_track(audio_path, model.audio_channels, model.samplerate)
        ref = wav.mean(0)
        wav = (wav - ref.mean()) / ref.std()
        self.logger.info('Starting separation')
        sources = apply_model(model, wav[None], device="cuda" if torch.cuda.is_available() else "cpu",
                              shifts=1, split=True, overlap=0.25, progress=True, num_workers=4)[0]
        self.logger.info('Separation done, saving stems')
        sources = sources * ref.std() + ref.mean()
        kwargs = {
            'samplerate': model.samplerate,
            'bitrate': 320,
            'clip': 'rescale',
            'as_float': False,
            'bits_per_sample': 16
        }
        output_dir = self.config.cache_dir

        sources = list(sources)
        vocal_tensor = sources.pop(model.sources.index('vocals'))
        # Warning : after poping the stem, selected stem is no longer in the list 'sources'
        instr_tensor = torch.zeros_like(sources[0])
        for i in sources:
            instr_tensor += i
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            vocal_stem_filepath = os.path.join(output_dir, 'vocals.mp3')
            executor.submit(save_audio, vocal_tensor, vocal_stem_filepath, preset=9, **kwargs)
            instrumental_stem_filepath = os.path.join(output_dir, 'instrumental.mp3')
            executor.submit(save_audio, instr_tensor, instrumental_stem_filepath, preset=5, **kwargs)
        
        self.add_artifact(
            key='Vocals_only',
            name=f'Vocals Stem',
            value=vocal_stem_filepath,
            type=ArtifactType.AUDIO,
            attached=True
        )
        self.add_artifact(
            key='Instrumental_only',
            name=f'Instrumental Stem',
            value=instrumental_stem_filepath,
            type=ArtifactType.AUDIO,
            attached=True
        )
        self.add_export(
            result_key='Instrumental_only',
            tag=ExportedArtifactTag.INSTRUMENTAL
        )

        self.logger.info('Separation completed')

if __name__ == "__main__":
    cli = CLI(
        description='Audio separation task.',
        actionDesc='Separate auido'
    )
    cli.add_local_arg(
        '--source_audio', required=True, help='Path to source audio'
    )
    
    task = SeparateAudio(run_id=cli.get_run_id())
    cli.execute(task)