"""Tests for semantic deduplication via embedding cosine similarity."""

from __future__ import annotations

import pytest

from app.agents.deduplication_agent import DeduplicationAgent
from app.services.llm_service import MockLLMService


@pytest.mark.asyncio
async def test_deduplication_removes_near_duplicate_stories(sample_articles):
    agent = DeduplicationAgent(llm_service=MockLLMService(), threshold=0.5)
    deduped = await agent.run(sample_articles)

    titles = [a.title for a in deduped]
    assert len(deduped) == 2
    assert "Novel benchmark dataset for LLM reasoning" in titles


@pytest.mark.asyncio
async def test_deduplication_keeps_freshest_copy(sample_articles):
    agent = DeduplicationAgent(llm_service=MockLLMService(), threshold=0.5)
    deduped = await agent.run(sample_articles)

    kept_global = next(
        a for a in deduped if a.url in {"https://a.com/1", "https://a.com/1-duplicate"}
    )
    assert kept_global.url == "https://a.com/1"  # the more recent of the two duplicates


@pytest.mark.asyncio
async def test_deduplication_empty_input_returns_empty():
    agent = DeduplicationAgent(llm_service=MockLLMService())
    assert await agent.run([]) == []


@pytest.mark.asyncio
async def test_deduplication_respects_high_threshold(sample_articles):
    agent = DeduplicationAgent(llm_service=MockLLMService(), threshold=0.999)
    deduped = await agent.run(sample_articles)
    assert len(deduped) == len(sample_articles)
