from typing import Dict, Iterator, List

from randovania.game_description.item.ammo import Ammo
from randovania.game_description.resources import PickupEntry, ResourceDatabase
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.ammo_state import AmmoState
from randovania.resolver.exceptions import InvalidConfiguration
from randovania.resolver.item_pool.pickup_creator import create_ammo_expansion


def add_ammo(resource_database: ResourceDatabase,
             ammo_configuration: AmmoConfiguration,
             included_ammo_for_item: Dict[int, int],
             ) -> Iterator[PickupEntry]:
    """
    Creates the necessary pickups for the given ammo_configuration.
    :param resource_database:
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

        ammo_per_pickup = items_for_ammo(ammo, state,
                                         included_ammo_for_item,
                                         previous_pickup_for_item,
                                         ammo_configuration.maximum_ammo)

        # TODO: we can just iterate over ammo_per_pickup
        for i in range(state.pickup_count):
            yield create_ammo_expansion(
                ammo,
                ammo_per_pickup[i],
                resource_database
            )


def items_for_ammo(ammo: Ammo,
                   state: AmmoState,
                   included_ammo_for_item: Dict[int, int],
                   previous_pickup_for_item: Dict[int, Ammo],
                   maximum_ammo: Dict[int, int],
                   ) -> List[List[int]]:
    """
    Helper function for add_ammo.

    :param maximum_ammo:
    :param ammo:
    :param state:
    :param included_ammo_for_item:
    :param previous_pickup_for_item:
    :return: An array that lists how many of each ammo each instance of the expansions should give
    """
    ammo_per_pickup: List[List[int]] = [[] for _ in range(state.pickup_count)]

    # TODO: add test for case of 0 pickups
    if state.pickup_count == 0:
        return ammo_per_pickup

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

        if maximum_ammo[item] < included_ammo_for_item[item]:
            raise InvalidConfiguration(
                "Ammo {0.name} was configured for a total of {1}, but major items gave {2}".format(
                    ammo, maximum_ammo[item], included_ammo_for_item[item]))

        adjusted_count = maximum_ammo[item] - included_ammo_for_item[item]
        count_per_expansion = adjusted_count // state.pickup_count
        expansions_with_extra_count = adjusted_count - count_per_expansion * state.pickup_count

        for i, pickup_ammo in enumerate(ammo_per_pickup):
            pickup_ammo.append(count_per_expansion)
            if i < expansions_with_extra_count:
                pickup_ammo[-1] += 1

    return ammo_per_pickup
