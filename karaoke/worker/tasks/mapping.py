import json
import re

from .execution import SoftFailure
from .task import Task, Execution, ArtifactType
from ..job import RemoteJob

def matching(transcription_characters: list, lyrics_characters: list) -> tuple:
    """
    Find the maximum substring match between the transcription and the lyrics with 
    longest common subsequence algorithm.
    After matching, we mark the matched characters with a pair index.
    """
    
    dp = [[0] * (len(lyrics_characters) + 1) for _ in range(len(transcription_characters) + 1)]
    route = [[0] * (len(lyrics_characters) + 1) for _ in range(len(transcription_characters) + 1)]

    for i in range(1, len(transcription_characters) + 1):
        for j in range(1, len(lyrics_characters) + 1):
            if transcription_characters[i - 1]['char'] == lyrics_characters[j - 1]['char']:
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
    i = len(transcription_characters)
    j = len(lyrics_characters)
    while i > 0 and j > 0:
        if route[i][j] == 0:
            lyrics_characters[j - 1]['pair'] = i
            transcription_characters[i - 1]['pair'] = j
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

def grouping(lyrics_characters: list, transcription_characters: list) -> list:
    """
    Group the lyrics characters into time segments based on the matching with the
    transcription characters.
    All characters in the lyrics and all time segments in the transcription should belong 
    to a group.
        1.  If the current character is not matched, add it to the current group as 
            a missing character.
        2.  If the unmatched character follows a character matched with a new group, we 
            merge the two groups as we don't know which group the character belongs to.
        3.  If a matched character follows a character matched with a new group
            4.  If the the two groups are not contiguous, we merge the two groups as 
                we don't know which group the voiced segment belongs to.
            5.  If previous matched character is not the last character of the group, we
                merge the two groups as the unmatched character could also be the duplicate
                of the word in the next group.
            
            7.  Otherwise, we move to the next group.
    """
    # Start filling groups of characters with an empty string
    sentences = [{
        'start': transcription_characters[0]['start'],
        'end': transcription_characters[0]['end'],
        'start_mapped_index': 0,
        'end_mapped_index': 0,
        'text': ''
    }]
    current_group = 0
    current_lyrics_character_index = 0
    # Iterate through the lyrics characters and check which group they belong to.
    while (current_lyrics_character_index < len(lyrics_characters)):            
        last_lyrics_character_pair = None # record if the last character was matched
        while (current_lyrics_character_index < len(lyrics_characters)):
            # Get the current character and check if it is matched
            pair = lyrics_characters[current_lyrics_character_index].get('pair')
            # Check #1
            if pair is not None:
                pair -= 1
                if should_insert_new_group(pair, transcription_characters, current_group, last_lyrics_character_pair):
                    sentences[-1]['end'] = transcription_characters[last_lyrics_character_pair]['end']
                    sentences[-1]['end_mapped_index'] = last_lyrics_character_pair
                    sentences.append({
                        'start': transcription_characters[pair]['start'],
                        'end': transcription_characters[pair]['end'],
                        'start_mapped_index': pair,
                        'end_mapped_index': pair,
                        'text': ''
                    })
                    current_group = transcription_characters[pair]['group']
                    break
                # Merge the two groups without appending a new group to the sentences
                current_group = transcription_characters[pair]['group']
            last_lyrics_character_pair = pair
            sentences[-1]['text'] += lyrics_characters[current_lyrics_character_index]['char']
            current_lyrics_character_index += 1
    sentences[-1]['end'] = transcription_characters[-1]['end']
    sentences[-1]['end_mapped_index'] = len(transcription_characters) - 1
    return sentences

def unwrap_misspelled_characters(sentences: list, transcription_characters: list) -> list:
    """
    Unwrap the sentences with the same length as the transcription characters but different
    characters.
    """
    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        start_mapped_index = sentence['start_mapped_index']
        end_mapped_index = sentence['end_mapped_index']
        text = sentence['text']
        # Check if the length of the grouped sentence is the same as the length of the transcription
        if len(text) != (end_mapped_index - start_mapped_index + 1):
            i += 1
            continue
        # Split the sentence into two sentences
        transcription_sentence = transcription_characters[start_mapped_index]
        transcription_sentence_len = len(transcription_sentence['text'])
        unwrap_end_mapped_index = start_mapped_index + transcription_sentence_len - 1
        mapped_sentence = {
            'start': transcription_sentence['start'],
            'end': transcription_sentence['end'],
            'text': text[:transcription_sentence_len],
            'start_mapped_index': start_mapped_index,
            'end_mapped_index': unwrap_end_mapped_index
        }

        remaining_text = text[transcription_sentence_len:]
        if len(remaining_text) == 0:
            # If the remaining text is empty, we can just update the sentence
            sentences[i] = mapped_sentence
        else:
            # If the remaining text is not empty, we need to split the sentence
            next_mapped_index = unwrap_end_mapped_index + 1
            sentences[i] = {
                'start': transcription_characters[next_mapped_index]['start'],
                'end': sentences[i]['end'],
                'text': remaining_text,
                'start_mapped_index': next_mapped_index,
                'end_mapped_index': end_mapped_index
            }
            sentences.insert(i, mapped_sentence)
        i += 1
    return sentences

class MapLyricsExecution(Execution):
    def _set_result(self, vocal_path : str, mapped_lyrics_cache_path: str, sentences: list[dict]) -> None:
        """
        Set the result of the mapping task.
        """
        self.passing_args['mapped_lyrics_cache_path'] = mapped_lyrics_cache_path
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
        """
        self.update(message='Mapping transcription with lyrics')
        transcription = args['transcription']
        vocal_path = args['Vocals_only']
        lyrics = args.get('lyrics')
        
        # if no lyrics found, use the transcription as the lyrics directly
        transcription_sentences = [
            {
                'start': t['start'],
                'end': t['end'],
                'text': t['text']
            }
            for t in transcription
        ]
        if not lyrics:
            self._set_result(vocal_path, args['transcription_cache_path'], transcription_sentences)
            raise SoftFailure('No lyrics found, using transcription')
        
        lyrics_cache_path = args['lyrics_cache_path']
        mapped_lyrics_cache_path = lyrics_cache_path + '.mapped'

        lyrics_characters = [
            {'char': c,}
            for c in list(''.join(re.split(r'\n| ', lyrics)))
        ]
        transcription_characters = [
            {'char': c, 'group': idx, **s}
            for idx, s in enumerate(transcription)
            for c in list(''.join(re.split(r'\n| ', s['text'])))
        ]
        
        _, dp = matching(transcription_characters, lyrics_characters)
        if dp[-1][-1] < len(lyrics_characters) * 0.4:
            self._set_result(vocal_path, args['transcription_cache_path'], transcription_sentences)
            raise SoftFailure(f"Not enough match found ({dp[-1][-1]} / {len(lyrics_characters)} / {len(transcription_characters)}), using transcription")

        self.update(message='Remapping timestamps')
        grouped_sentences = grouping(lyrics_characters, transcription_characters)
        sentences = unwrap_misspelled_characters(grouped_sentences, transcription_characters)

        self._set_result(vocal_path, mapped_lyrics_cache_path, sentences)
        with open(mapped_lyrics_cache_path, 'w') as f:
            json.dump(sentences, f, ensure_ascii=False)
                
        self.update(message='Mapping completed')

class MapLyrics(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Merge transcription and lyrics', job=job,
            execution_class=MapLyricsExecution
        )