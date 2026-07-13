"""
Database utility module for PostgreSQL connection using SQLAlchemy.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Uses PostgreSQL on Render (DATABASE_URL env var), falls back to SQLite locally
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./device_logs.db")

if DATABASE_URL.startswith("sqlite"):
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Creates all tables defined in models.
    """
    from app.models.log_models import Log, ErrorSummary
    Base.metadata.create_all(bind=engine)


def get_db_path():
    return os.environ.get("DATABASE_URL", "")
