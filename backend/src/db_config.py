"""
DATABASE CONFIGURATION
======================
Supports both SQLite (dev) and PostgreSQL/Supabase (prod).

Environment variable DATABASE_URL determines which to use:
- SQLite: sqlite:///./hackfusion.db
- Supabase: postgresql://user:pass@host:port/db
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from src.models import Base

# ------------------------------------------------------------------
# DATABASE URL
# ------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hackfusion.db")

# SQLite-specific settings
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# ------------------------------------------------------------------
# ENGINE & SESSION
# ------------------------------------------------------------------
def get_engine():
    return create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        echo=False,  # Set to True for SQL debugging
    )

engine = get_engine()

def get_session_local():
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

SessionLocal = get_session_local()


# ------------------------------------------------------------------
# DATABASE INITIALIZATION
# ------------------------------------------------------------------
def init_db():
    """
    Create all tables.
    Call this on application startup.
    """
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized: {DATABASE_URL}")


def drop_db():
    """
    Drop all tables.
    Use with caution! Only for development.
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All tables dropped")


# ------------------------------------------------------------------
# SESSION MANAGEMENT
# ------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes.
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Medicine).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for non-FastAPI usage.
    
    Usage:
        with get_db_context() as db:
            medicines = db.query(Medicine).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------------
# MIGRATION HELPERS
# ------------------------------------------------------------------
def is_sqlite() -> bool:
    """Check if using SQLite."""
    return DATABASE_URL.startswith("sqlite")


def is_postgres() -> bool:
    """Check if using PostgreSQL/Supabase."""
    return DATABASE_URL.startswith("postgresql")


def get_db_type() -> str:
    """Get database type string."""
    if is_sqlite():
        return "SQLite"
    elif is_postgres():
        return "PostgreSQL"
    else:
        return "Unknown"