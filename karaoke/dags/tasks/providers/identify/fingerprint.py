import acoustid

from typing import Any, Dict, cast, Optional
from .base import BaseIdentifier
from ..utils import NotEnabledException

class FingerprintIdentifier(BaseIdentifier):
    """
    Identify music using AcoustID fingerprinting.
    """
    @property
    def name(self) -> str:
        return "FingerprintIdentifier"
    
    def identify(self, audio_path: str) -> tuple[str, str]:
        if not self.config.provider.acoustid:
            raise NotEnabledException("AcoustID is not enabled")
        
        response = cast(Dict[str, Any],
            acoustid.match(self.config.provider.acoustid_api_key, audio_path, parse=False)
        )
        if response['status'] != 'ok':
            if 'error' in response:
                raise Exception(f"Error: {response['error']}")
            raise Exception(f"Error: {response}")
        
        for result in response['results']:
            score = result['score']
            if 'recordings' not in result:
                # No recording attached. This result is not very useful.
                continue
            for recording in result['recordings']:
                artists = recording.get("artists")
                if artists:
                    artist_name = "".join(
                        [
                            artist["name"] + artist.get("joinphrase", "")
                            for artist in artists
                        ]
                    )
                else:
                    artist_name = ''
            title = recording.get('title')
            self.logger.info(f"Found music: {title} by {artist_name} with score {score}")
            return title, artist_name
        raise Exception("No music found with fingerprint")
