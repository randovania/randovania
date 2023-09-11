from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from randovania.game_description.pickup import migrations
from randovania.game_description.pickup.ammo_pickup import AmmoPickupDefinition
from randovania.game_description.pickup.pickup_category import PickupCategory
from randovania.game_description.pickup.standard_pickup import StandardPickupDefinition

if TYPE_CHECKING:
    from randovania.games.game import RandovaniaGame


@dataclass(frozen=True)
class PickupDatabase:
    pickup_categories: dict[str, PickupCategory]
    standard_pickups: dict[str, StandardPickupDefinition]
    ammo_pickups: dict[str, AmmoPickupDefinition]
    default_pickups: dict[PickupCategory, tuple[StandardPickupDefinition, ...]]
    default_offworld_model: str

    def get_pickup_with_name(self, name: str) -> StandardPickupDefinition | AmmoPickupDefinition:
        return self.standard_pickups.get(name) or self.ammo_pickups[name]


def read_database(database_data: dict, game: RandovaniaGame) -> PickupDatabase:
    """
    :param database_data:
    :param game:
    :return:
    """
    migrations.migrate_current(database_data)

    pickup_categories = {
        name: PickupCategory.from_json(name, category) for name, category in database_data["pickup_categories"].items()
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

    standard_pickups = {name: pickup.as_json for name, pickup in database.standard_pickups.items()}

    ammo_pickups = {name: ammo.as_json for name, ammo in database.ammo_pickups.items()}

    default_pickups = {
        category.name: [pickup.name for pickup in pickups] for category, pickups in database.default_pickups.items()
    }

    default_offworld_model = database.default_offworld_model

    return {
        "schema_version": migrations.CURRENT_VERSION,
        "pickup_categories": pickup_categories,
        "standard_pickups": standard_pickups,
        "ammo_pickups": ammo_pickups,
        "default_pickups": default_pickups,
        "default_offworld_model": default_offworld_model,
    }
