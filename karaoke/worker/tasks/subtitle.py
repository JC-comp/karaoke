import io

from .task import Task, Execution, ArtifactType
from ..job import RemoteJob

class SubtitleGenerator:
    def __init__(self, duration: str):
        self.font_size = 0.9 / 15
        self.padding = self.font_size * 0.33
        self.duration = float(duration)
        self.line_count = 0
        self.currnet_line = None
        self.lines = []

    def add_poster(self, title: str, artist: str):
        if len(title) > 10:
            title = title[:9] + '...'
        if len(artist) > 10:
            artist = artist[:9] + '...'
        title_font_size = 0.9 / 10
        artist_font_size = title_font_size * 0.8

        head_height = (self.padding * 3 + self.font_size * 2) + self.padding * 2
        
        self.lines.append({
            'start': 1,
            'end': 6,
            'alignX': 'center',
            'alignY': 'center',
            'y': -title_font_size / 2 - self.padding,
            'bottom': head_height,
            'font_size': title_font_size,
            'words': [
                {
                    'word': title,
                    'text': title,
                    'start': 1,
                    'end': 1
                }
            ]
        })
        self.lines.append({
            'start': 1,
            'end': 6,
            'alignX': 'center',
            'alignY': 'center',
            'y': artist_font_size / 2 + self.padding,
            'bottom': head_height,
            'font_size': artist_font_size,
            'words': [
                {
                    'word': artist,
                    'text': artist,
                    'start': 1,
                    'end': 1
                }
            ]
        })

    def add_line(self, line: list[dict], next_line: list[dict]):
        if self.currnet_line is not None:
            # show next line when the current line is played to the middle
            mid = len(self.currnet_line) // 2
            start_time = self.currnet_line[mid]['start']
        else:
            # show the first line at 1 second before the first word
            start_time = max(line[0]['start'] - 1, 0)
        
        # Adjust poster time to fade out 3 seconds before the first line
        if self.line_count == 0:
            pre_first_line = start_time - 3
            for poster in self.lines:
                if pre_first_line > poster['end']:
                    poster['end'] = pre_first_line

        if next_line is not None:
            # goes away when the next line is played to the middle
            mid = len(next_line) // 2
            end = next_line[mid]['start']
        else:
            # goes away 2 seconds after the last word if no next line
            end = min(line[-1]['end'] + 2, int(float(self.duration)))

        if self.line_count % 2 == 0:
            alignX = 'left'
            alignY = 'bottom'
            x = 0.05
            y = self.font_size * 0.33 * 2 + self.font_size
        else:
            alignX = 'right'
            alignY = 'bottom'
            x = 0.95
            y = self.font_size * 0.33
        self.line_count += 1
        
        if line:
            line[0]['text'] = line[0]['word']
        if len(line) > 1:
            for l in line[1:]:
                if l['word'].isascii():
                    l['text'] = ' ' + l['word']
                else:
                    l['text'] = l['word']

        timed_line = {
            'start': start_time,
            'end': end,
            'alignX': alignX,
            'alignY': alignY,
            'x': x,
            'y': y,
            'font_size': self.font_size,
            'words': line
        }
        self.lines.append(timed_line)
        self.currnet_line = line

    def export(self):
        return self.lines

class GenerateSubtitleExecution(Execution):
    def _start(self, args):
        """
        Generate subtitles timestamp from aligned lyrics.
        """
        self.update(message='Generating subtitles')
        media = args['media']
        sentences_block = args['sentences_block']
        
        title = args.get('title') or media.metadata.get('title') or 'Unknown'
        artist = args.get('artist') or media.metadata.get('channel') or 'Unknown'
        
        generator = SubtitleGenerator(media.metadata.get('duration'))
        generator.add_poster(title, artist)

        self.logger.info("Start generating ...")
        for sentence, next_sentence in zip(sentences_block, sentences_block[1:] + [None]):
            generator.add_line(sentence, next_sentence)

        self.add_artifact(
            name="Subtitle",
            tag='subtitles',
            artifact_type=ArtifactType.JSON, 
            artifact=generator.export(),
            is_attached=True
        )
        self.update(message="Subtitle generation completed")
        
class GenerateSubtitle(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Subtitle Generation', job=job,
            execution_class=GenerateSubtitleExecution
        )
    
    