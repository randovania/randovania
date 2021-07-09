import argparse
import json
import typing
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, BinaryIO, Optional, TextIO, List, Any

from randovania.game_description import default_database, data_reader
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.resources.search import MissingResource, find_resource_info_with_long_name
from randovania.games.game import RandovaniaGame
from randovania.games import default_data, binary_data
from randovania.lib.enum_lib import iterate_enum


def _get_sorted_list_of_names(input_list: List[Any], prefix: str = "") -> List[str]:
    for item in sorted(input_list, key=lambda x: x.name):
        yield prefix + item.name


def decode_data_file(args) -> Dict:
    json_database: Optional[Path] = args.json_database
    if json_database is not None:
        with json_database.open() as data_file:
            return json.load(data_file)
    else:
        return default_data.read_json_then_binary(RandovaniaGame(args.game))[1]


def export_as_binary(data: dict, output_binary: Path):
    with output_binary.open("wb") as x:  # type: BinaryIO
        binary_data.encode(data, x)


def convert_database_command_logic(args):
    from randovania.game_description import data_reader, data_writer
    data = decode_data_file(args)

    if args.decode_to_game_description:
        data = data_writer.write_game_description(data_reader.decode_data(data))

    output_binary: Optional[Path] = args.output_binary
    output_json: Optional[Path] = args.output_json

    if output_binary is not None:
        export_as_binary(data, output_binary)

    elif output_json is not None:
        with output_json.open("w") as x:  # type: TextIO
            json.dump(data, x, indent=4)
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


def view_area_command_logic(args):
    from randovania.game_description import pretty_print
    game = load_game_description(args)
    world_list = game.world_list

    try:
        world = world_list.world_with_name(args.world)

    except KeyError:
        options = "\n".join(_get_sorted_list_of_names(world_list.worlds, " "))
        print(f"Unknown world named '{args.world}'. Options:\n{options}")
        raise SystemExit(1)

    try:
        area = world.area_by_name(args.area)

    except KeyError:
        options = "\n".join(_get_sorted_list_of_names(world.areas, " "))
        print(f"Unknown area named '{args.area}' in world {world}. Options:\n{options}")
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
        "world",
        type=str,
        help="The name of the world that contains the area."
    )
    parser.add_argument(
        "area",
        type=str,
        help="The name of the area."
    )

    parser.set_defaults(func=view_area_command_logic)


def update_human_readable_logic(args):
    from randovania.game_description import pretty_print
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


def _list_paths_with_resource(game,
                              print_only_area: bool,
                              resource: ResourceInfo,
                              needed_quantity: Optional[int]):
    from randovania.game_description.game_description import GameDescription

    count = 0
    game = typing.cast(GameDescription, game)

    for area in game.world_list.all_areas:
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
                            print("At {0}, from {1} to {2}:\n{3}\n".format(
                                game.world_list.area_name(area),
                                source.name,
                                target.name,
                                sorted(individual for individual in alternative.values()
                                       if individual.resource != resource)
                            ))
                        count += 1

        if area_had_resource and print_only_area:
            print(game.world_list.area_name(area))

    print("Total routes: {}".format(count))


def list_paths_with_dangerous_logic(args):
    game = load_game_description(args)
    print_only_area = args.print_only_area
    count = 0

    for area in game.world_list.all_areas:
        area_had_resource = False

        for source, connection in area.connections.items():
            for target, requirement in connection.items():
                for alternative in requirement.as_set(game.resource_database).alternatives:
                    for individual in alternative.values():
                        if individual.negate:
                            area_had_resource = True
                            if not print_only_area:
                                print("At {0}, from {1} to {2}:\n{4}\n".format(
                                    game.world_list.area_name(area),
                                    area,
                                    source.name,
                                    target.name,
                                    sorted(individual for individual in alternative.values())))
                            count += 1

        if area_had_resource and print_only_area:
            print(game.world_list.area_name(area))

    print("Total routes: {}".format(count))


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

    resource = None
    for resource_type in gd.resource_database:
        try:
            resource = find_resource_info_with_long_name(resource_type, args.resource)
            break
        except MissingResource:
            continue

    if resource is None:
        print(f"A resource named {args.resource} was not found.")
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


def pickups_per_area_command_logic(args):
    from randovania.game_description.world.node import PickupNode
    gd = load_game_description(args)

    for world in gd.world_list.worlds:
        num_pickups = sum(1 for node in world.all_nodes if isinstance(node, PickupNode))
        print(f"{world.correct_name(False)}: {num_pickups}")


def pickups_per_area_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "pickups-per-area",
        help="Print how many pickups there are in each area",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    parser.set_defaults(func=pickups_per_area_command_logic)


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
        default=RandovaniaGame.METROID_PRIME_ECHOES.value,
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
    list_paths_with_dangerous_command(sub_parsers)
    list_paths_with_resource_command(sub_parsers)
    pickups_per_area_command(sub_parsers)

    def check_command(args):
        if args.database_command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
