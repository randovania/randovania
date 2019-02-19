import itertools
from typing import List, Iterator, Set, Tuple, FrozenSet, Optional, Dict

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.item.major_item import MajorItem
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import PickupEntry, ResourceInfo, PickupIndex, ResourceDatabase
from randovania.layout.major_item_state import MajorItemState
from randovania.resolver.exceptions import GenerationFailure
from randovania.layout.permalink import Permalink


def _create_pickup_for(item: MajorItem, ammo_count: Optional[int],
                       resource_database: ResourceDatabase,
                       ) -> PickupEntry:
    """

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


def calculate_item_pool(permalink: Permalink,
                        game: GameDescription,
                        patches: GamePatches,
                        ) -> Tuple[GamePatches, List[PickupEntry]]:

    major_items_configuration = permalink.layout_configuration.major_items_configuration

    item_pool: List[PickupEntry] = []
    new_assignment: Dict[PickupIndex, PickupEntry] = {}
    initial_resources: List[Tuple[ResourceInfo, int]] = []

    # Adding major items to the pool
    for item, state in major_items_configuration.items_state.items():
        ammo_count = major_items_configuration.ammo_count_for_item.get(item)
        pickup = _create_pickup_for(item, ammo_count, game.resource_database)

        if state == MajorItemState.SHUFFLED:
            item_pool.append(pickup)

        elif state == MajorItemState.STARTING_ITEM:
            initial_resources.extend(pickup.resources)

        elif state == MajorItemState.ORIGINAL_LOCATION:
            if item.original_index is None:
                raise GenerationFailure(
                    "Item {0.name} does not exist in the original game, cannot use state {1}".format(item, state),
                    permalink=permalink,
                )
            new_assignment[PickupIndex(item.original_index)] = pickup

        elif state == MajorItemState.REMOVED:
            # Do nothing
            pass

        else:
            raise GenerationFailure(
                "Invalid state {1} for {0.name}".format(item, state),
                permalink=permalink,
            )

    # TODO: add Ammo to pool
    # TODO: add Dark Temple Keys to pool
    # TODO: add Sky Temple Keys to pool

    new_patches = patches.assign_pickup_assignment(new_assignment).assign_extra_initial_items(initial_resources)
    return new_patches, item_pool


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
