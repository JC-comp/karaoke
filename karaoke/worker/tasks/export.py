import io

from .task import Task, Execution, ArtifactType
from ..job import RemoteJob

def time_to_ts(time: str) -> str:
    """Convert time format from seconds to 00:00:00.000"""
    time = float(time)
    hours = int(time // 3600)
    minutes = int((time % 3600) // 60)
    seconds = int(time % 60)
    milliseconds = int((time - int(time)) * 100)
    return f"{hours:01}:{minutes:02}:{seconds:02}:{milliseconds:02}"

class ASSGenerator:
    def __init__(
        self, font: str,
        title: str, artist: str, duration: str,
        width: int, height: int
    ):
        self.output = io.StringIO()
        self.font_size = int(width * 0.9 / 15)
        self.width = width
        self.height = height
        self.duration = int(float(duration))
        self.line_count = 0
        self.currnet_line = None
        
        self.output.write(f"""[Script Info]
Title: {title}
Artist: {artist}
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601
PlayDepth: 0
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke, {font}, {self.font_size},&H00FF0000,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,2,0,1,10,10,30,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
    
    def add_line(self, line, next_line):
        if self.currnet_line is not None:
            mid = len(self.currnet_line) // 2
            start_time = self.currnet_line[mid]['start']
        else:
            start_time = max(line[0]['start'] - 1, 0)
        if next_line is not None:
            mid = len(next_line) // 2
            end = next_line[mid]['start']
        else:
            end = min(line[-1]['end'] + 2, int(float(self.duration)))

        if self.line_count % 2 == 0:
            x = int(self.width * 0.05)
            y = int(self.height - (self.font_size * 0.33 * 2) - self.font_size)
            text = ''
        else:
            x = int(self.width * 0.95)
            y = int(self.height - self.font_size * 0.33)
            text = f"{{\\an3}}"
        self.line_count += 1
        gap = line[0]["start"] - start_time
        start = time_to_ts(start_time)
        end = time_to_ts(end)
        text += f"{{\\pos({x},{y})}}"
        text += f"{{\\k{100*(gap)}}} "
        for idx, character in enumerate(line):
            word_gap = 0
            if idx - 1 >= 0:
                word_gap = line[idx]['start'] - line[idx-1]['end']
            if word_gap > 0:
                text += f"{{\\k{100*(word_gap)}}}"
            text += '{'
            text += '\\r'
            text += f'\\kf{100*(character["end"] - character["start"])}'
            text += f'\\t({1000*(character["start"]-line[0]["start"]+gap)},{1000*(character["end"]-line[0]["start"]+gap)},\\3c&HFFFFFF&)'
            text += '}'
            text += character['word']
        self.output.write(f"Dialogue: 1,{start},{end},Karaoke,,0,0,0,,{{\\fade(100,100)}}{text}\n")
        self.currnet_line = line

    def export(self, output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.output.getvalue())
        self.output.close()

class GenerateVideoExecution(Execution):
    def _start(self, args):
        """
        Generate video with karaoke subtitles using ass format and encoded with ffmpeg.
        """
        self.update(message='Generating video for the karaoke')
        media = args['media']
        source_path = args['source_video']
        instrumental_path = args['Instrumental_only']
        vocal_path = args['Vocals_only']
        sentences_block = args['sentences_block']
        
        title = args.get('title') or media.metadata.get('title') or 'Unknown Title'
        artist = args.get('artist') or media.metadata.get('channel') or 'Unknown Artist'
        
        ass_output_path = args['source_video'] + '.ass'
        video_output_path = source_path + '_karaoke.mp4'
        
        self.logger.info("Preparing subtitle generator")
        generator = ASSGenerator(
            self.config.export_font,
            title, artist, media.metadata.get('duration'),
            media.metadata.get('width'), media.metadata.get('height')
        )

        self.logger.info("Start generating ...")
        for sentence, next_sentence in zip(sentences_block, sentences_block[1:] + [None]):
            generator.add_line(sentence, next_sentence)

        generator.export(ass_output_path)
        
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-y", "-nostdin",
            "-i", source_path, "-i", instrumental_path, 
            "-vf", f"subtitles=filename='{ass_output_path}'",
            "-map", "0:v:0", "-map", "1:a:0",
            "-f", "mp4",
            video_output_path
        ]
        self.logger.info(f"Running command: {' '.join(cmd)}")

        self._start_external_command(cmd)

        self.add_artifact(
            name="Product", 
            artifact_type=ArtifactType.PRODUCT, 
            artifact={},
            attachments=[
                {
                    'name': 'vocal',
                    'artifact_type': ArtifactType.AUDIO,
                    'artifact': vocal_path
                },
                {
                    'name': 'result',
                    'artifact_type': ArtifactType.VIDEO,
                    'artifact': video_output_path
                }
            ]
        )
        self.update(message="Video generated successfully")
        
class GenerateVideo(Task):
    def __init__(self, job: RemoteJob):
        super().__init__(
            name='Video Generation', job=job,
            execution_class=GenerateVideoExecution
        )
    
    