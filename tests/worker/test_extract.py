import os
import logging

from karaoke.utils.task import TaskStatus
from karaoke.worker.tasks.extract import ExtractAudioExecution
from karaoke.worker.tasks.task import Task

def test_extraction(task: Task, logger: logging.Logger, passing_args: dict):
    source_path = passing_args['source_audio']
    expected_path = str(source_path) + '.mp3'
    
    exec = ExtractAudioExecution('test', task.config)
    exec.start(task, logger, passing_args)
    
    assert task.status == TaskStatus.COMPLETED
    assert task.execution.passing_args['audio_path'] == expected_path
    assert os.path.exists(expected_path)
    assert os.path.getsize(expected_path) > 0