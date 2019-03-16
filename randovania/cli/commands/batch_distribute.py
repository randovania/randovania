import multiprocessing
import time
from argparse import ArgumentParser
from pathlib import Path

from randovania.cli.echoes_lib import add_layout_configuration_arguments
from randovania.layout.permalink import Permalink
from randovania.resolver import generator


def batch_distribute_helper(base_permalink: Permalink, seed_number: int, output_dir: Path) -> float:
    permalink = Permalink(
        seed_number=seed_number,
        spoiler=True,
        patcher_configuration=base_permalink.patcher_configuration,
        layout_configuration=base_permalink.layout_configuration,
    )

    start_time = time.perf_counter()
    description = generator.generate_list(permalink, None, True)
    delta_time = time.perf_counter() - start_time

    description.save_to_file(output_dir.joinpath("{}.json".format(seed_number)))
    return delta_time


def batch_distribute_command_logic(args):
    finished_count = 0

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    base_permalink = Permalink.from_str(args.permalink)

    def callback(result):
        nonlocal finished_count
        finished_count += 1
        print("Finished seed in {} seconds. At {} of {} seeds.".format(result, finished_count, args.seed_count))

    def error_callback(e):
        nonlocal finished_count
        finished_count += 1
        print("Failed to generate seed: {}".format(e))

    with multiprocessing.Pool() as pool:
        for seed_number in range(base_permalink.seed_number, base_permalink.seed_number + args.seed_count):
            pool.apply_async(
                func=batch_distribute_helper,
                args=(base_permalink, seed_number, output_dir),
                callback=callback,
                error_callback=error_callback,
            )
        pool.close()
        pool.join()


def add_batch_distribute_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "batch-distribute",
        help="Generate multiple seeds in parallel"
    )

    add_layout_configuration_arguments(parser)
    parser.add_argument("permalink", type=str, help="The permalink to use")
    parser.add_argument(
        "seed_count",
        type=int,
        help="How many seeds to generate.")
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Where to place the seed logs.")
    parser.set_defaults(func=batch_distribute_command_logic)
