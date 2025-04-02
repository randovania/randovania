import asyncio
import base64
import collections
import dataclasses
import functools
import math
import statistics
import time
import typing
from argparse import Namespace
from asyncio import CancelledError
from concurrent.futures import Future, ProcessPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.game.game_enum import RandovaniaGame
from randovania.interface_common import sleep_inhibitor
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink, PermalinkBinary
from randovania.lib import json_lib
from randovania.resolver.exceptions import GenerationFailure, ImpossibleForSolver

if TYPE_CHECKING:
    from argparse import ArgumentParser


def read_file(path: Path) -> dict[str, float | None]:
    return typing.cast("dict[str, float | None]", json_lib.read_dict(path)["permalinks"])


def write_file(path: Path, permalinks: dict[str, float | None]) -> None:
    json_lib.write_path(
        path,
        {"schema_version": 1, "permalinks": permalinks},
    )


def generate_helper(parameter: GeneratorParameters) -> float | None:
    from randovania.generator import generator

    start_time = time.perf_counter()

    try:
        asyncio.run(
            generator.generate_and_validate_description(
                generator_params=parameter,
                status_update=None,
                validate_after_generation=True,
                attempts=0,
            )
        )

    except (ImpossibleForSolver, GenerationFailure, CancelledError):
        return None

    delta_time = time.perf_counter() - start_time

    return delta_time


def generate_list_of_permalinks(parameters: list[GeneratorParameters], process_count: int) -> list[float | None]:
    finished_count = 0
    all_futures: list[Future[float | None]] = []

    total_count = len(parameters)
    results: list[float | None] = [None] * total_count
    num_digits = math.ceil(math.log10(total_count + 1))
    number_format = "[{0:" + str(num_digits) + "d}/{1}] "

    def with_result(index: int, r: Future[float | None]) -> None:
        nonlocal finished_count
        finished_count += 1
        print(number_format.format(finished_count, total_count))

        try:
            results[index] = r.result()

        except (Exception, KeyboardInterrupt) as e:
            if isinstance(e, KeyboardInterrupt):
                print("Interrupt requested.")
            else:
                print(f"Unexpected exception: {e} ({type(e)}).")
            for f in all_futures:
                f.cancel()

    try:
        with sleep_inhibitor.get_inhibitor():
            with ProcessPoolExecutor(max_workers=process_count) as pool:
                for i, p in enumerate(parameters):
                    result = pool.submit(
                        generate_helper,
                        p,
                    )
                    result.add_done_callback(functools.partial(with_result, i))
                    all_futures.append(result)
    except KeyboardInterrupt:
        pass

    return results


@dataclasses.dataclass
class Report:
    times: list[float] = dataclasses.field(default_factory=list)
    failures: int = 0
    fixes: int = 0


def print_report(header: str, reports: dict[RandovaniaGame, Report]) -> None:
    print("{:>30} |{:>6} |{:>9} |{:>9} |{:>9} |{:>9}".format(header, "Fixes", "Failures", "Mean", "Stdev", "Median"))
    for game, report in reports.items():
        mean = 0.0
        stdev = 0.0
        median = 0.0
        if report.times:
            mean = statistics.mean(report.times)
            stdev = statistics.stdev(report.times)
            median = statistics.median(report.times)

        name = game.long_name
        print(f"{name:>30} |{report.fixes:> 6} |{report.failures:> 9} |{mean: 9.3f} |{stdev: 9.3f} |{median: 9.3f}")


def compare_reports(
    parameters: list[GeneratorParameters], reference: list[float | None], results: list[float | None]
) -> None:
    difference_report: dict[RandovaniaGame, Report] = collections.defaultdict(Report)

    for param, reference_dt, result_dt in zip(parameters, reference, results, strict=True):
        report = difference_report[param.get_preset(0).game]
        if result_dt is None:
            if reference_dt is None:
                pass
            else:
                report.failures += 1

        elif reference_dt is None:
            report.fixes += 1
        else:
            report.times.append(result_dt - reference_dt)

    print_report("Difference", difference_report)


