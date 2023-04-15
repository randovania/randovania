from randovania.lib import migration_lib


def _migrate_v2(data: dict) -> dict:
    for item in data["items"].values():
        item["must_be_starting"] = item["hide_from_gui"] = item.pop("required")

    return data


def _migrate_v3(data: dict) -> dict:
    for item in data["items"].values():
        if "is_major" in item:
            is_major = item["is_major"]
        else:
            is_major = data["item_categories"][item["item_category"]]["is_major"]
        item["preferred_location_category"] = "major" if is_major else "minor"

    for item in data["ammo"].values():
        item["preferred_location_category"] = "minor"

    for item in data["item_categories"].values():
        item["hinted_as_major"] = item.pop("is_major")

    return data


_MIGRATIONS = [
    None,
    _migrate_v2,
    _migrate_v3,
]
CURRENT_VERSION = migration_lib.get_version(_MIGRATIONS)


def migrate_current(data: dict):
    return migration_lib.apply_migrations(data, _MIGRATIONS)
