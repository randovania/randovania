from __future__ import annotations

import argparse
import logging
import typing
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database, trick_documentation
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.resources.search import MissingResource, find_resource_info_with_long_name
from randovania.game_description.trick_documentation import TrickUsageState
from randovania.games import binary_data, default_data
from randovania.lib import json_lib
from randovania.lib.enum_lib import iterate_enum

if typing.TYPE_CHECKING:
    from argparse import Namespace, _SubParsersAction

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.resource_info import ResourceInfo


def _get_sorted_list_of_names(input_list: list[Any], prefix: str = "") -> typing.Iterable[str]:
    for item in sorted(input_list, key=lambda x: x.name):
        yield prefix + item.name


def decode_data_file(args: Namespace) -> dict:
    json_database: Path | None = args.json_database
    if json_database is not None:
        return typing.cast("dict", json_lib.read_path(json_database))
    else:
        return default_data.read_json_then_binary(RandovaniaGame(args.game))[1]


def export_as_binary(data: dict, output_binary: Path) -> None:
    with output_binary.open("wb") as x:
        binary_data.encode(data, x)


def convert_database_command_logic(args: Namespace) -> None:
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


def create_convert_database_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "convert-database",
        help="Converts a database file between JSON and binary encoded formats. Input defaults to embedded database.",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.add_argument(
        "--decode-to-game-description",
        action="store_true",
        default=False,
        help="Decodes the input data to a GameDescription, then encodes it back.",
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


def export_videos_command_logic(args: Namespace) -> None:
    from randovania.cli.commands.export_db_videos import export_videos

    games = []

    if args.game is not None:
        games.append(RandovaniaGame(args.game))
    else:
        games = list(RandovaniaGame)

    for game in games:
        export_videos(game, args.output_dir)


def create_export_videos_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "export-videos",
        help="Create HTML pages for easy vewing of YouTube video comments.",
        formatter_class=argparse.MetavarTypeHelpFormatter,
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


def view_area_command_logic(args: Namespace) -> None:
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


def load_game_description(args: Namespace) -> GameDescription:
    from randovania.game_description import data_reader

    data = decode_data_file(args)
    gd = data_reader.decode_data(data)
    return gd


def view_area_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "view-area", help="View information about an area.", formatter_class=argparse.MetavarTypeHelpFormatter
    )
    parser.add_argument("--simplify", action="store_true", help="Simplify the RequirementSets")
    parser.add_argument("region", type=str, help="The name of the region that contains the area.")
    parser.add_argument("area", type=str, help="The name of the area.")

    parser.set_defaults(func=view_area_command_logic)


def update_human_readable_logic(args: Namespace) -> None:
    from randovania.game_description import data_reader, pretty_print

    game = RandovaniaGame(args.game)

    path, data = default_data.read_json_then_binary(game)
    gd = data_reader.decode_data(data)

    path.with_suffix("").mkdir(parents=True, exist_ok=True)
    pretty_print.write_human_readable_game(gd, path.with_suffix(""))


