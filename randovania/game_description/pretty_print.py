from __future__ import annotations

import typing
from typing import TYPE_CHECKING, TextIO

from randovania.game_description.data_writer import REGION_NAME_TO_FILE_NAME_RE
from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.teleporter_network_node import TeleporterNetworkNode
from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.node_requirement import NodeRequirement
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.layout.base.trick_level import LayoutTrickLevel

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.hint_features import HintFeature
    from randovania.game_description.resources.resource_database import ResourceDatabase


def pretty_print_resource_requirement(requirement: ResourceRequirement) -> str:
    if requirement.resource.resource_type == ResourceType.TRICK:
        return f"{requirement.resource} ({LayoutTrickLevel.from_number(requirement.amount).long_name})"
    else:
        return requirement.pretty_text


def get_template_name(db: ResourceDatabase, requirement: RequirementTemplate) -> str:
    try:
        return db.requirement_template[requirement.template_name].display_name
    except KeyError:
        return f"Unknown Template ({requirement.template_name})"


def pretty_print_requirement_array(
    requirement: RequirementArrayBase, db: ResourceDatabase, level: int
) -> Iterator[tuple[int, str]]:
    if len(requirement.items) == 1 and requirement.comment is None:
        yield from pretty_format_requirement(requirement.items[0], db, level)
        return

    resource_requirements = [item for item in requirement.items if isinstance(item, ResourceRequirement)]
    node_requirements = [item for item in requirement.items if isinstance(item, NodeRequirement)]
    template_requirements = [item for item in requirement.items if isinstance(item, RequirementTemplate)]
    other_requirements = [item for item in requirement.items if isinstance(item, RequirementArrayBase)]
    assert (
        len(resource_requirements) + len(node_requirements) + len(template_requirements) + len(other_requirements)
    ) == len(requirement.items)

    pretty_resources = [pretty_print_resource_requirement(item) for item in sorted(resource_requirements)]
    pretty_resources.extend(requirement.node_identifier.as_string for requirement in node_requirements)
    sorted_templates = sorted(get_template_name(db, item) for item in template_requirements)

    if isinstance(requirement, RequirementOr):
        title = "Any"
    else:
        title = "All"

    if len(other_requirements) == 0:
        if requirement.comment is not None:
            yield level, f"# {requirement.comment}"
        yield level, requirement.combinator().join(pretty_resources + sorted_templates)
    else:
        yield level, f"{title} of the following:"
        if requirement.comment is not None:
            yield level + 1, f"# {requirement.comment}"
        if pretty_resources or sorted_templates:
            yield level + 1, requirement.combinator().join(pretty_resources + sorted_templates)
        for item in other_requirements:
            yield from pretty_format_requirement(item, db, level + 1)


def pretty_format_requirement(
    requirement: Requirement, db: ResourceDatabase, level: int = 0
) -> Iterator[tuple[int, str]]:
    if requirement == Requirement.impossible():
        yield level, "Impossible"

    elif requirement == Requirement.trivial():
        yield level, "Trivial"

    elif isinstance(requirement, RequirementArrayBase):
        yield from pretty_print_requirement_array(requirement, db, level)

    elif isinstance(requirement, ResourceRequirement):
        yield level, pretty_print_resource_requirement(requirement)

    elif isinstance(requirement, RequirementTemplate):
        yield level, get_template_name(db, requirement)

    elif isinstance(requirement, NodeRequirement):
        yield level, f"Collected {requirement.node_identifier.as_string}"
    else:
        raise RuntimeError(f"Unknown requirement type: {type(requirement)} - {requirement}")


def pretty_print_requirement(
    requirement: Requirement,
    db: ResourceDatabase,
    prefix: str = "",
    print_function: typing.Callable[[str], None] = print,
) -> None:
    for nested_level, text in pretty_format_requirement(requirement, db):
        print_function("{}{}{}".format(prefix, "    " * nested_level, text))


def pretty_print_node_type(node: Node, region_list: RegionList, db: ResourceDatabase) -> str:
    if isinstance(node, DockNode):
        try:
            other = region_list.node_by_identifier(node.default_connection)
            other_name = region_list.node_name(other)
        except IndexError as e:
            other_name = f"(Area {node.default_connection.area}, index {node.default_connection.node}) [{e}]"

        message = f"{node.default_dock_weakness.name} to {other_name}"

        if node.exclude_from_dock_rando:
            message += "; Excluded from Dock Lock Rando"
        elif node.incompatible_dock_weaknesses:
            message += "; Dock Lock Rando incompatible with: "
            message += ", ".join(weak.name for weak in node.incompatible_dock_weaknesses)

        if node.ui_custom_name is not None:
            message += f"; Custom name: {node.ui_custom_name}"

        return message

    elif isinstance(node, PickupNode):
        message = f"Pickup {node.pickup_index.index}; Category? {node.location_category.long_name}"
        if node.custom_index_group is not None:
            message += f"; Index Group: {node.custom_index_group}"
        return message

    elif isinstance(node, EventNode):
        return f"Event {node.event.long_name}"

    elif isinstance(node, ConfigurableNode):
        return "Configurable Node"

    elif isinstance(node, HintNode):
        return "Hint"

    elif isinstance(node, TeleporterNetworkNode):
        unlocked_pretty = list(pretty_format_requirement(node.is_unlocked, db))
        if len(unlocked_pretty) > 1:
            unlocked_by = "Complex requirement"
        else:
            unlocked_by = unlocked_pretty[0][1]
        return f"Teleporter Network (Unlocked by {unlocked_by})"

    return ""


