import argparse
import multiprocessing
import random
import sys
from argparse import ArgumentParser
from collections import defaultdict

from randovania.cli import prime_database
from randovania.games.prime import log_parser
from randovania.resolver import debug
from randovania.resolver.echoes import run_resolver, search_seed, RandomizerConfiguration, \
    ResolverConfiguration

__all__ = ["create_subparsers"]


def build_resolver_configuration(args):
    return ResolverConfiguration(
        args.difficulty,
        args.minimum_difficulty,
        args.tricks,
        not args.skip_item_loss
    )


def add_resolver_config_arguments(parser):
    parser.add_argument(
        "--difficulty",
        type=int,
        default=0,
        choices=range(6),
        help=
        "The difficulty level to check with. Higher numbers implies in harder tricks."
    )
    parser.add_argument(
        "--minimum-difficulty",
        type=int,
        default=0,
        choices=range(6),
        help=
        "Also check if the seed needs the given difficulty."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--enable-tricks",
        action="store_true",
        dest="tricks",
        default=True,
        help=
        "Enable trick usage in the validation. "
        "Currently, there's no way to control which individual tricks gets enabled."
    )
    group.add_argument(
        "--disable-tricks",
        action="store_false",
        dest="tricks",
        default=True,
        help="Disable all tricks."
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


def build_randomizer_configuration(args):
    return RandomizerConfiguration(
        args.exclude_pickups,
        args.randomize_elevators
    )


def add_randomizer_configuration_arguments(parser):
    parser.add_argument(
        "--exclude-pickups",
        nargs='+',
        type=int,
        default=[],
        help="Pickups to exclude from the randomization."
    )
    parser.add_argument(
        "--randomize-elevators",
        action="store_true",
        help="Randomize elevators as well."
    )


def validate_command_logic(args):
    debug._DEBUG_LEVEL = args.debug
    data = prime_database.decode_data_file(args)
    randomizer_log = log_parser.parse_log(args.logfile)
    resolver_config = build_resolver_configuration(args)

    print(args)
    raise SystemExit

    if not run_resolver(data, randomizer_log, resolver_config):
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
    add_resolver_config_arguments(parser)
    prime_database.add_data_file_argument(parser)
    parser.add_argument(
        "--debug",
        choices=range(4),
        type=int,
        default=0,
        help="The level of debug logging to print.")
    parser.set_defaults(func=validate_command_logic)


def generate_seed_command_logic(args):
    data = prime_database.decode_data_file(args)
    randomizer_config = build_randomizer_configuration(args)
    resolver_config = build_resolver_configuration(args)

    seed, seed_count = search_seed(
        data,
        randomizer_config,
        resolver_config,
        args.minimum_difficulty,
        args.quiet,
        args.start_on_seed
    )
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

    add_resolver_config_arguments(parser)
    add_randomizer_configuration_arguments(parser)
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
    if args.output_file:
        out = open(args.output_file, "w")
    else:
        out = sys.stdout
    log_parser.generate_log(args.seed, args.exclude_pickups, args.randomize_elevators).write(out)
    out.close()


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
    add_randomizer_configuration_arguments(parser)
    parser.add_argument(
        "--output-file",
        type=str,
        help="Where to write output to. Defaults to standard output."
    )
    parser.set_defaults(func=generate_seed_log_command_logic)


def analyze_seed_log_command_logic(args):
    randomizer_log = log_parser.parse_log(args.logfile)

    major_pickups_per_world = defaultdict(int)
    world_importance = defaultdict(int)

    pickup_database = randomizer_log.pickup_database
    for entry in pickup_database.entries:
        if entry.item in pickup_database.pickup_importance:
            major_pickups_per_world[entry.world] += 1
            world_importance[entry.world] += pickup_database.pickup_importance[entry.item]

    print("World Major Pickup Count:")
    for world, count in major_pickups_per_world.items():
        print(world, count)
    print()

    print("World Importance Count:")
    for world, count in world_importance.items():
        print(world, count)


def add_analyze_seed_log_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "analyze-seed-log",
        help="Analyzes how the major pickups are distributed in a given seed.",
        formatter_class=argparse.MetavarTypeHelpFormatter
    )
    parser.add_argument(
        "logfile",
        type=str,
        help="Path to the log file of a Randomizer run.")
    parser.set_defaults(func=analyze_seed_log_command_logic)


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "echoes",
        help="Actions regarding Metroid Prime 2: Echoes"
    )
    sub_parsers = parser.add_subparsers(dest="command")
    add_validate_command(sub_parsers)
    add_generate_seed_command(sub_parsers)
    add_generate_seed_log_command(sub_parsers)
    add_analyze_seed_log_command(sub_parsers)
    prime_database.create_subparsers(sub_parsers)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
