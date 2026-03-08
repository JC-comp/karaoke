from abc import abstractmethod
from ..provider import BaseProvider

class BaseIdentifier(BaseProvider):
    @abstractmethod
    def identify(self, audio_path: str) -> tuple[str, str]:
        pass