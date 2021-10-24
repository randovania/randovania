from typing import Optional, Tuple

from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_category import GENERIC_KEY_CATEGORY, USELESS_ITEM_CATEGORY, ItemCategory
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceQuantity
from randovania.games.game import RandovaniaGame
from randovania.games.prime import corruption_items, echoes_items
from randovania.games.prime import prime_items
from randovania.layout.base.major_item_state import MajorItemState


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
    if include_percentage and resource_database.item_percentage is not None:
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
        model=PickupModel(
            game=resource_database.game_enum,
            name=item.model_name,
        ),
        item_category=item.item_category,
        broad_category=item.broad_category,
        probability_offset=item.probability_offset,
        probability_multiplier=item.probability_multiplier,
        unlocks_resource=item.unlocks_ammo,
        respects_lock=ammo_requires_major_item,
        resource_lock=ammo.create_resource_lock(resource_database) if ammo is not None else None,
    )


def create_ammo_expansion(ammo: Ammo,
                          ammo_count: Tuple[int, ...],
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

    if resource_database.item_percentage is not None:
        resources.append((resource_database.item_percentage, 1))

    return PickupEntry(
        name=ammo.name,
        progression=(),
        extra_resources=tuple(resources),
        model=PickupModel(
            game=resource_database.game_enum,
            name=ammo.model_name,
        ),
        item_category=ammo.item_category,
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
    TEMPLE_KEY_CATEGORY = ItemCategory(
        name="temple_key",
        long_name="",
        hint_details=("a ", "red Temple Key"),
        is_major=False,
        is_key=True
    )

    return PickupEntry(
        name=echoes_items.DARK_TEMPLE_KEY_NAMES[temple_index].format(key_number + 1),
        progression=((resource_database.get_item(echoes_items.DARK_TEMPLE_KEY_ITEMS[temple_index][key_number]), 1),),
        model=PickupModel(
            game=resource_database.game_enum,
            name=echoes_items.DARK_TEMPLE_KEY_MODEL,
        ),
        item_category=TEMPLE_KEY_CATEGORY,
        broad_category=GENERIC_KEY_CATEGORY,
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
    SKY_TEMPLE_KEY_CATEGORY = ItemCategory(
        name="sky_temple_key",
        long_name="",
        hint_details=("a ", "Sky Temple Key"),
        is_major=False,
        is_key=True
    )

    return PickupEntry(
        name="Sky Temple Key {}".format(key_number + 1),
        progression=((resource_database.get_item(echoes_items.SKY_TEMPLE_KEY_ITEMS[key_number]), 1),),
        model=PickupModel(
            game=resource_database.game_enum,
            name=echoes_items.SKY_TEMPLE_KEY_MODEL,
        ),
        item_category=SKY_TEMPLE_KEY_CATEGORY,
        broad_category=GENERIC_KEY_CATEGORY,
        probability_offset=3,
    )


def create_energy_cell(cell_index: int,
                       resource_database: ResourceDatabase,
                       ) -> PickupEntry:
    ENERGY_CELL_CATEGORY = ItemCategory(
        name="energy_cell",
        long_name="",
        hint_details=("an ", "energy cell"),
        is_major=False,
        is_key=True
    )

    return PickupEntry(
        name=f"Energy Cell {cell_index + 1}",
        progression=(
            (resource_database.get_item(corruption_items.ENERGY_CELL_ITEMS[cell_index]), 1),
        ),
        extra_resources=(
            (resource_database.get_item(corruption_items.ENERGY_CELL_TOTAL_ITEM), 1),
            (resource_database.item_percentage, 1),
        ),
        model=PickupModel(
            game=resource_database.game_enum,
            name=corruption_items.ENERGY_CELL_MODEL,
        ),
        item_category=ENERGY_CELL_CATEGORY,
        broad_category=GENERIC_KEY_CATEGORY,
        probability_offset=0.25,
    )


def create_artifact(artifact_index: int,
                    minimum_progression: int,
                    resource_database: ResourceDatabase,
                    ) -> PickupEntry:
    ARTIFACT_CATEGORY = ItemCategory(
        name="artifact",
        long_name="",
        hint_details=("an ", "artifact"),
        is_major=False,
        is_key=True
    )

    return PickupEntry(
        name=prime_items.ARTIFACT_NAMES[artifact_index],
        progression=(
            (resource_database.get_item(prime_items.ARTIFACT_ITEMS[artifact_index]), 1),
        ),
        model=PickupModel(
            game=resource_database.game_enum,
            name=prime_items.ARTIFACT_MODEL[artifact_index],
        ),
        item_category=ARTIFACT_CATEGORY,
        broad_category=GENERIC_KEY_CATEGORY,
        probability_offset=0.25,
        required_progression=minimum_progression,
    )


def create_echoes_useless_pickup(resource_database: ResourceDatabase) -> PickupEntry:
    """
    Creates an Energy Transfer Module pickup.
    :param resource_database:
    :return:
    """
    return PickupEntry(
        name="Energy Transfer Module",
        progression=(
            (resource_database.get_item(echoes_items.USELESS_PICKUP_ITEM), 1),
        ),
        model=PickupModel(
            game=resource_database.game_enum,
            name=echoes_items.USELESS_PICKUP_MODEL,
        ),
        item_category=USELESS_ITEM_CATEGORY,
        broad_category=USELESS_ITEM_CATEGORY,
    )


def create_nothing_pickup(resource_database: ResourceDatabase) -> PickupEntry:
    """
    Creates a Nothing pickup.
    :param resource_database:
    :return:
    """
    return PickupEntry(
        name="Nothing",
        progression=(
            (resource_database.get_item_by_name("Nothing"), 1),
        ),
        model=PickupModel(
            game=resource_database.game_enum,
            name="Nothing",
        ),
        item_category=USELESS_ITEM_CATEGORY,
        broad_category=USELESS_ITEM_CATEGORY,
    )


def create_visual_etm() -> PickupEntry:
    """
    Creates an ETM that should only be used as a visual pickup.
    :return:
    """
    return PickupEntry(
        name="Unknown item",
        progression=tuple(),
        model=PickupModel(
            game=RandovaniaGame.METROID_PRIME_ECHOES,
            name=echoes_items.USELESS_PICKUP_MODEL,
        ),
        item_category=USELESS_ITEM_CATEGORY,
        broad_category=USELESS_ITEM_CATEGORY,
    )
