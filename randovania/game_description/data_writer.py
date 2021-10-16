import copy
import json
import re
from pathlib import Path
from typing import List, TypeVar, Callable, Dict, Tuple, Iterator, Optional

from randovania.game_description.game_description import GameDescription, MinimalLogicData, IndexWithReason
from randovania.game_description.requirements import ResourceRequirement, \
    RequirementOr, RequirementAnd, Requirement, RequirementTemplate, RequirementArrayBase
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGainTuple, ResourceGain
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.game_description.world.area import Area
from randovania.game_description.world.dock import DockWeaknessDatabase, DockWeakness
from randovania.game_description.world.node import Node, GenericNode, DockNode, PickupNode, TeleporterNode, EventNode, \
    TranslatorGateNode, LogbookNode, LoreType, PlayerShipNode
from randovania.game_description.world.world import World
from randovania.game_description.world.world_list import WorldList


def write_resource_requirement(requirement: ResourceRequirement) -> dict:
    return {
        "type": "resource",
        "data": {
            "type": requirement.resource.resource_type.value,
            "index": requirement.resource.index,
            "amount": requirement.amount,
            "negate": requirement.negate,
        }
    }


def write_requirement_array(requirement: RequirementArrayBase, type_name: str) -> dict:
    return {
        "type": type_name,
        "data": {
            "comment": requirement.comment,
            "items": [
                write_requirement(item)
                for item in requirement.items
            ]
        }
    }


def write_requirement_template(requirement: RequirementTemplate) -> dict:
    return {
        "type": "template",
        "data": requirement.template_name
    }


def write_requirement(requirement: Requirement) -> dict:
    if isinstance(requirement, ResourceRequirement):
        return write_resource_requirement(requirement)

    elif isinstance(requirement, RequirementOr):
        return write_requirement_array(requirement, "or")

    elif isinstance(requirement, RequirementAnd):
        return write_requirement_array(requirement, "and")

    elif isinstance(requirement, RequirementTemplate):
        return write_requirement_template(requirement)

    else:
        raise ValueError(f"Unknown requirement type: {type(requirement)}")


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
        "short_name": resource.short_name,
    }


def write_item_resource(resource: ItemResourceInfo) -> dict:
    return {
        "index": resource.index,
        "long_name": resource.long_name,
        "short_name": resource.short_name,
        "max_capacity": resource.max_capacity,
        "extra": resource.extra,
    }


def write_trick_resource(resource: TrickResourceInfo) -> dict:
    return {
        "index": resource.index,
        "long_name": resource.long_name,
        "short_name": resource.short_name,
        "description": resource.description,
    }


X = TypeVar('X')


def write_array(array: List[X], writer: Callable[[X], dict]) -> list:
    return [
        writer(item)
        for item in array
    ]


def check_for_duplicated_index(array: List) -> Iterator[str]:
    indices_seen = set()
    for item in array:
        if item.index in indices_seen:
            yield f"Duplicated index {item.index} with {item.long_name}"
        else:
            indices_seen.add(item.index)


def write_resource_database(resource_database: ResourceDatabase):
    errors = []
    for array in (resource_database.item, resource_database.event, resource_database.trick, resource_database.damage,
                  resource_database.version, resource_database.misc):
        errors.extend(check_for_duplicated_index(array))

    if errors:
        raise ValueError("Errors in resource database: {}".format("\n".join(errors)))

    return {
        "items": write_array(resource_database.item, write_item_resource),
        "events": write_array(resource_database.event, write_simple_resource),
        "tricks": write_array(resource_database.trick, write_trick_resource),
        "damage": write_array(resource_database.damage, write_simple_resource),
        "versions": write_array(resource_database.version, write_simple_resource),
        "misc": write_array(resource_database.misc, write_simple_resource),
        "requirement_template": {
            name: write_requirement(requirement)
            for name, requirement in resource_database.requirement_template.items()
        },
        "damage_reductions": [
            {
                "index": resource.index,
                "reductions": [
                    {
                        "index": reduction.inventory_item.index if reduction.inventory_item is not None else None,
                        "multiplier": reduction.damage_multiplier
                    }
                    for reduction in reductions
                ]
            }
            for resource, reductions in resource_database.damage_reductions.items()
        ],
        "energy_tank_item_index": resource_database.energy_tank_item_index,
        "item_percentage_index": resource_database.item_percentage_index,
        "multiworld_magic_item_index": resource_database.multiworld_magic_item_index,
    }


