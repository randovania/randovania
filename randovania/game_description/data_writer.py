from randovania.game_description.area import Area
from randovania.game_description.node import Node, GenericNode, DockNode, PickupNode, TeleporterNode, EventNode


def write_node(node: Node) -> dict:
    """
    :param node:
    :return:
    """

    data = {
        "name": node.name,
        "heal": node.heal
    }

    if isinstance(node, GenericNode):
        data["node_type"] = 0

    elif isinstance(node, DockNode):
        data["node_type"] = 1
        data["dock_index"] = node.dock_index
        data["connected_area_asset_id"] = node.default_connection.area_asset_id
        data["connected_dock_index"] = node.default_connection.dock_index
        data["dock_type"] = node.default_dock_weakness.dock_type
        data["dock_weakness_index"] = node.default_dock_weakness.index

    elif isinstance(node, PickupNode):
        data["node_type"] = 2
        data["pickup_index"] = node.pickup_index.index

    elif isinstance(node, TeleporterNode):
        data["node_type"] = 3
        data["teleporter_instance_id"] = node.teleporter_instance_id
        data["destination_world_asset_id"] = node.default_connection.world_asset_id
        data["destination_area_asset_id"] = node.default_connection.area_asset_id

    elif isinstance(node, EventNode):
        data["node_type"] = 4
        data["event_index"] = node.resource().index

    else:
        raise Exception("Unknown node class: {}".format(node))

    return data


def write_area(area: Area) -> dict:
    """
    :param area:
    :return:
    """
    nodes = []

    for node in area.nodes:
        data = write_node(node)
        data["connections"] = {
            target_node.name: requirements_set
            for target_node, requirements_set in area.connections[node].items()
        }
        nodes.append(data)

    return {
        "name": area.name,
        "assert_id": area.area_asset_id,
        "default_node_index": area.default_node_index,
        "nodes": nodes
    }

