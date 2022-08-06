import pytest

from randovania.lib import migration_lib


def test_migrate_to_version_missing_migration():
    data = {
        "schema_version": 1,
    }

    with pytest.raises(migration_lib.UnsupportedVersion,
                       match=("Requested a migration from version 1, but it's no longer supported. "
                              f"You can try using an older Randovania version.")):
        migration_lib.migrate_to_version(data, 2, {})


def test_migrate_to_version_data_too_new():
    data = {
        "schema_version": 3,
    }

    with pytest.raises(migration_lib.UnsupportedVersion,
                       match=("Requested a migration up to version 2, but got version 3. "
                              "This file was created using a newer Randovania version.")):
        migration_lib.migrate_to_version(data, 2, {})
