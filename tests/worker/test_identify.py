import logging
import pytest

from pathlib import Path
from unittest.mock import MagicMock
from karaoke.worker.tasks.identify import IdentifyMusicExecution
import karaoke.worker.tasks.providers
import karaoke.worker.tasks.providers.identify
import karaoke.worker.tasks.providers.identify.gpt
from karaoke.worker.tasks.task import Task, TaskStatus

@pytest.fixture
def all_disabled(task: Task):
    task.config.acoustid_enabled = False
    task.config.gpt_enabled = False
    yield task
    task.config.acoustid_enabled = False
    task.config.gpt_enabled = False

@pytest.fixture
def acoustid_enabled(task: Task):
    task.config.acoustid_enabled = True
    task.config.gpt_enabled = False
    yield task
    task.config.acoustid_enabled = False

@pytest.fixture
def gpt_enabled(task: Task):
    task.config.gpt_enabled = True
    task.config.acoustid_enabled = False
    yield task
    task.config.gpt_enabled = False

def check_identify(task: Task):
    assert task.status == TaskStatus.COMPLETED
    assert task.execution.passing_args['title'] == '淚橋'
    assert task.execution.passing_args['artist'] == '伍佰 & China Blue'


def test_identify_null(all_disabled: Task, logger: logging.Logger, passing_args: dict):
    task = all_disabled
    exec = IdentifyMusicExecution('test', task.config)
    exec.start(task, logger, passing_args)
    
    assert task.status == TaskStatus.SOFT_FAILED
    assert task.execution.passing_args.get('title') is None
    assert task.execution.passing_args.get('artist') is None

def test_identify_acoustid(acoustid_enabled: Task, logger: logging.Logger, passing_args: dict, prepare_data: Path):
    task = acoustid_enabled
    
    passing_args['source_audio'] = prepare_data / 'fingerprint.mp3'
    
    exec = IdentifyMusicExecution('test', task.config)
    exec.start(task, logger, passing_args)

    check_identify(task)

def test_identify_gpt(gpt_enabled: Task, monkeypatch: MagicMock, logger: logging.Logger, passing_args: dict):
    task = gpt_enabled
    task.job.media.metadata = {
        'title': '淚橋',
        'artist': '伍佰 & China Blue'
    }
    monkeypatch.setattr(
        karaoke.worker.tasks.providers.identify.gpt, 'extract_artist_and_title', 
        MagicMock(return_value=(task.job.media.metadata['title'], task.job.media.metadata['artist']))
    )
    
    exec = IdentifyMusicExecution('test', task.config)
    exec.start(task, logger, passing_args)

    check_identify(task)
