import logging
import pytest

from karaoke.worker.tasks.align import AlignLyricsExecution
from karaoke.worker.tasks.task import Task, TaskStatus

@pytest.mark.parametrize(
    'prepare_hidden_data', [['audio_(Vocals)_Kim_Vocal_2.wav']], 
    indirect=True
)
def test_align(task: Task, logger: logging.Logger, passing_args: dict, prepare_hidden_data):
    passing_args['Vocals_only'] = str(prepare_hidden_data / 'audio_(Vocals)_Kim_Vocal_2.wav')
    passing_args['mapped_lyrics'] = [
        {"start": 7.15, "end": 29.580000000000002, "text": "你說一切是我的錯是你信任我的好結果"}, 
        {"start": 29.580000000000002, "end": 41.17, "text": "每一次都責怪我造成我們之間的冷漠"}, 
        {"start": 41.17, "end": 54.81, "text": "我說的話你選擇不聽把沈默變成你的武器怎麼就開始了戰爭雙方居然成為敵人"}, 
        {"start": 54.81, "end": 61.650000000000006, "text": "不能說我沒全力以赴是你挑選了這一條路"}, 
    ]
    text = ''.join([lyrics['text'] for lyrics in passing_args['mapped_lyrics']])
    exec = AlignLyricsExecution('test', task.config)
    exec.start(task, logger, passing_args)

    
    assert task.status == TaskStatus.COMPLETED
    assert len(text) == len(task.execution.passing_args['aligned_lyrics'])
    for i, lyrics in enumerate(task.execution.passing_args['aligned_lyrics']):
        assert lyrics['word'] == text[i]

@pytest.mark.parametrize(
    'prepare_hidden_data', [['vad.wav']],
    indirect=True
)
def test_align_failed(task: Task, logger: logging.Logger, passing_args: dict, prepare_hidden_data):
    passing_args['Vocals_only'] = str(prepare_hidden_data / 'vad.wav')
    start = 3.15
    end = 12.01
    passing_args['mapped_lyrics'] = [
        {"start": start, "end": end, "text": "息工戊封我耍和福起道可風對問美河頁氣屋戊夏紅定刃弓字旦會抄貫力九對頭向"}
    ]
    text = ''.join([lyrics['text'] for lyrics in passing_args['mapped_lyrics']])
    duration = (end - start) / len(text)

    exec = AlignLyricsExecution('test', task.config)
    exec.start(task, logger, passing_args)
    
    assert task.status == TaskStatus.COMPLETED
    assert len(text) == len(task.execution.passing_args['aligned_lyrics'])
    for i, lyrics in enumerate(task.execution.passing_args['aligned_lyrics']):
        assert lyrics['word'] == text[i]
        assert abs(lyrics['start'] - (start + i * duration)) < 0.01
        assert abs(lyrics['end'] - (start + (i + 1) * duration)) < 0.01
