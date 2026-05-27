from __future__ import annotations

import pytest

from randovania.lib import migration_lib


def test_migrate_to_version_missing_migration() -> None:
    data = {
        "schema_version": 1,
    }

    with pytest.raises(
        migration_lib.UnsupportedVersion,
        match=(
            "Requested a migration from something 1, but it's no longer supported. "
            "You can try using an older Randovania version."
        ),
    ):
        migration_lib.apply_migrations(data, [None], version_name="something")


def test_migrate_to_version_data_too_new() -> None:
    data = {
        "schema_version": 3,
    }

    with pytest.raises(
        migration_lib.UnsupportedVersion,
        match=(
            "Found version 3, but only up to 2 is supported. This file was created using a newer Randovania version."
        ),
    ):
        migration_lib.apply_migrations(data, [None])
