from __future__ import annotations

import collections
from typing import TYPE_CHECKING

from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.generator.pickup_pool.pool_creator import calculate_pool_results

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.layout.base.base_configuration import BaseConfiguration

_RESOURCE_NAME_TRANSLATION = {
    "Temporary Missile": "Missile",
    "Temporary Power Bomb": "Power Bomb",
}
_ITEMS_TO_PLURALIZE = {
    "Missile",
    "Missile Expansion",
    "Missile Tank",
    "Power Bomb",
    "Power Bomb Expansion",
    "Power Bomb Tank",
}


def add_quantity_to_resource(resource: str, quantity: int, always_add_quantity: bool = False) -> str:
    if always_add_quantity or quantity > 1:
        first_part = f"{quantity} "
    else:
        first_part = ""
    return "{}{}{}".format(first_part, resource, "s" if quantity > 1 and resource in _ITEMS_TO_PLURALIZE else "")


def resource_user_friendly_name(resource: ResourceInfo) -> str:
    """
    Gets a name that we should display to the user for the given resource.
    :param resource:
    :return:
    """
    return _RESOURCE_NAME_TRANSLATION.get(resource.long_name, resource.long_name)


def resource_user_friendly_delta(resource: ResourceInfo) -> str:
    return f"{resource_user_friendly_name(resource)}Changed"


def _pickups_count_by_name(pickups: list[PickupEntry]) -> dict[str, int]:
    result = collections.defaultdict(int)
    for it in pickups:
        result[it.name] += 1
    return result


def additional_starting_pickups(
    layout_configuration: BaseConfiguration, game: GameDescription, starting_pickups: list[PickupEntry]
) -> list[str]:
    initial_pickups = _pickups_count_by_name(calculate_pool_results(layout_configuration, game).starting)
    final_pickups = _pickups_count_by_name(starting_pickups)

    return [
        add_quantity_to_resource(name, delta)
        for name, value in sorted(final_pickups.items(), key=lambda it: it[0])
        if (delta := value - initial_pickups[name]) > 0
    ]


def additional_starting_items(
    layout_configuration: BaseConfiguration, game: GameDescription, starting_items: ResourceCollection
) -> list[str]:
    initial_items = ResourceCollection.with_database(game.resource_database)
    for pickup in calculate_pool_results(layout_configuration, game).starting:
        initial_items.add_resource_gain(pickup.resource_gain(initial_items))

    return [
        add_quantity_to_resource(resource_user_friendly_name(item), quantity)
        for item, quantity in sorted(starting_items.as_resource_gain(), key=lambda a: resource_user_friendly_name(a[0]))
        if 0 < quantity != initial_items[item]
    ]


def additional_starting_equipment(
    layout_configuration: BaseConfiguration, game: GameDescription, patches: GamePatches
) -> list[str]:
    if isinstance(patches.starting_equipment, ResourceCollection):
        return additional_starting_items(layout_configuration, game, patches.starting_equipment)
    else:
        return additional_starting_pickups(layout_configuration, game, patches.starting_equipment)
