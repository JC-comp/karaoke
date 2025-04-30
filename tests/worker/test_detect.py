import pytest
import logging

from tests.helper import check_file_exists
from karaoke.utils.task import TaskStatus
from karaoke.worker.tasks.detect import VoiceActivityExecution
from karaoke.worker.tasks.task import Task

@pytest.mark.parametrize(
    'prepare_hidden_data',
    [
        ['audio_(Vocals)_Kim_Vocal_2.wav'],
    ],
    indirect=True
)
def test_vad(task: Task, logger: logging.Logger, passing_args: dict, prepare_hidden_data):
    passing_args['Vocals_only'] = prepare_hidden_data / 'audio_(Vocals)_Kim_Vocal_2.wav'
    exec = VoiceActivityExecution('test', task.config)
    exec.start(task, logger, passing_args)
    
    assert task.status == TaskStatus.COMPLETED
    check_file_exists(task.execution.passing_args['vad_vocal_path'])
    assert len(task.execution.passing_args['vad_segments']) == 18
    assert 0 <= task.execution.passing_args['vad_segments'][0]['start'] <= 1
    assert 7 <= task.execution.passing_args['vad_segments'][0]['original_start'] <= 8
    