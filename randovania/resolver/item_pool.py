import itertools
from typing import List, Iterator, Set, Tuple, FrozenSet, Optional

from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources import PickupEntry, ResourceInfo
from randovania.resolver.exceptions import GenerationFailure
from randovania.resolver.permalink import Permalink


def calculate_item_pool(permalink: Permalink,
                        game: GameDescription,
                        ) -> List[PickupEntry]:

    item_pool: List[PickupEntry] = []
    pickup_quantities = permalink.layout_configuration.pickup_quantities

    try:
        pickup_quantities.validate_total_quantities()
    except ValueError as e:
        raise GenerationFailure(
            "Invalid configuration: {}".format(e),
            permalink=permalink,
        )

    quantities_pickups = set(pickup_quantities.pickups())
    database_pickups = set(game.pickup_database.all_useful_pickups)

    if quantities_pickups != database_pickups:
        raise GenerationFailure(
            "Diverging pickups in configuration.\nPickups in quantities: {}\nPickups in database: {}".format(
                [pickup.name for pickup in quantities_pickups],
                [pickup.name for pickup in database_pickups],
            ),
            permalink=permalink,
        )

    for pickup, quantity in pickup_quantities.items():
        item_pool.extend([pickup] * quantity)

    quantity_delta = len(item_pool) - game.pickup_database.total_pickup_count
    if quantity_delta > 0:
        raise GenerationFailure(
            "Invalid configuration: requested {} more items than available slots ({}).".format(
                quantity_delta, game.pickup_database.total_pickup_count
            ),
            permalink=permalink,
        )

    elif quantity_delta < 0:
        item_pool.extend([game.pickup_database.useless_pickup] * -quantity_delta)

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
