import itertools
from typing import List, Iterator, Set, Tuple

from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources import PickupEntry
from randovania.resolver.exceptions import GenerationFailure
from randovania.resolver.layout_configuration import LayoutConfiguration


def calculate_item_pool(configuration: LayoutConfiguration,
                        game: GameDescription,
                        ) -> List[PickupEntry]:
    split_pickups = game.resource_database.pickups_split_by_name()
    useless_item = split_pickups["Energy Transfer Module"][0]

    pickups_with_configured_quantity = configuration.pickups_with_configured_quantity

    for pickup_name, pickup_list in split_pickups.items():
        if pickup_name in pickups_with_configured_quantity:
            configured_quantity = configuration.quantity_for_pickup(pickup_name)
            pickups_with_configured_quantity.remove(pickup_name)
        else:
            configured_quantity = len(pickup_list)

        quantity_delta = configured_quantity - len(pickup_list)

        if quantity_delta > 0:
            # We need more: copy the last element
            pickup_list.extend(pickup_list[-1:] * quantity_delta)

        elif quantity_delta < 0:
            # We need less: drop the end of the list
            # Yes, the index of the following slice should be negative
            del pickup_list[quantity_delta:]

    if pickups_with_configured_quantity:
        raise GenerationFailure(
            "Invalid configuration: has custom quantity for unknown pickups: {}".format(pickups_with_configured_quantity),
            configuration=configuration,
            seed_number=-1
        )

    item_pool = list(itertools.chain.from_iterable(split_pickups.values()))
    quantity_delta = len(item_pool) - len(game.resource_database.pickups)
    if quantity_delta > 0:
        raise GenerationFailure(
            "Invalid configuration: requested {} more items than available slots ({}).".format(
                quantity_delta, len(game.resource_database.pickups)
            ),
            configuration=configuration,
            seed_number=-1
        )

    elif quantity_delta < 0:
        item_pool.extend([useless_item] * -quantity_delta)

    return item_pool


def calculate_available_pickups(remaining_items: Iterator[PickupEntry], categories: Set[str]) -> Iterator[PickupEntry]:
    for pickup in remaining_items:
        if pickup.item_category in categories:
            yield pickup


def remove_pickup_entry_from_list(available_item_pickups: Tuple[PickupEntry, ...],
                                  item: PickupEntry,
                                  ) -> Tuple[PickupEntry, ...]:
    return tuple(filter(lambda x, c=itertools.count(): x != item or next(c) != 0, available_item_pickups))
