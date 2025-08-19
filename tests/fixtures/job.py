import pytest
import logging

from pathlib import Path

from karaoke.utils.job import JobType
from karaoke.worker.job import CommandJob
from karaoke.worker.tasks.task import Task, Execution

class MockExecution(Execution):
    """
    Mock Task class for testing
    """

@pytest.fixture
def task():
    """
    Fixture to create a task for testing.
    """
    return Task(
        name='test_task',
        job=CommandJob(
            job_type=JobType.YOUTUBE, 
            media={
                'source': 'https://www.youtube.com/watch?v=lA7aQKpjgqM',
                'metadata': {
                    'title': '暖暖',
                    'channel': 'Fish Leong',
                    'duration': 180,
                    'width': 640,
                    'height': 360
                }
            }
        ),
        execution_class=MockExecution
    )

@pytest.fixture
def logger():
    """
    Mock logger for testing.
    """
    logger = logging.getLogger('test_logger')
    logger.setLevel(logging.DEBUG)
    return logger

@pytest.fixture
def passing_args(task: Task, prepare_data: Path):
    """
    Fixture to create a prerequisite task for testing.
    """
    passing_args = {
        'source_video': str(prepare_data / 'source.mp4'),
        'source_audio': str(prepare_data / 'source.wav'),
        'media': task.job.media,
    }
    return passing_args