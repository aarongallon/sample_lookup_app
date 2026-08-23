from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models import SampleTrack
from app.normalize import normalize_text

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class SampleRecord(Base):
    __tablename__ = "sample_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artist: Mapped[str] = mapped_column(String(512), index=True)
    title: Mapped[str] = mapped_column(String(512), index=True)
    artist_normalized: Mapped[str] = mapped_column(String(512), index=True)
    title_normalized: Mapped[str] = mapped_column(String(512), index=True)
    samples_json: Mapped[str] = mapped_column(Text, default="[]")
    source: Mapped[str] = mapped_column(String(32), default="curated")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_db(database_url: str) -> None:
    global _engine, _session_factory
    _engine = create_async_engine(database_url, echo=False)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized: %s", database_url.split("@")[-1] if "@" in database_url else database_url)


async def close_db() -> None:
    global _engine
    if _engine:
        await _engine.dispose()


def get_session() -> AsyncSession:
    if _session_factory is None:
        raise RuntimeError("Database not initialized — call init_db first")
    return _session_factory()


class DatabaseStore:
    """Postgres/SQLite-backed sample store, replacing the old JSON file."""

    async def lookup(self, artist: str, title: str) -> tuple[dict[str, str], list[SampleTrack]] | None:
        artist_n = normalize_text(artist)
        title_n = normalize_text(title)

        async with get_session() as session:
            stmt = select(SampleRecord).where(
                SampleRecord.artist_normalized == artist_n,
                SampleRecord.title_normalized == title_n,
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()

            if row is None:
                # Fuzzy fallback: title match with partial artist match
                stmt = select(SampleRecord).where(
                    SampleRecord.title_normalized == title_n
                )
                result = await session.execute(stmt)
                candidates = result.scalars().all()
                row = next(
                    (
                        r for r in candidates
                        if artist_n in r.artist_normalized or r.artist_normalized in artist_n
                    ),
                    None,
                )

            if row is None:
                return None

            return self._pack(row)

    async def upsert(self, artist: str, title: str, samples: list[SampleTrack], source: str = "whosampled") -> None:
        """Insert or update a sample record (used after WhoSampled lookups)."""
        import json

        artist_n = normalize_text(artist)
        title_n = normalize_text(title)
        samples_data = json.dumps([s.model_dump() for s in samples])

        async with get_session() as session:
            stmt = select(SampleRecord).where(
                SampleRecord.artist_normalized == artist_n,
                SampleRecord.title_normalized == title_n,
            )
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()

            if row:
                row.samples_json = samples_data
                row.source = source
            else:
                session.add(SampleRecord(
                    artist=artist,
                    title=title,
                    artist_normalized=artist_n,
                    title_normalized=title_n,
                    samples_json=samples_data,
                    source=source,
                ))
            await session.commit()

    @staticmethod
    def _pack(row: SampleRecord) -> tuple[dict[str, str], list[SampleTrack]]:
        import json
        matched = {"title": row.title, "artist": row.artist}
        raw_samples = json.loads(row.samples_json) if row.samples_json else []
        samples = [SampleTrack.model_validate(s) for s in raw_samples]
        return matched, samples
