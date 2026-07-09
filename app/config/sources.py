"""Static configuration of news sources used by the collector agents.

Where a publisher does not expose a stable, unauthenticated RSS feed (e.g.
Reuters, or per-company blogs), we fall back to Google News RSS search
queries, which are public and require no API key. This keeps every collector
agent functional out-of-the-box without credentials.
"""

from __future__ import annotations

GOOGLE_NEWS_RSS_BASE = "https://news.google.com/rss/search"


def google_news_query_url(query: str, when: str = "2d") -> str:
    """Build a Google News RSS search URL for a query, scoped to a recency window."""
    from urllib.parse import quote

    encoded = quote(f"{query} when:{when}")
    return f"{GOOGLE_NEWS_RSS_BASE}?q={encoded}&hl=en-US&gl=US&ceid=US:en"


# ---------------------------------------------------------------------------
# Global AI news - direct publisher RSS feeds plus a Google News proxy for
# publishers without a reliable direct feed.
# ---------------------------------------------------------------------------
GLOBAL_NEWS_RSS_FEEDS: dict[str, str] = {
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
    "The Verge AI": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "Reuters AI": google_news_query_url("Reuters artificial intelligence"),
}

SOURCE_CREDIBILITY: dict[str, float] = {
    "Reuters AI": 1.0,
    "MIT Technology Review": 0.95,
    "TechCrunch AI": 0.85,
    "VentureBeat AI": 0.8,
    "The Verge AI": 0.85,
    "arXiv": 0.9,
    "GitHub Trending": 0.75,
    "Hugging Face": 0.8,
    "Google News": 0.6,
}

# ---------------------------------------------------------------------------
# Company news - tracked via Google News RSS queries scoped to each company.
# ---------------------------------------------------------------------------
COMPANY_NEWS_QUERIES: dict[str, str] = {
    "OpenAI": "OpenAI",
    "Anthropic": "Anthropic AI",
    "Microsoft AI": "Microsoft AI Copilot",
    "Google DeepMind": "Google DeepMind",
    "Meta AI": "Meta AI Llama",
    "NVIDIA": "NVIDIA AI",
    "Amazon AI": "Amazon AWS AI",
    "xAI": "xAI Grok",
}

MODEL_RELEASE_QUERIES: dict[str, str] = {
    "OpenAI": "OpenAI new model release",
    "Anthropic": "Anthropic Claude new model",
    "Google DeepMind": "Google Gemini new model",
    "Meta AI": "Meta Llama new model release",
    "Mistral AI": "Mistral AI new model release",
    "xAI": "xAI Grok new model",
}

# ---------------------------------------------------------------------------
# Research - arXiv API (public, no key required).
# ---------------------------------------------------------------------------
ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_CATEGORIES: list[str] = ["cs.AI", "cs.LG", "cs.CL"]

# ---------------------------------------------------------------------------
# Funding - Crunchbase requires a paid API key; Google News RSS is used as a
# free supplementary/fallback source.
# ---------------------------------------------------------------------------
FUNDING_FALLBACK_QUERY = "AI startup funding round million"

# ---------------------------------------------------------------------------
# Talent - public job board APIs (Greenhouse & Lever), no auth required.
# ---------------------------------------------------------------------------
GREENHOUSE_JOB_BOARD_API = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
LEVER_POSTINGS_API = "https://api.lever.co/v0/postings/{company_slug}?mode=json"
AI_TALENT_KEYWORDS: list[str] = [
    "machine learning",
    "artificial intelligence",
    "ai ",
    "ml engineer",
    "llm",
    "deep learning",
    "research scientist",
]

# ---------------------------------------------------------------------------
# Open source - GitHub Search API and Hugging Face Hub API (both public).
# ---------------------------------------------------------------------------
GITHUB_SEARCH_API = "https://api.github.com/search/repositories"
HUGGINGFACE_MODELS_API = "https://huggingface.co/api/models"

# ---------------------------------------------------------------------------
# Policy - tracked via Google News RSS queries.
# ---------------------------------------------------------------------------
POLICY_QUERIES: dict[str, str] = {
    "EU AI Act": "EU AI Act",
    "India AI Mission": "India AI Mission IndiaAI",
    "US AI Executive Order": "United States AI executive order policy",
}

# ---------------------------------------------------------------------------
# NewsAPI.org - optional supplementary source for global/policy news.
# ---------------------------------------------------------------------------
NEWSAPI_EVERYTHING_URL = "https://newsapi.org/v2/everything"
