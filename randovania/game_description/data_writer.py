from typing import List, TypeVar, Callable, Dict, Tuple, TextIO, Union, Iterator

from randovania.game_description.area import Area
from randovania.game_description.dock import DockWeaknessDatabase, DockWeakness
from randovania.game_description.game_description import GameDescription
from randovania.game_description.echoes_game_specific import EchoesBeamConfiguration, EchoesGameSpecific
from randovania.game_description.node import Node, GenericNode, DockNode, PickupNode, TeleporterNode, EventNode, \
    TranslatorGateNode, LogbookNode, LoreType
from randovania.game_description.requirements import ResourceRequirement, \
    RequirementOr, RequirementAnd, Requirement
from randovania.game_description.resources.damage_resource_info import DamageResourceInfo
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGainTuple, ResourceGain
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.world import World
from randovania.game_description.world_list import WorldList
from randovania.layout.trick_level import LayoutTrickLevel


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


def write_requirement_and(requirement: RequirementAnd) -> dict:
    return {
        "type": "and",
        "data": [
            write_requirement(item)
            for item in requirement.items
        ]
    }


def write_requirement_or(requirement: RequirementOr) -> dict:
    return {
        "type": "or",
        "data": [
            write_requirement(item)
            for item in requirement.items
        ]
    }


def write_requirement(requirement: Requirement) -> dict:
    if isinstance(requirement, ResourceRequirement):
        return write_resource_requirement(requirement)

    elif isinstance(requirement, RequirementOr):
        return write_requirement_or(requirement)

    elif isinstance(requirement, RequirementAnd):
        return write_requirement_and(requirement)

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
        "requirement": write_requirement(dock_weakness.requirement)
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


# Game Specific

def write_echoes_beam_configuration(beam_config: EchoesBeamConfiguration) -> dict:
    return {
        "item_index": beam_config.item.index,
        "ammo_a": beam_config.ammo_a.index if beam_config.ammo_a is not None else None,
        "ammo_b": beam_config.ammo_b.index if beam_config.ammo_b is not None else None,
        "uncharged_cost": beam_config.uncharged_cost,
        "charged_cost": beam_config.charged_cost,
        "combo_missile_cost": beam_config.combo_missile_cost,
        "combo_ammo_cost": beam_config.combo_ammo_cost,
    }


def write_game_specific(game_specific: EchoesGameSpecific) -> dict:
    return {
        "energy_per_tank": game_specific.energy_per_tank,
        "beam_configurations": [
            write_echoes_beam_configuration(beam)
            for beam in game_specific.beam_configurations
        ]
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
            target_node.name: write_requirement(area.connections[node][target_node])
            for target_node in area.nodes
            if target_node in area.connections[node]
        }
        nodes.append(data)

    return {
        "name": area.name,
        "in_dark_aether": area.in_dark_aether,
        "asset_id": area.area_asset_id,
        "default_node_index": area.default_node_index,
        "nodes": nodes
    }


def write_world(world: World) -> dict:
    return {
        "name": world.name,
        "dark_name": world.dark_name,
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
    return {
        "game": game.game,
        "game_name": game.game_name,
        "resource_database": write_resource_database(game.resource_database),

        "game_specific": write_game_specific(game.game_specific),
        "starting_location": game.starting_location.as_json,
        "initial_states": write_initial_states(game.initial_states),
        "victory_condition": write_requirement(game.victory_condition),

        "dock_weakness_database": write_dock_weakness_database(game.dock_weakness_database),
        "worlds": write_world_list(game.world_list),
    }


def pretty_print_resource_requirement(requirement: ResourceRequirement) -> str:
    if requirement.resource.resource_type == ResourceType.TRICK:
        return f"{requirement.resource} ({LayoutTrickLevel.from_number(requirement.amount).long_name})"
    elif requirement.resource.resource_type == ResourceType.DIFFICULTY:
        trick_level = LayoutTrickLevel.from_number(requirement.amount)
        return f"Difficulty: {trick_level.long_name}"
    else:
        return requirement.pretty_text


def pretty_print_requirement_array(requirement: Union[RequirementAnd, RequirementOr],
                                   level: int) -> Iterator[Tuple[int, str]]:
    if len(requirement.items) == 1:
        yield from pretty_print_requirement(requirement.items[0], level)
        return

    resource_requirements = [item for item in requirement.items
                             if isinstance(item, ResourceRequirement)]
    other_requirements = [item for item in requirement.items
                          if not isinstance(item, ResourceRequirement)]
    pretty_resources = [
        pretty_print_resource_requirement(item)
        for item in sorted(resource_requirements)
    ]

    if isinstance(requirement, RequirementOr):
        title = "Any"
        combinator = " or "
    else:
        title = "All"
        combinator = " and "

    if len(other_requirements) == 0:
        yield level, combinator.join(pretty_resources)
    else:
        yield level, f"{title} of the following:"
        if pretty_resources:
            yield level + 1, combinator.join(pretty_resources)
        for item in other_requirements:
            yield from pretty_print_requirement(item, level + 1)


def pretty_print_requirement(requirement: Requirement, level: int = 0) -> Iterator[Tuple[int, str]]:
    if requirement == Requirement.impossible():
        yield level, "Impossible"

    elif requirement == Requirement.trivial():
        yield level, "Trivial"

    elif isinstance(requirement, (RequirementAnd, RequirementOr)):
        yield from pretty_print_requirement_array(requirement, level)

    elif isinstance(requirement, ResourceRequirement):
        yield level, pretty_print_resource_requirement(requirement)
    else:
        raise RuntimeError(f"Unknown requirement type: {type(requirement)} - {requirement}")


def pretty_print_area(game: GameDescription, area: Area, print_function=print):
    print_function(area.name)
    print_function("Asset id: {}".format(area.area_asset_id))
    for node in area.nodes:
        print_function(f"> {node.name}; Heals? {node.heal}")
        for target_node, requirement in game.world_list.potential_nodes_from(node, game.create_game_patches()):
            if target_node is None:
                print_function("  > None?")
            else:
                print_function("  > {}".format(game.world_list.node_name(target_node)))
                for level, text in pretty_print_requirement(requirement.simplify()):
                    print_function("      {}{}".format("    " * level, text))
        print_function()


def write_human_readable_world_list(game: GameDescription, output: TextIO) -> None:
    def print_to_file(*args):
        output.write("\t".join(str(arg) for arg in args) + "\n")

    for world in game.world_list.worlds:
        output.write("====================\n{}\n".format(world.name))
        for area in world.areas:
            output.write("----------------\n")
            pretty_print_area(game, area, print_function=print_to_file)
