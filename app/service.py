from __future__ import annotations

import logging

from app.database import DatabaseStore
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
        whosampled: WhoSampledClient | None = None,
        enable_whosampled: bool = True,
    ) -> None:
        self.store = store
        self.cache = cache
        self.whosampled = whosampled or WhoSampledClient()
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

        # 2. Postgres (curated + previously scraped)
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

        # 3. WhoSampled scrape
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
                # Persist to Postgres so future lookups skip scraping
                if samples:
                    try:
                        await self.store.upsert(
                            artist=matched.get("artist", artist),
                            title=matched.get("title", title),
                            samples=samples,
                            source="whosampled",
                        )
                    except Exception:
                        logger.warning("Failed to persist WhoSampled result to DB", exc_info=True)
                return response

        return SamplesResponse(
            query=query,
            matched_track=None,
            samples=[],
            source="none",
            message="No sample data found for this track.",
        )
