from __future__ import annotations

import argparse
import logging
import typing
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from randovania.game_description import default_database
from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.search import MissingResource, find_resource_info_with_long_name
from randovania.games import binary_data, default_data
from randovania.games.game import RandovaniaGame
from randovania.lib import json_lib
from randovania.lib.enum_lib import iterate_enum

if typing.TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.resource_info import ResourceInfo


def _get_sorted_list_of_names(input_list: list[Any], prefix: str = "") -> list[str]:
    for item in sorted(input_list, key=lambda x: x.name):
        yield prefix + item.name


def decode_data_file(args) -> dict:
    json_database: Path | None = args.json_database
    if json_database is not None:
        return json_lib.read_path(json_database)
    else:
        return default_data.read_json_then_binary(RandovaniaGame(args.game))[1]


def export_as_binary(data: dict, output_binary: Path):
    with output_binary.open("wb") as x:
        binary_data.encode(data, x)


def convert_database_command_logic(args):
    from randovania.game_description import data_reader, data_writer
    data = decode_data_file(args)

    if args.decode_to_game_description:
        data = data_writer.write_game_description(data_reader.decode_data(data))

    output_binary: Path | None = args.output_binary
    output_json: Path | None = args.output_json

    if output_binary is not None:
        export_as_binary(data, output_binary)

    elif output_json is not None:
        json_lib.write_path(output_json, data)
    else:
        raise ValueError("Neither binary nor JSON set. Argparse is broken?")


def create_convert_database_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "convert-database",
        help="Converts a database file between JSON and binary encoded formats. Input defaults to embedded database.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    parser.add_argument(
        "--decode-to-game-description",
        action="store_true",
        default=False,
        help="Decodes the input data to a GameDescription, then encodes it back."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--output-binary",
        type=Path,
        help="Export as a binary file.",
    )
    group.add_argument(
        "--output-json",
        type=Path,
        help="Export as a JSON file.",
    )

    parser.set_defaults(func=convert_database_command_logic)


def export_videos_command_logic(args):
    from randovania.cli.commands.export_db_videos import export_videos
    games = []

    if args.game is not None:
        games.append(RandovaniaGame(args.game))
    else:
        games = list(RandovaniaGame)

    for game in games:
        export_videos(game, args.output_dir)


def create_export_videos_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "export-videos",
        help="Create HTML pages for easy vewing of YouTube video comments.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default="exported_videos",
        help="Folder to write html file to.",
    )
    parser.add_argument(
        "--game",
        type=str,
        default=None,
        help="Game to export videos for.",
    )
    parser.set_defaults(func=export_videos_command_logic)


def view_area_command_logic(args):
    from randovania.game_description import pretty_print
    game = load_game_description(args)
    region_list = game.region_list

    try:
        region = region_list.region_with_name(args.region)

    except KeyError:
        options = "\n".join(_get_sorted_list_of_names(region_list.regions, " "))
        print(f"Unknown region named '{args.region}'. Options:\n{options}")
        raise SystemExit(1)

    try:
        area = region.area_by_name(args.area)

    except KeyError:
        options = "\n".join(_get_sorted_list_of_names(region.areas, " "))
        print(f"Unknown area named '{args.area}' in region {region}. Options:\n{options}")
        raise SystemExit(1)

    pretty_print.pretty_print_area(game, area)


def load_game_description(args):
    from randovania.game_description import data_reader

    data = decode_data_file(args)
    gd = data_reader.decode_data(data)
    return gd


def view_area_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "view-area",
        help="View information about an area.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    parser.add_argument(
        "--simplify",
        action="store_true",
        help="Simplify the RequirementSets"
    )
    parser.add_argument(
        "region",
        type=str,
        help="The name of the region that contains the area."
    )
    parser.add_argument(
        "area",
        type=str,
        help="The name of the area."
    )

    parser.set_defaults(func=view_area_command_logic)


def update_human_readable_logic(args):
    from randovania.game_description import data_reader, pretty_print
    game = RandovaniaGame(args.game)

    path, data = default_data.read_json_then_binary(game)
    gd = data_reader.decode_data(data)

    path.with_suffix("").mkdir(parents=True, exist_ok=True)
    pretty_print.write_human_readable_game(gd, path.with_suffix(""))


