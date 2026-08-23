from typing import Literal

from pydantic import BaseModel, Field


class SampleTrack(BaseModel):
    title: str
    artist: str
    year: int | None = None
    type: str | None = Field(
        default=None,
        description="How the sample is used, e.g. Vocals / Lyrics, Drums, Multiple Elements",
    )
    url: str | None = None


class SamplesResponse(BaseModel):
    query: dict[str, str]
    matched_track: dict[str, str] | None = None
    samples: list[SampleTrack]
    source: Literal["local", "cache", "whosampled", "none"]
    message: str | None = None
