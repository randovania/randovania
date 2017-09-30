import argparse

from randovania import log_parser, impossible_check


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("logfile", help="Path to the log file of a Randomizer run.")
    parser.add_argument("--game", choices=("prime2", "auto"), default="auto",
                        help="The game to check. Auto will try to decide based on zone names in the log.")
    args = parser.parse_args()
    log = log_parser.parse_log(args.logfile)

    if args.game == "auto":
        args.game = log_parser.deduce_game(log)

    if args.game == "prime2":
        impossible_check.echoes(log)



if __name__ == "__main__":
    main()