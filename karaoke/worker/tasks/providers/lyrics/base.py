from ..provider import BaseProvider

class BaseLyricsProvider(BaseProvider):
    
    def search(self, title: str, artist:str) -> str:
        raise NotImplementedError("Subclasses must implement this method")