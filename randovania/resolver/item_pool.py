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
                       ammo_count: Optional[int],
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
    for ammo in item.ammo:
        resources.append((resource_database.get_by_type_and_index(ResourceType.ITEM, ammo), ammo_count))
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
                          ammo_count: int,
                          extra_count: bool,
                          resource_database: ResourceDatabase,
                          ) -> PickupEntry:
    """
    Creates a Pickup for an expansion of the given ammo.
    :param ammo:
    :param ammo_count:
    :param resource_database:
    :return:
    """

    if extra_count:
        ammo_count += 1

    resources = [
        (resource_database.get_by_type_and_index(ResourceType.ITEM, ammo.item), ammo_count),
        (resource_database.get_by_type_and_index(ResourceType.ITEM, _ITEM_PERCENTAGE), 1),
    ]

    return PickupEntry(
        name=ammo.name,
        resources=tuple(resources),
        model_index=ammo.models[0],
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
    energy_tank_pickup_count = 12
    starting_energy_tanks = 2

    item_pool = [
        _create_energy_tank_pickup(True, game.resource_database)
        for _ in range(energy_tank_pickup_count)
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

    # TODO: add Dark Temple Keys to pool

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

    for item, state in ammo_configuration.items_state.items():
        if state.pickup_count == 0:
            continue

        if item.item not in included_ammo_for_item:
            raise InvalidConfiguration(
                "Invalid configuration: ammo {0.name} was configured for {1.pickup_count}"
                "expansions, but main pickup was removed".format(item, state)
            )

        if state.variance != 0:
            raise InvalidConfiguration("Variance was configured for {0.name}, but it is currently NYI".format(item))

        if state.total_count < included_ammo_for_item[item.item]:
            raise InvalidConfiguration(
                "Ammo {0.name} was configured for a total of {1.total_count}, but major items gave {2}".format(
                    item, state, included_ammo_for_item[item.item]))

        adjusted_count = state.total_count - included_ammo_for_item[item.item]
        count_per_expansion = adjusted_count // state.pickup_count
        expansions_with_extra_count = adjusted_count - count_per_expansion * state.pickup_count

        for i in range(state.pickup_count):
            yield _create_expansion_for(
                item,
                count_per_expansion,
                i < expansions_with_extra_count,
                game.resource_database
            )


def _add_major_items(game: GameDescription,
                     major_items_configuration: MajorItemsConfiguration,
                     ) -> Tuple[PoolResults, Dict[int, int]]:
    item_pool: List[PickupEntry] = []
    new_assignment: PickupAssignment = {}
    initial_resources: List[ResourceQuantity] = []
    included_ammo_for_item = {}

    for item, state in major_items_configuration.items_state.items():
        ammo_count = major_items_configuration.ammo_count_for_item.get(item)

        if state == MajorItemState.SHUFFLED:
            item_pool.append(_create_pickup_for(item, ammo_count, True, game.resource_database))

        elif state == MajorItemState.STARTING_ITEM:
            initial_resources.extend(_create_pickup_for(item, ammo_count, False, game.resource_database).resources)

        elif state == MajorItemState.ORIGINAL_LOCATION:
            if item.original_index is None:
                raise InvalidConfiguration(
                    "Item {0.name} does not exist in the original game, cannot use state {1}".format(item, state),
                )
            new_assignment[PickupIndex(item.original_index)] = _create_pickup_for(item, ammo_count, True,
                                                                                  game.resource_database)

        elif state == MajorItemState.REMOVED:
            # Do nothing
            continue

        else:
            raise InvalidConfiguration("Invalid state {1} for {0.name}".format(item, state))

        for ammo in item.ammo:
            included_ammo_for_item[ammo] = included_ammo_for_item.get(ammo, 0) + ammo_count

    return (item_pool, new_assignment, initial_resources), included_ammo_for_item


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


def calculate_available_pickups(remaining_items: Iterator[PickupEntry],
                                banned_categories: Set[str],
                                relevant_resources: Optional[FrozenSet[ResourceInfo]]) -> Iterator[PickupEntry]:
    for pickup in remaining_items:
        if pickup.item_category not in banned_categories:
            if relevant_resources is None or any(resource in relevant_resources
                                                 for resource, _ in pickup.all_resources):
                yield pickup


def remove_pickup_entry_from_list(available_item_pickups: Tuple[PickupEntry, ...],
                                  item: PickupEntry,
                                  ) -> Tuple[PickupEntry, ...]:
    return tuple(filter(lambda x, c=itertools.count(): x != item or next(c) != 0, available_item_pickups))
