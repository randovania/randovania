from typing import List

from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, CurrentResources
from randovania.generator.item_pool.pool_creator import calculate_pool_results
from randovania.layout.base.base_configuration import BaseConfiguration

_RESOURCE_NAME_TRANSLATION = {
    'Temporary Missile': 'Missile',
    'Temporary Power Bomb': 'Power Bomb',
}
_ITEMS_TO_PLURALIZE = {
    "Missile",
    "Power Bomb",
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


def additional_starting_items(layout_configuration: BaseConfiguration,
                              resource_database: ResourceDatabase,
                              starting_items: CurrentResources) -> List[str]:
    initial_items = calculate_pool_results(layout_configuration, resource_database)[2]

    return [
        add_quantity_to_resource(resource_user_friendly_name(item), quantity)
        for item, quantity in sorted(starting_items.items(), key=lambda a: resource_user_friendly_name(a[0]))
        if 0 < quantity != initial_items.get(item, 0)
    ]
