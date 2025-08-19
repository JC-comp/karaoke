import json
import re
import os

from .execution import SoftFailure
from .task import Task, Execution, ArtifactType
from ..job import RemoteJob

def compare_word(a: str, b: str) -> bool:
    """
    Compare two words and check if they are the same.
    """
    if a.lower() == b.lower():
        return True
    return False

def matching(transcription_words: list, lyrics_words: list) -> tuple:
    """
    Find the maximum substring match between the transcription and the lyrics with 
    longest common subsequence algorithm.
    After matching, we mark the matched characters with a pair index.
    """

    dp = [[0] * (len(lyrics_words) + 1) for _ in range(len(transcription_words) + 1)]
    route = [[0] * (len(lyrics_words) + 1) for _ in range(len(transcription_words) + 1)]

    for i in range(1, len(transcription_words) + 1):
        for j in range(1, len(lyrics_words) + 1):
            if compare_word(transcription_words[i - 1]['word']['word'], lyrics_words[j - 1]['word']['word']):
                max_index = 0
                max_match = dp[i - 1][j - 1] + 1
            else:
                choices = [dp[i - 1][j], dp[i][j - 1]]
                max_index = choices.index(max(choices))
                max_match = choices[max_index]
                max_index += 1
            route[i][j] = max_index
            dp[i][j] = max_match
    # traceback matching characters
    i = len(transcription_words)
    j = len(lyrics_words)
    while i > 0 and j > 0:
        if route[i][j] == 0:
            lyrics_words[j - 1]['pair'] = i
            transcription_words[i - 1]['pair'] = j
            i -= 1
            j -= 1
        elif route[i][j] == 1:
            i -= 1
        else:
            j -= 1
    return route, dp

def should_insert_new_group(
    pair: int, transcription_characters: list, current_group: int,
    last_lyrics_character_pair: int
) -> bool:
    # Check #2
    if (transcription_characters[pair]['group'] == current_group):
        return False
    # Check #3
    if last_lyrics_character_pair is None:
        return False
    # Check #4
    if current_group + 1 != transcription_characters[pair]['group']:
        return False
    # Check #5
    if last_lyrics_character_pair + 1 < len(transcription_characters):
        if transcription_characters[last_lyrics_character_pair + 1]['group'] == transcription_characters[last_lyrics_character_pair]['group']:
            return False

    if pair - 1 >= 0:
        if transcription_characters[pair]['group'] == transcription_characters[pair - 1]['group']:
            return False
    return True

def grouping(lyrics_words: list, transcription_words: list) -> list:
    """
    Group the lyrics words into time segments based on the matching with the
    transcription words.
    All words in the lyrics and all time segments in the transcription should belong
    to a group.
        1.  If the current word is not matched, add it to the current group as
            a missing word.
        2.  If the unmatched word follows a word matched with a new group, we
            merge the two groups as we don't know which group the word belongs to.
        3.  If a matched word follows a word matched with a new group
            4.  If the the two groups are not contiguous, we merge the two groups as 
                we don't know which group the voiced segment belongs to.
            5.  If previous matched character is not the last character of the group, we
                merge the two groups as the unmatched character could also be the duplicate
                of the word in the next group.
            
            7.  Otherwise, we move to the next group.
    """
    # Start filling groups of characters with an empty string
    sentences = [{
        'start': transcription_words[0]['start'],
        'end': transcription_words[0]['end'],
        'start_mapped_index': 0,
        'end_mapped_index': 0,
        'words': []
    }]
    current_group = 0
    current_lyrics_character_index = 0
    # Iterate through the lyrics characters and check which group they belong to.
    while (current_lyrics_character_index < len(lyrics_words)):            
        last_lyrics_character_pair = None # record if the last character was matched
        while (current_lyrics_character_index < len(lyrics_words)):
            # Get the current character and check if it is matched
            pair = lyrics_words[current_lyrics_character_index].get('pair')
            # Check #1
            if pair is not None:
                pair -= 1
                if should_insert_new_group(pair, transcription_words, current_group, last_lyrics_character_pair):
                    sentences[-1]['end'] = transcription_words[last_lyrics_character_pair]['end']
                    sentences[-1]['end_mapped_index'] = last_lyrics_character_pair
                    sentences.append({
                        'start': transcription_words[pair]['start'],
                        'end': transcription_words[pair]['end'],
                        'start_mapped_index': pair,
                        'end_mapped_index': pair,
                        'words': []
                    })
                    current_group = transcription_words[pair]['group']
                    break
                # Merge the two groups without appending a new group to the sentences
                current_group = transcription_words[pair]['group']
            last_lyrics_character_pair = pair
            sentences[-1]['words'].append(lyrics_words[current_lyrics_character_index]['word'])
            current_lyrics_character_index += 1
    sentences[-1]['end'] = transcription_words[-1]['end']
    sentences[-1]['end_mapped_index'] = len(transcription_words) - 1
    return sentences

