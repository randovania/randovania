from typing import Dict

from randovania.game_description import data_reader
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import SimpleResourceInfo, ResourceGain, ResourceDatabase
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.starting_resources import StartingResources


def _add_items_in_resource_gain_to_dict(gain: ResourceGain,
                                        target: Dict[SimpleResourceInfo, int],
                                        ):
    """
    :param gain:
    :param target:
    :return:
    """
    for resource, quantity in gain:
        if resource.resource_type == ResourceType.ITEM:
            target[resource] = target.get(resource, 0) + quantity


def _create_spawn_point_field(resource_database: ResourceDatabase,
                              starting_resources: StartingResources,
                              patches: GamePatches,
                              ) -> dict:
    item_quantities: Dict[SimpleResourceInfo, int] = {}
    _add_items_in_resource_gain_to_dict(starting_resources.resource_gain,
                                        item_quantities)
    _add_items_in_resource_gain_to_dict(patches.extra_initial_items,
                                        item_quantities)

    capacities = [
        {
            "index": item.index,
            "amount": item_quantities.get(item, 0),
        }
        for item in resource_database.item
    ]

    return {
        "location": patches.starting_location.as_json,
        "amount": capacities,
        "capacity": capacities,
    }


def create_patcher_file(description: LayoutDescription) -> dict:
    result = {}

    layout = description.permalink.layout_configuration
    patches = description.patches
    game = data_reader.decode_data(layout.game_data, add_self_as_requirement_to_resources=False)

    result["spawn_point"] = _create_spawn_point_field(game.resource_database,
                                                      layout.starting_resources,
                                                      patches)

    return result
