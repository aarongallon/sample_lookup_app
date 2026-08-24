"""Seed the database with curated samples from data/samples.json."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.database import DatabaseStore, init_db
from app.models import SampleTrack


async def seed() -> None:
    url = settings.database_url
    scheme = url.split("://")[0] if "://" in url else "UNKNOWN"
    has_at = "@" in url
    print(f"  DB URL scheme={scheme}, has_credentials={has_at}, length={len(url)}")
    await init_db(url)

    data_path = Path(__file__).resolve().parent.parent / "data" / "samples.json"
    with data_path.open(encoding="utf-8") as f:
        entries = json.load(f)

    store = DatabaseStore()
    for entry in entries:
        samples = [SampleTrack.model_validate(s) for s in entry.get("samples", [])]
        await store.upsert(
            artist=entry["artist"],
            title=entry["title"],
            samples=samples,
            source="curated",
        )
        print(f"  Seeded: {entry['artist']} — {entry['title']} ({len(samples)} samples)")

    print(f"\nDone — {len(entries)} tracks seeded.")


if __name__ == "__main__":
    asyncio.run(seed())
