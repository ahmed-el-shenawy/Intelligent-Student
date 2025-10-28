from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from alembic import context

# Import your Base model
from models.postgres.tables_schema.tables import Base
from helpers.db_connection import DATABASE_URL  # Only need the URL, not engine

# -------------------------------
# Alembic config setup
# -------------------------------
config = context.config

# Programmatically set DB URL
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Enable Alembic’s logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic to your model metadata
target_metadata = Base.metadata


# -------------------------------
# Migration functions
# -------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection):
    """Helper to run actual migrations."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' (async) mode."""
    connectable = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# -------------------------------
# Entry point
# -------------------------------
import asyncio

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
