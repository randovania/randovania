import re
from typing import Dict

from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import PickupNode, TeleporterNode, Node
from randovania.game_description.resources import PickupAssignment, find_resource_info_with_long_name
from randovania.game_description.world_list import WorldList
from randovania.layout.layout_configuration import LayoutConfiguration


def _pickup_assignment_to_item_locations(world_list: WorldList,
                                         pickup_assignment: PickupAssignment,
                                         ) -> Dict[str, Dict[str, str]]:
    items_locations = {}

    for world in world_list.worlds:
        items_in_world = {}
        items_locations[world.name] = items_in_world

        for node in world.all_nodes:
            if not node.is_resource_node or not isinstance(node, PickupNode):
                continue

            if node.pickup_index in pickup_assignment:
                pickup = pickup_assignment[node.pickup_index]
                if pickup.item_category == ItemCategory.EXPANSION:
                    first_quantity = pickup.resources[0].resources[0][1]
                    item_name = f"{pickup.name} {first_quantity}"
                else:
                    item_name = pickup.name
            else:
                item_name = "Nothing"

            items_in_world[world_list.node_name(node)] = item_name

    return items_locations


def _node_mapping_to_elevator_connection(world_list: WorldList,
                                         elevators: Dict[str, str],
                                         ) -> Dict[int, AreaLocation]:
    result = {}
    for source_name, target_node in elevators.items():
        source_node: TeleporterNode = world_list.node_from_name(source_name)
        target_node = world_list.node_from_name(target_node)

        result[source_node.teleporter_instance_id] = AreaLocation(
            world_list.nodes_to_world(target_node).world_asset_id,
            world_list.nodes_to_area(target_node).area_asset_id
        )

    return result


def _find_node_with_teleporter(world_list: WorldList, teleporter_id: int) -> Node:
    for node in world_list.all_nodes:
        if isinstance(node, TeleporterNode):
            if node.teleporter_instance_id == teleporter_id:
                return node
    raise ValueError("Unknown teleporter_id: {}".format(teleporter_id))


def serialize(patches: GamePatches, game_data: dict) -> dict:
    """
    Encodes a given GamePatches into a JSON-serializable dict.
    :param patches:
    :param game_data:
    :return:
    """
    world_list = data_reader.decode_data(game_data).world_list

    result = {
        "starting_location": world_list.area_name(world_list.area_by_area_location(patches.starting_location)),
        "starting_items": {
            resource_info.long_name: quantity
            for resource_info, quantity in sorted(patches.extra_initial_items, key=lambda x: x[0].long_name)
        },
        "elevators": {
            world_list.area_name(world_list.nodes_to_area(_find_node_with_teleporter(world_list, teleporter_id))):
                world_list.area_name(world_list.nodes_to_area(world_list.resolve_teleporter_connection(connection)))
            for teleporter_id, connection in patches.elevator_connection.items()
        },
        "locations": {
            key: value
            for key, value in sorted(_pickup_assignment_to_item_locations(world_list,
                                                                          patches.pickup_assignment).items())
        },
    }

    return result


def _area_name_to_area_location(world_list: WorldList, area_name: str) -> AreaLocation:
    world_name, area_name = re.match("([^/]+)/([^/]+)", area_name).group(1, 2)
    starting_world = world_list.world_with_name(world_name)
    starting_area = starting_world.area_by_name(area_name)
    return AreaLocation(starting_world.world_asset_id, starting_area.area_asset_id)


def decode(game_modifications: dict, configuration: LayoutConfiguration) -> GamePatches:
    """
    Decodes a dict created by `serialize` back into a GamePatches.
    :param game_modifications:
    :param configuration:
    :return:
    """
    game = data_reader.decode_data(configuration.game_data)
    world_list = game.world_list

    # Starting Location
    starting_location = _area_name_to_area_location(world_list, game_modifications["starting_location"])

    # Initial items
    extra_initial_items = tuple([
        (find_resource_info_with_long_name(game.resource_database.item, resource_name), quantity)
        for resource_name, quantity in game_modifications["starting_items"].items()
    ])

    # Elevators
    elevator_connection = {}
    for source_name, target_name in game_modifications["elevators"].items():
        source_area = _area_name_to_area_location(world_list, source_name)
        target_area = _area_name_to_area_location(world_list, target_name)

        elevator_connection[world_list.resolve_teleporter_connection(source_area).teleporter_instance_id] = target_area

    # Pickups
    pickup_assignment = {}

    return GamePatches(
        pickup_assignment=pickup_assignment,  # PickupAssignment
        elevator_connection=elevator_connection,  # Dict[int, AreaLocation]
        dock_connection={},  # Dict[Tuple[int, int], DockConnection]
        dock_weakness={},  # Dict[Tuple[int, int], DockWeakness]
        extra_initial_items=extra_initial_items,  # ResourceGainTuple
        starting_location=starting_location,  # AreaLocation
    )
