import requests
import logging
import re

from .base import BaseIdentifier
from ..utils import NotEnabledException
from .....utils.config import Config

def chat_with_model(query: str) -> str:
    """
    Chat with the model using the provided query and return the response.
    """
    config = Config()
    headers = {
        'Authorization': f'Bearer {config.gpt_token}',
        'Content-Type': 'application/json'
    }
    data = {
      "model": "llama3.1:latest",
      "messages": [
        {
          "role": "user",
          "content": query
        }
      ]
    }
    raw_response = requests.post(config.gpt_endpoint, headers=headers, json=data)
    response = raw_response.json()
    content = response['choices'][0]['message']['content']
    return content

def extract_artist_and_title(query, logger: logging.Logger = None) -> tuple[str, str]:
    """
    Extract artist and song name from the query using LLM models.
    This function retries up to 3 times in case of failure due to the randomness of the model.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    prompt = "Extract one pair of artist and song name in json format of two keys: artist and title. Remove translated info or extra info in the results: '" + query + "'"
    retry = 0
    while retry < 3:
        try:        
            logger.info(f"Attempt {retry + 1} to chat with model")
            retry += 1
            content = chat_with_model(prompt)
            logger.debug(f"Response content: {content}")
            json_pattern = r'"artist":[^"]*"(.*?)"[^"]*"title":[^"]*"(.*)"'
            match = re.search(json_pattern, content)
            if match:
                artist, title = match.groups()
                if artist in query and title in query:
                    return artist, title
                else:
                    raise ValueError("Artist or song name not found in the requested content")
            else:
                raise ValueError("Failed to extract artist and song name from the response")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed with error: {e}")
            retry += 1
    raise Exception("Failed to extract artist and song name after multiple attempts")

class GPTIdentifier(BaseIdentifier):
    name="GPTIdentifier"
    """
    Identify music using artist and title extracted by GPT.
    """
    def identify(self, audio_path: str, title: str, artist: str) -> tuple[str, str]:
        if not self.config.gpt_enabled:
            raise NotEnabledException("GPT is not enabled")
        if title is None or artist is None:
            raise Exception("YouTube title or artist not provided")
        if title and artist:
            title, artist = extract_artist_and_title(title + ' - ' + artist, self.logger)
            self.logger.info(f"Extracted artist: {artist}, title: {title}")
            return title, artist
        raise Exception("No title or artist found")