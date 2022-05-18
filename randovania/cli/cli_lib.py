import statistics
from argparse import ArgumentParser


def add_debug_argument(parser: ArgumentParser):
    parser.add_argument(
        "--debug",
        choices=range(4),
        type=int,
        default=0,
        help="The level of debug logging to print.")


def add_validate_argument(parser: ArgumentParser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--validate", action="store_true", dest="validate", default=True,
                       help="After generating a layout, validate if it's possible. Default behaviour.")
    group.add_argument("--no-validate", action="store_false", dest="validate", default=True,
                       help="After generating a layout, don't validate if it's possible.")


def print_report_multiple_times(total_times: list[float]):
    print(
        "Result after doing {repeat} times:\n"
        "Mean: {mean:.3f} seconds\n"
        "stdev: {stdev:.3f} seconds\n"
        "Median: {median:.3f} seconds".format(
            repeat=len(total_times),
            mean=statistics.mean(total_times),
            median=statistics.median(total_times),
            stdev=statistics.stdev(total_times)
        ))
