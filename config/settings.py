"""Configurações centralizadas da aplicação via Pydantic Settings."""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Aplicação ────────────────────────────────────────────────
    app_name: str = Field(default="News Automation")
    debug: bool = Field(default=False)

    # ── Banco de dados ───────────────────────────────────────────
    database_url: str = Field(default="sqlite:///./data/news_automation.db")

    # ── OpenAI ──────────────────────────────────────────────────
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o")

    # ── Portal de notícias ───────────────────────────────────────
    portal_url: str = Field(default="")
    portal_username: str = Field(default="")
    portal_password: str = Field(default="")

    # ── Paths ────────────────────────────────────────────────────
    upload_dir: Path = Field(default=Path("data/uploads"))
    log_dir: Path = Field(default=Path("logs"))

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
