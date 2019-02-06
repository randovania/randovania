from typing import Dict

from randovania.game_description import data_reader
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import TeleporterNode
from randovania.game_description.resource_type import ResourceType
from randovania.game_description.resources import SimpleResourceInfo, ResourceGain, ResourceDatabase, PickupDatabase
from randovania.game_description.world_list import WorldList
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.starting_location import StartingLocationConfiguration
from randovania.layout.starting_resources import StartingResources, StartingResourcesConfiguration


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


def _create_pickup_list(patches: GamePatches,
                        pickup_database: PickupDatabase
                        ) -> list:
    useless_pickup = pickup_database.useless_pickup
    pickup_assignment = patches.pickup_assignment

    pickups = [
        {
            "pickup_index": original_index.index,
            # "model": 1234,
            # "scan": "This is a description.",
            "resources": [
                {
                    "index": resource.index,
                    "amount": quantity
                }
                for resource, quantity in pickup_assignment.get(original_index, useless_pickup).resource_gain()
                if quantity > 0 and resource.resource_type == ResourceType.ITEM
            ]
        }
        for original_index in pickup_database.original_pickup_mapping.keys()
    ]

    return pickups


def _create_elevators_field(world_list: WorldList, patches: GamePatches) -> list:
    nodes_by_teleporter_id = {
        node.teleporter_instance_id: node
        for node in world_list.all_nodes
        if isinstance(node, TeleporterNode)
    }

    elevators = [
        {
            "origin_location": world_list.node_to_area_location(nodes_by_teleporter_id[instance_id]).as_json,
            "target_location": connection.as_json,
            "room_name": "Transport to {}".format(world_list.world_by_area_location(connection).name)
        }
        for instance_id, connection in patches.elevator_connection.items()
    ]

    return elevators


def create_patcher_file(description: LayoutDescription) -> dict:
    result = {}

    layout = description.permalink.layout_configuration
    patches = description.patches
    game = data_reader.decode_data(layout.game_data, add_self_as_requirement_to_resources=False)

    result["spawn_point"] = _create_spawn_point_field(game.resource_database,
                                                      layout.starting_resources,
                                                      patches)

    result["pickups"] = _create_pickup_list(patches, game.pickup_database)

    result["elevators"] = _create_elevators_field(game.world_list,
                                                  patches)

    result["specific_patches"] = {
        "hive_chamber_b_post_state": not is_vanilla_starting_location(layout)
    }

    return result


def is_vanilla_starting_location(configuration: LayoutConfiguration) -> bool:
    loc_config = configuration.starting_location.configuration
    resource_config = configuration.starting_resources.configuration
    return (loc_config == StartingLocationConfiguration.SHIP and
            resource_config == StartingResourcesConfiguration.VANILLA_ITEM_LOSS_ENABLED)
