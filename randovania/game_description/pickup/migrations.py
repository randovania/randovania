import itertools

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


def _migrate_v4(data: dict) -> dict:
    data["pickup_categories"] = data.pop("item_categories")

    data["standard_pickups"] = data.pop("items")
    for pickup in data["standard_pickups"].values():
        pickup["pickup_category"] = pickup.pop("item_category")
        if "original_index" in pickup:
            pickup["original_location"] = pickup.pop("original_index")
        if "warning" in pickup:
            pickup["description"] = pickup.pop("warning")

    data["ammo_pickups"] = data.pop("ammo")
    for pickup in data["ammo_pickups"].values():
        if "is_major" in pickup:
            pickup.pop("is_major")

    data["default_pickups"] = data.pop("default_items")

    return data


def _migrate_v5(data: dict) -> dict:
    is_prime2 = "Dark Visor" in data["standard_pickups"]
    is_prime3 = "Nova Beam" in data["standard_pickups"]

    if is_prime2 or is_prime3:
        percentage = "Percent" if is_prime2 else "ItemPercentage"

        for pickup in itertools.chain(data["standard_pickups"].values(), data["ammo_pickups"].values()):
            pickup["additional_resources"] = {
                percentage: 1
            }

    return data


_MIGRATIONS = [
    None,
    _migrate_v2,
    _migrate_v3,
    _migrate_v4,
    _migrate_v5,
]
CURRENT_VERSION = migration_lib.get_version(_MIGRATIONS)


def migrate_current(data: dict):
    return migration_lib.apply_migrations(data, _MIGRATIONS)
