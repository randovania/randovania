import multiprocessing

from randovania import cli


def main():
    multiprocessing.freeze_support()
    cli.run_cli()


if __name__ == "__main__":
    main()
