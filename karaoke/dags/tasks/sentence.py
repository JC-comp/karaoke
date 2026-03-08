import jieba
import json
import re

from .base import Task
from .cli import CLI
from .utils.artifact import ArtifactType

def merge_small_chunks(aligned_lyrics: list[list[dict]]):
    idx = 0
    while idx < len(aligned_lyrics):
        sentence = aligned_lyrics[idx]
        # If the chunk is already long enough, move to the next
        if len(sentence) > 3:
            idx += 1
            continue

        prev_gap = float('inf')
        next_gap = float('inf')

        if idx - 1 >= 0:
            if aligned_lyrics[idx - 1][-1]['end'] == sentence[0]['start']:
                aligned_lyrics[idx - 1].extend(sentence)
                aligned_lyrics.pop(idx)
                continue
            prev_gap = abs(aligned_lyrics[idx - 1][-1]['end'] - sentence[0]['start'])
        if idx + 1 < len(aligned_lyrics):
            if aligned_lyrics[idx + 1][0]['start'] == sentence[-1]['end']:
                aligned_lyrics[idx + 1] = sentence + aligned_lyrics[idx + 1]
                aligned_lyrics.pop(idx)
                continue
            next_gap = abs(aligned_lyrics[idx + 1][0]['start'] - sentence[-1]['end'])
        
        if prev_gap <= next_gap and prev_gap != float('inf'):
            aligned_lyrics[idx-1].extend(sentence)
            aligned_lyrics.pop(idx)
        elif next_gap < prev_gap and next_gap != float('inf'):
            aligned_lyrics[idx + 1] = sentence + aligned_lyrics[idx + 1]
            aligned_lyrics.pop(idx)

        idx += 1

def heuristic_split(sentence: list[str]) -> list[str]:
    eng_pattern = re.compile(r'^[a-zA-Z0-9]+$')
    words = []
    for word in sentence:
        if eng_pattern.match(word):
            # It's an English word, keep it as a single token
            words.append(word)
        else:
            # It's Chinese, use jieba to split it into proper tokens
            words.extend(jieba.lcut(word))
    
    if len(words) <= 1:
        return sentence
    
    sentence_len = sum([len(word) for word in sentence])
    mid_point = sentence_len / 2
    first_half = ''
    idx = 0
    while idx < len(words) - 1 and len(first_half) < mid_point:
        next_word = words[idx]
        
        current_diff = abs(len(first_half) - mid_point)
        new_diff = abs(len(first_half) + len(next_word) - mid_point)
        if len(first_half) > 0 and new_diff > current_diff:
            break
        first_half += next_word
        idx += 1
    return [first_half, "".join(words[idx:])]

def split_long_lines(aligned_lyrics: list[list[dict]]):
    idx = 0
    eng_pattern = re.compile(r'^[a-zA-Z0-9]+$')

    while idx < len(aligned_lyrics):
        sentence = aligned_lyrics[idx]
        # Only split if the line is long
        sentence_len = sum([2 if eng_pattern.match(word['word']) else 1 for word in sentence])
        if sentence_len < 15:
            idx += 1
            continue
        
        words = [item['word'] for item in sentence]
        split_sentences = heuristic_split(words)
        if len(split_sentences) >= 2:
            target_char_count = len(split_sentences[0])
            
            current_chars = 0
            split_idx = 0
            for i, item in enumerate(sentence):
                current_chars += len(item['word'])
                if current_chars >= target_char_count:
                    split_idx = i + 1
                    break

            aligned_lyrics.pop(idx)
            aligned_lyrics.insert(idx, sentence[:split_idx])
            aligned_lyrics.insert(idx + 1, sentence[split_idx:])
        else:
            idx+=1

class GenerateSentence(Task):
    task_method_name="generate"
    def __init__(self, run_id: str):
        super().__init__(name='Generate Sentence', run_id=run_id, arglist=['mapped_lyrics'])
        
    def generate(self, aligned_lyrics_path: str):
        """
        Generate the subtitle from the aligned lyrics by grouping them into sentences.

        Output:
            - sentences_block (list[list[Word]]): List of sentences, where each sentence is a list of aligned lyric characters.
        """
        with open(aligned_lyrics_path) as f:
            aligned_lyrics: list[list[dict]] = json.loads(f.read())

        self.logger.info('Building sentences from aligned lyrics')
        merge_small_chunks(aligned_lyrics)
        self.logger.info('Splitting long lines')
        split_long_lines(aligned_lyrics)

        self.add_json_artifact(
            key='sentences_block',
            name='Generated Sentences',
            value=aligned_lyrics,
            type=ArtifactType.JSON,
            attached=False
        )
        self.add_result(
            key='sentences_block_viewer',
            name='Generated Sentences',
            value={
                'segment': 'sentences_block',
                'audio': 'Vocals_only'
            },
            type=ArtifactType.SENTENCE,
            attached=True
        )
        self.logger.info("Subtitle generation complete")
    
if __name__ == "__main__":
    cli = CLI(
        description='Generate sentence from aligned segments.',
        actionDesc='Generate'
    )
    cli.add_local_arg(
        '--mapped_lyrics', required=True, help='Path to aligned lyrics result'
    )
    
    task = GenerateSentence(run_id=cli.get_run_id())
    cli.execute(task)