def update_human_readable(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "update-human-readable",
        help="Update the human readable versions",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    parser.set_defaults(func=update_human_readable_logic)


def write_game_descriptions(game_descriptions: dict[RandovaniaGame, GameDescription]):
    from randovania.game_description import data_writer, pretty_print

    for game, gd in game_descriptions.items():
        logging.info("Writing %s", game.long_name)
        new_data = data_writer.write_game_description(gd)

        path = game.data_path.joinpath("json_data")
        data_writer.write_as_split_files(new_data, path)
        pretty_print.write_human_readable_game(gd, path)


def refresh_game_description_logic(args):
    from randovania.game_description import integrity_check

    gd_per_game = {}

    for game in RandovaniaGame.all_games():
        logging.info("Reading %s", game.long_name)
        gd_per_game[game] = default_database.game_description_for(game)

    should_stop = False
    if args.integrity_check:
        for game, gd in gd_per_game.items():
            errors = integrity_check.find_database_errors(gd)
            if errors:
                logging.warning("Integrity errors for %s:\n%s", game.long_name,
                                "\n".join(errors))
                if game.data.development_state.is_stable:
                    should_stop = True

    if not should_stop:
        write_game_descriptions(gd_per_game)


def refresh_game_description_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "refresh-game-description",
        help="Re-exports the json and txt files of all game descriptions",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.add_argument(
        "--integrity-check",
        help="Runs the integrity check on all games, refusing to continue if a non-experimental game has issues.",
        action="store_true",
    )
    parser.set_defaults(func=refresh_game_description_logic)


def refresh_pickup_database_logic(args):
    for game in iterate_enum(RandovaniaGame):
        logging.info("Updating %s", game.long_name)
        pdb = default_database.pickup_database_for_game(game)
        default_database.write_pickup_database_for_game(pdb, game)


def refresh_pickup_database_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "refresh-pickup-database",
        help="Re-exports the json of all pickup databases",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.set_defaults(func=refresh_pickup_database_logic)


def _list_paths_with_resource(game,
                              print_only_area: bool,
                              resource: ResourceInfo,
                              needed_quantity: int | None):
    from randovania.game_description.game_description import GameDescription

    count = 0
    game = typing.cast(GameDescription, game)

    for area in game.region_list.all_areas:
        area_had_resource = False

        for source, connection in area.connections.items():
            for target, requirement in connection.items():
                for alternative in requirement.as_set(game.resource_database).alternatives:
                    individual = alternative.get(resource)
                    if individual is None:
                        continue

                    if needed_quantity is None or needed_quantity == individual.amount:
                        area_had_resource = True
                        if not print_only_area:
                            print("At {}, from {} to {}:\n{}\n".format(
                                game.region_list.area_name(area),
                                source.name,
                                target.name,
                                sorted(individual for individual in alternative.values()
                                       if individual.resource != resource)
                            ))
                        count += 1

        if area_had_resource and print_only_area:
            print(game.region_list.area_name(area))

    print(f"Total routes: {count}")


def list_paths_with_dangerous_logic(args):
    game = load_game_description(args)
    print_only_area = args.print_only_area
    count = 0

    for area in game.region_list.all_areas:
        area_had_resource = False

        for source, connection in area.connections.items():
            for target, requirement in connection.items():
                for alternative in requirement.as_set(game.resource_database).alternatives:
                    for individual in alternative.values():
                        if individual.negate:
                            area_had_resource = True
                            if not print_only_area:
                                print("At {}, from {} to {}:\n{}\n".format(
                                    game.region_list.area_name(area),
                                    area,
                                    source.name,
                                    sorted(individual for individual in alternative.values()),
                                ))
                            count += 1

        if area_had_resource and print_only_area:
            print(game.region_list.area_name(area))

    print(f"Total routes: {count}")


def list_paths_with_dangerous_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "list-dangerous-usage",
        help="List all connections that needs a resource to be missing.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    parser.add_argument("--print-only-area", help="Only print the area names, not each specific path",
                        action="store_true")
    parser.set_defaults(func=list_paths_with_dangerous_logic)


def list_paths_with_resource_logic(args):
    gd = load_game_description(args)
    resource_name: str = args.resource

    resource = None
    for resource_type in gd.resource_database:
        try:
            resource = find_resource_info_with_long_name(resource_type, resource_name)
            break
        except MissingResource:
            continue

    if resource is None:
        print(f"A resource named {resource_name} was not found.")
        raise SystemExit(1)

    _list_paths_with_resource(
        gd,
        args.print_only_area,
        resource,
        None
    )


def list_paths_with_resource_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "list-resource-usage",
        help="List all connections that needs the resource.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    parser.add_argument("--print-only-area", help="Only print the area names, not each specific path",
                        action="store_true")
    parser.add_argument("resource", type=str)
    parser.set_defaults(func=list_paths_with_resource_logic)


