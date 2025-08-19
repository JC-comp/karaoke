import logging
import pytest

from karaoke.worker.tasks.transcript import TranscriptLyricsExecution
from karaoke.worker.tasks.task import Task, TaskStatus

@pytest.mark.parametrize(
    'prepare_hidden_data', [['vad.wav']], 
    indirect=True
)
def test_transcript(task: Task, logger: logging.Logger, passing_args: dict, prepare_hidden_data):
    passing_args['vad_vocal_path'] = str(prepare_hidden_data / 'vad.wav')
    passing_args['vad_segments'] = [{"start": 0, "end": 6.050000000000001, "duration": 6.050000000000001, "original_start": 6.75, "original_end": 12.8}]
    exec = TranscriptLyricsExecution('test', task.config)
    exec.start(task, logger, passing_args)
    
    assert task.status == TaskStatus.COMPLETED
    transcript = task.execution.passing_args['transcription']
    assert len(transcript) == 1
    assert 6 <= transcript[0]['start'] <= 7
    assert 11 <= transcript[0]['end'] <= 13
    assert len(set(transcript[0]['text']) - set('無心過問你的心裡我的吻 无心过问你的心里我答问')) < 4
    
