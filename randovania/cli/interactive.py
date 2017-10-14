from argparse import ArgumentParser

import os
from typing import BinaryIO, List

from randovania import get_data_path
from randovania.games.prime import binary_data
from randovania.resolver.echoes import search_seed, RandomizerConfiguration, ResolverConfiguration


def value_parser_int(s: str) -> int:
    try:
        return int(s)
    except ValueError:
        raise ValueError("'{}' is not a number.".format(s)) from None


def value_parser_bool(s: str) -> bool:
    false_values = ("off", "false", "no", "0")
    true_values = ("on", "true", "yes", "1")
    s = s.lower()
    if s not in false_values and s not in true_values:
        raise ValueError("{} is not a boolean value.".format(s))
    return s in true_values


def value_parser_int_array(s: str) -> List[int]:
    if s.lower() == "none":
        return []
    return [
        value_parser_int(x) for x in s.split()
    ]


value_parsers = {
    int: value_parser_int,
    bool: value_parser_bool,
    list: value_parser_int_array,
}


def try_apply_seed(randomizer_config, item_loss, seed):
    if not os.path.isfile("Randomizer.exe"):
        print("* Randomizer.exe not found in the current directory, cannot automatically apply the seed.")
        return False


def interactive_shell(args):
    data_file_path = os.path.join(get_data_path(), "prime2.bin")
    with open(data_file_path, "rb") as x:  # type: BinaryIO
        data = binary_data.decode(x)

    print("Welcome to randovania interactive shell!")

    parsing_commands = True
    options = {
        "max_difficulty": 3,
        "min_difficulty": 0,
        "item_loss": False,
        "tricks": True,
        "exclude_pickups": [],
        "randomize_elevators": False
    }

    def print_config():
        print("Current seed generation config:\n"
              "Max Difficulty: {max_difficulty}; Min Difficulty: {min_difficulty}; "
              "Item Loss Enabled? {item_loss}; Tricks Enabled? {tricks}\n"
              "Exclude Pickups: {exclude_pickups}\n"
              "Randomize Elevators? {randomize_elevators}\n"
              "".format(**options))

    def quit_shell():
        raise SystemExit(0)

    def stop_parsing_commands():
        nonlocal parsing_commands
        parsing_commands = False

    commands = {
        "view_config": print_config,
        "quit": quit_shell,
        "generate": stop_parsing_commands,
    }

    def print_help():
        print("You can:\n"
              "* Type an option name followed by it's new value.\n"
              "* Type an command to execute it.\n"
              "\n"
              "Options: {options}\n"
              "Commands: {commands}\n"
              "\n"
              "Example:\n"
              "max_difficulty 5\n"
              "item_loss true\n"
              "exclude_pickups 15 36 47\n"
              "generate\n"
              "".format(options=", ".join(option for option in sorted(options.keys())),
                        commands=", ".join(command for command in sorted(commands.keys()))))

    commands["help"] = print_help
    print_help()
    print_config()

    while parsing_commands:
        command = input("> ").split(" ", 1)
        first_part = command[0]

        if first_part in options:
            try:
                options[first_part] = value_parsers[type(options[first_part])](command[1])
            except ValueError as e:
                print("Invalid value for '{}': {}".format(first_part, e))
            except IndexError:
                print("Missing value!")

        elif first_part in commands:
            commands[first_part]()

        else:
            print("Unknown command '{}'. If in doubt, type 'help'.".format(command))

    randomizer_config = RandomizerConfiguration(options["exclude_pickups"], options["randomize_elevators"])
    resolver_config = ResolverConfiguration(options["max_difficulty"],
                                            options["min_difficulty"],
                                            options["tricks"],
                                            options["item_loss"])

    seed, seed_count = search_seed(data, randomizer_config, resolver_config)
    print("A seed was found with the given configuration after {} attempts.".format(seed_count))
    print("\n=== Seed: {}".format(seed))

    if not try_apply_seed(randomizer_config, options["item_loss"], seed):
        input("Press anything to exit.")


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "interactive",
        help="Enter an interactive console"
    )
    parser.set_defaults(func=interactive_shell)
