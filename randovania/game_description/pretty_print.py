import re
from pathlib import Path
from typing import Iterator, TextIO

from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.area import Area
from randovania.game_description.world.configurable_node import ConfigurableNode
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.event_node import EventNode
from randovania.game_description.world.logbook_node import LoreType, LogbookNode
from randovania.game_description.world.node import (
    Node
)
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.player_ship_node import PlayerShipNode
from randovania.game_description.world.teleporter_node import TeleporterNode
from randovania.game_description.world.world_list import WorldList
from randovania.layout.base.trick_level import LayoutTrickLevel


def pretty_print_resource_requirement(requirement: ResourceRequirement) -> str:
    if requirement.resource.resource_type == ResourceType.TRICK:
        return f"{requirement.resource} ({LayoutTrickLevel.from_number(requirement.amount).long_name})"
    else:
        return requirement.pretty_text


def pretty_print_requirement_array(requirement: RequirementArrayBase,
                                   level: int) -> Iterator[tuple[int, str]]:
    if len(requirement.items) == 1 and requirement.comment is None:
        yield from pretty_print_requirement(requirement.items[0], level)
        return

    resource_requirements = [item for item in requirement.items if isinstance(item, ResourceRequirement)]
    template_requirements = [item for item in requirement.items if isinstance(item, RequirementTemplate)]
    other_requirements = [item for item in requirement.items if isinstance(item, RequirementArrayBase)]
    assert len(resource_requirements) + len(template_requirements) + len(other_requirements) == len(requirement.items)

    pretty_resources = [
        pretty_print_resource_requirement(item)
        for item in sorted(resource_requirements)
    ]
    sorted_templates = list(sorted(item.template_name for item in template_requirements))

    if isinstance(requirement, RequirementOr):
        title = "Any"
    else:
        title = "All"

    if len(other_requirements) == 0 and requirement.comment is None:
        yield level, requirement.combinator().join(pretty_resources + sorted_templates)
    else:
        yield level, f"{title} of the following:"
        if requirement.comment is not None:
            yield level + 1, f"# {requirement.comment}"
        if pretty_resources or sorted_templates:
            yield level + 1, requirement.combinator().join(pretty_resources + sorted_templates)
        for item in other_requirements:
            yield from pretty_print_requirement(item, level + 1)


def pretty_print_requirement(requirement: Requirement, level: int = 0) -> Iterator[tuple[int, str]]:
    if requirement == Requirement.impossible():
        yield level, "Impossible"

    elif requirement == Requirement.trivial():
        yield level, "Trivial"

    elif isinstance(requirement, RequirementArrayBase):
        yield from pretty_print_requirement_array(requirement, level)

    elif isinstance(requirement, ResourceRequirement):
        yield level, pretty_print_resource_requirement(requirement)

    elif isinstance(requirement, RequirementTemplate):
        yield level, requirement.template_name
    else:
        raise RuntimeError(f"Unknown requirement type: {type(requirement)} - {requirement}")


def pretty_print_node_type(node: Node, world_list: WorldList):
    if isinstance(node, DockNode):
        try:
            other = world_list.node_by_identifier(node.default_connection)
            other_name = world_list.node_name(other)
        except IndexError as e:
            other_name = (f"(Area {node.default_connection.area_name}, "
                          f"index {node.default_connection.node_name}) [{e}]")

        return f"{node.default_dock_weakness.name} to {other_name}"

    elif isinstance(node, TeleporterNode):
        other = world_list.area_by_area_location(node.default_connection)
        return f"Teleporter to {world_list.area_name(other)}"

    elif isinstance(node, PickupNode):
        return f"Pickup {node.pickup_index.index}; Major Location? {node.major_location}"

    elif isinstance(node, EventNode):
        return f"Event {node.event.long_name}"

    elif isinstance(node, ConfigurableNode):
        return f"Configurable Node"

    elif isinstance(node, LogbookNode):
        message = ""
        if node.lore_type == LoreType.REQUIRES_ITEM:
            message = f" ({node.required_translator.long_name})"
        return f"Logbook {node.lore_type.long_name}{message} for {node.string_asset_id:x}"

    elif isinstance(node, PlayerShipNode):
        unlocked_pretty = list(pretty_print_requirement(node.is_unlocked))
        if len(unlocked_pretty) > 1:
            unlocked_by = "Complex requirement"
        else:
            unlocked_by = unlocked_pretty[0][1]
        return f"Player Ship (Unlocked by {unlocked_by})"

    return ""


