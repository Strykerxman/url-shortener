# URL Shortener API

FastAPI service to create, redirect, and manage shortened URLs. Uses PostgreSQL for storage, Redis for caching, and Alembic for migrations. Runs locally or via Docker Compose.

## Quick Start

```cmd
docker compose up --build
```

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

Stop:

```cmd
docker compose down
```

## Configuration

Create a `.env` file (used by Compose) with minimal settings:

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

## API Summary

- `GET /health`: service and DB health.
- `POST /url`: body `{"target_url": "https://example.com"}` → returns `url` (short key) and `admin_url` (secret key).
- `GET /{key}`: redirect to target URL.
- `GET /admin/{secret_key}`: admin info and stats.
- `DELETE /admin/{secret_key}`: deactivate the short URL.

## Local Development

```cmd
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing

```cmd
pytest -q
```