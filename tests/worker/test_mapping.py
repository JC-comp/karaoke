import logging
import pytest
import json

from karaoke.worker.tasks.mapping import MapLyricsExecution, matching, grouping
from karaoke.worker.tasks.task import Task, TaskStatus
from tests.helper import check_file_exists

@pytest.mark.parametrize(
    'prepare_hidden_data', [['audio.transcript', 'audio.lib']], 
    indirect=True
)
def test_mapping(task: Task, logger: logging.Logger, passing_args: dict, prepare_hidden_data):
    passing_args['transcription_cache_path'] = str(prepare_hidden_data / 'audio.transcript')
    passing_args['lyrics_cache_path'] = str(prepare_hidden_data / 'audio.lib')
    passing_args['Vocals_only'] = 'source_Vocals.mp3'
    with open(passing_args['transcription_cache_path'], 'r') as f:
        passing_args['transcription'] = json.load(f)
    with open(passing_args['lyrics_cache_path'], 'r', encoding='utf-8') as f:
        lyrics = f.read()
        passing_args['lyrics'] = lyrics

    exec = MapLyricsExecution('test', task.config)
    exec.start(task, logger, passing_args)
    
    assert task.status == TaskStatus.COMPLETED
    check_file_exists(task.execution.passing_args['mapped_lyrics_cache_path'])

@pytest.mark.parametrize(
    's1, s2, match_count', [
        ('a', 'a', 1),
        ('a', 'b', 0),
        ('abc', 'abc', 3),
        ('abc', 'ab', 2),
        ('abc', 'bc', 2),
        ('abc', 'ac', 2),
        ('abc', 'a', 1),
        ('abc', 'c', 1),
        ('abc', 'd', 0),
        ('abc', 'acd', 2),
        ('aggtab', 'gxtxayb', 4),
        ('abc', 'cba', 1),
        ('', '', 0),
        ('', 'a', 0),
        ('a', '', 0)
    ]
)
def test_matching(s1: str, s2: str, match_count: int):
    s1 = [{'char': c} for c in list(s1)]
    s2 = [{'char': c} for c in list(s2)]
    _, dp = matching(s1, s2)
    assert dp[-1][-1] == match_count

@pytest.mark.parametrize(
    'transcription, lyrics, expected_sentences', [
        ('abc de abc', 'abcdeabc', ['abc', 'de', 'abc']),
        ('abc de abc', 'abcdeac', ['abc', 'de', 'ac']),
        ('abc de abc', 'abceabc', ['abce', 'abc']),
        ('abc de abc', 'abdeabc', ['abde', 'abc']),
        ('abc de abc', 'abcfabc', ['abcfabc']),
        ('abc de abc', 'deabc', ['de', 'abc']),
        ('abc de abc', 'bc', ['bc']),
    ]
)
def test_grouping(transcription: str, lyrics: str, expected_sentences: list[str]):
    transcription = [
        {
            'text': t,
            'start': idx,
            'end': idx + 1,
        }
        for idx, t in enumerate(transcription.split())
    ]
    lyrics_characters = [
        {'char': c,}
        for c in list(lyrics)
    ]
    transcription_characters = [
        {'char': c, 'group': idx, **s}
        for idx, s in enumerate(transcription)
        for c in list(s['text'])
    ]
    
    matching(transcription_characters, lyrics_characters)
    sentences = grouping(lyrics_characters, transcription_characters)

    assert len(sentences) == len(expected_sentences)
    for i in range(len(sentences)):
        assert sentences[i]['text'] == expected_sentences[i]
        if i > 0:
            assert sentences[i]['start'] == sentences[i - 1]['end']
    assert sentences[0]['start'] == transcription_characters[0]['start']
    assert sentences[-1]['end'] == transcription_characters[-1]['end']