def pretty_print_hint_features(features: Iterable[HintFeature]) -> str:
    return f"Hint Features - {', '.join([feature.long_name for feature in sorted(features)])}"


def pretty_print_area(game: GameDescription, area: Area, print_function: typing.Callable[[str], None] = print) -> None:
    print_function(area.name)
    for extra_name, extra_field in area.extra.items():
        print_function(f"Extra - {extra_name}: {extra_field}")

    if area.hint_features:
        print_function(pretty_print_hint_features(area.hint_features))

    for i, node in enumerate(area.nodes):
        if node.is_derived_node:
            continue

        message = f"> {node.name}; Heals? {node.heal}"
        if node.valid_starting_location:
            message += "; Spawn Point"
        if area.default_node == node.name:
            message += "; Default Node"
        print_function(message)
        print_function(f"  * Layers: {', '.join(node.layers)}")

        description_line = pretty_print_node_type(node, game.region_list, game.resource_database)
        if description_line:
            print_function(f"  * {description_line}")
        if isinstance(node, PickupNode) and node.hint_features:
            print_function(f"  * {pretty_print_hint_features(node.hint_features)}")
        if node.description:
            print_function(f"  * {node.description}")
        for extra_name, extra_field in node.extra.items():
            print_function(f"  * Extra - {extra_name}: {extra_field}")

        if isinstance(node, DockNode):
            for label, req in (
                ("open", node.override_default_open_requirement),
                ("lock", node.override_default_lock_requirement),
            ):
                if req is not None:
                    print_function(f"  * Override default {label} requirement:")
                    pretty_print_requirement(
                        req.simplify(keep_comments=True),
                        game.resource_database,
                        prefix="    ",
                        print_function=print_function,
                    )
                    print_function("")

        for target_node, requirement in game.region_list.area_connections_from(node):
            if target_node.is_derived_node:
                continue

            print_function(f"  > {target_node.name}")
            pretty_print_requirement(
                requirement.simplify(keep_comments=True),
                game.resource_database,
                prefix="      ",
                print_function=print_function,
            )
        print_function("")


def write_human_readable_meta(game: GameDescription, output: TextIO) -> None:
    output.write("====================\nTemplates\n")
    for template_name, template in game.resource_database.requirement_template.items():
        output.write(f"\n* {template.display_name}:\n")
        for level, text in pretty_format_requirement(template.requirement, game.resource_database):
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
            for level, text in pretty_format_requirement(weakness.requirement, game.resource_database, level=1):
                output.write("      {}{}\n".format("    " * level, text))

            if weakness.lock is not None:
                output.write(f"      Lock type: {weakness.lock}\n")
                for level, text in pretty_format_requirement(
                    weakness.lock.requirement, game.resource_database, level=1
                ):
                    output.write("      {}{}\n".format("    " * level, text))
            else:
                output.write("      No lock\n")
            output.write("\n")

        dock_rando = game.dock_weakness_database.dock_rando_params.get(dock_type)
        if dock_rando is None:
            output.write("  > Dock Rando: Disabled\n\n")
        else:
            output.write("  > Dock Rando:")

            output.write(f"\n      Unlocked: {dock_rando.unlocked.name}")
            output.write(f"\n      Locked: {dock_rando.locked.name}")

            output.write("\n      Change from:")
            for weakness in sorted(dock_rando.change_from):
                output.write(f"\n          {weakness.name}")

            output.write("\n      Change to:")
            for weakness in sorted(dock_rando.change_to):
                output.write(f"\n          {weakness.name}")

            output.write("\n\n")


def write_human_readable_region_list(game: GameDescription, output: TextIO) -> None:
    def print_to_file(*args: typing.Any) -> None:
        output.write("\t".join(str(arg) for arg in args) + "\n")

    output.write("\n")
    for region in game.region_list.regions:
        output.write(f"====================\n{region.name}\n")
        for area in region.areas:
            output.write("----------------\n")
            pretty_print_area(game, area, print_function=print_to_file)


def write_human_readable_game(game: GameDescription, base_path: Path) -> None:
    with base_path.joinpath("header.txt").open("w", encoding="utf-8") as meta:
        write_human_readable_meta(game, meta)

    for region in game.region_list.regions:
        name = REGION_NAME_TO_FILE_NAME_RE.sub(r"", region.name)
        with base_path.joinpath(f"{name}.txt").open("w", encoding="utf-8") as region_file:

            def print_to_file(*args: typing.Any) -> None:
                region_file.write("\t".join(str(arg) for arg in args) + "\n")

            for area in region.areas:
                region_file.write("----------------\n")
                pretty_print_area(game, area, print_function=print_to_file)
