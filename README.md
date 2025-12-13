# url-shortener

A simple URL shortener API built with **FastAPI**, **SQLAlchemy**, **PostgreSQL**, and **Alembic**.

## Requirements

### Option 1: Docker (Recommended)
- Docker Desktop
- Docker Compose

### Option 2: Local Development
- Python 3.10+
- PostgreSQL 14+ (running locally)
- pip

## Setup

### Option 1: Using Docker (Recommended)

#### 1) Create `.env` file from template

````bash
copy .env.example .env
````

Edit `.env` with your desired database credentials (or use defaults).

#### 2) Build and start containers

````bash
docker-compose up --build
````

The application will be accessible at `http://localhost:8000`. The FastAPI documentation can be found at `http://localhost:8000/docs`.

#### 3) Stop containers

````bash
docker-compose down
````

---

### Option 2: Local Development (Windows)

#### 1) Create and activate a virtual environment

````bash
py -m venv .venv
.\.venv\Scripts\activate
````

#### 2) Install dependencies

````bash
pip install -r requirements.txt
````

#### 3) Configure the database

- Create a new PostgreSQL database locally
- Copy `.env.example` to `.env`
- Update `DATABASE_URL` in `.env` with your local database connection:
  ```
  DATABASE_URL=postgresql://username:password@localhost:5432/database_name
  ```

#### 4) Run migrations

````bash
alembic upgrade head
````

#### 5) Start the application

````bash
uvicorn app.main:app --host 0.0.0.0
````

The application will be accessible at `http://localhost:8000`. The FastAPI documentation can be found at `http://localhost:8000/docs`.

---

## Testing Endpoints

Once the application is running, test it with:

```bash
# Health check
curl http://localhost:8000/health

# API documentation (open in browser)
http://localhost:8000/docs
```

## Notes

- For Docker, the database is created automatically with credentials from `.env`.
- For local development, ensure PostgreSQL is running and the database exists before starting the app.