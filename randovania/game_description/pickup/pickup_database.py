from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from randovania.game_description.hint_features import HintFeature
from randovania.game_description.pickup import pickup_migration
from randovania.game_description.pickup.pickup_definition.ammo_pickup import AmmoPickupDefinition
from randovania.game_description.pickup.pickup_definition.standard_pickup import StandardPickupDefinition

if TYPE_CHECKING:
    from randovania.game.game_enum import RandovaniaGame


@dataclass(frozen=True)
class PickupDatabase:
    pickup_categories: dict[str, HintFeature]
    generated_pickups: dict[str, StandardPickupDefinition]
    standard_pickups: dict[str, StandardPickupDefinition]
    ammo_pickups: dict[str, AmmoPickupDefinition]
    default_pickups: dict[HintFeature, tuple[StandardPickupDefinition, ...]]
    default_offworld_model: str

    def get_pickup_with_name(self, name: str) -> StandardPickupDefinition | AmmoPickupDefinition:
        return self.standard_pickups.get(name) or self.ammo_pickups[name]


def read_database(database_data: dict, game: RandovaniaGame) -> PickupDatabase:
    """
    :param database_data:
    :param game:
    :return:
    """
    pickup_migration.migrate_current(database_data, game)

    pickup_categories = {
        name: HintFeature.from_json(category, name=name)
        for name, category in database_data["pickup_categories"].items()
    }

    generated_pickups = {
        group_name: StandardPickupDefinition.from_json_with_categories(
            pickup.pop("name_template"),
            game,
            pickup_categories,
            pickup,
        )
        for group_name, pickup in database_data["generated_pickups"].items()
    }

    standard_pickups = {
        name: StandardPickupDefinition.from_json_with_categories(name, game, pickup_categories, pickup)
        for name, pickup in database_data["standard_pickups"].items()
    }

    ammo_pickups = {
        name: AmmoPickupDefinition.from_json_with_categories(name, game, pickup_categories, pickup)
        for name, pickup in database_data["ammo_pickups"].items()
    }

    default_pickups = {
        pickup_categories[category_name]: tuple(standard_pickups[pickup_name] for pickup_name in pickup_names)
        for category_name, pickup_names in database_data["default_pickups"].items()
    }

    default_offworld_model = database_data["default_offworld_model"]

    return PickupDatabase(
        pickup_categories,
        generated_pickups,
        standard_pickups,
        ammo_pickups,
        default_pickups,
        default_offworld_model,
    )


def write_database(database: PickupDatabase) -> dict:
    """

    :param database:
    :return:
    """
    pickup_categories = {name: pickup_category.as_json for name, pickup_category in database.pickup_categories.items()}

    generated_pickups = {
        group_name: {
            "name_template": pickup.name,
            **pickup.as_json,
        }
        for group_name, pickup in database.generated_pickups.items()
    }

    standard_pickups = {name: pickup.as_json for name, pickup in database.standard_pickups.items()}

    ammo_pickups = {name: ammo.as_json for name, ammo in database.ammo_pickups.items()}

    default_pickups = {
        category.name: [pickup.name for pickup in pickups] for category, pickups in database.default_pickups.items()
    }

    default_offworld_model = database.default_offworld_model

    return {
        "schema_version": pickup_migration.CURRENT_VERSION,
        "pickup_categories": pickup_categories,
        "generated_pickups": generated_pickups,
        "standard_pickups": standard_pickups,
        "ammo_pickups": ammo_pickups,
        "default_pickups": default_pickups,
        "default_offworld_model": default_offworld_model,
    }