def unwrap_mistranscribed_words(sentences: list, transcription_words: list) -> list:
    """
    Unwrap the sentences with the same length as the transcription sentences but different
    words.
    """
    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        start_mapped_index = sentence['start_mapped_index']
        end_mapped_index = sentence['end_mapped_index']
        words = sentence['words']
        # Check if the length of the grouped sentence is the same as the length of the transcription
        if len(words) != (end_mapped_index - start_mapped_index + 1):
            i += 1
            continue
        # Split the sentence into two sentences
        transcription_sentence = transcription_words[start_mapped_index]
        transcription_sentence_len = len(transcription_sentence['words'])
        unwrap_end_mapped_index = start_mapped_index + transcription_sentence_len - 1
        mapped_sentence = {
            'start': transcription_sentence['start'],
            'end': transcription_sentence['end'],
            'words': words[:transcription_sentence_len],
            'start_mapped_index': start_mapped_index,
            'end_mapped_index': unwrap_end_mapped_index
        }

        remaining_text = words[transcription_sentence_len:]
        if len(remaining_text) == 0:
            # If the remaining text is empty, we can just update the sentence
            sentences[i] = mapped_sentence
        else:
            # If the remaining text is not empty, we need to split the sentence
            next_mapped_index = unwrap_end_mapped_index + 1
            sentences[i] = {
                'start': transcription_words[next_mapped_index]['start'],
                'end': sentences[i]['end'],
                'words': remaining_text,
                'start_mapped_index': next_mapped_index,
                'end_mapped_index': end_mapped_index
            }
            sentences.insert(i, mapped_sentence)
        i += 1
    return sentences

def separate_sentence(lyrics: str) -> str:
    """
    Separate a sentence into words.
    """
    return [token for token in re.split(r'([^\x00-\x7F])|\s+', lyrics) if token and not token.isspace()]

class MapLyricsExecution(Execution):
    def _set_result(self, vocal_path : str, sentences: list[dict]) -> None:
        """
        Set the result of the mapping task.
        """
        self.passing_args['mapped_lyrics'] = sentences
        self.add_artifact(
            name='Mapped lyrics', 
            artifact_type=ArtifactType.SEGMENTS, 
            artifact={
                'segments': sentences
            },
            attachments=[{
                'name': 'audio',
                'artifact_type': ArtifactType.AUDIO,
                'artifact': vocal_path
            }]
        )

    def _start(self, args: dict) -> None:
        """
        Map the correct lyrics with the transcription to get sentence level timestamps.

        Output:
            - mapped_lyrics (list[TimedSentence]): List of sentences with their start and end times.

        TimedSentence:
            - start (float): Start time of the sentence in seconds.
            - end (float): End time of the sentence in seconds.
            - words (list[Word]): List of words in the sentence.
            - text (str): The sentence itself.
        
        Word:
            - word (str): The word in the sentence.
            - group (int): The group index of the word in the sentence.
        """
        self.update(message='Mapping transcription with lyrics')
        transcription = args['transcription']
        vocal_path = args['Vocals_only']
        lyrics = args.get('lyrics')
        mapped_lyrics_cache_path = os.path.join(self.config.media_path, args['identifier'] + '.mapped')
        
        transcription_sentences = [
            {
                **t,
                'words': [
                    {
                        'word': w,
                        'group': idx
                    }
                    for w in separate_sentence(t['text'])
                ],
            }
            for idx, t in enumerate(transcription)
        ]
        
        # if no lyrics found, use the transcription as the lyrics directly
        if not lyrics:
            self._set_result(vocal_path, transcription_sentences)
            raise SoftFailure('No lyrics found, using transcription')

        lyrics_sentences = [
            {
                'words': [
                    {
                        'word': w,
                        'group': idx
                    }
                    for w in separate_sentence(l)
                ],
                'text': l
            }
            for idx, l in enumerate(lyrics.split('\n'))
        ]
        
        lyrics_words = [
            {'word': w, 'group': idx}
            for idx, l in enumerate(lyrics_sentences)
            for w in l['words']
        ]
        transcription_words = [
            {'word': w, 'group': idx, **s}
            for idx, s in enumerate(transcription_sentences)
            for w in s['words']
        ]
        
        _, dp = matching(transcription_words, lyrics_words)
        if dp[-1][-1] < len(lyrics_words) * 0.4:
            self._set_result(vocal_path, transcription_sentences)
            raise SoftFailure(f"Not enough match found ({dp[-1][-1]} / {len(lyrics_words)} / {len(transcription_words)}), using transcription")

        self.update(message='Remapping timestamps')
        grouped_sentences = grouping(lyrics_words, transcription_words)
        sentences = unwrap_mistranscribed_words(grouped_sentences, transcription_words)

        for sentence in sentences:
            if not sentence['words']:
                continue
            sentence['text'] = sentence['words'][0]['word']
            for word in sentence['words'][1:]:
                if word['word'].isascii():
                    sentence['text'] += ' ' + word['word']
                else:
                    sentence['text'] += word['word']

        with open(mapped_lyrics_cache_path, 'w') as f:
            json.dump(sentences, f, ensure_ascii=False)
        self._set_result(vocal_path, sentences)                
        self.update(message='Mapping completed')

class MapLyrics(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Merge transcription and lyrics', job=job,
            execution_class=MapLyricsExecution
        )