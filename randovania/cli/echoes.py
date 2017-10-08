import argparse
import os
import subprocess
from argparse import ArgumentParser
from typing import Dict, Set, Optional

from randovania.cli import prime_database
from randovania.games.prime import log_parser
from randovania.games.prime.log_parser import RandomizerLog
from randovania.resolver import resolver, data_reader
from randovania.resolver.debug import _n
from randovania.resolver.state import State


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
        action="store_true",
        help=
        "Enable trick usage in the validation. "
        "Currently, there's no way to control which individual tricks gets enabled."
    )
    parser.add_argument(
        "--skip-item-loss",
        action="store_true",
        help="Assumes the Item Loss trigger is disabled."
    )
    parser.add_argument(
        "--print-final-path",
        action="store_true",
        help=
        "If seed is possible, print the sequence of events/pickups taken to reach the ending."
    )


def run_resolver(args, data: Dict, randomizer_log: RandomizerLog) -> Optional[State]:
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
    return final_state


def validate_command_logic(args):
    data = prime_database.decode_data_file(args)
    randomizer_log = log_parser.parse_log(args.logfile)
    if not run_resolver(args, data, randomizer_log):
        print("Impossible.")
        raise SystemExit(1)


def create_validate_command(sub_parsers):
    parser = sub_parsers.add_parser(
        "validate",
        help="Validate a randomizer log."
    )  # type: ArgumentParser

    parser.add_argument(
        "logfile",
        type=str,
        help="Path to the log file of a Randomizer run.")
    add_difficulty_arguments(parser)
    prime_database.add_data_file_argument(parser)

    parser.set_defaults(func=validate_command_logic)


def invoke_randomizer(args):
    subprocess_argument = [
        args.randomizer_binary,
        args.game_folder,
        "-g", "MP2",
        "-e", ",".join(str(pickup) for pickup in args.exclude_pickups),
    ]
    if args.remove_hud_memo_popup:
        subprocess_argument.append("-h")
    if args.skip_item_loss:
        subprocess_argument.append("-i")

    print("Invoking Randomizer with {}.".format(subprocess_argument))
    print("=== You will need to press Enter when it finishes to proceed ===\n")
    subprocess.run(subprocess_argument, check=True)


def list_logs_in(log_dir: str) -> Set[str]:
    if os.path.isdir(log_dir):
        return {
            log_name
            for log_name in os.listdir(log_dir)
            if "Randomizer_Log" in log_name
        }
    return set()


def randomize_command_logic(args):
    data = prime_database.decode_data_file(args)
    if not os.path.isfile(args.randomizer_binary):
        raise ValueError("Randomizer binary '{}' does not exist.".format(args.randomizer_binary))

    while True:
        log_dir = os.path.join(os.path.dirname(args.randomizer_binary), "logs")
        previous_logs = list_logs_in(log_dir)
        invoke_randomizer(args)
        new_logs = list_logs_in(log_dir)
        difference = new_logs - previous_logs
        if len(difference) != 1:
            raise RuntimeError("Could not find the new randomizer log, found this log difference: {}".format(difference))

        log_file = difference.pop()
        full_log_file = os.path.join(log_dir, log_file)

        randomizer_log = log_parser.parse_log(full_log_file)
        print("Randomizer finished succesfuly with log {}.".format(full_log_file))
        print("Validating...")
        if run_resolver(args, data, randomizer_log):
            break

        print("Seed was impossible, retrying.\n\n")


def create_randomize_command(sub_parsers):
    parser = sub_parsers.add_parser(
        "randomize",
        help="Randomize until a valid seed is found.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )  # type: ArgumentParser

    add_difficulty_arguments(parser)
    prime_database.add_data_file_argument(parser)
    parser.add_argument(
        "--randomizer-binary",
        type=str,
        required=True,
        help="Path to the randomizer executable."
    )
    parser.add_argument(
        "game_folder",
        type=str,
        help="Folder to pass to the randomizer executable."
    )
    parser.add_argument(
        "--exclude-pickups",
        nargs='*',
        type=int,
        default=[23],
        help="Pickups to exclude from the randomization."
    )
    parser.add_argument(
        "--remove-hud-memo-popup",
        action="store_true",
        help="Changes the type of HUD Memo used for pickups, to remove the popup."
    )

    parser.set_defaults(func=randomize_command_logic)


def create_subparsers(sub_parsers):
    parser = sub_parsers.add_parser(
        "echoes",
        help="Actions regarding Metroid Prime 2: Echoes"
    )  # type: ArgumentParser

    command_subparser = parser.add_subparsers(dest="command")
    create_validate_command(command_subparser)
    create_randomize_command(command_subparser)
    prime_database.create_subparsers(command_subparser)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
