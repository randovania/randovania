import itertools
from typing import List, Iterator, Set, Tuple, FrozenSet, Optional, Dict

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import PickupEntry, ResourceInfo, PickupIndex, ResourceDatabase, \
    ResourceQuantity, PickupAssignment
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.ammo_state import AmmoState
from randovania.layout.layout_configuration import LayoutSkyTempleKeyMode
from randovania.layout.major_item_state import MajorItemState
from randovania.layout.major_items_configuration import MajorItemsConfiguration
from randovania.layout.permalink import Permalink
from randovania.resolver.exceptions import InvalidConfiguration

PoolResults = Tuple[List[PickupEntry], PickupAssignment, List[ResourceQuantity]]

_ENERGY_TANK_ITEM = 42
_ENERGY_TANK_MODEL = 36
_ITEM_PERCENTAGE = 47
_GUARDIAN_INDICES = [
    PickupIndex(43),  # Dark Suit
    PickupIndex(79),  # Dark Visor
    PickupIndex(115),  # Annihilator Beam
]
_SUB_GUARDIAN_INDICES = [
    PickupIndex(38),  # Morph Ball Bomb
    PickupIndex(37),  # Space Jump Boots
    PickupIndex(75),  # Boost Ball
    PickupIndex(86),  # Grapple Beam
    PickupIndex(102),  # Spider Ball
    PickupIndex(88),  # Main Power Bombs
]
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


def _extend_pool_results(base_results: PoolResults, extension: PoolResults):
    base_results[0].extend(extension[0])
    base_results[1].update(extension[1])
    base_results[2].extend(extension[2])


def _create_pickup_for(item: MajorItem,
                       state: MajorItemState,
                       include_percentage: bool,
                       resource_database: ResourceDatabase,

                       ) -> PickupEntry:
    """
    Creates a Pickup for the given MajorItem
    :param item:
    :param ammo_count:
    :param resource_database:
    :return:
    """

    resources = [(resource_database.get_by_type_and_index(ResourceType.ITEM, item.item), 1)]

    for ammo_index, ammo_count in zip(item.ammo, state.included_ammo):
        resources.append((resource_database.get_by_type_and_index(ResourceType.ITEM, ammo_index), ammo_count))

    if include_percentage:
        resources.append((resource_database.get_by_type_and_index(ResourceType.ITEM, _ITEM_PERCENTAGE), 1))

    return PickupEntry(
        name=item.name,
        resources=tuple(resources),
        model_index=item.model_index,
        conditional_resources=None,
        item_category=item.item_category.value,
        probability_offset=item.probability_offset,
    )


def _create_expansion_for(ammo: Ammo,
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
        conditional_resources=None,
        item_category="expansion",
        probability_offset=0,
    )


def _create_energy_tank_pickup(include_percentage: bool,
                               resource_database: ResourceDatabase,
                               ) -> PickupEntry:
    """

    :param resource_database:
    :param include_percentage:
    :return:
    """

    resources = [(resource_database.get_by_type_and_index(ResourceType.ITEM, _ENERGY_TANK_ITEM), 1)]
    if include_percentage:
        resources.append((resource_database.get_by_type_and_index(ResourceType.ITEM, _ITEM_PERCENTAGE), 1))

    return PickupEntry(
        name="Energy Tank",
        resources=tuple(resources),
        model_index=_ENERGY_TANK_MODEL,
        conditional_resources=None,
        item_category="energy_tank",
        probability_offset=0,
    )


def _create_dark_temple_key_pickup(key_number: int,
                                   temple_index: int,
                                   resource_database: ResourceDatabase,
                                   ) -> PickupEntry:
    return PickupEntry(
        name=_DARK_TEMPLE_KEY_NAMES[temple_index].format(key_number + 1),
        resources=tuple([
            (resource_database.get_by_type_and_index(ResourceType.ITEM,
                                                     _DARK_TEMPLE_KEY_ITEMS[temple_index][key_number]), 1)
        ]),
        model_index=_DARK_TEMPLE_KEY_MODEL,
        conditional_resources=None,
        item_category="temple_key",
        probability_offset=0,
    )


