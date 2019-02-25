from typing import List, TypeVar, Callable, Dict, Tuple

from randovania.game_description.area import Area
from randovania.game_description.dock import DockWeaknessDatabase, DockWeakness
from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import Node, GenericNode, DockNode, PickupNode, TeleporterNode, EventNode
from randovania.game_description.requirements import RequirementSet, RequirementList, IndividualRequirement
from randovania.game_description.resources import ResourceGain, ResourceDatabase, SimpleResourceInfo, \
    DamageResourceInfo, ResourceInfo, ResourceGainTuple
from randovania.game_description.world import World
from randovania.game_description.world_list import WorldList


def write_individual_requirement(individual: IndividualRequirement) -> dict:
    return {
        "requirement_type": individual.resource.resource_type.value,
        "requirement_index": individual.resource.index,
        "amount": individual.amount,
        "negate": individual.negate
    }


def write_requirement_list(requirement_list: RequirementList) -> list:
    return [
        write_individual_requirement(individual)
        for individual in sorted(requirement_list.values())
    ]


def write_requirement_set(requirement_set: RequirementSet) -> list:
    return [
        write_requirement_list(l)
        for l in sorted(requirement_set.alternatives, key=lambda x: x.sorted)
    ]


# Resource

def write_resource_gain(resource_gain: ResourceGain) -> list:
    def sorter(item: Tuple[ResourceInfo, int]):
        return item[0].resource_type, item[0].index, item[1]

    return [
        {
            "resource_type": resource.resource_type.value,
            "resource_index": resource.index,
            "amount": gain,
        }
        for resource, gain in sorted(resource_gain, key=sorter)
    ]


def write_simple_resource(resource: SimpleResourceInfo) -> dict:
    return {
        "index": resource.index,
        "long_name": resource.long_name,
        "short_name": resource.short_name
    }


def write_damage_resource(resource: DamageResourceInfo) -> dict:
    return {
        "index": resource.index,
        "long_name": resource.long_name,
        "short_name": resource.short_name,
        "reductions": [
            {
                "index": reduction.inventory_item.index,
                "multiplier": reduction.damage_multiplier
            }
            for reduction in resource.reductions
        ]
    }


X = TypeVar('X')


def write_array(array: List[X], writer: Callable[[X], dict]) -> list:
    return [
        writer(item)
        for item in array
    ]


def write_resource_database(resource_database: ResourceDatabase):
    return {
        "items": write_array(resource_database.item, write_simple_resource),
        "events": write_array(resource_database.event, write_simple_resource),
        "tricks": write_array(resource_database.trick, write_simple_resource),
        "damage": write_array(resource_database.damage, write_damage_resource),
        "versions": write_array(resource_database.version, write_simple_resource),
        "misc": write_array(resource_database.misc, write_simple_resource),
        "difficulty": write_array(resource_database.difficulty, write_simple_resource),
    }


# Dock Weakness Database

def write_dock_weakness(dock_weakness: DockWeakness) -> dict:
    return {
        "index": dock_weakness.index,
        "name": dock_weakness.name,
        "is_blast_door": dock_weakness.is_blast_shield,
        "requirement_set": write_requirement_set(dock_weakness.requirements)
    }


def write_dock_weakness_database(database: DockWeaknessDatabase) -> dict:
    return {
        "door": [
            write_dock_weakness(weakness)
            for weakness in database.door
        ],
        "portal": [
            write_dock_weakness(weakness)
            for weakness in database.portal
        ],
    }


# World/Area/Nodes

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
        data["dock_type"] = node.default_dock_weakness.dock_type.value
        data["dock_weakness_index"] = node.default_dock_weakness.index

    elif isinstance(node, PickupNode):
        data["node_type"] = 2
        data["pickup_index"] = node.pickup_index.index

    elif isinstance(node, TeleporterNode):
        data["node_type"] = 3
        data["destination_world_asset_id"] = node.default_connection.world_asset_id
        data["destination_area_asset_id"] = node.default_connection.area_asset_id
        data["teleporter_instance_id"] = node.teleporter_instance_id

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
            target_node.name: write_requirement_set(requirements_set)
            for target_node, requirements_set in area.connections[node].items()
        }
        nodes.append(data)

    return {
        "name": area.name,
        "asset_id": area.area_asset_id,
        "default_node_index": area.default_node_index,
        "nodes": nodes
    }


def write_world(world: World) -> dict:
    return {
        "name": world.name,
        "asset_id": world.world_asset_id,
        "areas": [
            write_area(area)
            for area in world.areas
        ]
    }


def write_world_list(world_list: WorldList) -> list:
    return [
        write_world(world)
        for world in world_list.worlds
    ]


# Game Description

def write_initial_states(initial_states: Dict[str, ResourceGainTuple]) -> dict:
    return {
        name: write_resource_gain(initial_state)
        for name, initial_state in initial_states.items()
    }


def write_game_description(game: GameDescription) -> dict:
    if game.add_self_as_requirement_to_resources:
        raise ValueError("Attempting to encode a GameDescription's created with add_self_as_requirement_to_resources "
                         "is an invalid operation")
    return {
        "game": game.game,
        "game_name": game.game_name,
        "resource_database": write_resource_database(game.resource_database),

        "starting_location": game.starting_location.as_json,
        "initial_states": write_initial_states(game.initial_states),
        "victory_condition": write_requirement_set(game.victory_condition),

        "dock_weakness_database": write_dock_weakness_database(game.dock_weakness_database),
        "worlds": write_world_list(game.world_list),
    }
