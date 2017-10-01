import argparse

import os

from randovania import log_parser, impossible_check, datareader, resolver
from randovania.log_parser import Game


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("logfile", help="Path to the log file of a Randomizer run.")
    parser.add_argument("--game", choices=log_parser.generate_game_choices(), default="auto",
                        help="The game to check. Auto will try to decide based on zone names in the log.")
    args = parser.parse_args()
    log = log_parser.parse_log(args.logfile)

    game = log_parser.resolve_game_argument(args.game, log)
    if game == Game.PRIME2:
        game_description = datareader.read(os.path.join(os.path.dirname(__file__), "data", "prime2.bin"),
                                           log.pickup_entries)
        resolver.resolve(game_description)


if __name__ == "__main__":
    main()
