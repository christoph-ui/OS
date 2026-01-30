"""
Console Backend Database Connection

Standalone database connection for Console backend,
independent of Platform (to avoid config issues).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://0711:0711_dev_password@localhost:4005/0711_control"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,  # Use static pool for console backend
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, let the caller handle it


def get_db_dependency():
    """FastAPI dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
