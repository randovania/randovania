import argparse
import os

from randovania import cli
from randovania.resolver import resolver, data_reader
from randovania.games.prime import log_parser


def main():
    parser = argparse.ArgumentParser()
    cli.create_subparsers(parser.add_subparsers())
    args = parser.parse_args()
    args.func(args)



if __name__ == "__main__":
    main()
