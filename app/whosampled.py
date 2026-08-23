from __future__ import annotations

import re
from urllib.parse import quote_plus, unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.models import SampleTrack
from app.normalize import clean_title, normalize_text, slugify, track_slug_candidates

BASE_URL = "https://www.whosampled.com"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# Artist hubs are /Artist/ ; track pages are /Artist/Track-Name/
_TRACK_PATH_RE = re.compile(r"^/[^/]+/[^/]+/?$")
_ARTIST_HUB_TITLE_RE = re.compile(
    r".+\s+-\s+Samples,\s+Covers and Remixes",
    re.IGNORECASE,
)


class WhoSampledClient:
    """Best-effort WhoSampled lookup. Site HTML can change; local store is the stable path."""

    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout
        self._headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def lookup(self, artist: str, title: str) -> tuple[dict[str, str], list[SampleTrack]] | None:
        async with httpx.AsyncClient(
            headers=self._headers,
            follow_redirects=True,
            timeout=self.timeout,
            trust_env=False,
        ) as client:
            track_url = await self._resolve_track_url(client, artist, title)
            if not track_url:
                return None

            response = await client.get(track_url)
            if response.status_code != 200:
                return None
            if not self._is_track_page(str(response.url), response.text):
                return None

            samples = self._parse_samples(response.text)
            matched = self._parse_track_identity(response.text, artist, title, str(response.url))
            return matched, samples

    async def _resolve_track_url(self, client: httpx.AsyncClient, artist: str, title: str) -> str | None:
        cleaned = clean_title(title)
        artist_slug = slugify(artist)
        for title_slug in track_slug_candidates(cleaned):
            direct = f"{BASE_URL}/{artist_slug}/{title_slug}/"
            direct_resp = await client.get(direct)
            if direct_resp.status_code != 200:
                continue
            final_url = str(direct_resp.url)
            if self._is_track_page(final_url, direct_resp.text):
                return final_url

        # Search fallback using the cleaned title (no feat/remaster tags)
        query = quote_plus(f"{artist} {cleaned}")
        search_url = f"{BASE_URL}/search/?q={query}"
        search_resp = await client.get(search_url)
        if search_resp.status_code != 200:
            return None

        return self._best_search_hit(search_resp.text, artist, cleaned)

    def _best_search_hit(self, html: str, artist: str, title: str) -> str | None:
        soup = BeautifulSoup(html, "lxml")
        artist_n = normalize_text(artist)
        title_n = normalize_text(title)
        title_slugs = {normalize_text(s.replace("-", " ")) for s in track_slug_candidates(title)}

        candidates: list[tuple[int, str]] = []
        for anchor in soup.select("a[href]"):
            href = anchor.get("href") or ""
            path = unquote(urlparse(href).path)
            if not _TRACK_PATH_RE.match(path):
                continue
            if any(skip in path for skip in ("/user/", "/news/", "/browse/", "/sample/", "/cover/", "/remix/")):
                continue

            text = normalize_text(anchor.get_text(" ", strip=True))
            parent_text = normalize_text(anchor.parent.get_text(" ", strip=True) if anchor.parent else "")
            haystack = f"{text} {parent_text}"
            path_title = normalize_text(path.rstrip("/").rsplit("/", 1)[-1].replace("-", " "))

            score = 0
            if title_n and text == title_n:
                score += 8
            elif title_n and title_n == path_title:
                score += 7
            elif title_n and path_title in title_slugs:
                score += 6
            elif title_n and (title_n in text or title_n in path_title):
                # Substring matches are weak ("Stop" inside "Don't Stop")
                score += 2
            if artist_n and artist_n in haystack:
                score += 2
            # Prefer shorter path titles when scores tie (exact "Stop!" vs long names containing stop)
            score -= min(len(path_title), 20) // 10

            if score > 0:
                candidates.append((score, urljoin(BASE_URL, href)))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def _is_track_page(self, url: str, html: str) -> bool:
        """Reject artist hubs and Cloudflare interstitial pages."""
        path = unquote(urlparse(url).path)
        if not _TRACK_PATH_RE.match(path):
            return False

        soup = BeautifulSoup(html, "lxml")
        page_title = (soup.title.get_text(" ", strip=True) if soup.title else "") or ""
        if "just a moment" in page_title.lower():
            return False
        # Artist hubs: "J Dilla - Samples, Covers and Remixes"
        # Track pages: "Stop! by J Dilla - Samples, Covers and Remixes"
        if _ARTIST_HUB_TITLE_RE.search(page_title) and " by " not in page_title.lower():
            return False

        lowered = html.lower()
        return (
            "contains samples of" in lowered
            or "contains sample of" in lowered
            or "sampled in" in lowered
            or 'property="og:title"' in lowered
        )

    def _parse_track_identity(
        self,
        html: str,
        fallback_artist: str,
        fallback_title: str,
        track_url: str,
    ) -> dict[str, str]:
        soup = BeautifulSoup(html, "lxml")
        title_el = soup.select_one("h1 .trackName, h1, meta[property='og:title']")
        artist_el = soup.select_one(
            ".trackArtistNames a, .trackArtist a, .artistName a, .trackReleaseDetails a"
        )

        title = fallback_title
        artist = fallback_artist

        if title_el:
            raw = title_el.get("content") if title_el.name == "meta" else title_el.get_text(" ", strip=True)
            if raw:
                raw = re.sub(r"\s*\|\s*WhoSampled\s*$", "", raw, flags=re.IGNORECASE)
                raw = re.split(r"\s+-\s+Samples,", raw, maxsplit=1)[0].strip()
                # og:title is often "Song by Artist"
                if " by " in raw:
                    maybe_title, maybe_artist = raw.rsplit(" by ", 1)
                    title = maybe_title.strip() or title
                    artist = maybe_artist.strip() or artist
                else:
                    title = raw

        if artist_el:
            artist = artist_el.get_text(" ", strip=True) or artist

        artist = re.sub(r"\s+on WhoSampled\s*$", "", artist, flags=re.IGNORECASE).strip()
        return {"title": title, "artist": artist, "url": track_url}

    def _parse_samples(self, html: str) -> list[SampleTrack]:
        soup = BeautifulSoup(html, "lxml")
        samples: list[SampleTrack] = []

        section = self._find_contains_section(soup)
        if section is None:
            return samples

        # Current WhoSampled layout: table.tdata rows under the section
        entries = section.select("table.tdata tbody tr")
        if not entries:
            entries = section.select(".listEntry, .sampleEntry, .track-connection")
        if not entries:
            return samples

        seen: set[tuple[str, str]] = set()
        for entry in entries:
            sample = self._parse_entry(entry)
            if not sample:
                continue
            key = (normalize_text(sample.title), normalize_text(sample.artist))
            if key in seen:
                continue
            seen.add(key)
            samples.append(sample)

        return samples

    def _find_contains_section(self, soup: BeautifulSoup):
        # Prefer the subsection that owns "Contains samples of N songs"
        for header in soup.select("h3.section-header-title, h3, h2"):
            text = header.get_text(" ", strip=True).lower()
            if "contains samples of" in text or text.startswith("contains sample"):
                section = header.find_parent("section")
                if section is not None:
                    return section
                for parent in header.parents:
                    if parent.name in {"section", "div", "article"}:
                        return parent
                return header.parent
        return None

    def _parse_entry(self, entry) -> SampleTrack | None:
        # New layout: title in td.tdata__td2, then artist / year / type in td.tdata__td3
        cells = entry.select("td.tdata__td2, td.tdata__td3")
        if len(cells) >= 2:
            title_el = cells[0].select_one("a.trackName, a") or cells[0]
            title = title_el.get_text(" ", strip=True)
            artist = cells[1].get_text(" ", strip=True)
            year = None
            sample_type = None
            if len(cells) >= 3:
                year_match = re.search(r"(19|20)\d{2}", cells[2].get_text(" ", strip=True))
                if year_match:
                    year = int(year_match.group(0))
            if len(cells) >= 4:
                sample_type = cells[3].get_text(" ", strip=True) or None
            if title and artist:
                href = title_el.get("href") if hasattr(title_el, "get") else None
                url = urljoin(BASE_URL, href) if href else None
                return SampleTrack(title=title, artist=artist, year=year, type=sample_type, url=url)

        title_el = entry.select_one("a.trackName, .trackName a, a[href*='/']")
        artist_el = entry.select_one("a.trackArtist, .trackArtist a, .artist a")
        year_el = entry.select_one(".trackYear, .year, span.trackYear")
        type_el = entry.select_one(".sampleType, .trackSampleType, .connection-type")

        title = title_el.get_text(" ", strip=True) if title_el else None
        artist = artist_el.get_text(" ", strip=True) if artist_el else None

        if not title or not artist:
            text = entry.get_text(" ", strip=True)
            match = re.search(r"(.+?)\s+by\s+(.+?)(?:\s+\(|$)", text, re.IGNORECASE)
            if match:
                title = title or match.group(1).strip()
                artist = artist or match.group(2).strip()

        if not title or not artist:
            return None

        if "contains samples" in title.lower():
            return None

        year = None
        if year_el:
            year_match = re.search(r"(19|20)\d{2}", year_el.get_text(" ", strip=True))
            if year_match:
                year = int(year_match.group(0))

        sample_type = type_el.get_text(" ", strip=True) if type_el else None
        url = urljoin(BASE_URL, title_el["href"]) if title_el and title_el.get("href") else None

        return SampleTrack(title=title, artist=artist, year=year, type=sample_type, url=url)
