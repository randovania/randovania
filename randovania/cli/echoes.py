from argparse import ArgumentParser

from randovania.cli import prime_database
from randovania.cli.commands.batch_distribute import add_batch_distribute_command
from randovania.cli.commands.create_permalink import add_create_permalink_command
from randovania.cli.commands.distribute import add_distribute_command
from randovania.cli.commands.randomize_command import add_randomize_command
from randovania.cli.commands.validate import add_validate_command

__all__ = ["create_subparsers"]


def create_subparsers(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "echoes",
        help="Actions regarding Metroid Prime 2: Echoes"
    )
    sub_parsers = parser.add_subparsers(dest="command")
    add_validate_command(sub_parsers)
    add_create_permalink_command(sub_parsers)
    add_distribute_command(sub_parsers)
    add_randomize_command(sub_parsers)
    add_batch_distribute_command(sub_parsers)
    prime_database.create_subparsers(sub_parsers)

    def check_command(args):
        if args.command is None:
            parser.print_help()
            raise SystemExit(1)

    parser.set_defaults(func=check_command)
