from argparse import ArgumentParser


def server_command_logic(args):
    from randovania.server import app
    server_app = app.create_app()
    server_app.sio.sio.run(server_app, host="0.0.0.0")


def add_server_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "server",
        help="Hosts a multiworld server."
    )
    parser.set_defaults(func=server_command_logic)


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "multiworld",
        help="CLI tools for handling multiworld"
    )
    sub_parsers = parser.add_subparsers(dest="command")
    add_server_command(sub_parsers)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
