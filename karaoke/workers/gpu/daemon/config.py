from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings, 
    SettingsConfigDict
)

class TranscriptionConfig(BaseModel):
    cpu_model: str = "large-v3-turbo"
    gpu_model: str = "medium"
    initial_prompt: str = ""

class AppConfig(BaseSettings):
    log_level: str = 'INFO'
    cache_dir: str = "/tmp"
    model_dir: str = "/data/models"

    transcription: TranscriptionConfig = TranscriptionConfig()

    # Configuration to handle case sensitivity and env files
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="", 
        env_nested_delimiter="__",
        case_sensitive=False
    )

config = AppConfig()

if __name__ == "__main__":
    # Test it out
    print(config.model_dump())
    