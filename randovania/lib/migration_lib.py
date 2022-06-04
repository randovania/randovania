import copy
from typing import Callable


class UnsupportedVersion(ValueError):
    pass


def unsupported_migration(data: dict) -> dict:
    raise UnsupportedVersion("Support for migrating from this version has been removed")


def migrate_to_version(data: dict, version: int, migrations: dict[int, Callable[[dict], dict]],
                       *, copy_before_migrating: bool = False) -> dict:
    schema_version = data.get("schema_version", 1)

    while schema_version < version:
        if copy_before_migrating:
            data = copy.deepcopy(data)
            copy_before_migrating = False

        data = migrations[schema_version](data)
        schema_version += 1

    if schema_version > version:
        raise UnsupportedVersion(f"Requested a migration up to version {version}, but got version {schema_version}. "
                                 f"This file was created using a newer Randovania version.")

    data["schema_version"] = schema_version

    return data