def update_human_readable(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "update-human-readable",
        help="Update the human readable versions",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.set_defaults(func=update_human_readable_logic)


def write_game_descriptions(game_descriptions: dict[RandovaniaGame, GameDescription]) -> None:
    from randovania.game_description import data_writer, pretty_print

    for game, gd in game_descriptions.items():
        logging.info("Writing %s", game.long_name)
        new_data = data_writer.write_game_description(gd)

        path = game.data_path.joinpath("logic_database")
        data_writer.write_as_split_files(new_data, path)
        pretty_print.write_human_readable_game(gd, path)


def refresh_game_description_logic(args: Namespace) -> None:
    from randovania.game_description import integrity_check

    if args.game is not None:
        games = [RandovaniaGame(args.game)]
    else:
        games = list(RandovaniaGame.all_games())

    gd_per_game = {}

    for game in games:
        logging.info("Reading %s", game.long_name)
        gd_per_game[game] = default_database.game_description_for(game)

    should_stop = False
    if args.integrity_check:
        for game, gd in gd_per_game.items():
            errors = integrity_check.find_database_errors(gd)
            if errors:
                logging.warning("Integrity errors for %s:\n%s", game.long_name, "\n".join(errors))
                if game.data.development_state.is_stable:
                    should_stop = True

    if not should_stop:
        write_game_descriptions(gd_per_game)


def refresh_game_description_command(sub_parsers: _SubParsersAction) -> None:
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


def refresh_pickup_database_logic(args: Namespace) -> None:
    for game in iterate_enum(RandovaniaGame):
        logging.info("Updating %s", game.long_name)
        pdb = default_database.pickup_database_for_game(game)
        default_database.write_pickup_database_for_game(pdb, game)


def refresh_pickup_database_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "refresh-pickup-database",
        help="Re-exports the json of all pickup databases",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.set_defaults(func=refresh_pickup_database_logic)


def _list_paths_with_resource(
    game: GameDescription, print_only_area: bool, resource: ResourceInfo, needed_quantity: int | None
) -> None:
    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.resources.resource_collection import ResourceCollection

    count = 0
    context = NodeContext(None, ResourceCollection(), game.resource_database, game.region_list)

    for area in game.region_list.all_areas:
        area_had_resource = False

        for source, connection in area.connections.items():
            for target, requirement in connection.items():
                for individual in requirement.iterate_resource_requirements(context):
                    if needed_quantity is None or needed_quantity == individual.amount:
                        area_had_resource = True
                        if not print_only_area:
                            print(
                                "At {}, from {} to {}:\n{}\n".format(
                                    game.region_list.area_name(area),
                                    source.name,
                                    target.name,
                                    sorted(
                                        individual
                                        for individual in requirement.iterate_resource_requirements(context)
                                        if individual.resource != resource
                                    ),
                                )
                            )
                        count += 1

        if area_had_resource and print_only_area:
            print(game.region_list.area_name(area))

    print(f"Total routes: {count}")


def list_paths_with_dangerous_logic(args: Namespace) -> None:
    game = load_game_description(args)
    print_only_area = args.print_only_area
    count = 0

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.resources.resource_collection import ResourceCollection

    context = NodeContext(None, ResourceCollection(), game.resource_database, game.region_list)

    for area in game.region_list.all_areas:
        area_had_resource = False

        for source, connection in area.connections.items():
            for target, requirement in connection.items():
                for individual in requirement.iterate_resource_requirements(context):
                    if individual.negate:
                        area_had_resource = True
                        if not print_only_area:
                            sorted_resources = sorted(
                                individual for individual in requirement.iterate_resource_requirements(context)
                            )
                            print(
                                f"At {game.region_list.area_name(area)}, from {area} to {source.name}:\n"
                                f"{sorted_resources}\n"
                            )
                        count += 1

        if area_had_resource and print_only_area:
            print(game.region_list.area_name(area))

    print(f"Total routes: {count}")


def list_paths_with_dangerous_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "list-dangerous-usage",
        help="List all connections that needs a resource to be missing.",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.add_argument(
        "--print-only-area", help="Only print the area names, not each specific path", action="store_true"
    )
    parser.set_defaults(func=list_paths_with_dangerous_logic)


def list_paths_with_resource_logic(args: Namespace) -> None:
    gd = load_game_description(args)
    resource_name: str = args.resource

    resource = None
    # TODO: make this nicer
    for resource_type in [gd.resource_database.item + gd.resource_database.event + gd.resource_database.trick]:
        try:
            resource = find_resource_info_with_long_name(resource_type, resource_name)
            break
        except MissingResource:
            continue

    if resource is None:
        print(f"A resource named {resource_name} was not found.")
        raise SystemExit(1)

    _list_paths_with_resource(gd, args.print_only_area, resource, None)


def list_paths_with_resource_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "list-resource-usage",
        help="List all connections that needs the resource.",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.add_argument(
        "--print-only-area", help="Only print the area names, not each specific path", action="store_true"
    )
    parser.add_argument("resource", type=str)
    parser.set_defaults(func=list_paths_with_resource_logic)


def pickups_per_area_command_logic(args: Namespace) -> None:
    from randovania.game_description.db.pickup_node import PickupNode

    gd = load_game_description(args)

    total = 0
    for region in gd.region_list.regions:
        num_pickups = sum(1 for node in region.all_nodes if isinstance(node, PickupNode))
        total += num_pickups
        print(f"{region.correct_name(False)}: {num_pickups}")
    print(f"Total: {total}")


def pickups_per_area_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "pickups-per-area",
        help="Print how many pickups there are in each area",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.set_defaults(func=pickups_per_area_command_logic)


def trick_usage_documentation_logic(args: Namespace) -> None:
    gd = load_game_description(args)
    output_path: Path = args.output_path

    symbol_for_state = {
        TrickUsageState.DOCUMENTED: "Documented",
        TrickUsageState.UNDOCUMENTED: "Missing",
        TrickUsageState.SKIPPED: "Skipped",
    }

    lines = []
    for region in gd.region_list.regions:
        lines.append(f"\n\n# {region.name}")
        for area in region.areas:
            paths = trick_documentation.get_area_connection_docs(area)

            if paths and any(paths.values()):
                lines.append(f"\n## {area.name}")
                for source_name, connections in paths.items():
                    if connections:
                        for target_name, docs in connections.items():
                            lines.append(f"### {source_name} -> {target_name}:")
                            for it, state in docs.items():
                                lines.append(f"- ({symbol_for_state[state]}) {it}")

    output_path.write_text("\n".join(lines))


def trick_usage_documentation_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "trick-usage-documentation",
        help="Creates a list of all trick usages and if they're documented or not.",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="Where to write the output.",
    )
    parser.set_defaults(func=trick_usage_documentation_logic)


