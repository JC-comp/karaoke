import json
import re
import difflib

from pypinyin import lazy_pinyin
from collections import defaultdict
from typing import Any
from .base import Task
from .cli import CLI
from .utils.artifact import ArtifactType

def fill_unmatched_pair(sentences: list[list[list[str | int]]], target_len: int):
    words = [word for sentence in sentences for word in sentence]
    anchors = [i for i, word in enumerate(words) if word[1] != -1]
    if not anchors:
        return
    if anchors[-1] != len(words) - 1:
        if int(words[anchors[-1]][1]) < target_len - 1:
            words[-1][1] = target_len - 1
            anchors.append(len(words) - 1)
    # Fill Leading Gaps
    first_idx = anchors[0]
    for i in range(first_idx - 1, -1, -1):
        words[i][1] = max(int(words[i+1][1]) - 1, -1)
    # Fill gaps
    for a in range(len(anchors) - 1):
        idx1, idx2 = anchors[a], anchors[a+1]
        val1, val2 = int(words[idx1][1]), int(words[idx2][1])
        print(idx1, idx2, val1, val2)
        distance = idx2 - idx1
        gap = val2 - val1
        step = distance / gap
        for val in range(val1, val2):
            idx = round(idx1 + (val - val1) * step)
            if words[idx][1] == -1:
                words[idx][1] = val

def expand_sentence(sentences: list[list[list[str | int]]], transcription_maps: list[dict]) -> None:
    # Fill backward
    last_transcription_pos = -1
    for sentence in sentences:
        start_pos = next((i for i, word in enumerate(sentence) if word[1] != -1), 0)
        for cur_pos in range(start_pos - 1, -1, -1):
            target_transcription_pos = int(sentence[cur_pos + 1][1]) - 1
            if target_transcription_pos <= last_transcription_pos:
                break
            if transcription_maps[target_transcription_pos]['end'] != transcription_maps[target_transcription_pos + 1]['start']:
                break
            sentence[cur_pos][1] = target_transcription_pos
        
        end_pos = next((i for i, word in enumerate(sentence[::-1]) if word[1] != -1), None)
        if end_pos is not None:
            last_transcription_pos = int(sentence[::-1][end_pos][1])
    # Fill forward
    last_transcription_pos = len(transcription_maps)
    for sentence in sentences[::-1]:
        end_pos = next((i for i, word in enumerate(sentence[::-1]) if word[1] != -1), 0)
        end_pos = len(sentence) - end_pos
        for cur_pos in range(end_pos + 1, len(sentence)):
            target_transcription_pos = int(sentence[cur_pos - 1][1]) + 1
            if target_transcription_pos >= last_transcription_pos:
                break
            if transcription_maps[target_transcription_pos]['start'] != transcription_maps[target_transcription_pos - 1]['end']:
                break
            sentence[cur_pos][1] = target_transcription_pos
        
        start_pos = next((i for i, word in enumerate(sentence) if word[1] != -1), None)
        if start_pos is not None:
            last_transcription_pos = int(sentence[start_pos][1])

def fill_typo_sequence(data: list[int], target_len: int) -> None:
    # Get all known indices
    known_indices = [i for i, x in enumerate(data) if x != -1]
    if not known_indices:
        return
    # Fill leading -1
    first_idx = known_indices[0]
    if data[first_idx] == first_idx:
        for i in range(first_idx):
            data[i] = i
    # Fill internal
    for k in range(len(known_indices) - 1):
        idx1, idx2 = known_indices[k], known_indices[k+1]
        # Fill the -1s in between
        if data[idx2] - data[idx1] == idx2 - idx1:
            for fill_idx in range(idx1 + 1, idx2):
                data[fill_idx] = data[fill_idx - 1] + 1
    # Fill tailing -1
    last_idx = known_indices[-1]
    last_val = data[last_idx]
    if len(data) - last_idx + last_val == target_len:
        for i in range(last_idx + 1, len(data)):
            data[i] = data[i-1] + 1

def separate_sentence(lyrics: str) -> list[str]:
    """
    Separate a sentence into words.
    """
    return [token for token in re.split(r'([^\x00-\x7F])|\s+', lyrics) if token and not token.isspace()]

