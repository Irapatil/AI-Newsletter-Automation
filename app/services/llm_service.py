"""LLM abstraction layer: chat completion + embeddings.

Supports OpenAI, Azure OpenAI, and a dependency-free Mock implementation.
The mock is selected automatically whenever no provider credentials are
configured (see `Settings.uses_mock_llm`), so the LangGraph workflow, the
FastAPI endpoints, and the test suite all run without any API key.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

from app.config.logging_config import get_logger
from app.config.settings import Settings, get_settings
from app.utils.text_utils import truncate

logger = get_logger(__name__)

MOCK_EMBEDDING_DIM = 64


class LLMService(ABC):
    """Abstract interface for text generation and embeddings."""

    @abstractmethod
    async def generate_text(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 400
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class OpenAILLMService(LLMService):
    """OpenAI-backed implementation using LangChain's chat + embeddings clients."""

    def __init__(self, settings: Settings) -> None:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings

        self._chat = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=0.3,
        )
        self._embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
        )

    async def generate_text(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 400
    ) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage

        response = await self._chat.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)],
            max_tokens=max_tokens,
        )
        return str(response.content).strip()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await self._embeddings.aembed_documents(texts)


class AzureOpenAILLMService(LLMService):
    """Azure OpenAI-backed implementation using LangChain's Azure clients."""

    def __init__(self, settings: Settings) -> None:
        from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

        self._chat = AzureChatOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            azure_deployment=settings.azure_openai_chat_deployment,
            temperature=0.3,
        )
        self._embeddings = AzureOpenAIEmbeddings(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            azure_deployment=settings.azure_openai_embedding_deployment,
        )

    async def generate_text(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 400
    ) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage

        response = await self._chat.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)],
            max_tokens=max_tokens,
        )
        return str(response.content).strip()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await self._embeddings.aembed_documents(texts)


class MockLLMService(LLMService):
    """Deterministic, offline implementation for demos, tests, and CI.

    - `generate_text` returns an extractive truncation of the user prompt so
      output stays deterministic and human-readable without any API call.
    - `embed_texts` hashes words into a fixed-size bag-of-words vector so
      near-duplicate titles still score highly similar under cosine
      similarity, keeping the deduplication stage meaningfully testable.
    """

    async def generate_text(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 400
    ) -> str:
        return truncate(user_prompt.strip(), max_chars=max_tokens)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_embed(text) for text in texts]

    @staticmethod
    def _hash_embed(text: str) -> list[float]:
        vector = [0.0] * MOCK_EMBEDDING_DIM
        words = text.lower().split()
        if not words:
            return vector
        for word in words:
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            index = digest[0] % MOCK_EMBEDDING_DIM
            vector[index] += 1.0
        norm = sum(v * v for v in vector) ** 0.5
        if norm == 0.0:
            return vector
        return [v / norm for v in vector]


def get_llm_service() -> LLMService:
    settings = get_settings()

    if settings.uses_mock_llm:
        logger.info("llm_service_selected", provider="mock")
        return MockLLMService()

    if settings.llm_provider == "azure_openai":
        logger.info("llm_service_selected", provider="azure_openai")
        return AzureOpenAILLMService(settings)

    logger.info("llm_service_selected", provider="openai")
    return OpenAILLMService(settings)