def run_logic(args: Namespace) -> None:
    base_seed = 1000
    process_count = 6
    preset_manager = PresetManager(None)

    link_str_for_param = []
    reference_params = []

    games = RandovaniaGame.all_games()
    if args.game is not None:
        games = [RandovaniaGame(args.game)]

    count = args.seed_count

    for game in games:
        for i in range(count):
            permalink = Permalink.from_parameters(
                GeneratorParameters(
                    seed_number=base_seed + i,
                    spoiler=True,
                    development=True,
                    presets=[preset_manager.default_preset_for_game(game).get_preset()],
                )
            )
            if i % 1000 == 0 and i > 0:
                print(f"Generated Permalink {i}...")
            link_str_for_param.append(permalink.as_base64_str)
            reference_params.append(permalink.parameters)

    results: list[float | None]
    if args.no_data:
        results = [None] * len(reference_params)
    else:
        results = generate_list_of_permalinks(reference_params, process_count)

    if args.output_file:
        write_file(args.output_file, dict(zip(link_str_for_param, results, strict=True)))

    game_report: dict[RandovaniaGame, Report] = collections.defaultdict(Report)

    for param, dt in zip(reference_params, results, strict=True):
        report = game_report[param.get_preset(0).game]
        if dt is None:
            report.failures += 1
        else:
            report.times.append(dt)

    print_report("Results", game_report)


def repeat_logic(args: Namespace) -> None:
    input_file: Path = args.input_file

    reference = read_file(input_file)
    process_count = 6

    link_str_for_param = []
    reference_params = []
    reference_results = []

    for link_str, link_data in reference.items():
        link_str_for_param.append(link_str)
        reference_params.append(Permalink.from_str(link_str).parameters)
        reference_results.append(link_data)

    generate_results = generate_list_of_permalinks(reference_params, process_count)

    if args.output_file:
        write_file(args.output_file, dict(zip(link_str_for_param, generate_results, strict=True)))

    compare_reports(reference_params, reference_results, generate_results)


def _extract_generator_params_bytes(link: str) -> bytes:
    encoded_param = link.encode("utf-8")
    encoded_param += b"=" * ((4 - len(encoded_param)) % 4)

    b = base64.b64decode(encoded_param, altchars=b"-_", validate=True)
    data = PermalinkBinary.parse(b).value
    return data.generator_params


def compare_logic(args: Namespace) -> None:
    reference_data = read_file(args.reference_file)
    new_data = read_file(args.new_file)

    results = {
        _extract_generator_params_bytes(link_str): (link_str, link_data) for link_str, link_data in new_data.items()
    }

    reference_params = []
    reference_times = []
    result_times = []

    for link_str, reference_time in reference_data.items():
        param_bytes = _extract_generator_params_bytes(link_str)
        generator_params = GeneratorParameters.from_bytes(param_bytes)
        reference_params.append(generator_params)

        reference_times.append(reference_time)
        if param_bytes not in results:
            raise ValueError(f"Missing data for permalink {link_str} in results")
        result_times.append(results.pop(param_bytes)[1])

    if results:
        bad_permalinks = [link for link, _ in results.values()]
        raise ValueError(f"The following permalinks have no reference data: {bad_permalinks}")

    compare_reports(reference_params, reference_times, result_times)


def add_commands(sub_parsers: typing.Any) -> None:
    create_parser: ArgumentParser = sub_parsers.add_parser("run", help="Create a session file.")
    create_parser.add_argument(
        "--game",
        type=str,
        choices=[game.value for game in RandovaniaGame.all_games()],
        help="Use the included database for the given game.",
    )
    create_parser.add_argument("--no-data", action="store_true", help="Do not include any data in the report.")
    create_parser.add_argument("--output-file", type=Path, help="Saves the results to a file, to compare later on.")
    create_parser.add_argument(
        "--seed-count", type=int, default=100, help="How many seeds should be genned for the benchmark."
    )
    create_parser.set_defaults(func=run_logic)

    repeat_parser: ArgumentParser = sub_parsers.add_parser("repeat", help="Repeats a benchmark session")
    repeat_parser.add_argument("--output-file", type=Path, help="Save the new session.")
    repeat_parser.add_argument("input_file", type=Path, help="The session to repeat.")
    repeat_parser.set_defaults(func=repeat_logic)

    compare_parse: ArgumentParser = sub_parsers.add_parser("compare", help="Compares two result files")
    compare_parse.add_argument("reference_file", type=Path, help="The session to compare against.")
    compare_parse.add_argument("new_file", type=Path, help="The new session data.")
    compare_parse.set_defaults(func=compare_logic)
