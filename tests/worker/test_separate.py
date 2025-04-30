import logging
import pytest

from unittest.mock import MagicMock
from karaoke.utils.task import TaskStatus
from karaoke.worker.tasks.seprate import SeperateAudioExecution
from karaoke.worker.tasks.task import Task
from tests.helper import check_file_exists

@pytest.mark.parametrize(
    'model_name,passing_key',
    [
        ('Kim_Vocal_2.onnx', 'Vocals'),
        ('UVR_MDXNET_KARA_2.onnx', 'Instrumental')
    ],
)
def test_seperate(task: Task, logger: logging.Logger, passing_args: dict, model_name: str, passing_key: str):
    exec = SeperateAudioExecution('test', task.config, model_name=model_name, passing_key=passing_key)
    exec.start(task, logger, passing_args)
    
    assert task.status == TaskStatus.COMPLETED
    assert task.message == 'Separation completed'
    check_file_exists(task.execution.passing_args[passing_key + '_only'])

@pytest.mark.parametrize(
    'model_name,passing_key', [
        ('Kim_Vocal_2.onnx', 'Vocals'),
        ('UVR_MDXNET_KARA_2.onnx', 'Instrumental')
    ], 
)
@pytest.mark.parametrize(
    'prepare_hidden_data,cache_hit',
    [
        ([], []),
        (['source_Vocals.mp3'], ['Vocals']),
        (['source_Instrumental.mp3'], ['Instrumental']),
        (['source_Vocals.mp3', 'source_Instrumental.mp3'], ['Vocals', 'Instrumental']),
    ],
    indirect=['prepare_hidden_data']
)
def test_seperate_cache_check(
    task: Task, logger: logging.Logger, passing_args: dict,
    model_name: str, cache_hit: list, passing_key: str,
    prepare_hidden_data, monkeypatch
):
    separator_mock = MagicMock()
    separator_mock.return_value = ('test', )
    monkeypatch.setattr('audio_separator.separator.Separator.separate', separator_mock)
    
    exec = SeperateAudioExecution('test', task.config, model_name=model_name, passing_key=passing_key)
    exec.start(task, logger, passing_args)    
    
    assert task.status == TaskStatus.COMPLETED
    if passing_key in cache_hit:
        assert not separator_mock.called
        assert task.message == 'Found separated audio in cache'
    else:
        assert separator_mock.called
        assert task.message == 'Separation completed'
