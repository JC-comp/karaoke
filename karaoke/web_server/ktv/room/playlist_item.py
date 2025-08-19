import enum
import uuid

class PlaylistItemType(enum.Enum):
    """
    Enum for the type of playlist item.
    """
    YOUTUBE = 'youtube'
    SCHEDULE = 'schedule'

class PlaylistItem:
    def __init__(self, item_type: PlaylistItemType, identifier: str = None, **kwargs):
        self.item_id = str(uuid.uuid4())
        self.type = item_type
        self.identifier = identifier
        self.title = kwargs['title']
        self.artist = kwargs['channel']

    def serialize(self) -> dict:
        """
        Serialize the playlist item to a dictionary.
        """
        return {
            'item_id': self.item_id,
            'type': self.type.value,
            'identifier': self.identifier,
            'title': self.title,
            'artist': self.artist
        }

class YoutubePlaylistItem(PlaylistItem):
    """
    Class representing a YouTube playlist item.
    """
    def __init__(self, **kwargs):
        super().__init__(
            item_type=PlaylistItemType.YOUTUBE, 
            identifier=kwargs['id'],
            **kwargs
        )

class SchedulePlaylistItem(PlaylistItem):
    """
    Class representing a playlist item that is from a scheduler.
    """
    def __init__(self, **kwargs):
        super().__init__(
            item_type=PlaylistItemType.SCHEDULE, 
            identifier=kwargs['job_id'],
            **kwargs
        )