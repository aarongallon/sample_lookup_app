from __future__ import annotations

import logging

from app.database import DatabaseStore
from app.genius import GeniusClient
from app.models import SampleTrack, SamplesResponse
from app.normalize import cache_key
from app.redis_cache import NullCache, RedisCache
from app.whosampled import WhoSampledClient

logger = logging.getLogger(__name__)


class SampleService:
    def __init__(
        self,
        store: DatabaseStore,
        cache: RedisCache | NullCache,
        genius: GeniusClient | None = None,
        whosampled: WhoSampledClient | None = None,
        enable_genius: bool = True,
        enable_whosampled: bool = False,
    ) -> None:
        self.store = store
        self.cache = cache
        self.genius = genius
        self.whosampled = whosampled or WhoSampledClient()
        self.enable_genius = enable_genius and genius is not None
        self.enable_whosampled = enable_whosampled

    async def get_samples(self, artist: str, title: str) -> SamplesResponse:
        artist = artist.strip()
        title = title.strip()
        query = {"artist": artist, "title": title}
        key = cache_key(artist, title)

        # 1. Redis cache
        cached = await self.cache.get(key)
        if cached is not None:
            cached.source = "cache"
            cached.query = query
            return cached

        # 2. Postgres (curated + previously fetched)
        local = await self.store.lookup(artist, title)
        if local is not None:
            matched, samples = local
            response = SamplesResponse(
                query=query,
                matched_track=matched,
                samples=samples,
                source="local",
            )
            await self.cache.set(key, response)
            return response

        # 3. Genius API (primary remote source)
        if self.enable_genius:
            try:
                remote = await self.genius.lookup(artist, title)
            except Exception:
                logger.exception("Genius lookup failed for %r / %r", artist, title)
                remote = None

            if remote is not None:
                matched, samples = remote
                response = SamplesResponse(
                    query=query,
                    matched_track=matched,
                    samples=samples,
                    source="genius",
                    message=None if samples else "Track found, but no listed samples.",
                )
                await self.cache.set(key, response)
                if samples:
                    await self._persist(matched, artist, title, samples, "genius")
                return response

        # 4. WhoSampled fallback (local dev only)
        if self.enable_whosampled:
            try:
                remote = await self.whosampled.lookup(artist, title)
            except Exception:
                logger.exception("WhoSampled lookup failed for %r / %r", artist, title)
                remote = None

            if remote is not None:
                matched, samples = remote
                response = SamplesResponse(
                    query=query,
                    matched_track=matched,
                    samples=samples,
                    source="whosampled",
                    message=None if samples else "Track found, but no listed samples.",
                )
                await self.cache.set(key, response)
                if samples:
                    await self._persist(matched, artist, title, samples, "whosampled")
                return response

        return SamplesResponse(
            query=query,
            matched_track=None,
            samples=[],
            source="none",
            message="No sample data found for this track.",
        )

    async def _persist(
        self,
        matched: dict[str, str],
        artist: str,
        title: str,
        samples: list[SampleTrack],
        source: str,
    ) -> None:
        try:
            await self.store.upsert(
                artist=matched.get("artist", artist),
                title=matched.get("title", title),
                samples=samples,
                source=source,
            )
        except Exception:
            logger.warning("Failed to persist %s result to DB", source, exc_info=True)
