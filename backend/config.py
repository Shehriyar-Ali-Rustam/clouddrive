"""
Central configuration, loaded from environment variables / .env file.

Everything that differs between "running on my laptop" and "running on AWS"
lives here, so the rest of the code never hard-codes an environment.
"""
import os

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Security
    secret_key: str = "dev-insecure-secret-change-me"
    access_token_expire_minutes: int = 120
    algorithm: str = "HS256"

    # Database
    database_url: str = "sqlite:///./clouddrive.db"

    # Storage
    storage_backend: str = "local"          # "local" or "s3"
    local_storage_dir: str = "./storage_data"

    # AWS S3
    aws_region: str = "us-east-1"
    s3_bucket: str = "my-clouddrive-bucket"

    # App
    default_quota_mb: int = 200
    public_api_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def _use_platform_url(self):
        # Render (and similar hosts) inject the public URL automatically.
        # Prefer it so share links use the real domain without manual config.
        platform_url = os.environ.get("RENDER_EXTERNAL_URL")
        if platform_url:
            self.public_api_url = platform_url
        return self


settings = Settings()
