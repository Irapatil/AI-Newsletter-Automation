"""Centralized application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator
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
    api_auth_token: str = ""

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

    # HTTP
    http_timeout_seconds: int = 15
    http_max_retries: int = 3

    @field_validator("dedup_similarity_threshold")
    @classmethod
    def _validate_threshold(cls, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("dedup_similarity_threshold must be between 0.0 and 1.0")
        return value

    @property
    def greenhouse_board_token_list(self) -> list[str]:
        return [token.strip() for token in self.greenhouse_board_tokens.split(",") if token.strip()]

    @property
    def lever_company_slug_list(self) -> list[str]:
        return [slug.strip() for slug in self.lever_company_slugs.split(",") if slug.strip()]

    @property
    def uses_mock_llm(self) -> bool:
        if self.llm_provider == "mock":
            return True
        if self.llm_provider == "openai":
            return not self.openai_api_key
        if self.llm_provider == "azure_openai":
            return not (self.azure_openai_api_key and self.azure_openai_endpoint)
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
