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
        head_height = 1 - (self.padding * 3 + self.font_size * 2)
        head_mid = head_height / 2
        title_font_size = 0.9 / len(title)
        artist_font_size = 0.9 / len(artist)
        if artist_font_size > title_font_size:
            artist_font_size = title_font_size * 0.6
        self.lines.append({
            'start': 0,
            'end': 3,
            'alignX': 'center',
            'alignY': 'top',
            'y': head_mid - title_font_size,
            'font_size': title_font_size,
            'words': [
                {
                    'word': title,
                    'start': 0,
                    'end': 0
                }
            ]
        })
        self.lines.append({
            'start': 0,
            'end': 3,
            'alignX': 'center',
            'alignY': 'top',
            'y': head_mid,
            'font_size': artist_font_size,
            'words': [
                {
                    'word': artist,
                    'start': 0,
                    'end': 0
                }
            ]
        })

    def add_line(self, line, next_line):
        if self.currnet_line is not None:
            # show next line when the current line is played to the middle
            mid = len(self.currnet_line) // 2
            start_time = self.currnet_line[mid]['start']
        else:
            # show the first line at 1 second before the first word
            start_time = max(line[0]['start'] - 1, 0)
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
        instrumental_path = args['Instrumental_only']
        sentences_block = args['sentences_block']
        
        title = args.get('title') or media.metadata.get('title') or 'Unknown Title'
        artist = args.get('artist') or media.metadata.get('channel') or 'Unknown Artist'
        
        generator = SubtitleGenerator(media.metadata.get('duration'))
        generator.add_poster(title, artist)

        self.logger.info("Start generating ...")
        for sentence, next_sentence in zip(sentences_block, sentences_block[1:] + [None]):
            generator.add_line(sentence, next_sentence)

        self.add_artifact(
            name="Product", 
            artifact_type=ArtifactType.PRODUCT, 
            artifact={
                'subtitle': generator.export()
            },
            attachments=[
                {
                    'name': 'instrumental',
                    'artifact_type': ArtifactType.AUDIO,
                    'artifact': instrumental_path
                }
            ]
        )
        self.update(message="Subtitle generation completed")
        
class GenerateSubtitle(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Subtitle Generation', job=job,
            execution_class=GenerateSubtitleExecution
        )
    
    