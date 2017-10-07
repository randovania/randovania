import argparse
import os

from randovania.resolver import resolver, data_reader
from randovania.games.prime import log_parser


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "logfile", help="Path to the log file of a Randomizer run.")
    parser.add_argument(
        "--difficulty",
        type=int,
        default=0,
        choices=range(6),
        help=
        "The difficulty level to check with. Higher numbers implies in harder tricks."
    )
    parser.add_argument(
        "--enable-tricks",
        action="store_const",
        const=True,
        help=
        "Enable trick usage in the validation. " 
        "Currently, there's no way to control which individual tricks gets enabled."
    )
    parser.add_argument(
        "--data-file",
        type=str,
        help="Path to the game description file. Defaults to a provided file based on game."
    )
    args = parser.parse_args()
    randomizer_log = log_parser.parse_log(args.logfile)

    if args.data_file is None:
        args.data_file = os.path.join(os.path.dirname(__file__), "data", "prime2.bin")

    game_description = data_reader.read(args.data_file, randomizer_log.pickup_database)
    possible = resolver.resolve(args.difficulty, args.enable_tricks, game_description)
    print("Game is possible: ", possible)
    if not possible:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
