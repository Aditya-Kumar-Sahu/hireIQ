"""Embedding helpers with Redis caching and a deterministic local fallback."""

from __future__ import annotations

import hashlib
import json
from statistics import mean

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.redis import redis_client


class EmbeddingService:
    """Generate and cache embeddings for jobs, resumes, and search queries."""

    model = "text-embedding-3-small"
    dimension = 1536
    cache_ttl_seconds = 60 * 60 * 24

    def __init__(self) -> None:
        self.redis = redis_client
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize whitespace before hashing or embedding."""
        return " ".join(text.split()).strip()

    def build_cache_key(self, text: str) -> str:
        """Build the Redis cache key for a text payload."""
        normalized = self.normalize_text(text)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"embedding:{self.model}:{digest}"

    def chunk_text(
        self,
        text: str,
        chunk_size_words: int = 512,
        overlap_words: int = 50,
    ) -> list[str]:
        """Split long text into overlapping word chunks."""
        words = self.normalize_text(text).split()
        if not words:
            return []
        if len(words) <= chunk_size_words:
            return [" ".join(words)]

        chunks: list[str] = []
        start = 0
        step = max(chunk_size_words - overlap_words, 1)
        while start < len(words):
            chunk = words[start : start + chunk_size_words]
            if not chunk:
                break
            chunks.append(" ".join(chunk))
            start += step
        return chunks

    async def embed_text(self, text: str) -> list[float]:
        """Return a cached embedding for the provided text."""
        normalized = self.normalize_text(text)
        cache_key = self.build_cache_key(normalized)
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        if self._client is not None:
            response = await self._client.embeddings.create(model=self.model, input=normalized)
            embedding = list(response.data[0].embedding)
        else:
            embedding = self._local_embedding(normalized)

        await self.redis.set(cache_key, json.dumps(embedding), ex=self.cache_ttl_seconds)
        return embedding

    async def embed_job_text(self, text: str) -> list[float]:
        """Embed job content, averaging chunk vectors for larger inputs."""
        chunks = self.chunk_text(text)
        if not chunks:
            return self._local_embedding("")
        embeddings = [await self.embed_text(chunk) for chunk in chunks]
        return [mean(values) for values in zip(*embeddings, strict=True)]

    def _local_embedding(self, text: str) -> list[float]:
        """Produce a deterministic local embedding when OpenAI is unavailable."""
        vector = [0.0] * self.dimension
        tokens = self.normalize_text(text).lower().split()
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for offset in range(0, min(len(digest), 16), 2):
                index = int.from_bytes(digest[offset : offset + 2], "big") % self.dimension
                sign = 1.0 if digest[offset] % 2 == 0 else -1.0
                vector[index] += sign

        magnitude = sum(value * value for value in vector) ** 0.5
        if magnitude == 0:
            return vector
        return [value / magnitude for value in vector]
