from randovania.lib import migration_lib

CURRENT_VERSION = 3


def _migrate_v2(data: dict) -> dict:
    for item in data["items"].values():
        item["must_be_starting"] = item["hide_from_gui"] = item.pop("required")

    return data


_MIGRATIONS = {
    1: migration_lib.unsupported_migration,
    2: _migrate_v2,
}


def migrate_current(data: dict):
    return migration_lib.migrate_to_version(data, CURRENT_VERSION, _MIGRATIONS)
