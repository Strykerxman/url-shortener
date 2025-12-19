# URL Shortener API

FastAPI application that persists shortened URLs in PostgreSQL, caches lookups in Redis, and manages schema changes with Alembic.

## Highlights

- FastAPI + Uvicorn with Pydantic validation
- SQLAlchemy ORM targeting PostgreSQL 14+
- Redis cache layer with a 24-hour TTL per entry
- Docker Compose topology (API, Postgres, Redis) with health checks

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

| Scenario                   | Requirements                             |
| -------------------------- | ---------------------------------------- |
| Docker (recommended)       | Docker Desktop 4+, Docker Compose v2      |
| Local development          | Python 3.10+, pip, PostgreSQL 14+, Redis 7+ |

## 1. Configure Environment Variables

1. Copy the template and edit values as needed:

```cmd
copy .env.example .env
```

2. Reference values from `.env.example`:

| Variable       | Purpose                                         | Template default                         | Docker override                          |
| -------------- | ----------------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| `DATABASE_URL` | SQLAlchemy connection string                    | `postgresql://...@db:5432/...`           | Use `compose.yaml` env substitution      |
| `DATABASE_USER`/`PW`/`NAME` | Individual DB credentials           | `urlshortener` / `changeme...` / `urlshortener_db` | Keep in sync with Postgres service |
| `BASE_URL`     | Base used to build public/admin links           | `http://127.0.0.1:8000`                  | Update to external hostname if exposed   |
| `REDIS_HOST`   | Redis hostname                                  | `localhost`                              | Override to `redis` inside Compose       |
| `REDIS_PORT`   | Redis port                                      | `6379`                                   | `6379`                                   |

Set `REDIS_HOST=redis` for containers via the `server.environment` block in `compose.yaml` or by adjusting `.env` before composing. Update `BASE_URL` whenever the API is published under a different domain.

## 2. Run with Docker Compose (Recommended)

```cmd
docker compose up --build
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Persistent volumes: `postgres_data`, `redis_data`

Gracefully stop everything with:

```cmd
docker compose down
```

### Compose Notes

- `alembic upgrade head` runs automatically before Uvicorn starts.
- Health checks guard startup; inspect `docker compose logs server` if the service restarts.

## 3. Local Development Workflow

```cmd
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Provision PostgreSQL and Redis instances that match the values in `.env` before running the application locally.

## Database Migrations

Generate a migration after changing models:

```cmd
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

The compose entrypoint already runs `alembic upgrade head`, so schema changes apply automatically in containers once a migration exists.

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

- **Redis connection errors**: confirm `REDIS_HOST` matches the host reachable from the running process (`redis` inside Compose, `localhost` when developing locally). Use `docker compose exec server redis-cli -h redis ping` to validate connectivity.
- **Database auth failures**: verify both `DATABASE_URL` and individual `DATABASE_*` vars are in sync; Alembic uses whichever is set.
- **Stale migrations**: rerun `alembic upgrade head` after generating new revisions and restart the API.