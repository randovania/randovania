from __future__ import annotations

import asyncio
import time
import typing
from pathlib import Path

from randovania.cli import cli_lib
from randovania.cli.commands import permalink as permalink_command
from randovania.resolver import debug

if typing.TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction

    from randovania.layout.permalink import Permalink


def common_generate_logic(args: Namespace, permalink: Permalink) -> None:
    from randovania.generator import generator
    from randovania.layout.layout_description import LayoutDescription, shareable_hash

    def status_update(s: str | None) -> None:
        if args.status_update:
            print(s)

    if permalink.parameters.spoiler:
        debug.set_level(args.debug)

    attempts = generator.DEFAULT_ATTEMPTS
    if args.no_retry:
        attempts = 0

    shareable_hashes = []
    total_times = []

    layout_description: LayoutDescription | None = None
    for _ in range(args.repeat):
        before = time.perf_counter()
        layout_description = asyncio.run(
            generator.generate_and_validate_description(
                generator_params=permalink.parameters,
                status_update=status_update,
                validate_after_generation=args.validate,
                timeout=None,
                attempts=attempts,
            )
        )
        after = time.perf_counter()
        total_times.append(after - before)
        shareable_hashes.append(layout_description.shareable_hash)
        print(f"Took {total_times[-1]:.3f} seconds. Hash: {shareable_hashes[-1]}")

    assert layout_description is not None
    layout_description.save_to_file(args.output_file)
    if args.repeat > 1:
        cli_lib.print_report_multiple_times(total_times)

    if permalink.seed_hash is not None and permalink.seed_hash != layout_description.shareable_hash_bytes:
        print(f"!WARNING! Expected {shareable_hash(permalink.seed_hash)}.")


def generate_from_permalink_logic(args: Namespace) -> None:
    from randovania.layout.permalink import Permalink

    permalink = Permalink.from_str(args.permalink)
    common_generate_logic(args, permalink)


def generate_from_preset_logic(args: Namespace) -> None:
    if args.seed_number is None:
        args.seed_number = 0

    permalink = permalink_command.create_permalink(args)
    print(f"Permalink: {permalink.as_base64_str}")
    common_generate_logic(args, permalink)


def common_generate_arguments(parser: ArgumentParser) -> None:
    cli_lib.add_debug_argument(parser)
    cli_lib.add_validate_argument(parser)
    parser.add_argument("--repeat", default=1, type=int, help="Generate multiple times. Used for benchmarking.")
    parser.add_argument("--no-retry", default=False, action="store_true", help="Disable retries in the generation.")
    parser.add_argument("--status-update", default=False, action="store_true", help="Print the status updates.")
    parser.add_argument("output_file", type=Path, help="Where to place the seed log.")


def add_generate_commands(sub_parsers: _SubParsersAction) -> None:
    parser_permalink: ArgumentParser = sub_parsers.add_parser(
        "generate-from-permalink", help="Generate a layout from a permalink."
    )
    common_generate_arguments(parser_permalink)
    parser_permalink.add_argument("--permalink", required=True, type=str, help="The permalink to use")
    parser_permalink.set_defaults(func=generate_from_permalink_logic)

    parser_presets: ArgumentParser = sub_parsers.add_parser(
        "generate-from-presets", help="Generate a layout from a list of presets."
    )
    common_generate_arguments(parser_presets)
    permalink_command.add_permalink_arguments(parser_presets)
    parser_presets.set_defaults(func=generate_from_preset_logic)
