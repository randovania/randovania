import argparse
import multiprocessing

from randovania import cli


def main():
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser()
    cli.create_subparsers(parser.add_subparsers(dest="game"))
    args = parser.parse_args()
    if args.game is None:
        parser.print_help()
        raise SystemExit(1)

    args.func(args)


if __name__ == "__main__":
    main()
