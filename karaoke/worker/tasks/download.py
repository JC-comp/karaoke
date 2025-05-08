import os

from yt_dlp import YoutubeDL
from .task import Task, Execution, ArtifactType
from ..job import RemoteJob

class LoggerHook:
    def __init__(self, execution: Execution):
        self.execution = execution

    def handle(self, msg):
        self.execution.update(message=msg)
        
    def progress_hooks(self, d):
        message = d['_default_template']
        if d['status'] == 'finished':
            message += '\n'
        else:
            message += '\r'
        self.execution.progress_buffer.write(message)
    
    def flush(self):
        self.execution.progress_buffer.flush_progress()

    def info(self, msg):
        self.handle(msg)

    def debug(self, msg):
        self.handle(msg)

    def warning(self, msg):
        self.handle(msg)

    def error(self, msg):
        self.handle(msg)

class DownloadYoutubeExecution(Execution):
    def __init__(self, name, config, format_key):
        super().__init__(name, config)
        self.format_key = format_key

    def _start(self, args: dict) -> None:
        """
        Download video from youtube using yt-dlp. Extract metadata and 
        update the job with the metadata.
        See https://github.com/yt-dlp/yt-dlp for more details.
        """
        self.update(message='Downloading video from youtube')
        url = args['media'].source

        logger = LoggerHook(self)
        

        ydl_opts = {
            "format": f"best{self.format_key}",
            "outtmpl": os.path.join(self.config.media_path, f"%(id)s_{self.format_key}.%(ext)s"),
            'color': 'no_color',
            'logger': logger,
            'noprogress': True,
            'noplaylist': True,
            'progress_hooks': [logger.progress_hooks],
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            # Extract metadata without downloading
            info = ydl.extract_info(url, download=False)
            
            self.passing_args['source_' + self.format_key] = ydl.prepare_filename(info)

            if 'duration' not in info:
                raise ValueError("Duration not found in the video metadata")
            
            # Update the job with metadata
            self.update_job(media={
                'metadata': {
                    'id': info['id'],
                    'title': info['title'],
                    'channel': info['channel'],
                    'duration': info['duration']
                }
            })
            if self.format_key == 'video':
                self.update_job(media={
                    'metadata': {
                        'width': info['width'],
                        'height': info['height'],
                        'fps': info['fps'],
                    }
                })

            if info['duration'] > 60 * 10:
                raise ValueError(f"Video duration is too long: {info['duration']} seconds")

            # Download the video
            ydl.process_info(info)

            artifact_type = ArtifactType.VIDEO if self.format_key == 'video' else ArtifactType.AUDIO
            self.add_artifact('Original ' + self.format_key, artifact_type, self.passing_args['source_' + self.format_key])
        self.update(message='Download successful')
        logger.flush()

class DownloadYoutubeVideo(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Video Downloading',
            job=job,
            execution_class=DownloadYoutubeExecution,
            execution_kargs={
                'format_key': 'video'
            }
        )

class DownloadYoutubeAudio(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Audio Downloading',
            job=job,
            execution_class=DownloadYoutubeExecution,
            execution_kargs={
                'format_key': 'audio'
            }
        )
