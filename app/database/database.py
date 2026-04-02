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
from app.core import logging

# Global variables for engine and session factory.
# Initialized as None to allow for late-binding (Inversion of Control).
# This prevents early DB connection attempts at import time.
engine = None
SessionLocal = None


def init_db():
    """
    Initialize the database engine and session factory.
    Called during application startup to ensure configuration is ready.
    Allows for easier testing and prevents side effects during module imports.
    """
    global engine, SessionLocal
    settings = get_settings()
    
    if engine is None:
        engine = create_engine(settings.sqlalchemy_database_url, echo=settings.debug)
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        logging.logger.info("Database engine and SessionLocal factory initialized.")


# Declarative base class for all ORM models in the application.
# All SQLAlchemy model classes must inherit from this Base class.
class Base(DeclarativeBase):
    pass


def get_db():
    # Dependency for FastAPI endpoints: yields a scoped SQLAlchemy session.
    # Ensures connection cleanup after the request completes.
    if SessionLocal is None:
        init_db()
        
    db = SessionLocal()
    try:
        # Yield the session to the requesting endpoint for use within the request context.
        yield db
    finally:
        # Ensure the session is closed after the request completes,
        # releasing database connections and cleaning up resources.
        db.close()
