"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import make_url
from typing import Generator

from .config import settings

# Determine connection arguments based on database backend
db_url = make_url(str(settings.DATABASE_URL))

connect_args = {}
if db_url.drivername.startswith("sqlite"):
    # SQLite does not support client_encoding/connect_timeout and needs relaxed threading
    connect_args["check_same_thread"] = False
else:
    connect_args = {
        "client_encoding": "utf8",
        "connect_timeout": 10,
    }

# Create database engine
engine = create_engine(
    str(settings.DATABASE_URL),
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG,
    connect_args=connect_args,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for database models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)


def get_session_for_thread() -> Session:
    """
    Create a new database session for use in threads.
    
    Returns:
        New database session (caller must close it)
    """
    return SessionLocal()