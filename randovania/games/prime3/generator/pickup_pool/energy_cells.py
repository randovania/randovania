from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.pickup import pickup_category
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupGeneratorParams, PickupModel
from randovania.game_description.resources.location_category import LocationCategory
from randovania.games.prime3.patcher import corruption_items
from randovania.generator.pickup_pool import PoolResults

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_database import ResourceDatabase

ENERGY_CELL_CATEGORY = pickup_category.PickupCategory(
    name="energy_cell", long_name="Energy Cell", hint_details=("an ", "energy cell"), hinted_as_major=True, is_key=True
)


def add_energy_cells(
    resource_database: ResourceDatabase,
) -> PoolResults:
    """
    :param resource_database:
    :return:
    """
    item_pool: list[PickupEntry] = []

    for i in range(9):
        item_pool.append(create_energy_cell(i, resource_database))

    return PoolResults(item_pool, {}, [])


def create_energy_cell(
    cell_index: int,
    resource_database: ResourceDatabase,
) -> PickupEntry:
    return PickupEntry(
        name=f"Energy Cell {cell_index + 1}",
        progression=((resource_database.get_item(corruption_items.ENERGY_CELL_ITEMS[cell_index]), 1),),
        extra_resources=(
            (resource_database.get_item(corruption_items.ENERGY_CELL_TOTAL_ITEM), 1),
            (resource_database.get_item(corruption_items.PERCENTAGE), 1),
        ),
        model=PickupModel(
            game=resource_database.game_enum,
            name=corruption_items.ENERGY_CELL_MODEL,
        ),
        pickup_category=ENERGY_CELL_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=0.25,
        ),
    )
