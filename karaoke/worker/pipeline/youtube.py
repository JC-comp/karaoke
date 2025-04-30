from .pipeline import Pipeline
from ..tasks.task import Task
from ..tasks.download import DownloadYoutubeVideo, DownloadYoutubeAudio
from ..tasks.extract import ExtractAudio
from ..tasks.seprate import SeperateVocal, SeperateInstrument
from ..tasks.lyric import FetchLyrics
from ..tasks.align import AlignLyrics
from ..tasks.mapping  import MapLyrics
from ..tasks.transcript import TranscriptLyrics
from ..tasks.subtitle import GenerateSubtitle
from ..tasks.generate import GenerateVideo
from ..tasks.identify import IdentifyMusic
from ..tasks.detect import VoiceActivity

class YoutubePipeline(Pipeline):
    def build_pipeline(self) -> list[Task]:
        download_video = DownloadYoutubeVideo(self.job)
        download_audio = DownloadYoutubeAudio(self.job)
        identify = IdentifyMusic(self.job)
        lyric = FetchLyrics(self.job)
        seperate_vocal = SeperateVocal(job=self.job)
        seperate_instrument = SeperateInstrument(job=self.job)
        voice_activity = VoiceActivity(self.job)
        transcript = TranscriptLyrics(self.job)
        mapping = MapLyrics(self.job)
        align = AlignLyrics(self.job)
        subtitle = GenerateSubtitle(self.job)
        video = GenerateVideo(self.job)

        identify.add_prerequisite(download_video) # extract from downloaded metadata
        identify.add_prerequisite(download_audio) # using the audio fingerprint

        lyric.add_prerequisite(identify)
        lyric.add_prerequisite(download_video) # using the download metadata for the case of no identify 

        seperate_vocal.add_prerequisite(download_audio)
        seperate_instrument.add_prerequisite(download_audio)
        seperate_instrument.add_prerequisite(seperate_vocal) # ensure one gpu task at a time

        voice_activity.add_prerequisite(seperate_vocal)

        transcript.add_prerequisite(voice_activity) # using audio without silence to reduce hallucination
        # transcript.add_prerequisite(seperate_instrument) # ensure one gpu task at a time

        mapping.add_prerequisite(lyric)
        mapping.add_prerequisite(transcript)
        mapping.add_prerequisite(seperate_vocal) # preview with vocal only audio
        
        align.add_prerequisite(seperate_vocal)
        align.add_prerequisite(mapping)

        subtitle.add_prerequisite(align)

        video.add_prerequisite(download_video)
        video.add_prerequisite(identify) # get metadata info
        video.add_prerequisite(seperate_instrument)
        video.add_prerequisite(seperate_vocal) # for production preview
        video.add_prerequisite(subtitle)

        return [
            download_video,
            download_audio,
            identify,
            lyric,
            seperate_vocal,
            seperate_instrument,
            voice_activity,
            transcript,
            mapping,
            align,
            subtitle,
            video
        ]