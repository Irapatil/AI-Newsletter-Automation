"""Centralized application configuration loaded from environment variables."""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Any, Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    All fields have safe defaults so the application boots and the LangGraph
    workflow runs end-to-end (using mock providers) even with an empty `.env`.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_env: Literal["development", "staging", "production"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    api_auth_token: SecretStr = SecretStr("")
    allowed_hosts: str = "*"
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # LLM provider
    llm_provider: Literal["openai", "azure_openai", "mock"] = "openai"

    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    azure_openai_api_key: SecretStr = SecretStr("")
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-08-01-preview"
    azure_openai_chat_deployment: str = ""
    azure_openai_embedding_deployment: str = ""

    # News source providers
    newsapi_api_key: SecretStr = SecretStr("")
    github_token: SecretStr = SecretStr("")
    crunchbase_api_key: SecretStr = SecretStr("")

    greenhouse_board_tokens: str = "stripe,airbnb,openai"
    lever_company_slugs: str = "netflix,palantir"

    linkedin_jobs_provider: Literal["mock", "api"] = "mock"
    linkedin_api_key: SecretStr = SecretStr("")

    # Deduplication & ranking
    dedup_similarity_threshold: float = 0.88

    ranking_top_stories_per_section: int = 5
    ranking_weight_freshness: float = 0.20
    ranking_weight_importance: float = 0.25
    ranking_weight_business_impact: float = 0.20
    ranking_weight_source_credibility: float = 0.15
    ranking_weight_research_impact: float = 0.10
    ranking_weight_ai_relevance: float = 0.10

    # Newsletter
    newsletter_timezone: str = "UTC"
    newsletter_sender_name: str = "AI Newsletter Automation"
    newsletter_history_dir: str = "data/history"
    max_article_age_hours: int = 48
    newsletter_max_total_articles: int = 24
    llm_cost_per_million_tokens_usd: float = 2.5

    # HTTP
    http_timeout_seconds: int = 15
    http_max_retries: int = 3

    @field_validator("dedup_similarity_threshold")
    @classmethod
    def _validate_threshold(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("dedup_similarity_threshold must be between 0.0 and 1.0")
        return value

    @field_validator(
        "ranking_weight_freshness",
        "ranking_weight_importance",
        "ranking_weight_business_impact",
        "ranking_weight_source_credibility",
        "ranking_weight_research_impact",
        "ranking_weight_ai_relevance",
    )
    @classmethod
    def _validate_ranking_weight(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("ranking_weight_* fields must be between 0.0 and 1.0")
        return value

    @field_validator("ranking_top_stories_per_section", "max_article_age_hours", "http_max_retries")
    @classmethod
    def _validate_positive_int(cls, value: int, info: Any) -> int:
        if value < 1:
            raise ValueError(f"{info.field_name} must be >= 1")
        return value

    @field_validator("llm_cost_per_million_tokens_usd")
    @classmethod
    def _validate_non_negative_cost_rate(cls, value: float) -> float:
        if value < 0:
            raise ValueError("llm_cost_per_million_tokens_usd must be >= 0")
        return value

    @model_validator(mode="after")
    def _validate_ranking_weights_sum(self) -> Settings:
        total = sum(self.ranking_weights.values())
        if not math.isclose(total, 1.0, abs_tol=0.01):
            raise ValueError(f"ranking_weight_* fields must sum to ~1.0, got {total:.3f}")
        return self

    @model_validator(mode="after")
    def _validate_production_requires_auth_token(self) -> Settings:
        if self.app_env == "production" and not self.api_auth_token.get_secret_value():
            raise ValueError(
                "API_AUTH_TOKEN must be set when APP_ENV=production - "
                "refusing to start an unauthenticated production API"
            )
        return self

    @property
    def greenhouse_board_token_list(self) -> list[str]:
        return [token.strip() for token in self.greenhouse_board_tokens.split(",") if token.strip()]

    @property
    def lever_company_slug_list(self) -> list[str]:
        return [slug.strip() for slug in self.lever_company_slugs.split(",") if slug.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def uses_mock_llm(self) -> bool:
        if self.llm_provider == "mock":
            return True
        if self.llm_provider == "openai":
            return not self.openai_api_key.get_secret_value()
        if self.llm_provider == "azure_openai":
            return not (
                self.azure_openai_api_key.get_secret_value()
                and self.azure_openai_endpoint
                and self.azure_openai_chat_deployment
                and self.azure_openai_embedding_deployment
            )
        return True

    @property
    def ranking_weights(self) -> dict[str, float]:
        return {
            "freshness": self.ranking_weight_freshness,
            "importance": self.ranking_weight_importance,
            "business_impact": self.ranking_weight_business_impact,
            "source_credibility": self.ranking_weight_source_credibility,
            "research_impact": self.ranking_weight_research_impact,
            "ai_relevance": self.ranking_weight_ai_relevance,
        }


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached Settings instance."""
    return Settings()
