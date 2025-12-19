# URL Shortener API

FastAPI service that persists shortened URLs in PostgreSQL, caches lookups in Redis, and tracks schema changes with Alembic.

## Highlights

- FastAPI + Uvicorn with Pydantic validation
- SQLAlchemy ORM targeting PostgreSQL 14+
- Redis cache layer with 24-hour TTL per entry
- Docker Compose stack (API, Postgres, Redis) with health checks

## Project Layout

```
app/
  api/v1/...        # FastAPI routers
  core/...          # settings, logging, helpers
  database/...      # SQLAlchemy session, CRUD, Redis
  models/, schemas/ # SQLAlchemy + Pydantic definitions
alembic/            # migration environment and versions
compose.yaml        # docker compose stack
```

## Prerequisites

| Scenario          | Requirements                               |
| ----------------- | ------------------------------------------ |
| Docker            | Docker Desktop 4+, Docker Compose v2       |
| Local development | Python 3.10+, pip, PostgreSQL 14+, Redis 7+|

## Configure Environment Variables

Copy the template and edit values as needed:

```cmd
copy .env.example .env
```

| Variable                  | Purpose                                    | Template default                          | Notes for Docker                  |
| ------------------------- | ------------------------------------------ | ----------------------------------------- | --------------------------------- |
| `DATABASE_URL`            | SQLAlchemy connection string               | `postgresql://...@db:5432/...`            | Leave as `db` host in containers  |
| `DATABASE_USER` / `PW` / `NAME` | Individual DB credentials             | `urlshortener` / `changeme...` / `urlshortener_db` | Keep consistent with Postgres service |
| `BASE_URL`                | Base used to build public/admin links      | `http://127.0.0.1:8000`                   | Change to your public hostname if exposed |
| `REDIS_HOST`              | Redis hostname                             | `localhost`                               | Override to `redis` inside Compose |
| `REDIS_PORT`              | Redis port                                 | `6379`                                    | `6379`                             |

## Run with Docker Compose (recommended)

```cmd
docker compose up --build
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Persistent volumes: `postgres_data`, `redis_data`

Stop containers:

```cmd
docker compose down
```

Notes: migrations run automatically (`alembic upgrade head`) before Uvicorn starts. Check `docker compose logs server` if the service restarts.

## Local Development

```cmd
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Ensure PostgreSQL and Redis instances match the values in `.env` before running locally.

## Database Migrations

```cmd
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

The compose entrypoint runs `alembic upgrade head`, so existing migrations apply automatically in containers.

## API Quickstart

```cmd
# Health check
curl http://localhost:8000/health

# Create a shortened URL
curl -X POST http://localhost:8000/url \
     -H "Content-Type: application/json" \
     -d "{\"target_url\":\"https://example.com\"}"

# Follow the short link (replace <key> with response.url)
curl -i http://localhost:8000/<key>

# Administration info (replace <secret>)
curl http://localhost:8000/admin/<secret>

# Delete/disable a link
curl -X DELETE http://localhost:8000/admin/<secret>
```

Responses include `url` (public short key) and `admin_url` (secret key).

## Troubleshooting

- Redis: ensure `REDIS_HOST` is reachable (`redis` in Compose, `localhost` locally). Validate with `docker compose exec server redis-cli -h redis ping`.
- Database: keep `DATABASE_URL` and `DATABASE_*` in sync; Alembic uses whichever is set.
- Migrations: rerun `alembic upgrade head` after generating new revisions and restart the API.