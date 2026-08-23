import json
from pathlib import Path

from app.models import SampleTrack
from app.normalize import normalize_text


class LocalSampleStore:
    """Curated offline sample database for fast, reliable lookups."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._entries: list[dict] = []
        self.reload()

    def reload(self) -> None:
        with self.path.open(encoding="utf-8") as handle:
            self._entries = json.load(handle)

    def lookup(self, artist: str, title: str) -> tuple[dict[str, str], list[SampleTrack]] | None:
        artist_n = normalize_text(artist)
        title_n = normalize_text(title)

        # Exact-ish match first
        for entry in self._entries:
            if normalize_text(entry["artist"]) == artist_n and normalize_text(entry["title"]) == title_n:
                return self._pack(entry)

        # Title-only fallback when artist string is messy (e.g. featuring tags)
        title_hits = [
            entry
            for entry in self._entries
            if normalize_text(entry["title"]) == title_n
            and (
                artist_n in normalize_text(entry["artist"])
                or normalize_text(entry["artist"]) in artist_n
            )
        ]
        if len(title_hits) == 1:
            return self._pack(title_hits[0])

        return None

    @staticmethod
    def _pack(entry: dict) -> tuple[dict[str, str], list[SampleTrack]]:
        matched = {"title": entry["title"], "artist": entry["artist"]}
        samples = [SampleTrack.model_validate(sample) for sample in entry.get("samples", [])]
        return matched, samples
