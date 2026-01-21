from __future__ import annotations

import pathlib
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class CollectionConfig(BaseModel):
    roots: List[str]
    include: List[str]
    exclude: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    hooks: dict[str, str] = Field(default_factory=dict)


class CorporaConfig(BaseModel):
    collections: dict[str, CollectionConfig]

    @classmethod
    def load(cls, path: pathlib.Path) -> CorporaConfig:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        return cls.model_validate(data)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="NEXUS_", case_sensitive=False)

    database_url: str = "postgresql://nexus:nexus@localhost:5432/nexus"
    ollama_url: str = "http://localhost:11434"
    api_key: str | None = None
    api_key_file: pathlib.Path | None = None
    allow_origins: List[str] = ["http://localhost:3000"]
    embed_model: str = "mxbai-embed-large"
    chat_model: str = "llama3.1:8b-instruct"
    embed_dim: int = 1024
    chunk_size: int = 800
    chunk_overlap: int = 80
    min_chars: int = 500
    max_empty_ratio: float = 0.30
    max_file_size_mb: int = 100
    max_response_tokens: int = 4096
    timeout_seconds: int = 120
    corpora_manifest: pathlib.Path = pathlib.Path("corpora.yml")
    processed_dir: pathlib.Path = pathlib.Path("/processed")

    # Cloud AI API Keys
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: Optional[str] = None
    google_ai_api_key: Optional[str] = None
    google_ai_project_id: Optional[str] = None
    google_ai_location: str = "us-central1"

    @model_validator(mode="after")
    def load_api_key_from_file(self) -> "Settings":
        if self.api_key_file and not self.api_key:
            key_path = pathlib.Path(self.api_key_file)
            if key_path.exists():
                self.api_key = key_path.read_text().strip()
        return self

    @model_validator(mode="after")
    def validate_api_key_strength(self) -> "Settings":
        if self.api_key is not None and len(self.api_key) < 16:
            import logging

            logging.warning(
                "API key is shorter than 16 characters. "
                "Consider using a longer key for better security."
            )
        return self

    def corpora(self) -> CorporaConfig:
        return CorporaConfig.load(self.corpora_manifest)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
