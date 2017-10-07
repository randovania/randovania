import argparse
import os

from randovania import cli
from randovania.resolver import resolver, data_reader
from randovania.games.prime import log_parser


def main():
    parser = argparse.ArgumentParser()
    cli.create_subparsers(parser.add_subparsers(dest="game"))
    args = parser.parse_args()
    if args.game is None:
        parser.print_help()
        raise SystemExit(1)

    args.func(args)



if __name__ == "__main__":
    main()
