from typing import Iterator

from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import ResourceDatabase, PickupEntry, ConditionalResources
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

    def _create_resources(index):
        resources = [(resource_database.get_by_type_and_index(ResourceType.ITEM, index), 1)]

        for ammo_index, ammo_count in zip(item.ammo_index, state.included_ammo):
            resources.append((resource_database.get_by_type_and_index(ResourceType.ITEM, ammo_index), ammo_count))

        if include_percentage:
            resources.append((resource_database.get_by_type_and_index(ResourceType.ITEM, _ITEM_PERCENTAGE), 1))

        return tuple(resources)

    previous_resource = item.progression[0]
    conditional_resources = []

    for progression in item.progression[1:]:
        conditional_resources.append(ConditionalResources(
            item=resource_database.get_by_type_and_index(ResourceType.ITEM, previous_resource),
            resources=_create_resources(progression)
        ))
        previous_resource = progression

    return PickupEntry(
        name=item.name,
        resources=_create_resources(item.progression[0]),
        model_index=item.model_index,
        conditional_resources=tuple(conditional_resources),
        item_category=item.item_category.value,
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
        (resource_database.get_by_type_and_index(ResourceType.ITEM, item), count)
        for item, count in zip(ammo.items, ammo_count)
    ]
    resources.append((resource_database.get_by_type_and_index(ResourceType.ITEM, _ITEM_PERCENTAGE), 1))

    return PickupEntry(
        name=ammo.name,
        resources=tuple(resources),
        model_index=ammo.models[0],  # TODO: use a random model
        conditional_resources=tuple(),
        item_category="expansion",
        probability_offset=0,
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
        resources=tuple([
            (resource_database.get_by_type_and_index(ResourceType.ITEM,
                                                     _DARK_TEMPLE_KEY_ITEMS[temple_index][key_number]), 1)
        ]),
        model_index=_DARK_TEMPLE_KEY_MODEL,
        conditional_resources=tuple(),
        item_category="temple_key",
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
        resources=tuple([
            (resource_database.get_by_type_and_index(ResourceType.ITEM, _SKY_TEMPLE_KEY_ITEMS[key_number]), 1)
        ]),
        model_index=_SKY_TEMPLE_KEY_MODEL,
        conditional_resources=tuple(),
        item_category="sky_temple_key",
        probability_offset=3,
    )
