from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-4o"
    fcm_server_key: Optional[str] = None
    reports_dir: str = "data/reports"
    max_followup_attempts: int = 3
    report_retention_days: int = 180
    azure_storage_connection_string: Optional[str] = None
    azure_storage_container: str = "email-reports"
    chroma_persist_dir: str = "data/chroma"
    embedding_model: str = "text-embedding-3-small"
    rag_top_k: int = 5

    model_config = {"env_file": ".env"}


settings = Settings()
