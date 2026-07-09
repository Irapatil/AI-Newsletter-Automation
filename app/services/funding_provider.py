"""Funding-news provider abstraction (Crunchbase, with a free fallback).

Crunchbase's funding-rounds search requires a paid API key. To keep the
FundingAgent functional without one, a `GoogleNewsFundingProvider` fallback
parses AI-funding headlines from Google News RSS. Swap in a real Crunchbase
key via `CRUNCHBASE_API_KEY` to switch providers automatically.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TypedDict

from app.config.logging_config import get_logger
from app.config.settings import get_settings
from app.config.sources import FUNDING_FALLBACK_QUERY, google_news_query_url
from app.services.http_client import HttpClientError, fetch_json
from app.services.rss_service import fetch_feed_entries

logger = get_logger(__name__)

CRUNCHBASE_FUNDING_ROUNDS_URL = "https://api.crunchbase.com/api/v4/searches/funding_rounds"

_AMOUNT_RE = re.compile(r"\$\s?(\d+(?:\.\d+)?)\s?(million|billion|M|B)", re.IGNORECASE)


class FundingRound(TypedDict):
    title: str
    url: str
    company: str
    amount_usd: float | None
    published_at: datetime | str
    snippet: str


def _extract_amount_usd(title: str) -> float | None:
    match = _AMOUNT_RE.search(title)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    multiplier = 1_000_000_000 if unit.startswith("b") else 1_000_000
    return value * multiplier


class FundingProvider(ABC):
    """Abstract provider for AI startup funding news."""

    @abstractmethod
    async def fetch_recent_funding_rounds(self, max_results: int = 15) -> list[FundingRound]:
        raise NotImplementedError


class CrunchbaseFundingProvider(FundingProvider):
    """Real Crunchbase API v4 integration; requires `CRUNCHBASE_API_KEY`."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def fetch_recent_funding_rounds(self, max_results: int = 15) -> list[FundingRound]:
        headers = {"X-cb-user-key": self._api_key, "Content-Type": "application/json"}
        params = {
            "field_ids": "identifier,announced_on,money_raised,investor_identifiers",
            "order": [{"field_id": "announced_on", "sort": "desc"}],
            "limit": max_results,
        }
        try:
            payload = await fetch_json(
                CRUNCHBASE_FUNDING_ROUNDS_URL, params=params, headers=headers
            )
        except HttpClientError as exc:
            logger.warning("crunchbase_fetch_failed", error=str(exc))
            return []

        entities = payload.get("entities", []) if isinstance(payload, dict) else []
        rounds: list[FundingRound] = []
        for entity in entities:
            properties = entity.get("properties", {})
            identifier = properties.get("identifier", {})
            money = properties.get("money_raised", {})
            rounds.append(
                FundingRound(
                    title=f"{identifier.get('value', 'Unknown company')} raises funding",
                    url=identifier.get("permalink", ""),
                    company=identifier.get("value", "Unknown"),
                    amount_usd=money.get("value_usd"),
                    published_at=properties.get("announced_on"),
                    snippet=f"Funding round announced {properties.get('announced_on', '')}.",
                )
            )
        return rounds[:max_results]


class GoogleNewsFundingProvider(FundingProvider):
    """Free fallback: parses AI-funding headlines from Google News RSS."""

    async def fetch_recent_funding_rounds(self, max_results: int = 15) -> list[FundingRound]:
        url = google_news_query_url(FUNDING_FALLBACK_QUERY)
        entries = await fetch_feed_entries(url, source_name="Google News (Funding)")
        rounds: list[FundingRound] = [
            FundingRound(
                title=entry["title"],
                url=entry["url"],
                company=entry["title"].split(" raises")[0].split(" secures")[0].strip(),
                amount_usd=_extract_amount_usd(entry["title"]),
                published_at=entry["published_at"],
                snippet=entry["snippet"],
            )
            for entry in entries
        ]
        return rounds[:max_results]


def get_funding_provider() -> FundingProvider:
    settings = get_settings()
    if settings.crunchbase_api_key:
        return CrunchbaseFundingProvider(settings.crunchbase_api_key.get_secret_value())
    return GoogleNewsFundingProvider()
