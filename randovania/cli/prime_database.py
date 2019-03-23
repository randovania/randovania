import argparse
import csv
import json
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, BinaryIO, Optional, TextIO, List, Any

from randovania import get_data_path
from randovania.game_description import data_reader, data_writer
from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements import RequirementSet, RequirementList, IndividualRequirement
from randovania.game_description.resources import ResourceInfo, find_resource_info_with_long_name
from randovania.games.prime import binary_data, default_data
from randovania.resolver import debug


def _get_sorted_list_of_names(input_list: List[Any], prefix: str = "") -> List[str]:
    for item in sorted(input_list, key=lambda x: x.name):
        yield prefix + item.name


def decode_data_file(args) -> Dict:
    json_database: Optional[Path] = args.json_database
    if json_database is not None:
        with json_database.open() as data_file:
            return json.load(data_file)

    data_file_path: Optional[Path] = args.binary_database
    if data_file_path is None:
        return default_data.decode_default_prime2()
    else:
        extra_path = data_file_path.parent.joinpath(data_file_path.stem + "_extra.json")
        return binary_data.decode_file_path(data_file_path, extra_path)


def add_data_file_argument(parser: ArgumentParser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--binary-database",
        type=Path,
        help="Path to the binary encoded database.",
    )
    group.add_argument(
        "--json-database",
        type=Path,
        help="Path to the JSON encoded database.",
    )


def export_as_binary(data: dict, output_binary: Path):
    with output_binary.open("wb") as x:  # type: BinaryIO
        extra_data = binary_data.encode(data, x)

    with output_binary.parent.joinpath(output_binary.stem + "_extra.json").open("w") as x:  # type: TextIO
        json.dump(extra_data, x, indent=4)


def convert_database_command_logic(args):
    data = decode_data_file(args)

    if args.decode_to_game_description:
        data = data_writer.write_game_description(data_reader.decode_data(data, False))

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
    add_data_file_argument(parser)
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
    world_list = load_game_description(args).world_list

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

    debug.pretty_print_area(area)


def load_game_description(args) -> GameDescription:
    data = decode_data_file(args)

    gd = data_reader.decode_data(data)
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


def export_areas_command_logic(args):
    gd = load_game_description(args)

    with args.output_file.open("w", newline='') as output:
        writer = csv.writer(output)
        writer.writerow(("World", "Area", "Node", "Can go back in bounds",
                         "Interact while OOB and go back in bounds",
                         "Interact while OOB and stay out of bounds",
                         "Requirements for going OOB"))
        for world in gd.world_list.worlds:
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
    parser.add_argument("output_file", type=Path)
    parser.set_defaults(func=export_areas_command_logic)


def _modify_resources(game: GameDescription,
                      resource: ResourceInfo,
                      ):
    """
    This change all occurrences of the given resource to have difficulty 4
    :param game:
    :param resource:
    :return:
    """
    new_difficulty = 4
    database = game.resource_database

    def _replace(alternative: RequirementList) -> RequirementList:
        if alternative.get(resource) is not None:
            return RequirementList.without_misc_resources(
                database=database,
                items=[
                    (individual if individual.resource != database.difficulty_resource
                     else IndividualRequirement(database.difficulty_resource, new_difficulty, False))
                    for individual in alternative.values()
                ]
            )
        else:
            return alternative

    for world in game.world_list.worlds:
        for area in world.areas:
            for source, connection in area.connections.items():
                connection.update({
                    target: RequirementSet(
                        _replace(alternative)
                        for alternative in requirements.alternatives
                    )
                    for target, requirements in connection.items()
                })


def _list_paths_with_resource(game: GameDescription,
                              resource: ResourceInfo,
                              needed_quantity: Optional[int]):
    count = 0

    for world in game.world_list.worlds:
        for area in world.areas:
            for source, connection in area.connections.items():
                for target, requirements in connection.items():
                    for alternative in requirements.alternatives:
                        individual = alternative.get(resource)
                        if individual is None:
                            continue

                        if needed_quantity is None or needed_quantity == individual.amount:
                            print("At {0.name}/{1.name}, from {2} to {3}:\n{4}\n".format(
                                world,
                                area,
                                source.name,
                                target.name,
                                sorted(individual for individual in alternative.values()
                                       if individual.resource != resource)
                            ))
                            count += 1

    print("Total routes: {}".format(count))


def list_paths_with_difficulty_logic(args):
    gd = load_game_description(args)
    _list_paths_with_resource(
        gd,
        gd.resource_database.difficulty_resource,
        args.difficulty
    )


def list_paths_with_difficulty_command(sub_parsers):
    parser = sub_parsers.add_parser(
        "list-difficulty-usage",
        help="List all connections that needs the difficulty.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )  # type: ArgumentParser
    add_data_file_argument(parser)
    parser.add_argument("difficulty", type=int)
    parser.set_defaults(func=list_paths_with_difficulty_logic)


def list_paths_with_resource_logic(args):
    gd = load_game_description(args)

    resource_types = [gd.resource_database.item, gd.resource_database.event, gd.resource_database.trick]

    resource = None
    for resource_type in resource_types:
        try:
            resource = find_resource_info_with_long_name(resource_type, args.resource)
            break
        except ValueError:
            continue

    if resource is None:
        print(f"A resource named {args.resource} was not found.")
        raise SystemExit(1)

    _list_paths_with_resource(
        gd,
        resource,
        None
    )


def list_paths_with_resource_command(sub_parsers):
    parser = sub_parsers.add_parser(
        "list-resource-usage",
        help="List all connections that needs the resource.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )  # type: ArgumentParser
    add_data_file_argument(parser)
    parser.add_argument("resource", type=str)
    parser.set_defaults(func=list_paths_with_resource_logic)


def create_subparsers(sub_parsers):
    parser = sub_parsers.add_parser(
        "database",
        help="Actions for database manipulation"
    )  # type: ArgumentParser

    sub_parsers = parser.add_subparsers(dest="database_command")
    create_convert_database_command(sub_parsers)
    view_area_command(sub_parsers)
    export_areas_command(sub_parsers)
    list_paths_with_difficulty_command(sub_parsers)
    list_paths_with_resource_command(sub_parsers)

    def check_command(args):
        if args.database_command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
