import logging
import multiprocessing
import sys

from randovania import cli

logging.basicConfig(level=logging.WARNING)


# logging.root.setLevel(logging.DEBUG)


def main():
    multiprocessing.freeze_support()
    cli.run_cli(sys.argv)


if __name__ == "__main__":
    main()
