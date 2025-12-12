# -------------------------------------------------------
# Database Configuration and Session Management
# -------------------------------------------------------
# This module handles all SQLAlchemy configuration, database engine initialization,
# and session factory setup. It provides the get_db() dependency injection function
# used by FastAPI endpoints to obtain database sessions.
# The Base declarative class is the foundation for all ORM models in the application.
# -------------------------------------------------------

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()  # Load application settings from environment configuration

# Initialize the SQLAlchemy engine with the database URL from settings.
# echo=settings.debug enables SQL statement logging when in debug mode.
engine = create_engine(settings.database_url, echo=settings.debug)

# Create a sessionmaker factory bound to the engine.
# autoflush=False prevents automatic flushing of pending changes.
# autocommit=False requires explicit commits for data persistence.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Declarative base class for all ORM models in the application.
# All SQLAlchemy model classes must inherit from this Base class.
class Base(DeclarativeBase):
    pass

def get_db():
    # Create a new database session for the request.
    db = SessionLocal()
    try:
        # Yield the session to the requesting endpoint for use within the request context.
        yield db
    finally:
        # Ensure the session is closed after the request completes,
        # releasing database connections and cleaning up resources.
        db.close()