# Dock Weakness Database

def write_dock_weakness(dock_weakness: DockWeakness) -> dict:
    return {
        "index": dock_weakness.index,
        "name": dock_weakness.name,
        "lock_type": dock_weakness.lock_type.value,
        "requirement": write_requirement(dock_weakness.requirement)
    }


def write_dock_weakness_database(database: DockWeaknessDatabase) -> dict:
    errors = []
    for array in (database.door, database.portal, database.morph_ball):
        errors.extend(check_for_duplicated_index(array))

    if errors:
        raise ValueError("Errors in dock weaknesses: {}".format("\n".join(errors)))

    return {
        "door": [
            write_dock_weakness(weakness)
            for weakness in database.door
        ],
        "portal": [
            write_dock_weakness(weakness)
            for weakness in database.portal
        ],
        "morph_ball": [
            write_dock_weakness(weakness)
            for weakness in database.morph_ball
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
        "heal": node.heal,
        "coordinates": {"x": node.location.x, "y": node.location.y, "z": node.location.z} if node.location else None,
    }

    if isinstance(node, GenericNode):
        data["node_type"] = "generic"

    elif isinstance(node, DockNode):
        data["node_type"] = "dock"
        data["dock_index"] = node.dock_index
        data["connected_area_asset_id"] = node.default_connection.area_asset_id
        data["connected_dock_index"] = node.default_connection.dock_index
        data["dock_type"] = node.default_dock_weakness.dock_type.value
        data["dock_weakness_index"] = node.default_dock_weakness.index

    elif isinstance(node, PickupNode):
        data["node_type"] = "pickup"
        data["pickup_index"] = node.pickup_index.index
        data["major_location"] = node.major_location

    elif isinstance(node, TeleporterNode):
        data["node_type"] = "teleporter"
        data["destination_world_asset_id"] = node.default_connection.world_asset_id
        data["destination_area_asset_id"] = node.default_connection.area_asset_id
        data["teleporter_instance_id"] = node.teleporter_instance_id
        data["scan_asset_id"] = node.scan_asset_id
        data["keep_name_when_vanilla"] = node.keep_name_when_vanilla
        data["editable"] = node.editable

    elif isinstance(node, EventNode):
        data["node_type"] = "event"
        data["event_index"] = node.resource().index
        if not node.name.startswith("Event -"):
            raise ValueError(f"'{node.name}' is an Event Node, but naming doesn't start with 'Event -'")

    elif isinstance(node, TranslatorGateNode):
        data["node_type"] = "translator_gate"
        data["gate_index"] = node.gate.index

    elif isinstance(node, LogbookNode):
        data["node_type"] = "logbook"
        data["string_asset_id"] = node.string_asset_id
        data["lore_type"] = node.lore_type.value

        if node.lore_type == LoreType.LUMINOTH_LORE:
            data["extra"] = node.required_translator.index

        elif node.lore_type in {LoreType.LUMINOTH_WARRIOR, LoreType.SKY_TEMPLE_KEY_HINT}:
            data["extra"] = node.hint_index
        else:
            data["extra"] = 0

    elif isinstance(node, PlayerShipNode):
        data["node_type"] = "player_ship"
        data["is_unlocked"] = write_requirement(node.is_unlocked)

    else:
        raise ValueError("Unknown node class: {}".format(node))

    if node.name.startswith("Event -") and data["node_type"] != "event":
        raise ValueError(f"'{node.name}' is not an Event Node, but naming suggests it is.")

    return data


def write_area(area: Area) -> dict:
    """
    :param area:
    :return:
    """
    errors = []

    nodes = []
    for node in area.nodes:
        try:
            data = write_node(node)
            data["connections"] = {
                target_node.name: write_requirement(area.connections[node][target_node])
                for target_node in area.nodes
                if target_node in area.connections[node]
            }
            nodes.append(data)
        except ValueError as e:
            errors.append(str(e))

    if errors:
        raise ValueError("Area {} nodes has the following errors:\n* {}".format(
            area.name, "\n* ".join(errors)))

    return {
        "name": area.name,
        "in_dark_aether": area.in_dark_aether,
        "asset_id": area.area_asset_id,
        "default_node_index": area.default_node_index,
        "valid_starting_location": area.valid_starting_location,
        "nodes": nodes
    }


def write_world(world: World) -> dict:
    errors = []
    areas = []
    for area in world.areas:
        try:
            areas.append(write_area(area))
        except ValueError as e:
            errors.append(str(e))

    if errors:
        raise ValueError("World {} has the following errors:\n> {}".format(
            world.name, "\n\n> ".join(errors)))

    return {
        "name": world.name,
        "dark_name": world.dark_name,
        "asset_id": world.world_asset_id,
        "areas": areas,
    }


def write_world_list(world_list: WorldList) -> list:
    errors = []

    known_indices = {}

    worlds = []
    for world in world_list.worlds:
        try:
            worlds.append(write_world(world))

            for node in world.all_nodes:
                if isinstance(node, PickupNode):
                    name = world_list.node_name(node, with_world=True, distinguish_dark_aether=True)
                    if node.pickup_index in known_indices:
                        errors.append(f"{name} has {node.pickup_index}, "
                                      f"but it was already used in {known_indices[node.pickup_index]}")
                    else:
                        known_indices[node.pickup_index] = name

        except ValueError as e:
            errors.append(str(e))

    if errors:
        raise ValueError("\n\n".join(errors))

    return worlds


# Game Description

def write_initial_states(initial_states: Dict[str, ResourceGainTuple]) -> dict:
    return {
        name: write_resource_gain(initial_state)
        for name, initial_state in initial_states.items()
    }


def write_minimal_logic_db(db: Optional[MinimalLogicData]) -> Optional[dict]:
    if db is None:
        return None

    def expand(it: IndexWithReason, field_name: str) -> dict:
        if it.reason is not None:
            return {"index": it.index, field_name: it.reason}
        else:
            return {"index": it.index}

    return {
        "items_to_exclude": [
            {"index": it.index, "when_shuffled": it.reason}
            for it in db.items_to_exclude
        ],
        "custom_item_amount": [
            {
                "index": index,
                "value": value
            }
            for index, value in db.custom_item_amount.items()
        ],
        "events_to_exclude": [
            {"index": it.index, "reason": it.reason}
            for it in db.events_to_exclude
        ]
    }


def write_game_description(game: GameDescription) -> dict:
    return {
        "game": game.game.value,
        "resource_database": write_resource_database(game.resource_database),

        "starting_location": game.starting_location.as_json,
        "initial_states": write_initial_states(game.initial_states),
        "minimal_logic": write_minimal_logic_db(game.minimal_logic),
        "victory_condition": write_requirement(game.victory_condition),

        "dock_weakness_database": write_dock_weakness_database(game.dock_weakness_database),
        "worlds": write_world_list(game.world_list),
    }


def write_as_split_files(data: dict, base_path: Path):
    data = copy.copy(data)
    worlds = data.pop("worlds")
    data["worlds"] = []

    for world in worlds:
        name = re.sub(r'[^a-zA-Z\- ]', r'', world["name"])
        data["worlds"].append(f"{name}.json")
        with base_path.joinpath(f"{name}.json").open("w", encoding="utf-8") as world_file:
            json.dump(world, world_file, indent=4)

    with base_path.joinpath(f"header.json").open("w", encoding="utf-8") as meta:
        json.dump(data, meta, indent=4)
