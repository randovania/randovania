from argparse import ArgumentParser

from randovania.cli.commands.patcher_data import add_patcher_data_command
from randovania.cli.commands.batch_distribute import add_batch_distribute_command
from randovania.cli.commands.generate import add_generate_commands
from randovania.cli.commands.permalink import add_permalink_command
from randovania.cli.commands.validate import add_validate_command

__all__ = ["create_subparsers"]


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "layout",
        help="Actions regarding generating layouts and permalinks"
    )
    sub_parsers = parser.add_subparsers(dest="command")
    add_validate_command(sub_parsers)
    add_generate_commands(sub_parsers)
    add_patcher_data_command(sub_parsers)
    add_batch_distribute_command(sub_parsers)
    add_permalink_command(sub_parsers)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
