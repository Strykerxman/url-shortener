# URL Shortener API

A production-ready URL shortening service built with **FastAPI**, **PostgreSQL**, **Redis**, and **Docker**.  
Designed to demonstrate clean architecture, measurable performance choices, and solid engineering fundamentals.

---

## Features

| Feature | Details |
|---|---|
| ✅ Shorten URLs | `POST /url` — returns a 5-char alphanumeric key |
| ✅ Fast redirects | `GET /{key}` — Redis cache-first, PostgreSQL fallback |
| ✅ URL expiry | Optional `expires_at` timestamp; expired links return 404 automatically |
| ✅ Click analytics | Atomic `UPDATE … RETURNING` — no extra SELECT round-trip |
| ✅ Admin management | `GET /admin/{secret}` · `DELETE /admin/{secret}` |
| ✅ Rate limiting | 10 creates/min · 60 redirects/min per IP (SlowAPI) |
| ✅ Health check | `GET /health` — verifies DB connectivity |
| ✅ Soft deletes | Deactivated links return 404; historical data preserved |
| ✅ Cache resilience | Redis errors are caught and logged; API falls back to DB |

---

## Architecture

```
Client ──► FastAPI (uvicorn)
               │
    ┌──────────┴──────────┐
    │  Redis (cache)       │  ← cache-first reads, 24 h TTL, graceful fallback
    │  PostgreSQL (store)  │  ← source of truth, Alembic migrations
    └─────────────────────┘
```

**Key design choices and their measurable impact:**

- **Cache-first redirect** — Redis lookup costs ~0.1 ms vs ~5 ms for a DB read (≈ 50× faster at scale).
- **Atomic click increment** — single `UPDATE … RETURNING` eliminates the read-modify-write race condition that would double-count clicks under concurrency.
- **Rate limiting** — prevents abuse without requiring authentication; limits are per client IP.
- **Soft delete** — `is_active = False` keeps audit history while making the link inaccessible.
- **Expiry at query time** — `expires_at` is evaluated server-side via a SQL `WHERE` clause, so no cron job or background worker is needed.

---

## Quick Start (Docker)

```bash
cp .env.example .env      # edit passwords if needed
docker compose up --build
```

- API: <http://localhost:8000>
- Interactive docs: <http://localhost:8000/docs>

```bash
docker compose down
```

---

## Local Development

```bash
# 1. Create a virtual environment
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install runtime + dev dependencies
pip install -r requirements-dev.txt

# 3. Configure environment
cp .env.example .env.local
# Edit .env.local: set DATABASE_URL to postgresql+psycopg2://...@localhost:5432/...
#                  set REDIS_HOST=localhost

# 4. Run database migrations
alembic upgrade head

# 5. Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Welcome message |
| `GET` | `/health` | DB health check |
| `POST` | `/url` | Create a shortened URL |
| `GET` | `/{key}` | Redirect to target (rate-limited) |
| `GET` | `/admin/{secret}` | View URL stats |
| `DELETE` | `/admin/{secret}` | Deactivate (soft-delete) a URL |

### Create a URL

```bash
curl -X POST http://localhost:8000/url \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com", "expires_at": "2027-01-01T00:00:00Z"}'
```

Response:
```json
{
  "target_url": "https://example.com",
  "expires_at": "2027-01-01T00:00:00Z",
  "is_active": true,
  "clicks": 0,
  "url": "AB3XZ",
  "admin_url": "AB3XZ_GHIJKLMN"
}
```

---

## Testing

Tests use **SQLite in-memory** (no Postgres needed) and **fakeredis** (no Redis needed).  
No `AsyncMock` — the Redis fixture is a real in-memory implementation.

```bash
pytest -v
```

Test coverage includes:
- URL creation with and without expiry
- Redirect via cache hit and DB fallback
- Expired URL returns 404
- Atomic click counting
- Redis failure graceful fallback
- Rate limit enforcement (429 on 11th POST/minute)
- Admin info and soft delete

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | *(required)* | Full PostgreSQL connection string |
| `DATABASE_USER` | `urlshortener` | Postgres user (Compose only) |
| `DATABASE_PW` | `changeme` | Postgres password (Compose only) |
| `DATABASE_NAME` | `urlshortener_db` | Postgres database name (Compose only) |
| `BASE_URL` | `http://127.0.0.1:8000` | Public base URL for building short links |
| `REDIS_HOST` | `localhost` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `DEBUG` | `false` | Enable SQLAlchemy query logging |
| `ENV_NAME` | `development` | Environment label |

> For **Docker Compose**: copy `.env.example` → `.env`  
> For **local dev**: copy `.env.example` → `.env.local` (overrides `.env` values)

---

## Tech Stack

- **FastAPI** — async REST framework with automatic OpenAPI docs
- **SQLAlchemy 2 + Alembic** — ORM with schema migrations
- **PostgreSQL 17** — primary data store
- **Redis 7** — caching layer
- **SlowAPI** — per-IP rate limiting
- **Docker Compose** — multi-service orchestration
- **pytest + fakeredis + httpx** — test suite (no external services needed)