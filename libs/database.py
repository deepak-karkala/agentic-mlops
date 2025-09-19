"""
Database utilities for the Agentic MLOps platform.

This module provides database connection management and utilities
that are shared across the application, including SQLAlchemy models
and LangGraph checkpointing.
"""

import os
import logging
from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

# Import all available checkpointers with graceful fallbacks
try:
    from langgraph.checkpoint.postgres import PostgresSaver

    POSTGRES_CHECKPOINTER_AVAILABLE = True
except ImportError:
    PostgresSaver = None
    POSTGRES_CHECKPOINTER_AVAILABLE = False

try:
    from langgraph.checkpoint.sqlite import SqliteSaver

    SQLITE_CHECKPOINTER_AVAILABLE = True
except ImportError:
    SqliteSaver = None
    SQLITE_CHECKPOINTER_AVAILABLE = False

try:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    ASYNC_SQLITE_CHECKPOINTER_AVAILABLE = True
except ImportError:
    AsyncSqliteSaver = None
    ASYNC_SQLITE_CHECKPOINTER_AVAILABLE = False

try:
    from langgraph.checkpoint.memory import MemorySaver

    MEMORY_CHECKPOINTER_AVAILABLE = True
except ImportError:
    MemorySaver = None
    MEMORY_CHECKPOINTER_AVAILABLE = False


def get_database_url() -> str:
    """Get the database URL from environment variables."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Default to SQLite for local development and testing
        database_url = "sqlite:///./test.db"
    return database_url


def create_database_engine(database_url: Optional[str] = None) -> Engine:
    """Create a SQLAlchemy engine for database connections."""
    if database_url is None:
        database_url = get_database_url()

    # Configure engine options based on database type
    if database_url.startswith("sqlite"):
        # SQLite-specific configuration
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )

        # Automatically create tables for SQLite development databases to
        # prevent missing-table errors when migrations haven't been run.
        from libs.models import create_all_tables

        create_all_tables(engine)
    else:
        # PostgreSQL configuration
        engine = create_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )

    return engine


def create_session_maker(engine: Engine) -> sessionmaker[Session]:
    """Create a sessionmaker for database sessions."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_appropriate_checkpointer():
    """
    Create the most appropriate checkpointer based on the current environment.

    Selection logic:
    1. PostgreSQL environment → PostgresSaver (production)
    2. SQLite environment → SqliteSaver (development)
    3. Fallback → MemorySaver (testing/fallback)

    This ensures dev/prod parity while maintaining flexibility.

    Returns:
        Appropriate checkpointer instance or None if none available
    """
    database_url = get_database_url()

    # Production: Use PostgreSQL checkpointer
    logger = logging.getLogger(__name__)

    if database_url.startswith("postgresql://") and POSTGRES_CHECKPOINTER_AVAILABLE:
        try:
            checkpointer = PostgresSaver.from_conn_string(database_url)
            checkpointer.setup()
            logger.info("Using PostgresSaver for production persistence")
            return checkpointer
        except Exception as e:
            logger.warning(
                "PostgresSaver initialization failed", extra={"error": str(e)}
            )
            # Fall through to next option

    # Development: Use SQLite checkpointer
    if database_url.startswith("sqlite://") and SQLITE_CHECKPOINTER_AVAILABLE:
        try:
            # Convert SQLite URL to file path for SqliteSaver
            if database_url == "sqlite:///:memory:":
                # In-memory SQLite - use memory checkpointer instead
                if MEMORY_CHECKPOINTER_AVAILABLE:
                    checkpointer = MemorySaver()
                    logger.info("Using MemorySaver for in-memory testing")
                    return checkpointer
            else:
                # File-based SQLite
                sqlite_path = database_url.replace("sqlite:///", "").replace(
                    "sqlite://", ""
                )
                if sqlite_path.startswith("./"):
                    sqlite_path = sqlite_path[2:]  # Remove "./" prefix

                # Create checkpointer database file
                checkpoint_path = f"{sqlite_path}.checkpoints"
                # SqliteSaver needs an actual SQLite connection
                import sqlite3

                conn = sqlite3.connect(checkpoint_path, check_same_thread=False)
                checkpointer = SqliteSaver(conn)
                logger.info(
                    "Using SqliteSaver for development persistence",
                    extra={"path": checkpoint_path},
                )
                return checkpointer
        except Exception as e:
            logger.warning("SqliteSaver initialization failed", extra={"error": str(e)})
            # Fall through to memory checkpointer

    # Fallback: Use in-memory checkpointer
    if MEMORY_CHECKPOINTER_AVAILABLE:
        checkpointer = MemorySaver()
        logger.info("Using MemorySaver as fallback (no persistence)")
        return checkpointer

    # No checkpointer available
    logger.error("No checkpointer available - running without persistence")
    return None


