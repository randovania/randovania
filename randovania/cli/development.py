from argparse import ArgumentParser

from randovania.cli.commands.refresh_presets import add_refresh_presets_command

__all__ = ["create_subparsers"]


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "development",
        help="Actions that helps Randovania development"
    )
    sub_parsers = parser.add_subparsers(dest="command")
    add_refresh_presets_command(sub_parsers)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
