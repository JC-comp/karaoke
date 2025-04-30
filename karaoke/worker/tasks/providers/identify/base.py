from ..provider import BaseProvider

class BaseIdentifier(BaseProvider):
    
    def identify(self, audio_path: str, title: str, artist: str) -> tuple[str, str]:
        raise NotImplementedError("Subclasses should implement this method.")