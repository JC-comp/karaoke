import os

from yt_dlp import YoutubeDL
from typing import Any
from .base import Task
from .cli import CLI
from .utils.artifact import ExportedArtifactTag, ArtifactType

class DownloadYoutubeTask(Task):
    task_method_name = "download"

    def __init__(self, format_key: str, run_id: str):
        if format_key == 'video':
            name='Video Downloading'
        elif format_key == 'audio':
            name='Audio Downloading'
        else:
            raise NotImplementedError()
        super().__init__(name, run_id, arglist=['url'])
        self.format_key = format_key
    
    def download(self, url: str) -> None:
        """
        Download video from youtube using yt-dlp. Extract metadata and 
        update the job with the metadata.
        See https://github.com/yt-dlp/yt-dlp for more details.

        Output:
            - identifier (str): unique identifier for the video
            - source_video (str): path to the downloaded video
            - source_audio (str): path to the downloaded audio
        """
        self.logger.info('Downloading video from youtube')
        outtmpl = os.path.join(self.config.cache_dir, f"%(id)s_{self.run_id}_{self.format_key}.%(ext)s")
        ydl_opts: Any = {
            "format": f"best{self.format_key}",
            "outtmpl": outtmpl,
            'color': 'no_color',
            'logger': self.logger,
            'noprogress': True,
            'noplaylist': True
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            # Extract metadata without downloading
            info = ydl.extract_info(url, download=False)
            output_path = ydl.prepare_filename(info)

            duration = info.get('duration')

            if not duration:
                raise ValueError("Duration not found in the video metadata")
            elif duration > 60 * 10:
                raise ValueError(f"Video duration is too long: {duration} seconds")
            
            # Update the job with metadata
            metadata = {
                'id': info['id'],
                'title': info.get('title'),
                'channel': info.get('channel'),
                'duration': info.get('duration')
            }
            if self.format_key == 'video':
                metadata.update({
                    'width': info.get('width'),
                    'height': info.get('height'),
                    'fps': info.get('fps'),
                })

            # Download the video
            ydl.process_info(info)

        self.add_artifact(
            key='source_' + self.format_key,
            name='Original ' + self.format_key,
            value=output_path,
            type=ArtifactType.AUDIO,
            attached=True
        )
        self.add_result(
            key='metadata',
            name='Metadata',
            value=metadata,
            type=ArtifactType.JSON,
            attached=True
        )
        self.add_export(
            result_key='metadata',
            tag=ExportedArtifactTag.METADATA
        )

        self.logger.info('Download successful')

if __name__ == "__main__":
    cli = CLI(
        description='Download task.',
        actionDesc='Download media'
    )
    cli.add_common_args(
        '--type', choices=['video', 'audio'], required=True, help='Media type'
    )
    cli.add_local_arg(
        '--url', required=True, help='Link to target'
    )
    task = DownloadYoutubeTask(format_key=cli.get('type'), run_id=cli.get_run_id())
    cli.execute(task)
    