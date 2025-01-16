from __future__ import annotations

import itertools

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import migration_data
from randovania.lib import migration_lib


def _migrate_v2(pickup_data: dict, game: RandovaniaGame) -> None:
    for item in pickup_data["items"].values():
        item["must_be_starting"] = item["hide_from_gui"] = item.pop("required")


def _migrate_v3(pickup_data: dict, game: RandovaniaGame) -> None:
    for item in pickup_data["items"].values():
        if "is_major" in item:
            is_major = item["is_major"]
        else:
            is_major = pickup_data["item_categories"][item["item_category"]]["is_major"]
        item["preferred_location_category"] = "major" if is_major else "minor"

    for item in pickup_data["ammo"].values():
        item["preferred_location_category"] = "minor"

    for item in pickup_data["item_categories"].values():
        item["hinted_as_major"] = item.pop("is_major")


def _migrate_v4(pickup_data: dict, game: RandovaniaGame) -> None:
    pickup_data["pickup_categories"] = pickup_data.pop("item_categories")

    pickup_data["standard_pickups"] = pickup_data.pop("items")
    for pickup in pickup_data["standard_pickups"].values():
        pickup["pickup_category"] = pickup.pop("item_category")
        if "original_index" in pickup:
            pickup["original_location"] = pickup.pop("original_index")
        if "warning" in pickup:
            pickup["description"] = pickup.pop("warning")

    pickup_data["ammo_pickups"] = pickup_data.pop("ammo")
    for pickup in pickup_data["ammo_pickups"].values():
        if "is_major" in pickup:
            pickup.pop("is_major")

    pickup_data["default_pickups"] = pickup_data.pop("default_items")


def _migrate_v5(pickup_data: dict, game: RandovaniaGame) -> None:
    if game in {RandovaniaGame.METROID_PRIME_ECHOES, RandovaniaGame.METROID_PRIME_CORRUPTION}:
        percentage = "Percent" if game == RandovaniaGame.METROID_PRIME_ECHOES else "ItemPercentage"

        for pickup in itertools.chain(pickup_data["standard_pickups"].values(), pickup_data["ammo_pickups"].values()):
            pickup["additional_resources"] = {percentage: 1}


def _migrate_v6(pickup_data: dict, game: RandovaniaGame) -> None:
    for pickup in itertools.chain(pickup_data["standard_pickups"].values(), pickup_data["ammo_pickups"].values()):
        pickup["offworld_models"] = {}

    pickup_data["default_offworld_model"] = ""


def _migrate_v7(pickup_data: dict, game: RandovaniaGame) -> None:
    for pickup in pickup_data["standard_pickups"].values():
        default_shuffled_count = pickup.pop("default_shuffled_count")
        default_starting_count = pickup.pop("default_starting_count")

        if default_starting_count > 0:
            case = "starting_item"
        elif default_shuffled_count > 0:
            case = "shuffled"
        else:
            case = "missing"

        pickup["expected_case_for_describer"] = case

        if default_shuffled_count > 0 and default_shuffled_count != len(pickup["progression"]):
            pickup["custom_count_for_shuffled_case"] = default_shuffled_count

        if default_starting_count > 1:
            pickup["custom_count_for_starting_case"] = default_starting_count


def _migrate_v8(pickup_data: dict, game: RandovaniaGame) -> None:
    for pickup in pickup_data["standard_pickups"].values():
        if "original_location" in pickup:
            pickup["original_locations"] = [pickup.pop("original_location")]


def _migrate_v9(pickup_data: dict, game: RandovaniaGame) -> None:
    generated = migration_data.get_generated_pickups(game)
    pickup_data["pickup_categories"].update(generated["categories"])
    pickup_data["generated_pickups"] = generated["pickups"]


_MIGRATIONS = [
    None,
    _migrate_v2,
    _migrate_v3,
    _migrate_v4,
    _migrate_v5,
    _migrate_v6,
    _migrate_v7,
    _migrate_v8,
    _migrate_v9,
]
CURRENT_VERSION = migration_lib.get_version(_MIGRATIONS)


def migrate_current(data: dict, game: RandovaniaGame) -> dict:
    return migration_lib.apply_migrations_with_game(data, _MIGRATIONS, game)
