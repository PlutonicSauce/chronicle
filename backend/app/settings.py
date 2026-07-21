from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration with a safe, seed-backed local default."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Chronicle API"
    environment: str = "development"
    database_url: str | None = None
    project_slug: str = "atlas"
    project_name: str = "Atlas"
    project_repository: str = "acme/atlas"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    aws_region: str = "us-east-1"
    use_bedrock: bool = False
    bedrock_embedding_model: str = "amazon.titan-embed-text-v2:0"
    bedrock_text_model: str = "amazon.nova-lite-v1:0"
    embedding_dimensions: int = 512
    s3_export_bucket: str | None = None

    @property
    def is_demo(self) -> bool:
        return not self.database_url

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
