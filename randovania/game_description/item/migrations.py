from randovania.lib import migration_lib


def _migrate_v2(data: dict) -> dict:
    for item in data["items"].values():
        item["must_be_starting"] = item["hide_from_gui"] = item.pop("required")

    return data


_MIGRATIONS = [
    None,
    _migrate_v2,
]
CURRENT_VERSION = migration_lib.get_version(_MIGRATIONS)


def migrate_current(data: dict):
    return migration_lib.apply_migrations(data, _MIGRATIONS)
