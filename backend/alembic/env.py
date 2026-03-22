"""
Alembic environment configuration for async migrations.

This env.py configures Alembic to:
1. Use the same DATABASE_URL from the app's Settings
2. Run migrations asynchronously via asyncpg
3. Import all ORM models so autogenerate can detect schema changes
"""

from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig

# Add app directory to path so migrations can import from app.core
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.core.database import Base

# ── Import all models so Alembic sees them for autogenerate ────────
from app.models import (  # noqa: F401
    AgentRun,
    Application,
    Candidate,
    Company,
    Job,
    User,
)

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except KeyError:
        # Fallback if logging config is missing in the INI (e.g. truncated file)
        import logging
        logging.basicConfig(level=logging.INFO)

# Metadata for autogenerate support
target_metadata = Base.metadata


def get_url() -> str:
    """Get the database URL from app settings.

    Converts async URL (asyncpg) to sync URL (psycopg2) if needed
    for offline migrations.
    """
    return settings.DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:  # type: ignore[no-untyped-def]
    """Execute migrations within a connection context."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using an async engine.

    Creates an async engine from the alembic config and runs
    migrations within a connection context.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (async)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