def _create_sky_temple_key_pickup(key_number: int,
                                  resource_database: ResourceDatabase,
                                  ) -> PickupEntry:
    return PickupEntry(
        name="Sky Temple Key {}".format(key_number + 1),
        resources=tuple([
            (resource_database.get_by_type_and_index(ResourceType.ITEM, _SKY_TEMPLE_KEY_ITEMS[key_number]), 1)
        ]),
        model_index=_SKY_TEMPLE_KEY_MODEL,
        conditional_resources=None,
        item_category="sky_temple_key",
        probability_offset=0,
    )


def _add_energy_tanks(game: GameDescription) -> PoolResults:
    total_energy_tanks = 14
    starting_energy_tanks = 0

    item_pool = [
        _create_energy_tank_pickup(True, game.resource_database)
        for _ in range(total_energy_tanks - starting_energy_tanks)
    ]

    initial_resources = []
    for _ in range(starting_energy_tanks):
        initial_resources.extend(_create_energy_tank_pickup(False, game.resource_database).resources)

    return item_pool, {}, initial_resources


def calculate_item_pool(permalink: Permalink,
                        game: GameDescription,
                        patches: GamePatches,
                        ) -> Tuple[GamePatches, List[PickupEntry]]:
    layout_configuration = permalink.layout_configuration
    base_results = ([], {}, [])

    # Adding major items to the pool
    new_results, included_ammo_for_item = _add_major_items(game, layout_configuration.major_items_configuration)
    _extend_pool_results(base_results, new_results)

    # Adding ammo to the pool
    base_results[0].extend(_add_ammo(game, layout_configuration.ammo_configuration, included_ammo_for_item))

    # Adding E-Tanks
    _extend_pool_results(base_results, _add_energy_tanks(game))

    # Adding Dark Temple Keys to pool
    _extend_pool_results(base_results, _add_dark_temple_keys(game))

    # Adding Sky Temple Keys to pool
    _extend_pool_results(base_results, _add_sky_temple_key_distribution_logic(game,
                                                                              layout_configuration.sky_temple_keys))

    new_patches = patches.assign_pickup_assignment(base_results[1]).assign_extra_initial_items(base_results[2])
    return new_patches, base_results[0]


def _add_ammo(game: GameDescription,
              ammo_configuration: AmmoConfiguration,
              included_ammo_for_item: Dict[int, int],
              ) -> Iterator[PickupEntry]:
    """
    Creates the necessary pickups for the given ammo_configuration.
    :param game:
    :param ammo_configuration:
    :param included_ammo_for_item: How much of each item was provided based on the major items.
    :return:
    """

    previous_pickup_for_item = {}

    for ammo, state in ammo_configuration.items_state.items():
        if state.pickup_count == 0:
            continue

        if state.variance != 0:
            raise InvalidConfiguration("Variance was configured for {0.name}, but it is currently NYI".format(ammo))

        ammo_per_pickup = _items_for_ammo(ammo, state, included_ammo_for_item, previous_pickup_for_item)

        for i in range(state.pickup_count):
            yield _create_expansion_for(
                ammo,
                ammo_per_pickup[i],
                game.resource_database
            )


def _items_for_ammo(ammo: Ammo,
                    state: AmmoState,
                    included_ammo_for_item: Dict[int, int],
                    previous_pickup_for_item: Dict[int, Ammo],
                    ):
    ammo_per_pickup: List[List[int]] = [[] for _ in range(state.pickup_count)]

    for item in ammo.items:
        if item in previous_pickup_for_item:
            raise InvalidConfiguration(
                "Both {0.name} and {1.name} have non-zero pickup count for item {2}. This is unsupported.".format(
                    ammo, previous_pickup_for_item[item], item)
            )
        previous_pickup_for_item[item] = ammo

        if item not in included_ammo_for_item:
            raise InvalidConfiguration(
                "Invalid configuration: ammo {0.name} was configured for {1.pickup_count}"
                "expansions, but main pickup was removed".format(ammo, state)
            )

        if state.total_count < included_ammo_for_item[item]:
            raise InvalidConfiguration(
                "Ammo {0.name} was configured for a total of {1.total_count}, but major items gave {2}".format(
                    ammo, state, included_ammo_for_item[item]))

        adjusted_count = state.total_count - included_ammo_for_item[item]
        count_per_expansion = adjusted_count // state.pickup_count
        expansions_with_extra_count = adjusted_count - count_per_expansion * state.pickup_count

        for i, pickup_ammo in enumerate(ammo_per_pickup):
            pickup_ammo.append(count_per_expansion)
            if i < expansions_with_extra_count:
                pickup_ammo[-1] += 1

    return ammo_per_pickup


