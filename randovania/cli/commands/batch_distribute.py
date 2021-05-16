import asyncio
import math
import multiprocessing
import time
import typing
from argparse import ArgumentParser
from pathlib import Path

from randovania.cli import echoes_lib
from randovania.interface_common import sleep_inhibitor


def batch_distribute_helper(base_permalink,
                            seed_number: int,
                            timeout: int,
                            validate: bool,
                            output_dir: Path,
                            ) -> float:
    from randovania.generator import generator
    from randovania.layout.permalink import Permalink

    permalink = Permalink(
        seed_number=seed_number,
        spoiler=True,
        presets=typing.cast(Permalink, base_permalink).presets,
    )

    start_time = time.perf_counter()
    description = asyncio.run(generator.generate_and_validate_description(
        permalink=permalink, status_update=None,
        validate_after_generation=validate, timeout=timeout,
        attempts=0,
    ))
    delta_time = time.perf_counter() - start_time

    description.save_to_file(output_dir.joinpath("{}.{}".format(seed_number, description.file_extension())))
    return delta_time


def batch_distribute_command_logic(args):
    from randovania.layout.permalink import Permalink

    finished_count = 0

    timeout: int = args.timeout
    validate: bool = args.validate

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    seed_count = args.seed_count
    num_digits = math.ceil(math.log10(seed_count + 1))
    number_format = "[{0:" + str(num_digits) + "d}/{1}] "
    base_permalink = Permalink.from_str(args.permalink)

    def report_update(msg: str):
        nonlocal finished_count
        finished_count += 1
        print(number_format.format(finished_count, seed_count) + msg)

    def callback(result):
        report_update(f"Finished seed in {result} seconds.")

    def error_callback(e):
        report_update(f"Failed to generate seed: {e}")

    with multiprocessing.Pool(processes=args.process_count) as pool, sleep_inhibitor.get_inhibitor():
        for seed_number in range(base_permalink.seed_number, base_permalink.seed_number + args.seed_count):
            pool.apply_async(
                func=batch_distribute_helper,
                args=(base_permalink, seed_number, timeout, validate, output_dir),
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

    parser.add_argument("permalink", type=str, help="The permalink to use")
    parser.add_argument("--process-count", type=int, help="How many processes to use. Defaults to CPU count.")
    parser.add_argument(
        "--timeout",
        type=int,
        default=90,
        help="How many seconds to wait before timing out a generation/validation.")
    echoes_lib.add_validate_argument(parser)
    parser.add_argument(
        "seed_count",
        type=int,
        help="How many seeds to generate.")
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Where to place the seed logs.")
    parser.set_defaults(func=batch_distribute_command_logic)
