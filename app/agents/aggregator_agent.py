"""Merges the eight parallel collector outputs into a single article list."""

from __future__ import annotations

from typing import cast

from app.models.article import Article
from app.models.state import COLLECTOR_STATE_KEYS, GraphState


class AggregatorAgent:
    display_name = "AggregatorAgent"

    def run(self, state: GraphState) -> list[Article]:
        articles: list[Article] = []
        for key in COLLECTOR_STATE_KEYS:
            articles.extend(cast("list[Article]", state.get(key) or []))
        return articles
