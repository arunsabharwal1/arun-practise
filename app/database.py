"""
Database configuration and session management.
Uses SQLAlchemy async engine with SQLite (swappable via DATABASE_URL in .env).
"""

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./projectdb.sqlite")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DEBUG", "False").lower() == "true",
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def init_db():
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency: yields a DB session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
