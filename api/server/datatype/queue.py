import enum
import uuid
from dataclasses import dataclass, field, asdict

class QueueType(enum.StrEnum):
    """
    Enum for the type of queue list item.
    """
    YOUTUBE = 'youtube'
    JOB = 'job'

@dataclass(frozen=True)
class QueueItem:
    item_id: str = field(default_factory=lambda: uuid.uuid4().hex, init=False)
    type: QueueType
    identifier: str
    title: str
    artist: str

    def serialize(self) -> dict:
        """
        Converts the dataclass to a dictionary, handling Enum values.
        """
        data = asdict(self)
        data['type'] = self.type.value
        return data
