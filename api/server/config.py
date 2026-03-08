from pydantic import Field, BaseModel
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

class AirflowConfig(BaseModel):
    # Added fields from your legacy snippet
    base_url: str = "http://ktv-airflow-apiserver:8080/airflow/api/v2"
    username: str = "airflow"
    password: str = "airflow"
    dag_id: str = "Generate-from-link"

class ServerConfig(BaseModel):
    # Added fields from your legacy "server" and "socketio" logic
    web: bool = False
    yt: bool = False
    room: bool = False
    artifact: bool = False
    job: bool = False
    socketio_path: str = "/ws"
    socketio_cors_allowed_origins: str | None = None
    # Prioritizes env var, then default
    socketio_message_queue: str = Field(default="redis://localhost:6379/1")

class AppConfig(BaseSettings):
    log_level: str = 'INFO'

    storage: StorageConfig = StorageConfig()
    airflow: AirflowConfig = AirflowConfig()
    server: ServerConfig = ServerConfig()

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