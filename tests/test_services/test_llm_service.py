"""Tests for the LLM service abstraction and provider selection."""

from __future__ import annotations

import pytest

from app.services.llm_service import MockLLMService, OpenAILLMService, get_llm_service


@pytest.mark.asyncio
async def test_mock_generate_text_is_deterministic(mock_llm_service: MockLLMService) -> None:
    result_1 = await mock_llm_service.generate_text("system", "hello world", max_tokens=50)
    result_2 = await mock_llm_service.generate_text("system", "hello world", max_tokens=50)
    assert result_1 == result_2
    assert result_1 == "hello world"


@pytest.mark.asyncio
async def test_mock_generate_text_truncates_to_max_tokens(mock_llm_service: MockLLMService) -> None:
    long_text = "word " * 200
    result = await mock_llm_service.generate_text("system", long_text, max_tokens=20)
    assert len(result) <= 20


@pytest.mark.asyncio
async def test_mock_embed_texts_returns_unit_vectors(mock_llm_service: MockLLMService) -> None:
    embeddings = await mock_llm_service.embed_texts(["hello ai world"])
    assert len(embeddings) == 1
    norm = sum(v * v for v in embeddings[0]) ** 0.5
    assert norm == pytest.approx(1.0, abs=1e-6)


@pytest.mark.asyncio
async def test_mock_embed_similar_texts_are_highly_similar(
    mock_llm_service: MockLLMService,
) -> None:
    from app.utils.text_utils import cosine_similarity

    embeddings = await mock_llm_service.embed_texts(
        [
            "OpenAI announces breakthrough model",
            "OpenAI announces breakthrough model release",
            "A completely unrelated story about job postings in finance",
        ]
    )
    similar_score = cosine_similarity(embeddings[0], embeddings[1])
    dissimilar_score = cosine_similarity(embeddings[0], embeddings[2])
    assert similar_score > dissimilar_score


@pytest.mark.asyncio
async def test_mock_embed_empty_list_returns_empty(mock_llm_service: MockLLMService) -> None:
    assert await mock_llm_service.embed_texts([]) == []


def test_get_llm_service_defaults_to_mock_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    assert isinstance(get_llm_service(), MockLLMService)


def test_get_llm_service_uses_openai_when_key_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    assert isinstance(get_llm_service(), OpenAILLMService)
