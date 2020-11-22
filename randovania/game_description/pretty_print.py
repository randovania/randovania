from typing import Union, Iterator, Tuple, TextIO

from randovania.game_description.area import Area
from randovania.game_description.dock import DockType
from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import Node, DockNode, TeleporterNode, PickupNode, EventNode, TranslatorGateNode, \
    LogbookNode, LoreType, PlayerShipNode
from randovania.game_description.requirements import ResourceRequirement, RequirementAnd, RequirementOr, \
    RequirementTemplate, Requirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world_list import WorldList
from randovania.interface_common.enum_lib import iterate_enum
from randovania.layout.trick_level import LayoutTrickLevel


def pretty_print_resource_requirement(requirement: ResourceRequirement) -> str:
    if requirement.resource.resource_type == ResourceType.TRICK:
        return f"{requirement.resource} ({LayoutTrickLevel.from_number(requirement.amount).long_name})"
    else:
        return requirement.pretty_text


def pretty_print_requirement_array(requirement: Union[RequirementAnd, RequirementOr],
                                   level: int) -> Iterator[Tuple[int, str]]:
    if len(requirement.items) == 1:
        yield from pretty_print_requirement(requirement.items[0], level)
        return

    resource_requirements = [item for item in requirement.items if isinstance(item, ResourceRequirement)]
    template_requirements = [item for item in requirement.items if isinstance(item, RequirementTemplate)]
    other_requirements = [item for item in requirement.items if isinstance(item, (RequirementAnd, RequirementOr))]
    assert len(resource_requirements) + len(template_requirements) + len(other_requirements) == len(requirement.items)

    pretty_resources = [
        pretty_print_resource_requirement(item)
        for item in sorted(resource_requirements)
    ]
    sorted_templates = list(sorted(item.template_name for item in template_requirements))

    if isinstance(requirement, RequirementOr):
        title = "Any"
        combinator = " or "
    else:
        title = "All"
        combinator = " and "

    if len(other_requirements) == 0:
        yield level, combinator.join(pretty_resources + sorted_templates)
    else:
        yield level, f"{title} of the following:"
        if pretty_resources or sorted_templates:
            yield level + 1, combinator.join(pretty_resources + sorted_templates)
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

    elif isinstance(requirement, RequirementTemplate):
        yield level, requirement.template_name
    else:
        raise RuntimeError(f"Unknown requirement type: {type(requirement)} - {requirement}")


def pretty_print_node_type(node: Node, world_list: WorldList):
    if isinstance(node, DockNode):
        try:
            other = world_list.resolve_dock_connection(world_list.nodes_to_world(node), node.default_connection)
            other_name = world_list.node_name(other)
        except IndexError as e:
            other_name = (f"(Asset {node.default_connection.area_asset_id:x}, "
                          f"index {node.default_connection.dock_index}) [{e}]")

        return f"{node.default_dock_weakness.name} to {other_name}"

    elif isinstance(node, TeleporterNode):
        other = world_list.area_by_area_location(node.default_connection)
        return f"Teleporter to {world_list.area_name(other)}"

    elif isinstance(node, PickupNode):
        return f"Pickup {node.pickup_index.index}; Major Location? {node.major_location}"

    elif isinstance(node, EventNode):
        return f"Event {node.event.long_name}"

    elif isinstance(node, TranslatorGateNode):
        return f"Translator Gate ({node.gate})"

    elif isinstance(node, LogbookNode):
        message = ""
        if node.lore_type == LoreType.LUMINOTH_LORE:
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
    print_function("Asset id: {}".format(area.area_asset_id))
    for i, node in enumerate(area.nodes):
        message = f"> {node.name}; Heals? {node.heal}"
        if area.default_node_index == i:
            message += "; Spawn Point"
        print_function(message)

        description_line = pretty_print_node_type(node, game.world_list)
        if description_line:
            print_function(f"  * {description_line}")

        for target_node, requirement in game.world_list.area_connections_from(node):
            print_function("  > {}".format(target_node.name))
            for level, text in pretty_print_requirement(requirement.simplify()):
                print_function("      {}{}".format("    " * level, text))
        print_function()


def write_human_readable_world_list(game: GameDescription, output: TextIO) -> None:
    def print_to_file(*args):
        output.write("\t".join(str(arg) for arg in args) + "\n")

    output.write("====================\nTemplates\n")
    for template_name, template in game.resource_database.requirement_template.items():
        output.write(f"\n* {template_name}:\n")
        for level, text in pretty_print_requirement(template):
            output.write("      {}{}\n".format("    " * level, text))

    output.write("\n====================\nDock Weaknesses\n")
    for dock_type in iterate_enum(DockType):
        output.write(f"\n> {dock_type}")
        for weakness in game.dock_weakness_database.get_by_type(dock_type):
            output.write(f"\n  * ({weakness.index}) {weakness.name}; Blast Shield? {weakness.is_blast_shield}\n")
            for level, text in pretty_print_requirement(weakness.requirement):
                output.write("      {}{}\n".format("    " * level, text))

    output.write("\n")
    for world in game.world_list.worlds:
        output.write("====================\n{}\n".format(world.name))
        for area in world.areas:
            output.write("----------------\n")
            pretty_print_area(game, area, print_function=print_to_file)
