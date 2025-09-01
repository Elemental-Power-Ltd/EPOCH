"""Database migration utilities."""

from enum import Enum, auto
from pathlib import Path


class MigrationDirection(Enum):
    """Whether to look for up for down migrations."""

    Up = auto()
    Down = auto()


def extract_number_from_migration(fname: Path) -> int:
    """Extract the initial number from a migration file."""
    return int(fname.stem.split("_", maxsplit=1)[0])


def get_migration_files(
    directory: Path = Path("migrations"),
    start: int | float = -float("inf"),
    end: int | float = float("inf"),
    direction: MigrationDirection = MigrationDirection.Up,
) -> list[Path]:
    """
    Get all the migration .sql files in ascending order.

    A file must be named in the form 123456_{file_name}.up.sql, where the initial number
    represents an ordering.
    The start and end parameters represent the largest and smallest ID'd migrations you want to apply,
    e.g. start = 2 and end = 5 would select migrations 2, 3, 4.
    The end parameter is not included.

    Parameters
    ----------
    directory
        A directory containing migration .sql files

    start
        Integer representing the first migration to select, id >= start. By default selects all.
    end
        Integer representing the one-past-the-end migration, id < end. By default selects all.

    Returns
    -------
    list[Path]
        Ordered list of up migrations.
    """
    if direction == MigrationDirection.Up:
        glob_suffix = "*.up.sql"
    else:
        glob_suffix = "*.down.sql"
    all_files = [item.absolute() for item in directory.glob(glob_suffix)]

    return sorted(
        filter(lambda f: start <= extract_number_from_migration(f) < end, all_files), key=extract_number_from_migration
    )
