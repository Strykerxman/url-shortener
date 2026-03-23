# URL Shortener API

[![CI](https://github.com/Strykerxman/url-shortener/actions/workflows/ci.yml/badge.svg)](https://github.com/Strykerxman/url-shortener/actions/workflows/ci.yml)

A production-ready URL shortening service built with **FastAPI**, **PostgreSQL**, and **Redis**. Supports custom aliases, link expiry, QR code generation, and rate limiting — all containerised with Docker.

## Features

| Feature | Description |
|---|---|
| 🔗 **Shorten URLs** | Generate 5-character short keys automatically |
| ✏️ **Custom aliases** | Choose your own 3–20 character alias (e.g. `/mybrand`) |
| ⏳ **Link expiry** | Set an optional `expires_at` datetime; expired links return 404 |
| 📊 **Click tracking** | Every redirect increments an analytics counter |
| 🛡️ **Soft delete** | Deactivate links without permanent data loss |
| ⚡ **Redis caching** | Sub-millisecond redirects with 24-hour TTL; transparent DB fallback |
| 🔒 **Rate limiting** | 30 req/min on creation, 120 req/min on redirects |
| 🌐 **CORS** | Cross-origin requests enabled out of the box |
| 📷 **QR codes** | One-click PNG QR code for any shortened URL |
| 🔄 **DB migrations** | Alembic-managed schema versioning |

## Architecture

```
Client → FastAPI (uvicorn)
           ├── Redis  (read-through cache, 24h TTL)
           └── PostgreSQL (source of truth, Alembic migrations)
```

## Quick Start

```bash
docker compose up --build
```

- API: `http://localhost:8000`
- Interactive docs (Swagger): `http://localhost:8000/docs`

```bash
docker compose down   # stop
```

## Configuration

Create a `.env` file (used by Docker Compose):

```ini
DATABASE_URL=postgresql+psycopg2://urlshortener:changeme@db:5432/urlshortener_db
DATABASE_USER=urlshortener
DATABASE_PW=changeme
DATABASE_NAME=urlshortener_db
BASE_URL=http://127.0.0.1:8000
DEBUG=false
ENV_NAME=main
REDIS_HOST=redis
REDIS_PORT=6379
```

## API Reference

### Create a shortened URL

```http
POST /url
Content-Type: application/json

{
  "target_url": "https://example.com",
  "custom_alias": "mylink",       # optional, 3–20 alphanumeric chars
  "expires_at": "2026-12-31T23:59:59Z"  # optional ISO-8601 UTC datetime
}
```

Response:
```json
{
  "url": "MYLINK",
  "admin_url": "MYLINK_ABCD1234",
  "target_url": "https://example.com",
  "is_active": true,
  "clicks": 0,
  "expires_at": "2026-12-31T23:59:59Z"
}
```

### Redirect

```http
GET /{key}        → 307 redirect to target URL
```

### QR Code

```http
GET /qr/{key}     → PNG image of the QR code for the short URL
```

### Admin

```http
GET    /admin/{secret_key}    → URL info and click stats
DELETE /admin/{secret_key}    → Deactivate (soft-delete) the URL
```

### Health

```http
GET /health       → {"status": "db healthy"}
```

## Local Development

```bash
# Python ≥ 3.10
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Create .env.local with your local DATABASE_URL, REDIS_HOST, etc.
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing

```bash
pytest -q
```

Tests use an isolated PostgreSQL database and a mock Redis client — no separate infrastructure needed beyond a Postgres instance pointed at by `DATABASE_URL` in `.env.test`.
