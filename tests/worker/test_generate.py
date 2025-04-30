import logging

from karaoke.worker.tasks.generate import GenerateVideoExecution
from karaoke.worker.tasks.task import Task, TaskStatus

def test_generate(task: Task, logger: logging.Logger, passing_args: dict, prepare_data):
    passing_args['Vocals_only'] = 'source_Vocals.mp3'
    passing_args['Instrumental_only'] = str(prepare_data / 'source.wav')
    passing_args['sentences_block'] = [
        [
            {

                'word': character,
                'start': idx + sidx * 3,
                'end': (idx + 0.1) + sidx * 3,
            }
            for idx, character in enumerate(sentence)
        ]
        for sidx, sentence in enumerate(['ABC', 'DEF'])
    ]
    exec = GenerateVideoExecution('test', task.config)
    exec.start(task, logger, passing_args)
    
    assert task.status == TaskStatus.COMPLETED
    