def _add_major_items(game: GameDescription,
                     major_items_configuration: MajorItemsConfiguration,
                     ) -> Tuple[PoolResults, Dict[int, int]]:
    item_pool: List[PickupEntry] = []
    new_assignment: PickupAssignment = {}
    initial_resources: List[ResourceQuantity] = []
    included_ammo_for_item = {}

    for item, state in major_items_configuration.items_state.items():
        if len(item.ammo) != len(state.included_ammo):
            raise InvalidConfiguration(
                "Item {0.name} uses {0.ammo} as ammo, but there's only {1} values in included_ammo".format(
                    item, len(state.included_ammo)))

        total_pickups = 0

        if state.include_copy_in_original_location:
            if item.original_index is None:
                raise InvalidConfiguration(
                    "Item {0.name} does not exist in the original game, cannot use state {1}".format(item, state),
                )
            new_assignment[item.original_index] = _create_pickup_for(item, state, True, game.resource_database)
            total_pickups += 1

        for _ in range(state.num_shuffled_pickups):
            item_pool.append(_create_pickup_for(item, state, True, game.resource_database))
            total_pickups += 1

        for _ in range(state.num_included_in_starting_items):
            initial_resources.extend(_create_pickup_for(item, state, False, game.resource_database).resources)
            total_pickups += 1

        for ammo_index, ammo_count in zip(item.ammo, state.included_ammo):
            included_ammo_for_item[ammo_index] = included_ammo_for_item.get(ammo_index, 0) + ammo_count * total_pickups

    return (item_pool, new_assignment, initial_resources), included_ammo_for_item


def _add_dark_temple_keys(game: GameDescription,
                          ) -> PoolResults:
    """
    :param game:
    :return:
    """
    item_pool: List[PickupEntry] = []

    for temple_index in range(3):
        for i in range(3):
            item_pool.append(_create_dark_temple_key_pickup(i, temple_index, game.resource_database))

    return item_pool, {}, []


def _add_sky_temple_key_distribution_logic(game: GameDescription,
                                           mode: LayoutSkyTempleKeyMode,
                                           ) -> PoolResults:
    """
    Adds the given Sky Temple Keys to the item pool
    :param game:
    :param mode:
    :return:
    """

    item_pool: List[PickupEntry] = []
    new_assignment: PickupAssignment = {}
    initial_resources: List[ResourceQuantity] = []

    if mode == LayoutSkyTempleKeyMode.ALL_BOSSES or mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        locations_to_place = _GUARDIAN_INDICES[:]
        if mode == LayoutSkyTempleKeyMode.ALL_BOSSES:
            locations_to_place += _SUB_GUARDIAN_INDICES

        for key_number, location in enumerate(locations_to_place):
            new_assignment[location] = _create_sky_temple_key_pickup(key_number, game.resource_database)
        first_automatic_key = len(locations_to_place)

    else:
        keys_to_place = mode.value
        if not isinstance(keys_to_place, int):
            raise InvalidConfiguration("Unknown Sky Temple Key mode: {}".format(mode))

        for key_number in range(keys_to_place):
            item_pool.append(_create_sky_temple_key_pickup(key_number, game.resource_database))
        first_automatic_key = keys_to_place + 1

    for automatic_key_number in range(first_automatic_key, 9):
        initial_resources.extend(_create_sky_temple_key_pickup(automatic_key_number, game.resource_database).resources)

    return item_pool, new_assignment, initial_resources
