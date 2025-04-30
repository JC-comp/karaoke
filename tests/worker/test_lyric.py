import os
import pytest
import logging

from karaoke.utils.task import TaskStatus
from karaoke.worker.tasks.lyric import FetchLyricsExecution
from karaoke.worker.tasks.task import Task

def test_fetch_lyric_null(task: Task, logger: logging.Logger, passing_args: dict):
    exec = FetchLyricsExecution('test', task.config)
    passing_args['media'].metadata['title'] = None
    exec.start(task, logger, passing_args)
    
    assert task.status == TaskStatus.SOFT_FAILED
    assert task.message == "No title found to search for lyrics"

def check_lyrics(task: Task, message: str = 'Lyrics retrieval completed'):
    assert task.status == TaskStatus.COMPLETED

    if not task.execution.passing_args['lyrics'].startswith('Wee, huh'):
        pytest.fail(f"Lyrics {task.execution.passing_args['lyrics']} is not valid")
    assert task.message == message

    assert 'lyrics_cache_path' in task.execution.passing_args
    assert os.path.exists(task.execution.passing_args['lyrics_cache_path'])
    assert os.path.getsize(task.execution.passing_args['lyrics_cache_path']) > 0

def test_fetch_lyric_args(task: Task, logger: logging.Logger, passing_args: dict):
    exec = FetchLyricsExecution('test', task.config)
    passing_args['media'].metadata['title'] = None

    passing_args['source_video'] = ''
    passing_args['title'] = '暖暖'
    passing_args['artist'] = 'Fish Leong'
    exec.start(task, logger, passing_args)
    
    check_lyrics(task)

def test_fetch_lyric_metadata(task: Task, logger: logging.Logger, passing_args: dict):
    exec = FetchLyricsExecution('test', task.config)
    exec.start(task, logger, passing_args)
    check_lyrics(task)

@pytest.mark.parametrize('prepare_hidden_data', [['source.mp4.lib']], indirect=True)
def test_fetch_lyric_cache(task: Task, logger: logging.Logger, passing_args: dict, prepare_hidden_data):
    exec = FetchLyricsExecution('test', task.config)
    exec.start(task, logger, passing_args)
    
    check_lyrics(task, message='Using cached lyrics')