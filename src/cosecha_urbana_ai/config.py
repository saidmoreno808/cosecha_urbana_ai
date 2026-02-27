"""Configuracion centralizada usando Pydantic Settings."""
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Elasticsearch
    elasticsearch_url: str = "https://localhost:9200"
    elasticsearch_api_key: str = ""
    elasticsearch_index_prefix: str = "cosecha_urbana"
    elastic_cloud_id: str | None = None

    # -- GROQ (LLM activo) ------------------------------------------------
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_temperature: float = 0.1
    groq_max_tokens: int = 1024

    # Anthropic (fallback / opcional)
    anthropic_api_key: str = ""
    llm_model: str = "groq"       # "groq" | "anthropic"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    api_secret_key: str = "change-this-in-production"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Kibana
    kibana_url: str = ""

    # Notifications - Slack Incoming Webhook (simplest, no bot needed)
    # Get URL from: api.slack.com/apps -> Incoming Webhooks -> Add to workspace
    slack_webhook_url: str = ""

    # Notifications - Kibana Connector (Elastic-native, recommended for hackathon)
    # Created via: Kibana -> Stack Management -> Connectors -> Slack
    kibana_slack_connector_id: str = ""

    # Legacy / unused
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    whatsapp_api_token: str | None = None

    # Agente
    agent_max_steps: int = 10
    agent_timeout_seconds: int = 120
    max_distance_km: float = 15.0
    food_urgency_threshold_hours: int = 4

    # Logging
    log_level: str = "INFO"
    log_format: str = "console"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [v]
        return v

    @property
    def use_groq(self) -> bool:
        """True si Groq esta configurado y es el proveedor activo."""
        return bool(self.groq_api_key) and self.llm_model == "groq"

    # -- Indices de Elasticsearch ------------------------------------------
    @property
    def donors_index(self) -> str:
        return f"{self.elasticsearch_index_prefix}_donors"

    @property
    def recipients_index(self) -> str:
        return f"{self.elasticsearch_index_prefix}_recipients"

    @property
    def food_alerts_index(self) -> str:
        return f"{self.elasticsearch_index_prefix}_food_alerts"

    @property
    def donations_history_index(self) -> str:
        return f"{self.elasticsearch_index_prefix}_donations_history"

    @property
    def routes_index(self) -> str:
        return f"{self.elasticsearch_index_prefix}_routes"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
