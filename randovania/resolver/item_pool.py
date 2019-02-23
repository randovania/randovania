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
from randovania.layout.major_item_state import MajorItemState
from randovania.layout.major_items_configuration import MajorItemsConfiguration
from randovania.layout.permalink import Permalink
from randovania.resolver.exceptions import InvalidConfiguration


def _create_pickup_for(item: MajorItem,
                       ammo_count: Optional[int],
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

    resources.append((resource_database.get_by_type_and_index(ResourceType.ITEM, 47), 1))

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
    resources = [(resource_database.get_by_type_and_index(ResourceType.ITEM, ammo.item), ammo_count)]

    return PickupEntry(
        name=ammo.name,
        resources=tuple(resources),
        model_index=ammo.models[0],
        conditional_resources=None,
        item_category="expansion",
        probability_offset=0,
    )


def calculate_item_pool(permalink: Permalink,
                        game: GameDescription,
                        patches: GamePatches,
                        ) -> Tuple[GamePatches, List[PickupEntry]]:
    major_items_configuration = permalink.layout_configuration.major_items_configuration
    ammo_configuration = permalink.layout_configuration.ammo_configuration

    item_pool: List[PickupEntry] = []
    new_assignment: PickupAssignment = {}
    initial_resources: List[ResourceQuantity] = []

    # Adding major items to the pool
    included_ammo_for_item = _add_major_items(game, major_items_configuration, item_pool, new_assignment,
                                              initial_resources)

    # Adding ammo to the pool
    item_pool.extend(_add_ammo(game, ammo_configuration, included_ammo_for_item))

    # TODO: add Dark Temple Keys to pool
    # TODO: add Sky Temple Keys to pool

    new_patches = patches.assign_pickup_assignment(new_assignment).assign_extra_initial_items(initial_resources)
    return new_patches, item_pool


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
                     item_pool: List[PickupEntry],
                     new_assignment: PickupAssignment,
                     initial_resources: List[ResourceQuantity],
                     ) -> Dict[int, int]:

    included_ammo_for_item = {}
    for item, state in major_items_configuration.items_state.items():
        ammo_count = major_items_configuration.ammo_count_for_item.get(item)
        pickup = _create_pickup_for(item, ammo_count, game.resource_database)

        if state == MajorItemState.SHUFFLED:
            item_pool.append(pickup)

        elif state == MajorItemState.STARTING_ITEM:
            initial_resources.extend(pickup.resources)

        elif state == MajorItemState.ORIGINAL_LOCATION:
            if item.original_index is None:
                raise InvalidConfiguration(
                    "Item {0.name} does not exist in the original game, cannot use state {1}".format(item, state),
                )
            new_assignment[PickupIndex(item.original_index)] = pickup

        elif state == MajorItemState.REMOVED:
            # Do nothing
            continue

        else:
            raise InvalidConfiguration("Invalid state {1} for {0.name}".format(item, state))

        for ammo in item.ammo:
            included_ammo_for_item[ammo] = included_ammo_for_item.get(ammo, 0) + ammo_count

    return included_ammo_for_item


def calculate_available_pickups(remaining_items: Iterator[PickupEntry],
                                categories: Set[str],
                                relevant_resources: Optional[FrozenSet[ResourceInfo]]) -> Iterator[PickupEntry]:
    for pickup in remaining_items:
        if pickup.item_category in categories:
            if relevant_resources is None or any(resource in relevant_resources
                                                 for resource, _ in pickup.all_resources):
                yield pickup


def remove_pickup_entry_from_list(available_item_pickups: Tuple[PickupEntry, ...],
                                  item: PickupEntry,
                                  ) -> Tuple[PickupEntry, ...]:
    return tuple(filter(lambda x, c=itertools.count(): x != item or next(c) != 0, available_item_pickups))