def features_per_node_command_logic(args: Namespace) -> None:
    """Reports features for given pickup nodes, taking into account area and node specific features"""
    db = load_game_description(args)
    pickup_node_count = 0
    featureless_nodes = []
    no_features = 0
    one_features = 0
    two_features = 0
    threeplus_features = 0
    for area in db.region_list.all_areas:
        area_features = area.hint_features
        for node in area.nodes:
            if isinstance(node, PickupNode):
                pickup_node_count += 1
                node_features = node.hint_features
                all_features = list(area_features)
                for hint in node_features:
                    if hint not in area_features:
                        all_features.append(hint)
                match len(all_features):
                    case 0:
                        no_features += 1
                        featureless_nodes.append(node.identifier.as_string)
                    case 1:
                        one_features += 1
                    case 2:
                        two_features += 1
                    case _:
                        threeplus_features += 1
                print(f"{node.identifier.as_string}: {len(all_features)}")
    print(f"featureless nodes: {featureless_nodes}")
    print("-----------------------------")
    print(f"no features:     {no_features}")
    print(f"1 feature :      {one_features}")
    print(f"2 features:      {two_features}")
    print(f"3+ features:     {threeplus_features}")
    print(f"total pickups: /{pickup_node_count}")


def features_per_node_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser(
        "features-per-node",
        help="Print how many features per pickup node there are",
        formatter_class=argparse.MetavarTypeHelpFormatter,
    )
    parser.set_defaults(func=features_per_node_command_logic)


def create_subparsers(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser("database", help="Actions for database manipulation")

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
    pickups_per_area_command(sub_parsers)
    create_export_videos_command(sub_parsers)
    trick_usage_documentation_command(sub_parsers)
    features_per_node_command(sub_parsers)

    def check_command(args: Namespace) -> None:
        if args.database_command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