def create_postgres_checkpointer():
    """
    Create a PostgresSaver for LangGraph checkpointing.

    DEPRECATED: Use create_appropriate_checkpointer() instead for better
    environment handling and dev/prod parity.
    """
    if not POSTGRES_CHECKPOINTER_AVAILABLE or PostgresSaver is None:
        raise ValueError(
            "PostgresSaver is not available. Please ensure psycopg[binary] "
            "or psycopg[c] is installed for PostgreSQL checkpointing."
        )

    database_url = get_database_url()

    if database_url.startswith("sqlite"):
        raise ValueError(
            "PostgresSaver requires PostgreSQL. Use create_appropriate_checkpointer() "
            "for automatic environment detection."
        )

    checkpointer = PostgresSaver.from_conn_string(database_url)
    checkpointer.setup()
    return checkpointer


async def create_async_checkpointer():
    """
    Create an async checkpointer for use with async LangGraph operations.

    Returns:
        Async checkpointer instance suitable for async operations
    """
    database_url = get_database_url()
    logger = logging.getLogger(__name__)

    # Development: Use AsyncSqliteSaver for async operations
    if database_url.startswith("sqlite://") and ASYNC_SQLITE_CHECKPOINTER_AVAILABLE:
        try:
            # Convert SQLite URL to file path for AsyncSqliteSaver
            if database_url == "sqlite:///:memory:":
                # In-memory SQLite - use memory checkpointer instead
                if MEMORY_CHECKPOINTER_AVAILABLE:
                    checkpointer = MemorySaver()
                    logger.info("Using MemorySaver for in-memory async operations")
                    return checkpointer
            else:
                # File-based SQLite
                sqlite_path = database_url.replace("sqlite:///", "").replace(
                    "sqlite://", ""
                )
                if sqlite_path.startswith("./"):
                    sqlite_path = sqlite_path[2:]  # Remove "./" prefix

                # Create async checkpointer database file
                checkpoint_path = f"{sqlite_path}.async_checkpoints"
                checkpointer = AsyncSqliteSaver.from_conn_string(f"aiosqlite:///{checkpoint_path}")
                await checkpointer.setup()
                logger.info(
                    "Using AsyncSqliteSaver for async development persistence",
                    extra={"path": checkpoint_path},
                )
                return checkpointer
        except Exception as e:
            logger.warning("AsyncSqliteSaver initialization failed", extra={"error": str(e)})
            # Fall through to memory checkpointer

    # Fallback: Use in-memory checkpointer
    if MEMORY_CHECKPOINTER_AVAILABLE:
        checkpointer = MemorySaver()
        logger.info("Using MemorySaver as async fallback (no persistence)")
        return checkpointer

    # No async checkpointer available
    logger.error("No async checkpointer available - running without persistence")
    return None


def create_postgres_checkpointer_safe():
    """
    Create a checkpointer with error handling.

    DEPRECATED: Use create_appropriate_checkpointer() instead for better
    environment handling and automatic checkpointer selection.
    """
    return create_appropriate_checkpointer()
