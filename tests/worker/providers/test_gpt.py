import pytest
from karaoke.worker.tasks.providers.identify.gpt import extract_artist_and_title
    
@pytest.mark.gpt_server
def test_chat_with_model():
    artist, song_name = extract_artist_and_title("陳奕迅 Eason Chan《聖誕結(國)[OT:Lonely Christmas]》[Official MV]")
    assert artist == "陳奕迅"
    assert song_name == "聖誕結"
    
@pytest.mark.gpt_server
def test_chat_with_model_2():
    artist, song_name = extract_artist_and_title("愚人節快樂 - 盧廣仲")
    assert artist == "盧廣仲"
    assert song_name == "愚人節快樂"
