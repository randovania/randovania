import json
import os
import subprocess
from argparse import ArgumentParser
from typing import BinaryIO, List

import py

from randovania import get_data_path
from randovania.games.prime import binary_data
from randovania.resolver.echoes import search_seed, RandomizerConfiguration, ResolverConfiguration


def load_options_to(current_options):
    try:
        with open(os.path.expanduser("~/.config/randovania.json")) as options_file:
            new_options = json.load(options_file)

        for option_name in current_options.keys():
            if option_name in new_options:
                current_options[option_name] = new_options[option_name]

    except FileNotFoundError:
        pass


def save_options(options):
    config_folder = py.path.local(os.path.expanduser("~/.config"))
    config_folder.ensure_dir()
    with config_folder.join("randovania.json").open("w") as options_file:
        json.dump(options, options_file)


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


def value_parser_str(s: str) -> str:
    return s


def value_parser_int_array(s: str) -> List[int]:
    if s.lower() == "none":
        return []
    return [
        value_parser_int(x) for x in s.split()
    ]


value_parsers = {
    int: value_parser_int,
    bool: value_parser_bool,
    str: value_parser_str,
    list: value_parser_int_array,
}


def has_randomizer_binary():
    return os.path.isfile("Randomizer.exe")


def apply_seed(randomizer_config: RandomizerConfiguration,
               seed: int,
               item_loss: bool,
               hud_memo_popup_removal: bool,
               game_files: str):

    if not os.path.isdir(game_files):
        print("Cannot apply seed: '{}' is not a dir.".format(game_files))
        print("Enter the path to the game:")
        game_files = input("> ")

    args = [
        "Randomizer.exe",
        game_files,
        "-s", str(seed),
        "-e", ",".join(str(pickup) for pickup in randomizer_config.exclude_pickups) or "none",
    ]
    if not item_loss:
        args.append("-i")
    if hud_memo_popup_removal:
        args.append("-h")
    if randomizer_config.randomize_elevators:
        args.append("-v")

    print("Running the Randomizer with: ", args)
    subprocess.run(args, check=True)


def interactive_shell(args):
    data_file_path = os.path.join(get_data_path(), "prime2.bin")
    with open(data_file_path, "rb") as x:  # type: BinaryIO
        data = binary_data.decode(x)

    print("""
 _______  _______  _        ______   _______           _______  _       _________ _______ 
(  ____ )(  ___  )( (    /|(  __  \ (  ___  )|\     /|(  ___  )( (    /|\__   __/(  ___  )
| (    )|| (   ) ||  \  ( || (  \  )| (   ) || )   ( || (   ) ||  \  ( |   ) (   | (   ) |
| (____)|| (___) ||   \ | || |   ) || |   | || |   | || (___) ||   \ | |   | |   | (___) |
|     __)|  ___  || (\ \) || |   | || |   | |( (   ) )|  ___  || (\ \) |   | |   |  ___  |
| (\ (   | (   ) || | \   || |   ) || |   | | \ \_/ / | (   ) || | \   |   | |   | (   ) |
| ) \ \__| )   ( || )  \  || (__/  )| (___) |  \   /  | )   ( || )  \  |___) (___| )   ( |
|/   \__/|/     \||/    )_)(______/ (_______)   \_/   |/     \||/    )_)\_______/|/     \|

    ===  Welcome to the randovania interactive shell!
    
""")

    parsing_commands = True
    options = {
        "max_difficulty": 3,
        "min_difficulty": 0,
        "item_loss_enabled": False,
        "tricks_enabled": True,
        "excluded_pickups": [],
        "randomize_elevators": False,
        "hud_memo_popup_removal": True,
        "game_files": "",
    }
    load_options_to(options)

    def print_config():
        print("        === Current configuration ===\n"
              "         max_difficulty  {max_difficulty}\n"
              "         min_difficulty  {min_difficulty}\n"
              "      item_loss_enabled  {item_loss_enabled}\n"
              "         tricks_enabled  {tricks_enabled}\n"
              "       excluded_pickups  {excluded_pickups}\n"
              "    randomize_elevators  {randomize_elevators}\n"
              " hud_memo_popup_removal  {hud_memo_popup_removal}\n"
              "        game_files_path  {game_files_path}\n"
              "".format(**options))

    def quit_shell():
        raise SystemExit(0)

    def stop_parsing_commands():
        nonlocal parsing_commands
        parsing_commands = False

    commands = {
        "view_config": print_config,
        "quit": quit_shell,
        "exit": quit_shell,
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
    print_config()

    if not has_randomizer_binary():
        print("== WARNING ==\n"
              "Randomizer.exe not found in the current directory, cannot automatically apply the seed.\n")

    print("Please enter your commands. If in doubt, type 'help'.\n")

    while parsing_commands:
        try:
            command = input("> ").split(" ", 1)
        except EOFError:
            quit_shell()
        first_part = command[0]

        if first_part in options:
            try:
                options[first_part] = value_parsers[type(options[first_part])](command[1])
                save_options(options)
            except ValueError as e:
                print("Invalid value for '{}': {}".format(first_part, e))
            except IndexError:
                print("Missing value!")

        elif first_part in commands:
            commands[first_part]()

        elif first_part == '\x04':
            quit_shell()

        elif first_part:
            print("Unknown command '{}'. If in doubt, type 'help'.".format(first_part))

    randomizer_config = RandomizerConfiguration(options["excluded_pickups"], options["randomize_elevators"])
    resolver_config = ResolverConfiguration(options["max_difficulty"],
                                            options["min_difficulty"],
                                            options["tricks_enabled"],
                                            options["item_loss_enabled"])

    print("\n== Will now search for a seed!")
    print_config()
    print("\n* This may take a while, and your computer may not respond correctly while running.")

    seed, seed_count = search_seed(data, randomizer_config, resolver_config)
    print("A seed was found with the given configuration after {} attempts.".format(seed_count))
    print("\n=== Seed: {}".format(seed))

    if has_randomizer_binary():
        apply_seed(randomizer_config, seed,
                   options["item_loss"], options["hud_memo_popup_removal"], options["game_files"])

    input("Press anything to exit.")


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "interactive",
        help="Enter an interactive console"
    )
    parser.set_defaults(func=interactive_shell)
