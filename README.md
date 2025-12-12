# url-shortener

A simple URL shortener API built with **FastAPI**, **SQLAlchemy**, **PostgreSQL**, and **Alembic**.

## Requirements

- Python 3.10+ (recommended)
- PostgreSQL 14+ (or any recent version)
- (Optional) `psql` CLI for troubleshooting

## Setup (Windows)

### 1) Create and activate a virtual environment

````bash
py -m venv .venv
.\.venv\Scripts\activate
````

### 2) Install the dependencies

````bash
pip install -r requirements.txt
````

### 3) Configure the database

- Create a new PostgreSQL database for the URL shortener.
- Update the `DATABASE_URL` in your `.env` file with the connection string to your database.

### 4) Run the migrations

````bash
alembic upgrade head
````

### 5) Start the application

````bash
uvicorn app.main:app
````

The application will be accessible at `http://127.0.0.1:8000`. The FastAPI documentation can be found at `http://127.0.0.1:8000/docs`.