# Sample Lookup API

Backend that returns the song(s) sampled in a given track. Includes macOS menu bar and iOS companion apps.

## Quick start (local dev)

```bash
cd ~/projects/sample-lookup-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_db.py       # seed curated tracks into SQLite
uvicorn app.main:app --reload --port 8000
```

Open docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Endpoint

### `GET /samples`

| Query param | Required | Example |
|-------------|----------|---------|
| `artist`    | yes      | `Kanye West` |
| `title`     | yes      | `New Slaves` |

Example:

```bash
curl "http://127.0.0.1:8000/samples?artist=Kanye%20West&title=New%20Slaves"
```

`source` can be:

- `local` — hit Postgres/SQLite (curated + previously scraped)
- `cache` — Redis cache hit
- `whosampled` — live lookup from WhoSampled
- `none` — nothing found

## How lookup works

1. Normalize artist/title (strip accents, `feat.`, remaster tags)
2. Check Redis cache
3. Check database (Postgres in production, SQLite for dev)
4. Fall back to WhoSampled (best-effort scrape)
5. Persist result to database + cache for future lookups
6. Return empty list with a message if nothing matches

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/samples.db` | Postgres or SQLite connection string |
| `REDIS_URL` | (empty — no cache) | Redis connection string |
| `ENABLE_WHOSAMPLED` | `true` | Enable live WhoSampled scraping |
| `CACHE_TTL_SECONDS` | `86400` (24h) | Redis cache TTL |

## Deploy to Railway

```bash
# Push to your Railway project (after linking)
railway up
```

Set env vars in the Railway dashboard:
- `DATABASE_URL` → from the Postgres service
- `REDIS_URL` → from the Redis service

The Dockerfile seeds curated data on startup.

## Clients

- **macOS menu bar**: [`macos/README.md`](macos/README.md)
- **iOS app + widget + Control Center**: [`ios/README.md`](ios/README.md)

## Notes

- WhoSampled has no official public API; the live scraper can break if their HTML changes.
- Curated tracks in `data/samples.json` are seeded into the database for fast, reliable lookups.
- CORS is open for local and mobile clients.
