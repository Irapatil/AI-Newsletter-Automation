"""Tests for OpenSourceAgent: GitHub repo + Hugging Face model to Article mapping."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.agents.opensource_agent import OpenSourceAgent
from app.models.article import NewsCategory
from app.services.github_service import GithubRepo
from app.services.huggingface_service import HuggingFaceModel


def _make_repo(**overrides) -> GithubRepo:
    base: GithubRepo = {
        "name": "acme/awesome-llm",
        "url": "https://github.com/acme/awesome-llm",
        "description": "An awesome LLM framework.",
        "stars": 4321,
        "language": "Python",
        "created_at": datetime(2024, 1, 10, tzinfo=UTC),
    }
    base.update(overrides)
    return base


def _make_model(**overrides) -> HuggingFaceModel:
    base: HuggingFaceModel = {
        "model_id": "acme/tiny-bert",
        "url": "https://huggingface.co/acme/tiny-bert",
        "likes": 99,
        "downloads": 15000,
        "pipeline_tag": "text-classification",
        "last_modified": datetime(2024, 2, 5, tzinfo=UTC),
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_fetch_maps_repos_and_models_to_articles(monkeypatch: pytest.MonkeyPatch) -> None:
    repos = [_make_repo()]
    models = [_make_model()]

    async def _fake_repos(max_results: int = 15):
        return repos

    async def _fake_models(max_results: int = 15):
        return models

    monkeypatch.setattr("app.agents.opensource_agent.fetch_trending_ai_repos", _fake_repos)
    monkeypatch.setattr("app.agents.opensource_agent.fetch_trending_models", _fake_models)

    articles = await OpenSourceAgent().fetch()

    assert len(articles) == 2
    repo_article, model_article = articles

    assert repo_article.title == "acme/awesome-llm"
    assert repo_article.url == "https://github.com/acme/awesome-llm"
    assert repo_article.source == "GitHub Trending"
    assert repo_article.category == NewsCategory.OPENSOURCE
    assert repo_article.published_at == datetime(2024, 1, 10, tzinfo=UTC)
    assert repo_article.snippet == "An awesome LLM framework."
    assert repo_article.metadata == {"stars": 4321, "language": "Python"}

    assert model_article.title == "acme/tiny-bert"
    assert model_article.url == "https://huggingface.co/acme/tiny-bert"
    assert model_article.source == "Hugging Face"
    assert model_article.category == NewsCategory.OPENSOURCE
    assert model_article.published_at == datetime(2024, 2, 5, tzinfo=UTC)
    assert model_article.snippet == "Pipeline: text-classification | Likes: 99"
    assert model_article.metadata == {"likes": 99, "downloads": 15000}


@pytest.mark.asyncio
async def test_fetch_uses_na_for_missing_pipeline_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    models = [_make_model(pipeline_tag=None)]

    async def _fake_repos(max_results: int = 15):
        return []

    async def _fake_models(max_results: int = 15):
        return models

    monkeypatch.setattr("app.agents.opensource_agent.fetch_trending_ai_repos", _fake_repos)
    monkeypatch.setattr("app.agents.opensource_agent.fetch_trending_models", _fake_models)

    articles = await OpenSourceAgent().fetch()

    assert len(articles) == 1
    assert articles[0].snippet == "Pipeline: n/a | Likes: 99"


@pytest.mark.asyncio
async def test_fetch_defaults_missing_model_last_modified_to_now(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _make_model()
    del model["last_modified"]

    async def _fake_repos(max_results: int = 15):
        return []

    async def _fake_models(max_results: int = 15):
        return [model]

    monkeypatch.setattr("app.agents.opensource_agent.fetch_trending_ai_repos", _fake_repos)
    monkeypatch.setattr("app.agents.opensource_agent.fetch_trending_models", _fake_models)

    before = datetime.now(UTC)
    articles = await OpenSourceAgent().fetch()
    after = datetime.now(UTC)

    assert len(articles) == 1
    assert before <= articles[0].published_at <= after


@pytest.mark.asyncio
async def test_fetch_skips_repos_and_models_with_no_url(monkeypatch: pytest.MonkeyPatch) -> None:
    repos = [_make_repo(url="")]
    models = [_make_model(url="")]

    async def _fake_repos(max_results: int = 15):
        return repos

    async def _fake_models(max_results: int = 15):
        return models

    monkeypatch.setattr("app.agents.opensource_agent.fetch_trending_ai_repos", _fake_repos)
    monkeypatch.setattr("app.agents.opensource_agent.fetch_trending_models", _fake_models)

    articles = await OpenSourceAgent().fetch()

    assert articles == []


@pytest.mark.asyncio
async def test_fetch_returns_github_articles_when_huggingface_source_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repos = [
        _make_repo(),
        _make_repo(name="acme/other-repo", url="https://github.com/acme/other-repo"),
    ]

    async def _fake_repos(max_results: int = 15):
        return repos

    async def _fake_models(max_results: int = 15):
        return []

    monkeypatch.setattr("app.agents.opensource_agent.fetch_trending_ai_repos", _fake_repos)
    monkeypatch.setattr("app.agents.opensource_agent.fetch_trending_models", _fake_models)

    articles = await OpenSourceAgent().fetch()

    assert len(articles) == 2
    assert all(article.source == "GitHub Trending" for article in articles)


@pytest.mark.asyncio
async def test_fetch_returns_huggingface_articles_when_github_source_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    models = [
        _make_model(),
        _make_model(model_id="acme/other-model", url="https://huggingface.co/acme/other-model"),
    ]

    async def _fake_repos(max_results: int = 15):
        return []

    async def _fake_models(max_results: int = 15):
        return models

    monkeypatch.setattr("app.agents.opensource_agent.fetch_trending_ai_repos", _fake_repos)
    monkeypatch.setattr("app.agents.opensource_agent.fetch_trending_models", _fake_models)

    articles = await OpenSourceAgent().fetch()

    assert len(articles) == 2
    assert all(article.source == "Hugging Face" for article in articles)
