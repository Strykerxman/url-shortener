# URL Shortener API

FastAPI service to create, redirect, and manage shortened URLs. Uses PostgreSQL for storage, Redis for caching, and Alembic for migrations. Runs locally or via Docker Compose.

## Quick Start

```cmd
docker compose up --build
```

After startup, run migrations (alembic is NOT automatic):

```cmd
docker compose exec server alembic upgrade head
```

Then:

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

Stop:

```cmd
docker compose down
```

## Configuration

### For Docker Compose

Create a `.env.docker` file (used by Compose) with minimal settings:

```ini
DATABASE_URL=postgresql+psycopg2://urlshortener:changeme@db:5432/urlshortener_db
DATABASE_USER=urlshortener
DATABASE_PW=changeme
DATABASE_NAME=urlshortener_db
BASE_URL=http://127.0.0.1:8000
DEBUG=false
REDIS_HOST=redis
REDIS_PORT=6379
```

**REASON**: Separate config files for different environments (docker vs local) prevent accidental cross-environment pollution and make deployment safer.

### For Local Development

Create a `.env.local` file with local values.

Environment loading order is:
- `.env.local`
- `.env`

Later files override earlier ones, so values in `.env` take precedence over `.env.local`.

Example:

```ini
DATABASE_URL=postgresql+psycopg2://urlshortener:changeme@localhost:5432/urlshortener_db
REDIS_HOST=localhost
DEBUG=true
```

## API Summary

### Public Endpoints

- `GET /health`: Service and DB health check.
  - Returns `200` with `{"status": "db healthy"}` when DB is reachable.
  - Returns `503` with `{"status": "unhealthy", "detail": "Database connection error"}` when DB check fails.
- `POST /url`: Create a shortened URL.
  - Request: `{"target_url": "https://example.com"}`
  - Response: `{"url": "abc123", "admin_url": "Use Authorization header: Bearer <secret_key>", "target_url": "https://example.com", "is_active": true, "clicks": 0, "expires_at": null}`

### Protected Endpoints (Require Authorization Header)

All admin endpoints now use **Bearer token authentication** (secrets in Authorization header, not URL path).

**SECURITY CHANGE**: Moved secrets from URL path to Authorization header to prevent leakage via logs, browser history, and observability tools.

```bash
# Get admin info for a shortened URL
curl -H "Authorization: Bearer <secret_key>" http://localhost:8000/admin/info

# Delete a shortened URL
curl -X DELETE -H "Authorization: Bearer <secret_key>" http://localhost:8000/admin/delete
```

### Legacy URL Path Authentication (DEPRECATED)

❌ **No longer supported** (v1.1+): `GET /admin/{secret_key}`, `DELETE /admin/{secret_key}`

Use the Authorization header format above instead.

## Local Development

```cmd
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing

Testing uses `.env.test` values and runs migrations against `DATABASE_URL` from `.env.test`.
Ensure that test database is reachable before running tests.

```cmd
pytest -q
```