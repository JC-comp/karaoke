import jieba

from .task import Task, Execution
from ..job import RemoteJob

def should_split_line(word: dict, prev_word: dict) -> bool:
    """
    Check if a line should be split based on its length.
    """
    # If the start time of the current aligned lyric is greater than the
    # threshold from the end time of the last aligned lyric, move to the next block    
    if word['start'] - prev_word['end'] > 0.35:
        if word['group'] == prev_word['group']:
            # If the current word is in the same group as the previous word, do not split
            return False
        return True
    return False

def build_sentences_from_aligned_lyrics(aligned_lyrics: list[dict]) -> list[list[dict]]:
    """
    Build sentences from aligned lyrics by grouping them into sentences based on time intervals.
    Return a list of sentences, where each sentence is a list of aligned lyric characters.

    Output:
        - sentences_block (list[list[Word]]): List of sentences, where each sentence is a list of aligned lyric characters.
    """
    sentences_block = [[aligned_lyrics[0]]]
    for i in range(1, len(aligned_lyrics)):
        # Check if the current aligned lyric should be split into a new sentence
        if should_split_line(aligned_lyrics[i], aligned_lyrics[i-1]):
            sentences_block.append([aligned_lyrics[i]])
        else:
            sentences_block[-1].append(aligned_lyrics[i])
    return sentences_block

class WordBank:
    def __init__(self, sentences_block: list[list[dict]]):
        self.sentences_block = sentences_block
        self.current_group = 0
        self.current_word = 0
        self.char_index = 0

    @property
    def length(self) -> int:
        """
        Get the total character length of the sentences block.
        """
        return sum(len(w['word']) for s in self.sentences_block for w in s)
    
    @property
    def group_count(self) -> int:
        """
        Get the number of groups in the sentences block.
        """
        return len(self.sentences_block)
    
    @property
    def current_char_length(self) -> int:
        """
        Get the number of characters in the current group.
        """
        return sum(
            max(1, len(w['word']) / 2) # count 2 ascii characters as 1
            for w in self.sentences_block[self.current_group]
        )
    
    @property
    def current_word_length(self) -> int:
        """
        Get the number of words in the current group.
        """
        return len(self.sentences_block[self.current_group])
    
    def char_index_of_word(self, word_index: int) -> int:
        """
        Get the start character index of the given word index in the current group.
        """
        char_index = 0
        for i in range(word_index):
            char_index += len(self.sentences_block[self.current_group][i]['word'])
        return self.char_index + char_index
    
    def find_split_word_index(self) -> int:
        """
        Find the index of the word to split in the current group.
        """
        split_word_index = self.current_word_length // 2
        if self.sentences_block[self.current_group][0]['group'] != self.sentences_block[self.current_group][-1]['group']:
            while self.sentences_block[self.current_group][split_word_index]['group'] == self.sentences_block[self.current_group][split_word_index - 1]['group']:
                if self.sentences_block[self.current_group][split_word_index]['group'] == self.sentences_block[self.current_group][0]['group']:
                    split_word_index += 1
                elif self.sentences_block[self.current_group][split_word_index]['group'] == self.sentences_block[self.current_group][-1]['group']:
                    split_word_index -= 1
                else:
                    split_word_index += 1

        return split_word_index

    def find_start_char_index(self, char_index: int) -> int:
        while True:
            start_index = self.char_index
            end_index = self.char_index + len(self.sentences_block[self.current_group][self.current_word]['word'])
            if start_index <= char_index < end_index:
                return start_index
            elif char_index < start_index:
                self.previous_word()
            elif char_index >= end_index:
                self.next_word()

    def separate(self, char_index: int):
        """
        Separate the current group into two groups based on the given character index.
        """
        new_char_index = self.char_index
        new_word_index = self.current_word
        while new_char_index < char_index:
            new_char_index += len(self.sentences_block[self.current_group][new_word_index]['word'])
            new_word_index += 1
        
        new_group = self.sentences_block[self.current_group][:new_word_index]
        self.sentences_block[self.current_group] = self.sentences_block[self.current_group][new_word_index:]
        self.sentences_block.insert(self.current_group, new_group)

    def previous_word(self):
        """
        Move to the previous word in the sentences block.
        """
        if self.current_word == 0:
            self.current_group -= 1
            assert self.current_group >= 0, "Current group index cannot be negative"
            self.current_word = len(self.sentences_block[self.current_group])

        self.current_word -= 1
        assert self.current_word >= 0, "Current word index cannot be negative"
        self.char_index -= len(self.sentences_block[self.current_group][self.current_word]['word'])

    def next_word(self):
        """
        Move to the next word in the sentences block.
        """
        self.char_index += len(self.sentences_block[self.current_group][self.current_word]['word'])
        if self.current_word == len(self.sentences_block[self.current_group]) - 1:
            self.current_group += 1
            self.current_word = -1

        self.current_word += 1
        assert self.current_group < len(self.sentences_block), "Current group index out of range"
        assert self.current_word < len(self.sentences_block[self.current_group]), "Current word index out of range"
    
    def next_group(self):
        """
        Move to the next group in the sentences block.
        """
        while self.current_word < len(self.sentences_block[self.current_group]):
            word = self.sentences_block[self.current_group][self.current_word]
            self.char_index += len(word['word'])
            self.current_word += 1

        self.current_group += 1
        self.current_word = 0

