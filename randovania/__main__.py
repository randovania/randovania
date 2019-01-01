import multiprocessing
import sys

from randovania import cli


def main():
    multiprocessing.freeze_support()
    cli.run_cli(sys.argv)


if __name__ == "__main__":
    main()
