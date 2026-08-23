from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import DatabaseStore, close_db, init_db
from app.models import SamplesResponse
from app.redis_cache import build_cache
from app.service import SampleService
from app.whosampled import WhoSampledClient

cache = build_cache(settings.redis_url, settings.cache_ttl_seconds)
store = DatabaseStore()
service = SampleService(
    store=store,
    cache=cache,
    whosampled=WhoSampledClient(),
    enable_whosampled=settings.enable_whosampled,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.database_url)
    yield
    await cache.close()
    await close_db()


app = FastAPI(
    title="Sample Lookup API",
    description="Given a song title and artist, return the track(s) sampled in it.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/samples", response_model=SamplesResponse)
async def get_samples(
    artist: str = Query(..., min_length=1, description="Artist name, e.g. Kanye West"),
    title: str = Query(..., min_length=1, description="Song title, e.g. New Slaves"),
) -> SamplesResponse:
    if not artist.strip() or not title.strip():
        raise HTTPException(status_code=400, detail="artist and title are required")
    return await service.get_samples(artist=artist, title=title)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Sample Lookup API",
        "try": "/samples?artist=Kanye%20West&title=New%20Slaves",
        "docs": "/docs",
    }
