import argparse
import csv
import json
import os
from argparse import ArgumentParser
from typing import Dict, BinaryIO

from randovania import get_data_path
from randovania.games.prime import binary_data, log_parser
from randovania.resolver import resolver, data_reader, debug
from randovania.resolver.game_description import consistency_check, GameDescription


def decode_data_file(args) -> Dict:
    if args.json_database is not None:
        with open(args.json_database) as data_file:
            return json.load(data_file)

    data_file_path = args.binary_database
    if data_file_path is None:
        return binary_data.decode_default_prime2()
    else:
        return binary_data.decode_file_path(
            data_file_path,
            os.path.join(get_data_path(), "prime2_extra.json")
        )


def add_data_file_argument(parser: ArgumentParser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--binary-database",
        type=str,
        help="Path to the binary encoded database.",
    )
    group.add_argument(
        "--json-database",
        type=str,
        help="Path to the JSON encoded database.",
    )


def convert_database_command_logic(args):
    data = decode_data_file(args)

    if args.output_binary is not None:
        with open(args.output_binary, "wb") as x:  # type: BinaryIO
            binary_data.encode(data, x)
    elif args.output_json is not None:
        with open(args.output_json, "w") as x:  # type: BinaryIO
            json.dump(data, x, indent=4)
    else:
        raise ValueError("Neither binary nor JSON set. Argparse is broken?")


def create_convert_database_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "convert-database",
        help="Converts a database file between JSON and binary encoded formats. Input defaults to embedded database.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    add_data_file_argument(parser)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--output-binary",
        type=str,
        help="Export as a binary file.",
    )
    group.add_argument(
        "--output-json",
        type=str,
        help="Export as a JSON file.",
    )

    parser.set_defaults(func=convert_database_command_logic)


def view_area_command_logic(args):
    gd = load_game_description(args)

    if args.simplify:
        resolver.simplify_connections(gd, {})

    for world in gd.worlds:
        if world.name == args.world:
            for area in world.areas:
                if area.name == args.area:
                    debug.pretty_print_area(area)
                    raise SystemExit

            print("Unknown area named '{}' in world {}. Options:\n{}".format(
                args.area,
                world,
                "\n".join(" " + area.name for area in sorted(world.areas, key=lambda x: x.name))
            ))
            raise SystemExit(1)

    print("Unknown world named '{}'. Options:\n{}".format(
        args.world,
        "\n".join(" " + world.name for world in sorted(gd.worlds, key=lambda x: x.name))
    ))
    raise SystemExit(1)


def load_game_description(args) -> GameDescription:
    data = decode_data_file(args)
    logfile = os.path.join(get_data_path(), "prime2_original_log.txt")
    randomizer_log = log_parser.parse_log(logfile)

    gd = data_reader.decode_data(data, randomizer_log.elevators)
    debug._gd = gd
    return gd


def view_area_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "view-area",
        help="View information about an area.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    add_data_file_argument(parser)
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


def consistency_check_command_logic(args):
    gd = load_game_description(args)

    for node, warning in consistency_check(gd):
        print("> {}:\n{}\n".format(debug.n(node), warning))


def consistency_check_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "consistency-check",
        help="Check if all docks and teleporters are valid.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    add_data_file_argument(parser)
    parser.set_defaults(func=consistency_check_command_logic)


def export_areas_command_logic(args):
    gd = load_game_description(args)

    with open(args.output_file, "w", newline='') as output:
        writer = csv.writer(output)
        writer.writerow(("World", "Area", "Node", "Can go back in bounds",
                         "Interact while OOB and go back in bounds",
                         "Interact while OOB and stay out of bounds",
                         "Requirements for going OOB"))
        for world in gd.worlds:
            for area in world.areas:
                for node in area.nodes:
                    writer.writerow((world.name, area.name, node.name, False, False, False))


def export_areas_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "export-areas",
        help="Export a CSV with the areas of the game.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    add_data_file_argument(parser)
    parser.add_argument("output_file")
    parser.set_defaults(func=export_areas_command_logic)


def list_paths_with_difficulty_logic(args):
    gd = load_game_description(args)
    difficulty_requirement = gd.resource_database.difficulty[0]
    count = 0

    for world in gd.worlds:
        for area in world.areas:
            for source, connection in area.connections.items():
                for target, requirements in connection.items():
                    for alternative in requirements.alternatives:
                        if any(requirement.requirement == difficulty_requirement
                               and requirement.amount == args.difficulty
                               for requirement in alternative.values()):
                            print("At {}/{}, from {} to {}:\n{}\n".format(
                                world.name, area.name, source.name, target.name,
                                sorted(individual for individual in alternative.values()
                                       if individual.requirement != difficulty_requirement)
                            ))
                            count += 1

    print("Total routes: {}".format(count))


def list_paths_with_difficulty_command(sub_parsers):
    parser = sub_parsers.add_parser(
        "list-difficulty-usage",
        help="List all connections that needs the difficulty.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )  # type: ArgumentParser
    add_data_file_argument(parser)
    parser.add_argument("difficulty", type=int)
    parser.set_defaults(func=list_paths_with_difficulty_logic)


def create_subparsers(sub_parsers):
    parser = sub_parsers.add_parser(
        "database",
        help="Actions for database manipulation"
    )  # type: ArgumentParser

    sub_parsers = parser.add_subparsers(dest="database_command")
    create_convert_database_command(sub_parsers)
    view_area_command(sub_parsers)
    consistency_check_command(sub_parsers)
    export_areas_command(sub_parsers)
    list_paths_with_difficulty_command(sub_parsers)

    def check_command(args):
        if args.database_command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