def render_region_graph_logic(args):
    import hashlib
    import re

    import graphviz

    from randovania.game_description.db.dock_node import DockNode
    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.requirements.base import Requirement

    gd = load_game_description(args)

    regions = list(gd.region_list.regions)

    single_image: bool = args.single_image
    added_edges = set()
    vulnerabilities_colors = {
        "Normal Door": None,
        "Morph Ball Door": None,
        "Other Door": None,
        "Scan Portal": None,

        "Missile": "#ff1919",
        "Super Missile": "#38c914",
        "Seeker Launcher": "#b233e8",
        "Power Bomb": "#dfe833",

        "Wave Door": "#a30af5",
        "Ice Door": "#7cdede",
        "Plasma Door": "#870f0f",

        "Light Door": "#bfd9d9",
        "Dark Door": "#3b3647",
        "Annihilator Door": "#616969",
        "Light Portal": "#bfd9d9",
        "Dark Portal": "#3b3647",
    }

    def _weakness_name(s: str):
        return re.sub(r"\([^)]*\)", "", s).replace(" Blast Shield", "").strip()

    def _hash_to_color(s: str) -> str:
        h = hashlib.blake2b(s.encode("utf-8"), digest_size=3).digest()
        return "#{:06x}".format(int.from_bytes(h, "big"))

    def _add_connection(dot: graphviz.Digraph, dock_node: DockNode):
        the_region = gd.region_list.nodes_to_region(dock_node)
        source_area = gd.region_list.nodes_to_area(dock_node)
        target_node = gd.region_list.node_by_identifier(dock_node.default_connection)
        target_area = gd.region_list.nodes_to_area(target_node)

        if dock_node.default_dock_weakness.requirement == Requirement.impossible():
            return

        if dock_node.identifier in added_edges:
            return

        weak_name = _weakness_name(dock_node.default_dock_weakness.name)
        direction = None
        if isinstance(target_node, DockNode) and _weakness_name(target_node.default_dock_weakness.name) == weak_name:
            direction = "both"
            added_edges.add(target_node.identifier)

        color = vulnerabilities_colors.get(weak_name, _hash_to_color(weak_name))
        dot.edge(
            f"{the_region.name}-{source_area.name}",
            f"{the_region.name}-{target_area.name}",
            weak_name, dir=direction, color=color, fontcolor=color,
        )
        added_edges.add(dock_node.identifier)

    def _add_teleporter(dot: graphviz.Digraph, teleporter_node: DockNode):
        source_region = gd.region_list.nodes_to_region(teleporter_node)
        source_area = gd.region_list.nodes_to_area(teleporter_node)
        target_node = gd.region_list.node_by_identifier(teleporter_node.default_connection)
        target_region = gd.region_list.nodes_to_region(target_node)
        target_area = gd.region_list.nodes_to_area(target_node)
        weak_name = _weakness_name(teleporter_node.default_dock_weakness.name)
        color = vulnerabilities_colors.get(weak_name, _hash_to_color(weak_name))

        dot.edge(
            f"{source_region.name}-{source_area.name}",
            f"{target_region.name}-{target_area.name}",
            weak_name, color=color, fontcolor=color,
        )

    def _cross_region_dock(node: DockNode):
        return node.default_connection.region_name != node.identifier.region_name

    per_game_colors = {
        RandovaniaGame.METROID_PRIME_ECHOES: {
            "Agon Wastes": "#ffc61c",
            "Torvus Bog": "#20ff1c",
            "Sanctuary Fortress": "#3d62ff",
            "Temple Grounds": "#c917ff",
            "Great Temple": "#c917ff",
        },
    }
    colors = per_game_colors.get(gd.game)
    if colors is None:
        colors = {
            region.name: _hash_to_color(region.name)
            for region in gd.region_list.regions
        }

    dark_colors = {
        "Agon Wastes": "#a88332",
        "Torvus Bog": "#149612",
        "Sanctuary Fortress": "#112991",
        "Temple Grounds": "#7d2996",
        "Great Temple": "#7d2996",
    }

    if single_image:
        full_dot = graphviz.Digraph(name=gd.game.short_name,
                                    comment=gd.game.long_name)
    else:
        full_dot = None
    per_region_dot = {}

    for region in regions:
        if single_image:
            this_dot = full_dot
        else:
            this_dot = graphviz.Digraph(name=region.name)

        per_region_dot[region.name] = this_dot

        for area in region.areas:
            shape = None
            if any(isinstance(node, DockNode) and _cross_region_dock(node)
                   for node in area.nodes):
                shape = "polygon"

            c = (dark_colors if area.in_dark_aether else colors)[region.name]
            fillcolor = "".join(f"{max(0, int(c[i * 2 + 1:i * 2 + 3], 16) - 64):02x}"
                                for i in range(3))
            this_dot.node(
                f"{region.name}-{area.name}", area.name,
                color=c,
                fillcolor=f"#{fillcolor}",
                style="filled",
                fontcolor="#ffffff",
                shape=shape,
                penwidth="3.0",
            )

            for node in area.nodes:
                if args.include_pickups and isinstance(node, PickupNode):
                    this_dot.node(str(node.pickup_index), re.search(r"Pickup [^(]*\(([^)]+)\)", node.name).group(1),
                                  shape="house")
                    this_dot.edge(f"{region.name}-{area.name}", str(node.pickup_index))

    for region in regions:
        print(f"Adding docks for {region.name}")
        for area in region.areas:
            for node in area.nodes:
                if isinstance(node, DockNode) and not _cross_region_dock(node):
                    _add_connection(per_region_dot[region.name], node)
                elif isinstance(node, DockNode) and _cross_region_dock(node) and args.include_teleporters:
                    _add_teleporter(per_region_dot[region.name], node)

    if single_image:
        full_dot.render(format="png", view=True, cleanup=True)
    else:
        for name, this_dot in per_region_dot.items():
            this_dot.render(format="png", view=True, cleanup=True)


