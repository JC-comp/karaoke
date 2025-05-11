import unicodedata
import json
import os

from typing import TYPE_CHECKING
from pathlib import Path
from .task import Task, Execution, ArtifactType
from ..job import RemoteJob
import tqdm

if TYPE_CHECKING:
    from kalpy.fstext.lexicon import LexiconCompiler
    from montreal_forced_aligner.models import AcousticModel

class AlignLyricsExecution(Execution):
    def load_models(self, lang: str) -> tuple:
        """
        Load the acoustic model and lexicon compiler.
        """
        acoustic_model_path = self.config.get_mfa_model_path(lang, 'acoustic')
        dictionary_path = self.config.get_mfa_model_path(lang, 'dictionary')
        
        from kalpy.fstext.lexicon import LexiconCompiler
        from montreal_forced_aligner.models import AcousticModel
        acoustic_model = AcousticModel(acoustic_model_path)
        lexicon_compiler = LexiconCompiler(
            disambiguation=False,
            silence_probability=acoustic_model.parameters["silence_probability"],
            initial_silence_probability=acoustic_model.parameters["initial_silence_probability"],
            final_silence_correction=acoustic_model.parameters["final_silence_correction"],
            final_non_silence_correction=acoustic_model.parameters["final_non_silence_correction"],
            silence_phone=acoustic_model.parameters["optional_silence_phone"],
            oov_phone=acoustic_model.parameters["oov_phone"],
            position_dependent_phones=acoustic_model.parameters["position_dependent_phones"],
            phones=acoustic_model.parameters["non_silence_phones"],
            ignore_case=True,
        )
        lexicon_compiler.load_pronunciations(dictionary_path)

        return acoustic_model, lexicon_compiler

    def _preload(self):
        self.lang = 'zh'
        self.logger.info("Preloading models for alignment task")
        acoustic_model, lexicon_compiler = self.load_models(self.lang)
        self.acoustic_model = acoustic_model
        self.lexicon_compiler = lexicon_compiler
        self.logger.info("Models preloaded")

    def align(
        self, 
        pbar: tqdm.tqdm,
        acoustic_model: "AcousticModel", lexicon_compiler: "LexiconCompiler", 
        sound_file_path: Path,
        words: list[dict], start: float, end: float,
    ):
        """
        Align the lyrics with the audio.
        """
        from kalpy.feat.cmvn import CmvnComputer
        from kalpy.utterance import Segment
        from kalpy.utterance import Utterance as KalpyUtterance
        from montreal_forced_aligner.online.alignment import align_utterance_online
        # Remove unwanted characters
        removed_chars = ['\n', '\r', '\t', ' ']
        for char in removed_chars:
            for word in words:
                word['word'] = unicodedata.normalize("NFKC", word['word'].replace(char, ''))
        text = ' '.join([word['word'] for word in words])

        pbar.set_description(f"Generating audio features")

        seg = Segment(sound_file_path, start, end)
        utt = KalpyUtterance(seg, text)

        ctm = None
        try:
            utt.generate_mfccs(acoustic_model.mfcc_computer)
            cmvn = CmvnComputer().compute_cmvn_from_features([utt.mfccs])
            utt.apply_cmvn(cmvn)

            for beam in [10, 40]:
                try:
                    pbar.set_description(f'Aligning with beam {beam}')
                    ctm = align_utterance_online(
                        acoustic_model,
                        utt,
                        lexicon_compiler,
                        beam=beam,
                    )
                    break
                except Exception as e:
                    self.logger.debug(f'Error during alignment: {e}')
                    continue
        except Exception as e:
            self.logger.debug(f'Error during feature generation: {e}')
        
        if ctm is None:
            # If alignment fails, equally distribute the words
            # across the time interval
            pbar.write("Alignment failed, using fallback method")
            word_interval = (end - start) / len(words)
            for i in range(len(words)):
                words[i]['start'] = start + i * word_interval
                words[i]['end'] = start + (i + 1) * word_interval
        else:
            word_iter = iter(words)
            for word_interval in ctm.word_intervals:
                if word_interval.label != '<eps>':
                    word = next(word_iter)
                    word['start'] = word_interval.begin
                    word['end'] = word_interval.end
        return words
    
    def _set_result(self, audio_path: str, aligned_lyrics: list[dict]) -> None:
        """
        Set the result of the alignment task.
        """
        self.passing_args['aligned_lyrics'] = aligned_lyrics
        self.add_artifact(
            name='Aligned lyrics', 
            artifact_type=ArtifactType.SEGMENTS, 
            artifact={
                'segments': aligned_lyrics
            },
            attachments=[{
                'name': 'audio',
                'artifact_type': ArtifactType.AUDIO,
                'artifact': audio_path
            }]
        )

    def _external_long_running_task(self, args):
        lang, aligned_lyrics_cache_path, audio_path, sound_file_path, mapped_lyrics = args
        # Load the acoustic model and lexicon compiler
        self.update(message='Loading acoustic model')
        if self.lang != lang:
            acoustic_model, lexicon_compiler = self.load_models(lang)
            self.acoustic_model = acoustic_model
            self.lexicon_compiler = lexicon_compiler
        
        # Align the lyrics with the audio
        pbar = tqdm.tqdm(mapped_lyrics, unit='lyric')
        aligned_lyrics = []
        for lyrics in pbar:
            if len(lyrics['words']) == 1:
                word = lyrics['words'][0]
                word['start'] = lyrics['start']
                word['end'] = lyrics['end']
                result = [
                    word
                ]
            else:
                result = self.align(
                    pbar,
                    self.acoustic_model, self.lexicon_compiler, 
                    sound_file_path, 
                    lyrics['words'], lyrics['start'], lyrics['end']
                )
            
            aligned_lyrics.extend(result)

        with open(aligned_lyrics_cache_path, 'w', encoding='utf-8') as f:
            json.dump(aligned_lyrics, f, ensure_ascii=False, indent=4)
        self._set_result(audio_path, aligned_lyrics)
        self.update(message='Alignment completed')

    def _start(self, args):
        """
        Align each mapped lyric segment with the audio.

        Output:
            - aligned_lyrics (list[Word]): List of aligned lyrics with start and end times.
        
        Word:
            - word (str): The word in the lyric.
            - start (float): The start time of the word in seconds.
            - end (float): The end time of the word in seconds.
            - group (int): The group index of the word in the sentence.
        """
        self.update(message='Align lyrics from lyrics')
        audio_path = args['Vocals_only']
        mapped_lyrics = args['mapped_lyrics']
        aligned_lyrics_cache_path = os.path.join(self.config.media_path, audio_path + '.textgrid')

        # Check if the aligned lyrics are already cached
        if os.path.exists(aligned_lyrics_cache_path):
            with open(aligned_lyrics_cache_path, 'r', encoding='utf-8') as f:
                aligned_lyrics = json.load(f)
            self._set_result(audio_path, aligned_lyrics)
            self.update(message='Found aligned lyrics in cache')
            return
        
        lang = 'zh' # TODO: Determine language from audio
        sound_file_path = Path(audio_path)
                
        self._start_external_long_running_task((
            lang, aligned_lyrics_cache_path,
            audio_path, sound_file_path, mapped_lyrics
        ))
        
class AlignLyrics(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Lyrics alignment', job=job,
            execution_class=AlignLyricsExecution
        )
    
    