import argparse
import multiprocessing
import os
import random
import sys
from argparse import ArgumentParser
from typing import Dict, Set, Optional

from randovania.cli import prime_database
from randovania.games.prime import log_parser
from randovania.games.prime.log_parser import RandomizerLog
from randovania.resolver import resolver, data_reader, debug
from randovania.resolver.state import State

__all__ = ["create_subparsers"]


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


def run_resolver(args, data: Dict, randomizer_log: RandomizerLog, verbose=True) -> Optional[State]:
    game_description = data_reader.decode_data(data, randomizer_log.pickup_database)
    final_state = resolver.resolve(args.difficulty, args.enable_tricks, args.skip_item_loss, game_description)
    if final_state:
        if verbose:
            print("Game is possible!")

        item_percentage = final_state.resources.get(game_description.resource_database.item_percentage(), 0)
        if verbose:
            print("Victory with {}% of the items.".format(item_percentage))

        if args.print_final_path:
            states = []

            state = final_state
            while state:
                states.append(state)
                state = state.previous_state

            print("Path taken:")
            for state in reversed(states):
                print("> {}".format(debug.n(state.node)))
    return final_state


def validate_command_logic(args):
    debug._DEBUG_LEVEL = args.debug
    data = prime_database.decode_data_file(args)
    randomizer_log = log_parser.parse_log(args.logfile)
    if not run_resolver(args, data, randomizer_log):
        print("Impossible.")
        raise SystemExit(1)


def add_validate_command(sub_parsers):
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
    parser.add_argument(
        "--debug",
        choices=(0, 1, 2),
        type=int,
        default=0,
        help="The level of debug logging to print.")

    parser.set_defaults(func=validate_command_logic)


def list_logs_in(log_dir: str) -> Set[str]:
    if os.path.isdir(log_dir):
        return {
            log_name
            for log_name in os.listdir(log_dir)
            if "Randomizer_Log" in log_name
        }
    return set()


def generate_and_validate(args,
                          data,
                          input_queue: multiprocessing.Queue,
                          output_queue: multiprocessing.Queue):
    while True:
        seed = input_queue.get()
        randomizer_log = log_parser.generate_log(seed, args.exclude_pickups)
        output_queue.put((seed, run_resolver(args, data, randomizer_log, False) is not None))


def generate_seed_command_logic(args):
    data = prime_database.decode_data_file(args)

    input_queue = multiprocessing.Queue()
    output_queue = multiprocessing.Queue()

    cpu_count = args.limit_multi_threading
    if cpu_count is None:
        cpu_count = multiprocessing.cpu_count()

    process_list = [
        multiprocessing.Process(
            target=generate_and_validate,
            args=(args, data, input_queue, output_queue)
        )
        for _ in range(cpu_count)
    ]

    initial_seed = args.start_on_seed
    if initial_seed is None:
        initial_seed = random.randint(0, 2147483647)
    seed_count = 0

    def generate_seed():
        nonlocal seed_count
        seed_count += 1
        new_seed = initial_seed + seed_count
        if new_seed > 2147483647:
            new_seed -= 2147483647
        return new_seed

    for _ in range(cpu_count):
        input_queue.put_nowait(generate_seed())

    for process in process_list:
        process.start()

    while True:
        seed, valid = output_queue.get()
        if valid:
            break
        else:
            input_queue.put_nowait(generate_seed())
            if not args.quiet and seed_count % (100 * cpu_count) == 0:
                print("Total seed count so far: {}".format(seed_count))

    for process in process_list:
        process.terminate()

    if args.quiet:
        print(seed)
    else:
        print("== Successful seed: {} \nTotal seed count: {}".format(seed, seed_count))


def add_generate_seed_command(sub_parsers):
    parser = sub_parsers.add_parser(
        "generate-seed",
        help="Generates a valid seed with the given conditions.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )  # type: ArgumentParser

    add_difficulty_arguments(parser)
    parser.add_argument(
        "--exclude-pickups",
        nargs='+',
        type=int,
        default=[],
        help="Pickups to exclude from the randomization."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Generate no output, other than the final seed."
    )
    parser.add_argument(
        "--limit-multi-threading",
        type=int,
        help="Limit the seed generation to the given process count. If unsure, leave default."
    )
    parser.add_argument(
        "--start-on-seed",
        type=int,
        help="Starts checking with the given seed number. Defaults to a random value."
    )
    prime_database.add_data_file_argument(parser)
    parser.set_defaults(func=generate_seed_command_logic)


def generate_seed_log_command_logic(args):
    log_parser.generate_log(args.seed, args.exclude_pickups).write(sys.stdout)


def add_generate_seed_log_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "generate-seed-log",
        help="Generates a logfile for the given seed.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    parser.add_argument(
        "seed",
        type=int,
        help="The seed."
    )
    parser.add_argument(
        "--exclude-pickups",
        nargs='+',
        type=int,
        default=[],
        help="Pickups to exclude from the randomization."
    )
    parser.set_defaults(func=generate_seed_log_command_logic)


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "echoes",
        help="Actions regarding Metroid Prime 2: Echoes"
    )
    command_subparser = parser.add_subparsers(dest="command")
    add_validate_command(command_subparser)
    add_generate_seed_command(command_subparser)
    add_generate_seed_log_command(command_subparser)
    prime_database.create_subparsers(command_subparser)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
