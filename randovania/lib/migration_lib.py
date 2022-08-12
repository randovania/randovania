import copy
from typing import Callable


class UnsupportedVersion(ValueError):
    pass


Migrations = list[Callable[[dict], dict] | None]


def apply_migrations(data: dict, migrations: Migrations, *, copy_before_migrating: bool = False) -> dict:
    schema_version = data.get("schema_version", 1)
    version = get_version(migrations)

    while schema_version < version:
        if copy_before_migrating:
            data = copy.deepcopy(data)
            copy_before_migrating = False

        migration = migrations[schema_version - 1]
        if migration is None:
            raise UnsupportedVersion(
                f"Requested a migration from version {schema_version}, but it's no longer supported. "
                f"You can try using an older Randovania version."
            )

        data = migration(data)
        schema_version += 1

    if schema_version > version:
        raise UnsupportedVersion(f"Found version {schema_version}, but only {version} is known. "
                                 f"This file was created using a newer Randovania version.")

    data["schema_version"] = schema_version

    return data


def get_version(migrations: Migrations) -> int:
    return len(migrations) + 1
