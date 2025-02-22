from __future__ import annotations

import itertools

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import migration_data
from randovania.lib import migration_lib


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


def _migrate_v10(pickup_data: dict, game: RandovaniaGame) -> None:
    categories = pickup_data["pickup_categories"]

    no_global_categories = {
        RandovaniaGame.BLANK,
        RandovaniaGame.CAVE_STORY,
        RandovaniaGame.FACTORIO,
    }

    if game not in no_global_categories:
        categories.update(
            {
                "major": {"long_name": "Major Item", "hint_details": ["a ", "major item"]},
                "expansion": {"long_name": "Expansion", "hint_details": ["an ", "expansion"]},
            }
        )

    def add_generic_key_category() -> None:
        categories["key"] = {"long_name": "Key", "hint_details": ["a ", "key"]}

    def update_broad_category(category: str) -> None:
        categories[category]["is_broad_category"] = True

    for pickup in pickup_data["standard_pickups"].values():
        assert isinstance(pickup, dict)

        update_broad_category(pickup["broad_category"])

        category = categories[pickup["pickup_category"]]
        pickup["gui_category"] = pickup["pickup_category"]
        pickup["show_in_credits_spoiler"] = category["hinted_as_major"]

        hint_features = set()
        hint_features.add(pickup.pop("pickup_category"))
        hint_features.add(pickup.pop("broad_category"))
        if game not in no_global_categories:
            hint_features.add("major")
        pickup["hint_features"] = sorted(hint_features)

    for pickup in pickup_data["generated_pickups"].values():
        assert isinstance(pickup, dict)

        pickup["show_in_credits_spoiler"] = True

        hint_features = set()

        if "pickup_category" in pickup:
            hint_features.add(pickup["pickup_category"])
        else:
            add_generic_key_category()
            pickup["pickup_category"] = "key"
        pickup["gui_category"] = pickup.pop("pickup_category")

        if "broad_category" in pickup:
            update_broad_category(pickup["broad_category"])
            hint_features.add(pickup.pop("broad_category"))
        else:
            add_generic_key_category()
            update_broad_category("key")
            hint_features.add("key")

        pickup["hint_features"] = sorted(hint_features)

    broad_to_category = {
        "beam_related": "beam",
        "morph_ball_related": "morph_ball",
        "missile_related": "missile",
    }

    for pickup in pickup_data["ammo_pickups"].values():
        assert isinstance(pickup, dict)

        update_broad_category(pickup["broad_category"])

        hint_features = set()
        hint_features.add(pickup["broad_category"])
        if game not in no_global_categories:
            hint_features.add("expansion")
        pickup["hint_features"] = sorted(hint_features)

        pickup["gui_category"] = broad_to_category.get(pickup["broad_category"], pickup["broad_category"])
        pickup.pop("broad_category", None)

    for category in categories.values():
        category.pop("hinted_as_major", None)
        category.pop("is_key", None)


def _migrate_v11(pickup_data: dict, game: RandovaniaGame) -> None:
    for name, category in pickup_data["pickup_categories"].items():
        if not category["long_name"]:
            category["long_name"] = name

    for pickup in itertools.chain(
        pickup_data["standard_pickups"].values(),
        pickup_data["generated_pickups"].values(),
        pickup_data["ammo_pickups"].values(),
    ):
        if isinstance((offset := pickup.get("probability_offset", 0.0)), int):
            pickup["probability_offset"] = float(offset)

        if isinstance((mult := pickup.get("probability_multiplier", 1.0)), int):
            pickup["probability_multiplier"] = float(mult)


def _migrate_v12(pickup_data: dict, game: RandovaniaGame) -> None:
    for category in pickup_data["pickup_categories"].values():
        category.pop("is_broad_category", None)


_MIGRATIONS = [
    None,
    None,
    _migrate_v3,
    _migrate_v4,
    _migrate_v5,
    _migrate_v6,
    _migrate_v7,
    _migrate_v8,
    _migrate_v9,  # add generated_pickups
    _migrate_v10,  # move category fields to pickup and add hint_features
    _migrate_v11,  # fix the fact that old migrations don't actually work on old DBs, lol
    _migrate_v12,  # remove is_broad_category
]
CURRENT_VERSION = migration_lib.get_version(_MIGRATIONS)


def migrate_current(data: dict, game: RandovaniaGame) -> dict:
    return migration_lib.apply_migrations_with_game(data, _MIGRATIONS, game)
