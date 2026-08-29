"""Genius API client for fetching song sample relationships."""

from __future__ import annotations

import logging
from urllib.parse import quote

import httpx

from app.models import SampleTrack

logger = logging.getLogger(__name__)

_BASE = "https://api.genius.com"
_RELEVANT_TYPES = {"samples", "interpolates", "sample_of", "interpolated_by"}


class GeniusClient:
    def __init__(self, token: str) -> None:
        self._token = token
        self._headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "SampleLookupAPI/0.3",
        }

    async def lookup(
        self, artist: str, title: str
    ) -> tuple[dict[str, str], list[SampleTrack]] | None:
        song_id = await self._find_song(artist, title)
        if song_id is None:
            return None

        song = await self._get_song(song_id)
        if song is None:
            return None

        matched = {
            "title": song.get("title", title),
            "artist": song.get("primary_artist", {}).get("name", artist),
        }
        samples = self._extract_samples(song)
        return matched, samples

    async def _find_song(self, artist: str, title: str) -> int | None:
        query = f"{title} {artist}"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE}/search",
                params={"q": query},
                headers=self._headers,
            )
            if resp.status_code != 200:
                logger.warning("Genius search returned %d", resp.status_code)
                return None

        data = resp.json()
        hits = data.get("response", {}).get("hits", [])
        if not hits:
            return None

        artist_lower = artist.lower()
        title_lower = title.lower()
        for hit in hits:
            result = hit["result"]
            hit_title = result.get("title", "").lower()
            hit_artist = result.get("primary_artist", {}).get("name", "").lower()
            if title_lower in hit_title and (
                artist_lower in hit_artist or hit_artist in artist_lower
            ):
                return result["id"]

        return hits[0]["result"]["id"]

    async def _get_song(self, song_id: int) -> dict | None:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE}/songs/{song_id}",
                headers=self._headers,
            )
            if resp.status_code != 200:
                logger.warning("Genius song/%d returned %d", song_id, resp.status_code)
                return None

        return resp.json().get("response", {}).get("song")

    @staticmethod
    def _extract_samples(song: dict) -> list[SampleTrack]:
        samples: list[SampleTrack] = []
        for rel in song.get("song_relationships", []):
            rtype = rel.get("relationship_type", "")
            if rtype not in _RELEVANT_TYPES:
                continue

            for s in rel.get("songs", []):
                artist_name = s.get("primary_artist", {}).get("name", "Unknown")
                samples.append(
                    SampleTrack(
                        title=s.get("title", "Unknown"),
                        artist=artist_name,
                        year=None,
                        type=rtype.replace("_", " ").title(),
                        url=s.get("url"),
                    )
                )
        return samples
