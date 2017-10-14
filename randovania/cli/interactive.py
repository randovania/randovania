from argparse import ArgumentParser


def get_value(choices, cast):
    while True:
        print("Possible values: {}".format(", ".join(str(x) for x in choices)))
        command = input("> ")
        try:
            result = cast(command)
            if result in choices:
                return result
        except Exception:
            pass
        print("Invalid value.")


def interactive_shell(args):
    print("Welcome to randovania interactive shell!")
    print("We will now generate a Metroid Prime 2: Echoes randomizer seed.")
    print("Please choose a difficulty:")
    difficulty = get_value(list(range(6)), int)
    print("Item loss should be?")
    item_loss = get_value(["on", "off"], str.lower) == "on"


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "interactive",
        help="Enter an interactive console"
    )
    parser.set_defaults(func=interactive_shell)
