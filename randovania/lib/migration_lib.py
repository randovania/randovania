from typing import Callable


def migrate_to_version(data: dict, version: int, migrations: dict[int, Callable[[dict], dict]]) -> dict:
    schema_version = data.get("schema_version", 1)

    while schema_version < version:
        data = migrations[schema_version](data)
        schema_version += 1

    if schema_version > version:
        raise ValueError(f"Requested a migration up to version {version}, but got version {schema_version}.")

    data["schema_version"] = schema_version

    return data
