"""Test the SQL database migration files."""

from pathlib import Path

import asyncpg
import pytest
from app.internal.utils.database_utils import MigrationDirection, extract_number_from_migration, get_migration_files
from testing.postgresql import Database, PostgresqlFactory  # type: ignore

db_factory = PostgresqlFactory(cache_initialized_db=True)


@pytest.fixture
def db() -> Database:
    """Get an empty DB to test with."""
    return db_factory()


@pytest.fixture
def up_migrations() -> list[Path]:
    """List all the up migrations in decreasing order."""
    return get_migration_files(end=999, direction=MigrationDirection.Up)


@pytest.fixture
def down_migrations() -> list[Path]:
    """List all the down migrations in decreasing order."""
    return list(reversed(get_migration_files(end=999, direction=MigrationDirection.Down)))


class TestMigrations:
    """Test the migrations from the python side, going up and down."""

    def test_all_migrations_there(self, up_migrations: list[Path], down_migrations: list[Path]) -> None:
        """Test that we have all the migrations we expect."""
        # Migration #1 is the initial state and doesn't have a corresponding down
        assert len(up_migrations) == len(down_migrations) + 1

        assert set(map(extract_number_from_migration, up_migrations)) == {
            1,
            *map(extract_number_from_migration, down_migrations),
        }

    @pytest.mark.asyncio
    async def test_all_migrations(self, db: Database, up_migrations: list[Path], down_migrations: list[Path]) -> None:
        """Test that we can migrate up and down."""
        conn = await asyncpg.connect(db.url())
        for fname in up_migrations:
            response = await conn.execute(fname.read_text())
            assert response in {"INSERT 0 1", "COMMIT"}, response

        for fname in down_migrations:
            response = await conn.execute(fname.read_text())
            assert response in {"INSERT 0 1", "COMMIT"}, response
