import copy
import itertools
from typing import List, Iterator, Set, Tuple, FrozenSet, Optional

from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources import PickupEntry, ResourceInfo, ResourceDatabase
from randovania.resolver.exceptions import GenerationFailure
from randovania.resolver.layout_configuration import LayoutConfiguration


def calculate_item_pool(configuration: LayoutConfiguration,
                        game: GameDescription,
                        ) -> List[PickupEntry]:

    useless_item = game.pickup_database.pickup_by_name("Energy Transfer Module")
    item_pool: List[PickupEntry] = []

    symmetric_difference = set(configuration.pickup_quantities) ^ set(game.pickup_database.pickups.values())
    if symmetric_difference:
        raise GenerationFailure(
            "Invalid configuration: diverging pickups in configuration: {}".format(symmetric_difference),
            configuration=configuration,
            seed_number=-1
        )

    for pickup, quantity in configuration.pickup_quantities.items():
        item_pool.extend([pickup] * quantity)

    quantity_delta = len(item_pool) - game.pickup_database.total_pickup_count
    if quantity_delta > 0:
        raise GenerationFailure(
            "Invalid configuration: requested {} more items than available slots ({}).".format(
                quantity_delta, game.pickup_database.total_pickup_count
            ),
            configuration=configuration,
            seed_number=-1
        )

    elif quantity_delta < 0:
        item_pool.extend([useless_item] * -quantity_delta)

    return item_pool


def calculate_available_pickups(remaining_items: Iterator[PickupEntry],
                                categories: Set[str],
                                relevant_resources: Optional[FrozenSet[ResourceInfo]]) -> Iterator[PickupEntry]:
    for pickup in remaining_items:
        if pickup.item_category in categories:
            if relevant_resources is None or any(resource in relevant_resources
                                                 for resource, _ in pickup.resource_gain()):
                yield pickup


def remove_pickup_entry_from_list(available_item_pickups: Tuple[PickupEntry, ...],
                                  item: PickupEntry,
                                  ) -> Tuple[PickupEntry, ...]:
    return tuple(filter(lambda x, c=itertools.count(): x != item or next(c) != 0, available_item_pickups))