class MapLyrics(Task):
    task_method_name = "merge"
    def __init__(self, run_id: str):
        super().__init__("Merge transcription and lyrics", run_id, arglist=['transcription', 'lyrics'])

    def do_mapping(self, transcription_sentences: list[dict[str, Any]], lyrics: str) -> list[list[dict]]:
        lyrics_sentences = lyrics.splitlines()

        # convert sentences to words
        lyrics_maps = [
            {'word': w, 'group': idx}
            for idx, sentence in enumerate(lyrics_sentences)
            for w in separate_sentence(sentence)
        ]
        transcription_maps = [
            {'word': w, 'start': s['start'], 'end': s['end']}
            for s in transcription_sentences
            for w in separate_sentence(s['text'])
        ]
        
        # extract word list
        lyrics_words = [
            lyrics_map['word']
            for lyrics_map in lyrics_maps
        ]
        transcription_words = [
            transcription_map['word']
            for transcription_map in transcription_maps
        ]
        
        # match two list
        matcher = difflib.SequenceMatcher(None, lazy_pinyin(lyrics_words), lazy_pinyin(transcription_words))
        
        matched = [-1] * len(lyrics_words)
        for blocks in matcher.get_matching_blocks():
            matched[blocks.a:blocks.a+blocks.size] = list(range(blocks.b, blocks.b+blocks.size))
        # remove incorrect mapping with large gap
        for i in range(len(matched)):
            if matched[i] == -1:
                continue
            target_val = next((matched[prev] for prev in range(i - 1, -1, -1) if matched[prev] != -1), None)
            if target_val is not None:
                is_next_unassigned = (i + 1 < len(matched)) and (matched[i + 1] == -1)
                if (matched[i] - target_val > 3) and is_next_unassigned:
                    matched[i] = -1
        # fill sequence
        fill_typo_sequence(matched, len(transcription_words))
        # convert back to sentences
        sentences = defaultdict(list[list[str | int]])
        for is_matched, lyrics_map in zip(matched, lyrics_maps):
            sentences[lyrics_map['group']].append([lyrics_map['word'], is_matched])
        sentences = list(sentences.values())
        
        # fill head and tailing space
        expand_sentence(sentences, transcription_maps)
       
        # final edit
        fill_unmatched_pair(sentences, len(transcription_words))

        for line in sentences:
            self.logger.debug('  '.join([str(l[0]) for l in line]))
            self.logger.debug(''.join([transcription_words[int(l[1])].ljust(3) if l[1] != -1 else '    ' for l in line]))
            self.logger.debug(''.join([str(l[1]).ljust(4) if l[1] != -1 else '    ' for l in line]))
        

        resutls = []
        for sentence in sentences:
            timed_sentence = []
            fisrt_timestamp = next((i for i, word in enumerate(sentence) if word[1] != -1), None)
            # Skip non matching sentences
            if fisrt_timestamp is None:
                continue
            text = [str(sentence[i][0]) for i in range(fisrt_timestamp + 1)]
            target = transcription_maps[int(sentence[fisrt_timestamp][1])]
            for i in range(fisrt_timestamp + 1, len(sentence)):
                if sentence[i][1] == -1:
                    text.append(str(sentence[i][0]))
                else:
                    timed_sentence += [
                        {
                            "start": target["start"] + (idx * (target["end"] - target["start"]) / len(text)),
                            "end": target["start"] + ((idx + 1) * (target["end"] - target["start"]) / len(text)),
                            "word": word
                        }
                        for idx, word in enumerate(text)
                    ]
                    text = [sentence[i][0]]
                    target = transcription_maps[int(sentence[i][1])]
            if text:
                timed_sentence += [
                    {
                        "start": target["start"] + (idx * (target["end"] - target["start"]) / len(text)),
                        "end": target["start"] + ((idx + 1) * (target["end"] - target["start"]) / len(text)),
                        "word": word
                    }
                    for idx, word in enumerate(text)
                ]
            resutls.append(timed_sentence)
                
        return resutls

    def do_fallback(self, transcription: list[dict[str, Any]]) -> list[list[dict]]:
        return [
            [
                {
                    "start": line["start"] + (idx * (line["end"] - line["start"]) / len(words)),
                    "end": line["start"] + ((idx + 1) * (line["end"] - line["start"]) / len(words)),
                    "word": word
                }
                for idx, word in enumerate(words)
            ]
            for line in transcription
            for words in [separate_sentence(line['text'])]
            if words
        ]

    def merge(self, transcription_path: str, lyrics: str) -> None:
        """
        Map the correct lyrics with the transcription to get sentence level timestamps.

        Output:
            - mapped_lyrics (list[list[Word]]): List of sentences with their start and end times.

        Word:
            - start (float): Start time of the sentence in seconds.
            - end (float): End time of the sentence in seconds.
            - word (str): The word in the sentence.
        """
        self.logger.info('Mapping transcription with lyrics')
        with open(transcription_path) as f:
            transcription: list[dict[str, Any]] = json.loads(f.read())

        sentences = None
        if not lyrics:
            try:
                sentences = self.do_mapping(transcription, lyrics)
            except Exception as e:
                self.logger.error(f"{e}", exc_info=True)
        else:
            self.logger.warning('No lyrics found')

        if not sentences:
            # if no lyrics found, use the transcription as the lyrics directly
            self.logger.warning('Fallback to use raw transcription')
            sentences = self.do_fallback(transcription)
            
        self.add_json_artifact(
            key='mapped_lyrics',
            name='Mapped lyrics',
            value=sentences,
            type=ArtifactType.JSON,
            attached=False
        )
        self.add_result(
            key='mapped_lyrics_viewer',
            name='Mapped lyrics',
            value={
                'segment': 'mapped_lyrics',
                'audio': 'Vocals_only'
            },
            type=ArtifactType.SENTENCE,
            attached=True
        )
        self.logger.info('Mapping completed')


if __name__ == "__main__":
    cli = CLI(
        description='Map transcription and lyrics.',
        actionDesc='Merge'
    )
    cli.add_local_arg(
        '--transcription', required=True, help='Path to transcription result'
    )
    cli.add_local_arg(
        '--lyrics', required=True, help='Lyric text'
    )
   
    task = MapLyrics(run_id=cli.get_run_id())
    cli.execute(task)