def pretty_print_area(game: GameDescription, area: Area, print_function=print):
    print_function(area.name)
    if area.valid_starting_location:
        print_function("(Valid Starting Location)")
    for extra_name, extra_field in area.extra.items():
        print_function(f"Extra - {extra_name}: {extra_field}")

    for i, node in enumerate(area.nodes):
        if node.is_derived_node:
            continue

        message = f"> {node.name}; Heals? {node.heal}"
        if area.default_node == node.name:
            message += "; Spawn Point"
        print_function(message)
        print_function(f"  * Layers: {', '.join(node.layers)}")

        description_line = pretty_print_node_type(node, game.world_list)
        if description_line:
            print_function(f"  * {description_line}")
        if node.description:
            print_function(f"  * {node.description}")
        for extra_name, extra_field in node.extra.items():
            print_function(f"  * Extra - {extra_name}: {extra_field}")

        for target_node, requirement in game.world_list.area_connections_from(node):
            if target_node.is_derived_node:
                continue

            print_function(f"  > {target_node.name}")
            for level, text in pretty_print_requirement(requirement.simplify(keep_comments=True)):
                print_function("      {}{}".format("    " * level, text))
        print_function()


def write_human_readable_meta(game: GameDescription, output: TextIO) -> None:
    output.write("====================\nTemplates\n")
    for template_name, template in game.resource_database.requirement_template.items():
        output.write(f"\n* {template_name}:\n")
        for level, text in pretty_print_requirement(template):
            output.write("      {}{}\n".format("    " * level, text))

    output.write("\n====================\nDock Weaknesses\n")
    for dock_type in game.dock_weakness_database.dock_types:
        output.write(f"\n> {dock_type.long_name}")
        for extra_name, extra_field in dock_type.extra.items():
            output.write(f"\n* Extra - {extra_name}: {extra_field}")

        for weakness in game.dock_weakness_database.get_by_type(dock_type):
            output.write(f"\n  * {weakness.name}\n")
            for extra_name, extra_field in weakness.extra.items():
                output.write(f"      Extra - {extra_name}: {extra_field}\n")

            output.write("      Open:\n")
            for level, text in pretty_print_requirement(weakness.requirement, level=1):
                output.write("      {}{}\n".format("    " * level, text))

            if weakness.lock is not None:
                output.write(f"      Lock type: {weakness.lock}\n")
                for level, text in pretty_print_requirement(weakness.lock.requirement, level=1):
                    output.write("      {}{}\n".format("    " * level, text))
            else:
                output.write("      No lock\n")
            output.write("\n")

        dock_rando = game.dock_weakness_database.dock_rando_params[dock_type]
        if dock_rando.locked is None or dock_rando.unlocked is None:
            output.write("  > Dock Rando: Disabled\n\n")
        else:
            output.write("  > Dock Rando:")

            output.write(f"\n      Unlocked: {dock_rando.unlocked.name}")
            output.write(f"\n      Locked: {dock_rando.locked.name}")

            output.write(f"\n      Change from:")
            for weakness in sorted(dock_rando.change_from):
                output.write(f"\n          {weakness.name}")

            output.write(f"\n      Change to:")
            for weakness in sorted(dock_rando.change_to):
                output.write(f"\n          {weakness.name}")

            output.write("\n\n")


def write_human_readable_world_list(game: GameDescription, output: TextIO) -> None:
    def print_to_file(*args):
        output.write("\t".join(str(arg) for arg in args) + "\n")

    output.write("\n")
    for world in game.world_list.worlds:
        output.write(f"====================\n{world.name}\n")
        for area in world.areas:
            output.write("----------------\n")
            pretty_print_area(game, area, print_function=print_to_file)


def write_human_readable_game(game: GameDescription, base_path: Path):
    with base_path.joinpath(f"header.txt").open("w", encoding="utf-8") as meta:
        write_human_readable_meta(game, meta)

    for world in game.world_list.worlds:
        name = re.sub(r'[^a-zA-Z\- ]', r'', world.name)
        with base_path.joinpath(f"{name}.txt").open("w", encoding="utf-8") as world_file:
            def print_to_file(*args):
                world_file.write("\t".join(str(arg) for arg in args) + "\n")

            for area in world.areas:
                world_file.write("----------------\n")
                pretty_print_area(game, area, print_function=print_to_file)
