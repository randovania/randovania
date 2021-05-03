from typing import Optional, List

from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceQuantity
from randovania.games.prime import corruption_items
from randovania.games.prime import prime_items
from randovania.games.prime.echoes_items import DARK_TEMPLE_KEY_MODEL, DARK_TEMPLE_KEY_NAMES, DARK_TEMPLE_KEY_ITEMS, \
    SKY_TEMPLE_KEY_MODEL, SKY_TEMPLE_KEY_ITEMS, USELESS_PICKUP_MODEL, USELESS_PICKUP_ITEM
from randovania.layout.major_item_state import MajorItemState


def create_major_item(item: MajorItem,
                      state: MajorItemState,
                      include_percentage: bool,
                      resource_database: ResourceDatabase,
                      ammo: Optional[Ammo],
                      ammo_requires_major_item: bool,

                      ) -> PickupEntry:
    """
    Creates a Pickup for the given MajorItem
    :param include_percentage:
    :param state:
    :param item:
    :param resource_database:
    :param ammo:
    :param ammo_requires_major_item:
    :return:
    """

    extra_resources = [
        (resource_database.get_item(ammo_index), ammo_count)
        for ammo_index, ammo_count in zip(item.ammo_index, state.included_ammo)
    ]
    if include_percentage:
        extra_resources.append((resource_database.item_percentage, 1))

    def _create_resources(base_resource: Optional[int]) -> ResourceQuantity:
        # FIXME: hacky quantity for Hazard Shield
        quantity = 5 if item.name == "Hazard Shield" else 1
        return resource_database.get_item(base_resource), quantity

    return PickupEntry(
        name=item.name,
        progression=tuple(
            _create_resources(progression)
            for progression in item.progression
        ),
        extra_resources=tuple(extra_resources),
        model_index=item.model_index,
        item_category=item.item_category,
        broad_category=item.broad_category,
        probability_offset=item.probability_offset,
        probability_multiplier=item.probability_multiplier,
        unlocks_resource=item.unlocks_ammo,
        respects_lock=ammo_requires_major_item,
        resource_lock=ammo.create_resource_lock(resource_database) if ammo is not None else None,
    )


def create_ammo_expansion(ammo: Ammo,
                          ammo_count: List[int],
                          requires_major_item: bool,
                          resource_database: ResourceDatabase,
                          ) -> PickupEntry:
    """
    Creates a Pickup for an expansion of the given ammo.
    :param ammo:
    :param ammo_count:
    :param requires_major_item:
    :param resource_database:
    :return:
    """
    resources = [(resource_database.get_item(item), count)
                 for item, count in zip(ammo.items, ammo_count)]
    resources.append((resource_database.item_percentage, 1))

    return PickupEntry(
        name=ammo.name,
        progression=(),
        extra_resources=tuple(resources),
        model_index=ammo.models[0],  # TODO: use a random model
        item_category=ItemCategory.EXPANSION,
        broad_category=ammo.broad_category,
        respects_lock=requires_major_item,
        resource_lock=ammo.create_resource_lock(resource_database),
    )


def create_dark_temple_key(key_number: int,
                           temple_index: int,
                           resource_database: ResourceDatabase,
                           ) -> PickupEntry:
    """
    Creates a Dark Temple Key
    :param key_number:
    :param temple_index: The index of the temple: Dark Agon, Dark Torvus, Hive Temple
    :param resource_database:
    :return:
    """

    return PickupEntry(
        name=DARK_TEMPLE_KEY_NAMES[temple_index].format(key_number + 1),
        progression=((resource_database.get_item(DARK_TEMPLE_KEY_ITEMS[temple_index][key_number]), 1),),
        model_index=DARK_TEMPLE_KEY_MODEL,
        item_category=ItemCategory.TEMPLE_KEY,
        broad_category=ItemCategory.KEY,
        probability_offset=3,
    )


def create_sky_temple_key(key_number: int,
                          resource_database: ResourceDatabase,
                          ) -> PickupEntry:
    """

    :param key_number:
    :param resource_database:
    :return:
    """

    return PickupEntry(
        name="Sky Temple Key {}".format(key_number + 1),
        progression=((resource_database.get_item(SKY_TEMPLE_KEY_ITEMS[key_number]), 1),),
        model_index=SKY_TEMPLE_KEY_MODEL,
        item_category=ItemCategory.SKY_TEMPLE_KEY,
        broad_category=ItemCategory.KEY,
        probability_offset=3,
    )


def create_energy_cell(cell_index: int,
                       resource_database: ResourceDatabase,
                       ) -> PickupEntry:
    return PickupEntry(
        name=f"Energy Cell {cell_index + 1}",
        progression=(
            (resource_database.get_item(corruption_items.ENERGY_CELL_ITEMS[cell_index]), 1),
        ),
        extra_resources=(
            (resource_database.get_item(corruption_items.ENERGY_CELL_TOTAL_ITEM), 1),
            (resource_database.item_percentage, 1),
        ),
        model_index=corruption_items.ENERGY_CELL_MODEL,
        item_category=ItemCategory.TEMPLE_KEY,
        broad_category=ItemCategory.KEY,
        probability_offset=0.25,
    )


def create_artifact(artifact_index: int,
                    resource_database: ResourceDatabase,
                    ) -> PickupEntry:
    return PickupEntry(
        name=prime_items.ARTIFACT_NAMES[artifact_index],
        progression=(
            (resource_database.get_item(prime_items.ARTIFACT_ITEMS[artifact_index]), 1),
        ),
        extra_resources=(
            (resource_database.item_percentage, 1),
        ),
        model_index=prime_items.ARTIFACT_MODEL[artifact_index],
        item_category=ItemCategory.TEMPLE_KEY,
        broad_category=ItemCategory.KEY,
        probability_offset=0.25,
    )


def create_useless_pickup(resource_database: ResourceDatabase) -> PickupEntry:
    """
    Creates an Energy Transfer Module pickup.
    :param resource_database:
    :return:
    """
    return PickupEntry(
        name="Energy Transfer Module",
        progression=(
            (resource_database.get_item(USELESS_PICKUP_ITEM), 1),
        ),
        model_index=USELESS_PICKUP_MODEL,
        item_category=ItemCategory.ETM,
        broad_category=ItemCategory.ETM,
    )


def create_visual_etm() -> PickupEntry:
    """
    Creates an ETM that should only be used as a visual pickup.
    :return:
    """
    return PickupEntry(
        name="Unknown item",
        progression=tuple(),
        model_index=USELESS_PICKUP_MODEL,
        item_category=ItemCategory.ETM,
        broad_category=ItemCategory.ETM,
    )
