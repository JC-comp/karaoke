from ..provider import BaseProvider
from .....utils.translate import convert_simplified_to_traditional

def compare(source: str, target: str) -> bool:
    """
    Compare the source string with the target string for found lyrics.
    """
    if not source or not target:
        return False
    cleaned_source = convert_simplified_to_traditional(source.lower().replace(' ', ''))
    cleaned_target = convert_simplified_to_traditional(target.lower().replace(' ', ''))
    if cleaned_source in cleaned_target or cleaned_target in cleaned_source:
        return True
    return False

class BaseLyricsProvider(BaseProvider):
    
    def search(self, title: str, artist:str) -> str:
        raise NotImplementedError("Subclasses must implement this method")