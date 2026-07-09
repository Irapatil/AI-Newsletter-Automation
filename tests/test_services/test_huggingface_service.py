"""Tests for the Hugging Face Hub API client."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest
import respx

from app.config.sources import HUGGINGFACE_MODELS_API
from app.services.huggingface_service import fetch_trending_models


@pytest.mark.asyncio
async def test_fetch_trending_models_parses_response() -> None:
    payload = [
        {
            "id": "meta-llama/Llama-3-8B",
            "likes": 500,
            "downloads": 100_000,
            "pipeline_tag": "text-generation",
            "lastModified": "2024-05-01T10:00:00.000Z",
        },
        {
            "modelId": "bert-base-uncased",
            "likes": 300,
            "downloads": 50_000,
            "pipeline_tag": "fill-mask",
            "lastModified": "2024-04-15T08:30:00.000Z",
        },
    ]
    with respx.mock:
        respx.get(HUGGINGFACE_MODELS_API).mock(return_value=httpx.Response(200, json=payload))
        models = await fetch_trending_models()

    assert len(models) == 2

    first = models[0]
    assert first["model_id"] == "meta-llama/Llama-3-8B"
    assert first["url"] == "https://huggingface.co/meta-llama/Llama-3-8B"
    assert first["likes"] == 500
    assert first["downloads"] == 100_000
    assert first["pipeline_tag"] == "text-generation"
    assert first["last_modified"] == datetime(2024, 5, 1, 10, 0, 0, tzinfo=UTC)

    second = models[1]
    assert second["model_id"] == "bert-base-uncased"
    assert second["url"] == "https://huggingface.co/bert-base-uncased"
    assert second["last_modified"] == datetime(2024, 4, 15, 8, 30, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_fetch_trending_models_prefers_model_id_over_id() -> None:
    payload = [
        {
            "id": "should-not-be-used",
            "modelId": "actual/model-id",
            "likes": 1,
            "downloads": 1,
        }
    ]
    with respx.mock:
        respx.get(HUGGINGFACE_MODELS_API).mock(return_value=httpx.Response(200, json=payload))
        models = await fetch_trending_models()

    assert models[0]["model_id"] == "actual/model-id"


@pytest.mark.asyncio
async def test_fetch_trending_models_defaults_missing_fields() -> None:
    payload = [{}]
    with respx.mock:
        respx.get(HUGGINGFACE_MODELS_API).mock(return_value=httpx.Response(200, json=payload))
        before = datetime.now(UTC)
        models = await fetch_trending_models()
        after = datetime.now(UTC)

    model = models[0]
    assert model["model_id"] == "unknown"
    assert model["url"] == "https://huggingface.co/unknown"
    assert model["likes"] == 0
    assert model["downloads"] == 0
    assert model["pipeline_tag"] is None
    # lastModified is missing entirely, so the function should fall back to "now".
    assert before <= model["last_modified"] <= after


@pytest.mark.asyncio
async def test_fetch_trending_models_returns_empty_on_http_error() -> None:
    with respx.mock:
        respx.get(HUGGINGFACE_MODELS_API).mock(return_value=httpx.Response(500))
        models = await fetch_trending_models()

    assert models == []


@pytest.mark.asyncio
async def test_fetch_trending_models_returns_empty_for_empty_payload() -> None:
    with respx.mock:
        respx.get(HUGGINGFACE_MODELS_API).mock(return_value=httpx.Response(200, json=[]))
        models = await fetch_trending_models()

    assert models == []


@pytest.mark.asyncio
async def test_fetch_trending_models_sends_expected_query_params() -> None:
    with respx.mock:
        route = respx.get(HUGGINGFACE_MODELS_API).mock(return_value=httpx.Response(200, json=[]))
        await fetch_trending_models(max_results=5)

    assert route.called
    request = route.calls.last.request
    query = httpx.QueryParams(request.url.query)
    assert query["sort"] == "likes"
    assert query["direction"] == "-1"
    assert query["limit"] == "5"
