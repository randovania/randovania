import argparse
import os

from randovania import log_parser, datareader, resolver
from randovania.log_parser import Game


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "logfile", help="Path to the log file of a Randomizer run.")
    parser.add_argument(
        "--game",
        choices=log_parser.generate_game_choices(),
        default="auto",
        help=
        "The game to check. Auto will try to decide based on zone names in the log."
    )
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
    args = parser.parse_args()
    log = log_parser.parse_log(args.logfile)

    game = log_parser.resolve_game_argument(args.game, log)
    if game == Game.PRIME2:
        game_description = datareader.read(
            os.path.join(os.path.dirname(__file__), "data", "prime2.bin"),
            log.pickup_entries)
        resolver.resolve(args.difficulty, args.enable_tricks, game_description)


if __name__ == "__main__":
    main()
