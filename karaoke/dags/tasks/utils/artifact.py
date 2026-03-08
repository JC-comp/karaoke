from enum import Enum

class ArtifactType(Enum):
    TEXT = 'text'
    AUDIO = 'audio'
    JSON = 'json'
    SEGMENT = 'segment'
    SENTENCE = 'sentence'

class ExportedArtifactTag(Enum):
    METADATA = 'metadata'
    INSTRUMENTAL = 'Instrumental'
    SUBTITLES = 'subtitles'
