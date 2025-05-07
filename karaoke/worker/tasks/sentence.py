import jieba

from .task import Task, Execution
from ..job import RemoteJob

class WordBank:
    """
    A class to manage a list of grouped words and their positions.
    """
    def __init__(self, word_list: list[list[dict]]):
        self.word_list = word_list
        self.current_pos = 0 # current word position over all words
        self.current_group = 0 # current group of words
        self.current_index = 0 # current index of the word in the group

    @property
    def length(self) -> int:
        """
        Calculate the total length of all characters in the word list.
        """
        return sum(len(word) for word in self.word_list)
    
    @property
    def word_count(self) -> int:
        """
        Calculate the total count of word groups.
        """
        return len(self.word_list)

    @property
    def word_length(self) -> int:
        """
        Calculate the length of the current group of words.
        """
        return len(self.word_list[self.current_group])
    
    @property
    def word_start_index(self) -> int:
        """
        Calculate the start index of the current group of words.
        """
        return self.current_pos - self.current_index

    def move_by_character(self, step: int) -> None:
        """
        Move the current position by a specified number of characters.
        Adjust the current group and index accordingly.
        """
        self.current_pos += step
        while step > 0:
            # Get how many words are left in the current group
            length_left = len(self.word_list[self.current_group]) - self.current_index
            if length_left > step:
                # If there are enough words left in the current group
                # move the index forward directly
                self.current_index += step
                return
            elif length_left == step:
                # If the current group is finished, move to the next group
                self.current_group += 1
                self.current_index = 0
                return
            else:
                # If the current group is not finished, move to the next group
                # and adjust the step accordingly
                step -= length_left
                self.current_group += 1
                self.current_index = 0

    def move_by_word(self) -> int:
        """
        Move the current position to the next word group.
        """
        length_moved = self.word_length - self.current_index
        self.current_pos += length_moved
        self.current_index = 0
        self.current_group += 1
        return length_moved
    
    def find_split_index(self, index: int) -> int:
        """
        Find a word that ends after the specified index. Then we 
        split at the beginning of the word.
        """
        if self.current_pos > index:
            self.reset()
        while self.word_start_index + self.word_length <= index:
            self.move_by_word()
            
        return self.word_start_index
    
    def seperate(self, index: int) -> None:
        """
        Split the current group of words at the specified overall character index.
        """
        starting_index_in_word = index - self.word_start_index
        if starting_index_in_word <= 0:
            raise ValueError("Starting index is out of range")
        words_to_keep = self.word_list[self.current_group][:starting_index_in_word]
        words_to_move = self.word_list[self.current_group][starting_index_in_word:]
        self.word_list.insert(self.current_group + 1, words_to_move)
        self.word_list[self.current_group] = words_to_keep
        self.current_pos = self.word_start_index
        self.current_index = 0
        
    def reset(self) -> None:
        """
        Reset the current position, group, and index to the beginning.
        """
        self.current_pos = 0
        self.current_group = 0
        self.current_index = 0

def build_sentences_from_aligned_lyrics(aligned_lyrics: list[dict]) -> list[list[dict]]:
    """
    Build sentences from aligned lyrics by grouping them into sentences based on time intervals.
    Return a list of sentences, where each sentence is a list of aligned lyric characters.
    """
    sentences_block = [[aligned_lyrics[0]]]
    for i in range(1, len(aligned_lyrics)):
        # If the start time of the current aligned lyric is greater than the
        # threshold from the end time of the last aligned lyric, move to the next block
        if aligned_lyrics[i]['start'] - sentences_block[-1][-1]['end'] > 0.35:
            sentences_block.append([aligned_lyrics[i]])
        else:
            sentences_block[-1].append(aligned_lyrics[i])
    return sentences_block

def generate_word_bank(sentences_block: list[list[dict]]) -> list[str]:
    """
    Generate a word bank from the sentences block by extracting words from the characters.
    """
    sentences = [
        ''.join(
            character['word']
            for character in character_block
        )
        for character_block in sentences_block
    ]
    paragraph = ''.join(sentences)
    words = list(jieba.cut(paragraph))
    word_bank = WordBank(words)
    return word_bank

def split_long_lines(sentences_block: list[list[dict]], word_bank: WordBank) -> list[list[dict]]:
    """
    Split long lines in the sentences block by separating them into smaller segments.
    """
    sentence_bank = WordBank(sentences_block)
    while sentence_bank.current_group < sentence_bank.word_count:
        if sentence_bank.word_length > 15:
            mid_pos = sentence_bank.word_start_index + sentence_bank.word_length // 2
            seperate_at = word_bank.find_split_index(mid_pos)
            # check if the split index is in the current word
            if seperate_at <= sentence_bank.word_start_index:
                seperate_at = mid_pos
            sentence_bank.seperate(seperate_at)
        else:
            sentence_bank.move_by_word()
    return sentences_block

def merge_short_lines(sentences_block: list[list[dict]]) -> list[list[dict]]:
    """
    Merge short lines in the sentences block by combining them into larger segments.
    """
    sentences_block = [
        block
        for block in sentences_block
        if len(block) > 0
    ]
    i = 0
    while i < len(sentences_block):
        if len(sentences_block[i]) < 3:
            attemp_target = [False, False]
            # Check if we can merge with the previous block
            if i > 0 and len(sentences_block[i-1]) + len(sentences_block[i]) < 15:
                attemp_target[0] = True
            # Check if we can merge with the next block
            if i < len(sentences_block) - 1 and len(sentences_block[i]) + len(sentences_block[i+1]) < 15:
                attemp_target[1] = True
            # Skip if no merge is possible
            if not any(attemp_target):
                i += 1
                continue
            # Choose the nearest block to merge with
            target = attemp_target.index(True)
            if all(attemp_target):
                if sentences_block[i][0]['start'] - sentences_block[i-1][-1]['end'] > sentences_block[i+1][0]['start'] - sentences_block[i][-1]['end']:
                    # merge with next block
                    target = 1
                else:
                    # merge with previous block
                    target = 0
            if target == 0:
                sentences_block[i-1].extend(sentences_block[i])
            else:
                sentences_block[i+1][:0] = sentences_block[i]
            sentences_block.pop(i)
        else:
            i += 1
    return sentences_block

class GenerateSentenceExecution(Execution):
    def _start(self, args):
        """
        Generate the subtitle from the aligned lyrics by grouping them into sentences.
        """
        aligned_lyrics = args['aligned_lyrics']
        
        self.update(message='Building sentences from aligned lyrics')
        sentences_block = build_sentences_from_aligned_lyrics(aligned_lyrics)
        word_bank = generate_word_bank(sentences_block)
        
        self.update(message='Splitting long lines')
        sentences_block = split_long_lines(sentences_block, word_bank)

        self.update(message='Cleaning up sentences')
        sentences_block = merge_short_lines(sentences_block)

        self.passing_args['sentences_block'] = sentences_block
        self.update(message="Subtitle generation complete")

class GenerateSentence(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Generate Sentence',
            job=job,
            execution_class=GenerateSentenceExecution
        )
    
    