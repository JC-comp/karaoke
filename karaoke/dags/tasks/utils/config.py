from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings, 
    SettingsConfigDict
)

class StorageConfig(BaseModel):
    # File key: endpoint | Env: STORAGE_ENDPOINT
    endpoint: str = "127.0.0.1:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    secure: bool = False

class ProviderConfig(BaseModel):
    acoustid: bool = False
    acoustid_api_key: str = ""
    shazam: bool = True
    kkbox: bool = True
    musixmatch: bool = True

class TranscriptionConfig(BaseModel):
    cpu_model: str = "large-v3-turbo"
    gpu_model: str = "medium"
    initial_prompt: str = ""
    host: str = "127.0.0.1"
    port: int = 5000

class AppConfig(BaseSettings):
    log_level: str = 'INFO'
    cache_dir: str = "/tmp"
    model_dir: str = "/data/models"

    storage: StorageConfig = StorageConfig()
    provider: ProviderConfig = ProviderConfig()
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
    