import json
import os
from argparse import ArgumentParser
from typing import Dict, BinaryIO

from randovania.games.prime import binary_data, log_parser
from randovania.resolver import resolver, data_reader
from randovania.resolver.debug import _n


def decode_data_file(args) -> Dict:
    if args.json_data_file is not None:
        with open(args.json_data_file) as data_file:
            return json.load(data_file)

    data_file_path = args.binary_data_file
    if data_file_path is None:
        data_file_path = os.path.join(os.path.dirname(__file__), "..", "data", "prime2.bin")

    with open(data_file_path, "rb") as x:  # type: BinaryIO
        return binary_data.decode(x)


def add_data_file_argument(parser: ArgumentParser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--binary-data-file",
        help="Path to the binary encoded data file.",
    )
    group.add_argument(
        "--json-data-file",
        help="Path to the JSON decoded data file.",
    )


def add_difficulty_arguments(parser):
    parser.add_argument(
        "--difficulty",
        type=int,
        default=0,
        choices=range(6),
        help=
        "The difficulty level to check with. Higher numbers implies in harder tricks."
    )
    parser.add_argument(
        "--enable-tricks",
        action="store_const",
        const=True,
        help=
        "Enable trick usage in the validation. "
        "Currently, there's no way to control which individual tricks gets enabled."
    )
    parser.add_argument(
        "--skip-item-loss",
        action="store_const",
        const=True,
        help=
        "Assumes the Item Loss trigger is disabled."
    )


def patch_data(data: Dict):
    for world in data["worlds"]:
        for area in world["areas"]:
            # Aerie Transport Station has default_node_index not set
            if area["asset_id"] == 3136899603:
                area["default_node_index"] = 2

            # Hive Temple Access has incorrect requirements for unlocking Hive Temple gate
            if area["asset_id"] == 3968294891:
                area["connections"][1][2] = [[{
                    "requirement_type": 0,
                    "requirement_index": 38 + i,
                    "amount": 1,
                    "negate": False,
                } for i in range(3)]]


def create_validate_command(sub_parsers):
    parser = sub_parsers.add_parser(
        "validate",
        help="Validate a randomizer log."
    )  # type: ArgumentParser

    parser.add_argument(
        "logfile",
        help="Path to the log file of a Randomizer run.")
    add_difficulty_arguments(parser)
    parser.add_argument(
        "--print-final-path",
        action="store_const",
        const=True,
        help=
        "If seed is possible, print the sequence of events/pickups taken to reach the ending."
    )
    add_data_file_argument(parser)

    def logic(args):
        data = decode_data_file(args)
        patch_data(data)

        randomizer_log = log_parser.parse_log(args.logfile)

        game_description = data_reader.decode_data(data, randomizer_log.pickup_database)
        final_state = resolver.resolve(args.difficulty, args.enable_tricks, args.skip_item_loss, game_description)
        if final_state:
            print("Game is possible!")

            item_percentage = final_state.resources.get(game_description.resource_database.item_percentage(), 0)
            print("Victory with {}% of the items.".format(item_percentage))

            if args.print_final_path:
                states = []

                state = final_state
                while state:
                    states.append(state)
                    state = state.previous_state

                print("Path taken:")
                for state in reversed(states):
                    print("> {}".format(_n(state.node)))

        else:
            print("Impossible.")
            raise SystemExit(1)

    parser.set_defaults(func=logic)


def create_subparsers(sub_parsers):
    parser = sub_parsers.add_parser(
        "echoes",
        help="Actions regarding Metroid Prime 2: Echoes"
    )  # type: ArgumentParser

    command_subparser = parser.add_subparsers(dest="command")
    create_validate_command(command_subparser)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
