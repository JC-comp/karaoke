import logging
import os
import pytest

from karaoke.utils.task import TaskStatus
from karaoke.worker.tasks.task import Task
from karaoke.worker.tasks.download import DownloadYoutubeExecution
from karaoke.worker.job import CommandJob

@pytest.mark.parametrize(
    'format_key,expected_ext',
    [
        ('video', 'mp4'),
        ('audio', 'webm')
    ],
)
def test_download(task: Task, logger: logging.Logger, tmp_path, format_key, expected_ext):
    exec = DownloadYoutubeExecution('test', task.config, format_key)
    exec.start(task, logger, task.get_running_args())
    
    expected_path = tmp_path / f'lA7aQKpjgqM_{format_key}.{expected_ext}'
    
    assert task.status == TaskStatus.COMPLETED
    
    assert task.execution.passing_args[f'source_{format_key}'] == str(expected_path)
    assert expected_path.exists()
    assert os.path.getsize(expected_path) > 0
    
    if format_key == 'video':
        assert task.job.media.metadata['id'] == 'lA7aQKpjgqM'
        assert task.job.media.metadata['title'] == '南拳媽媽 -橘子汽水CHU TZU CHI SHUI (Official Music Video)'
        assert task.job.media.metadata['channel'] == '阿爾發音樂'
        assert task.job.media.metadata['duration'] == 217
        assert task.job.media.metadata['width'] == 640
        assert task.job.media.metadata['height'] == 480
        assert task.job.media.metadata['fps'] == 25

@pytest.mark.parametrize(
    'format_key',
    ['video', 'audio']
)
def test_download_failed(task: Task, logger: logging.Logger, format_key: str):
    exec = DownloadYoutubeExecution('test', task.config, format_key)
    task.job.media.source = 'https://www.youtube.com/watch?v=invalid_video_id'
    exec.start(task, logger, task.get_running_args())

    assert task.status == TaskStatus.FAILED