def render_regions_graph(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "render-region-graph",
        help="Renders an image with all area connections",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    parser.add_argument("--include-teleporters", action="store_true")
    parser.add_argument("--include-pickups", action="store_true")
    parser.add_argument("--single-image", action="store_true")

    parser.set_defaults(func=render_region_graph_logic)


def pickups_per_area_command_logic(args):
    from randovania.game_description.db.pickup_node import PickupNode
    gd = load_game_description(args)

    for region in gd.region_list.regions:
        num_pickups = sum(1 for node in region.all_nodes if isinstance(node, PickupNode))
        print(f"{region.correct_name(False)}: {num_pickups}")


def pickups_per_area_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "pickups-per-area",
        help="Print how many pickups there are in each area",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    parser.set_defaults(func=pickups_per_area_command_logic)


def _find_uncommented_tricks(requirement: Requirement):
    from randovania.layout.base.trick_level import LayoutTrickLevel
    if not isinstance(requirement, RequirementArrayBase):
        return

    trick_resources = []
    for it in requirement.items:
        if isinstance(it, RequirementArrayBase):
            yield from _find_uncommented_tricks(it)
        elif isinstance(it, ResourceRequirement) and it.resource.resource_type == ResourceType.TRICK:
            trick_resources.append(it)

    if requirement.comment is None and trick_resources:
        yield ", ".join(sorted(
            f"{req.resource.long_name} ({LayoutTrickLevel.from_number(req.amount).long_name})"
            for req in trick_resources
        ))


def uncommented_trick_usages_logic(args):
    gd = load_game_description(args)
    output_path: Path = args.output_path

    lines = []
    for region in gd.region_list.regions:
        lines.append(f"# {region.name}")
        for area in region.areas:

            paths = {}
            for source, connections in area.connections.items():
                paths[source.name] = {}
                for target, requirement in connections.items():
                    undocumented = sorted(set(_find_uncommented_tricks(requirement)))
                    if undocumented:
                        paths[source.name][target.name] = undocumented

            if paths and any(paths.values()):
                lines.append(f"## {area.name}")
                for source_name, connections in paths.items():
                    if connections:
                        lines.append(f"### {source_name}")
                        for target_name, undocumented in connections.items():
                            if len(undocumented) == 1:
                                lines.append(f"- [ ] {target_name}: {undocumented[0]}\n")
                            else:
                                lines.append(f"#### {target_name}")
                                for it in undocumented:
                                    lines.append(f"- [ ] {it}\n")

    output_path.write_text("\n".join(lines))


def uncommented_trick_usages_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "uncommented-trick-usages",
        help="Creates a list of all trick usages that are in uncommented groups.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="Where to write the output.",
    )
    parser.set_defaults(func=uncommented_trick_usages_logic)


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "database",
        help="Actions for database manipulation"
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--game",
        type=str,
        choices=[game.value for game in iterate_enum(RandovaniaGame)],
        help="Use the included database for the given game.",
    )
    group.add_argument(
        "--json-database",
        type=Path,
        help="Path to the JSON encoded database.",
    )

    sub_parsers = parser.add_subparsers(dest="database_command")
    create_convert_database_command(sub_parsers)
    view_area_command(sub_parsers)
    update_human_readable(sub_parsers)
    refresh_game_description_command(sub_parsers)
    refresh_pickup_database_command(sub_parsers)
    list_paths_with_dangerous_command(sub_parsers)
    list_paths_with_resource_command(sub_parsers)
    render_regions_graph(sub_parsers)
    pickups_per_area_command(sub_parsers)
    create_export_videos_command(sub_parsers)
    uncommented_trick_usages_command(sub_parsers)

    def check_command(args):
        if args.database_command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
