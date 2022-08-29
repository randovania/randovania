import logging
import multiprocessing
import sys

logging.basicConfig(level=logging.WARNING)


def main():
    multiprocessing.freeze_support()

    import randovania
    randovania.setup_logging('INFO', None, quiet=True)

    logging.debug("Starting Randovania...")

    from randovania import cli
    cli.run_cli(sys.argv)


if __name__ == "__main__":
    main()