def generate_word_bank(sentences_block: list[list[dict]]) -> WordBank:
    """
    Generate a word bank from the sentences block by extracting words from the characters.
    """
    words = []
    sentence_index = 0
    paragraph = ''
    while sentence_index < len(sentences_block):
        word_index = 0
        while word_index < len(sentences_block[sentence_index]):
            word: str = sentences_block[sentence_index][word_index]['word']
            if word.isascii():
                if paragraph:
                    words.extend(list(jieba.cut(paragraph)))
                    paragraph = ''
                words.append(word)
            else:
                paragraph += word
            word_index += 1
        sentence_index += 1
    if paragraph:
        words.extend(list(jieba.cut(paragraph)))
    sentence = [
        [
            {
                'word': word
            }
            for word in words
        ]
    ]
    bank = WordBank(sentence)
    return bank

def split_long_lines(sentences_block: list[list[dict]], word_bank: WordBank) -> list[list[dict]]:
    """
    Split long lines in the sentences block by separating them into smaller segments.
    """
    sentence_bank = WordBank(sentences_block)
    assert sentence_bank.length == word_bank.length, "Word bank length does not match the sentences block length"
    while sentence_bank.current_group < sentence_bank.group_count:
        if sentence_bank.current_char_length > 15 and sentence_bank.current_word_length > 1:
            split_at_word = sentence_bank.find_split_word_index()
            mid_char_index = sentence_bank.char_index_of_word(split_at_word)
            separate_at_char = word_bank.find_start_char_index(mid_char_index)
            # check if the split index is in the current word
            if separate_at_char <= sentence_bank.char_index:
                separate_at_char = mid_char_index
            sentence_bank.separate(separate_at_char)
        else:
            sentence_bank.next_group()
    return sentences_block

class GenerateSentenceExecution(Execution):
    def _start(self, args):
        """
        Generate the subtitle from the aligned lyrics by grouping them into sentences.

        Output:
            - sentences_block (list[list[Word]]): List of sentences, where each sentence is a list of aligned lyric characters.
        """
        aligned_lyrics = args['aligned_lyrics']
        
        self.update(message='Building sentences from aligned lyrics')
        sentences_block = build_sentences_from_aligned_lyrics(aligned_lyrics)
        word_bank = generate_word_bank(sentences_block)
        
        self.update(message='Splitting long lines')
        sentences_block = split_long_lines(sentences_block, word_bank)

        self.passing_args['sentences_block'] = sentences_block
        self.update(message="Subtitle generation complete")

class GenerateSentence(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Generate Sentence',
            job=job,
            execution_class=GenerateSentenceExecution
        )
    
    