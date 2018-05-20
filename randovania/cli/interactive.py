import os
import subprocess
from argparse import ArgumentParser
from typing import BinaryIO

from randovania import get_data_path
from randovania.games.prime import binary_data
from randovania.interface_common.options import value_parsers, options_validation, Options
from randovania.resolver.echoes import search_seed, RandomizerConfiguration, ResolverConfiguration


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
                     _                       _       
                    | |                     (_)      
 _ __ __ _ _ __   __| | _____   ____ _ _ __  _  __ _ 
| '__/ _` | '_ \ / _` |/ _ \ \ / / _` | '_ \| |/ _` |
| | | (_| | | | | (_| | (_) \ V / (_| | | | | | (_| |
|_|  \__,_|_| |_|\__,_|\___/ \_/ \__,_|_| |_|_|\__,_|

    ===  Welcome to randovania interactive mode!

""")

    parsing_commands = True
    options = Options()
    options.load_from_disk()

    def print_config():
        print("        === Current configuration ===")
        spacing: int = max(len(option_name) for option_name in options.keys())
        for option_name, value in options.items():
            print("{0:>{spacing}}  {1}".format(option_name, value, spacing=spacing))
        print()

    def change_option(key, value):
        options[key] = value
        options.save_to_disk()

    def quit_shell():
        raise SystemExit(0)

    def generate():
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
        change_option("seed", seed)
        print("Try the 'randomize' command to use this seed.")

    def randomize():
        if not has_randomizer_binary():
            print("== WARNING ==\n"
                  "Randomizer.exe not found in the current directory, cannot randomize the game files.\n")
            return

        if not options["game_files_path"]:
            print("game_files_path is not set, no game to randomize.")
            return

        randomizer_config = RandomizerConfiguration(options["excluded_pickups"], options["randomize_elevators"])
        apply_seed(randomizer_config, options["seed"],
                   options["item_loss_enabled"], options["hud_memo_popup_removal"], options["game_files_path"])

    commands = {
        "view_config": print_config,
        "quit": quit_shell,
        "exit": quit_shell,
        "generate": generate,
        "randomize": randomize,
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

    print("Please enter your commands. If in doubt, type 'help'.\n")

    while parsing_commands:
        try:
            command = input("> ").split(" ", 1)
        except EOFError:
            quit_shell()
        first_part = command[0]

        if first_part in options:
            try:
                the_value = value_parsers[type(options[first_part])](command[1])
                if first_part in options_validation:
                    options_validation[first_part](the_value, options)
                change_option(first_part, the_value)
            except ValueError as e:
                print("'{}' is an invalid value for '{}': {}".format(command[1], first_part, e))
            except IndexError:
                print("Missing value!")

        elif first_part in commands:
            commands[first_part]()

        elif first_part == '\x04':
            quit_shell()

        elif first_part:
            print("Unknown command '{}'. If in doubt, type 'help'.".format(first_part))

    input("Press anything to exit.")


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "interactive",
        help="Enter an interactive console"
    )
    parser.set_defaults(func=interactive_shell)
