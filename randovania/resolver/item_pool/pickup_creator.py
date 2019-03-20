from typing import Iterator, Optional, Tuple

from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import ResourceDatabase, PickupEntry, ConditionalResources, \
    ResourceQuantity, SimpleResourceInfo
from randovania.layout.major_item_state import MajorItemState

_ITEM_PERCENTAGE = 47
_DARK_TEMPLE_KEY_MODEL = 37
_DARK_TEMPLE_KEY_NAMES = [
    "Dark Agon Key {0}",
    "Dark Torvus Key {0}",
    "Ing Hive Key {0}"
]
_DARK_TEMPLE_KEY_ITEMS = [
    [32, 33, 34, ],
    [35, 36, 37, ],
    [38, 39, 40, ],
]
_SKY_TEMPLE_KEY_MODEL = 38
_SKY_TEMPLE_KEY_ITEMS = [
    29,
    30,
    31,
    101,
    102,
    103,
    104,
    105,
    106,
]
_USELESS_PICKUP_MODEL = 30
_USELESS_PICKUP_ITEM = 107


def _get_item(resource_database: ResourceDatabase, index: int,
              ) -> SimpleResourceInfo:
    return resource_database.get_by_type_and_index(ResourceType.ITEM, index)


def create_major_item(item: MajorItem,
                      state: MajorItemState,
                      include_percentage: bool,
                      resource_database: ResourceDatabase,

                      ) -> PickupEntry:
    """
    Creates a Pickup for the given MajorItem
    :param include_percentage:
    :param state:
    :param item:
    :param resource_database:
    :return:
    """

    def _create_resources(base_resource: Optional[int]) -> Tuple[ResourceQuantity, ...]:
        resources = []

        if base_resource is not None:
            resources.append((_get_item(resource_database, base_resource), 1))

        for ammo_index, ammo_count in zip(item.ammo_index, state.included_ammo):
            resources.append((_get_item(resource_database, ammo_index), ammo_count))

        if include_percentage:
            resources.append((_get_item(resource_database, _ITEM_PERCENTAGE), 1))

        return tuple(resources)

    if item.progression:
        conditional_resources = tuple(
            ConditionalResources(
                name=_get_item(resource_database, item.progression[i]).long_name,
                item=_get_item(resource_database, item.progression[i - 1]) if i > 0 else None,
                resources=_create_resources(progression)
            )
            for i, progression in enumerate(item.progression)
        )
    else:
        conditional_resources = (
            ConditionalResources(name=item.name, item=None, resources=_create_resources(None)),
        )

    return PickupEntry(
        name=item.name,
        resources=conditional_resources,
        model_index=item.model_index,
        item_category=item.item_category,
        probability_offset=item.probability_offset,
    )


def create_ammo_expansion(ammo: Ammo,
                          ammo_count: Iterator[int],
                          resource_database: ResourceDatabase,
                          ) -> PickupEntry:
    """
    Creates a Pickup for an expansion of the given ammo.
    :param ammo:
    :param ammo_count:
    :param resource_database:
    :return:
    """

    resources = [
        (_get_item(resource_database, item), count)
        for item, count in zip(ammo.items, ammo_count)
    ]
    resources.append((_get_item(resource_database, _ITEM_PERCENTAGE), 1))

    return PickupEntry(
        name=ammo.name,
        resources=(
            ConditionalResources(None, None, tuple(resources)),
        ),
        model_index=ammo.models[0],  # TODO: use a random model
        item_category=ItemCategory.EXPANSION,
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
        name=_DARK_TEMPLE_KEY_NAMES[temple_index].format(key_number + 1),
        resources=(
            ConditionalResources(None, None, tuple([
                (_get_item(resource_database, _DARK_TEMPLE_KEY_ITEMS[temple_index][key_number]), 1)
            ])),
        ),
        model_index=_DARK_TEMPLE_KEY_MODEL,
        item_category=ItemCategory.TEMPLE_KEY,
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
        resources=(
            ConditionalResources(None, None, tuple([
                (_get_item(resource_database, _SKY_TEMPLE_KEY_ITEMS[key_number]), 1)
            ])),
        ),
        model_index=_SKY_TEMPLE_KEY_MODEL,
        item_category=ItemCategory.SKY_TEMPLE_KEY,
        probability_offset=3,
    )


def create_useless_pickup(resource_database: ResourceDatabase) -> PickupEntry:
    """
    Creates an Energy Transfer Module pickup.
    :param resource_database:
    :return:
    """
    return PickupEntry(
        name="Energy Transfer Module",
        resources=(
            ConditionalResources(None, None, tuple([
                (_get_item(resource_database, _USELESS_PICKUP_ITEM), 1)
            ])),
        ),
        model_index=_USELESS_PICKUP_MODEL,
        item_category=ItemCategory.ETM,
    )


def create_visual_etm() -> PickupEntry:
    """
    Creates an ETM that should only be used as a visual pickup.
    :return:
    """
    return PickupEntry(
        name="Unknown item",
        resources=(
            ConditionalResources(None, None, tuple()),
        ),
        model_index=_USELESS_PICKUP_MODEL,
        item_category=ItemCategory.ETM,
    )
