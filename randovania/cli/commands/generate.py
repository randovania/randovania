import asyncio
import time
from argparse import ArgumentParser
from pathlib import Path

from randovania.cli import cli_lib
from randovania.cli.commands import permalink as permalink_command
from randovania.resolver import debug


def common_generate_logic(args, permalink):
    from randovania.generator import generator

    def status_update(s):
        if args.status_update:
            print(s)

    if permalink.parameters.spoiler:
        debug.set_level(args.debug)

    extra_args = {}
    if args.no_retry:
        extra_args["attempts"] = 0

    before = time.perf_counter()
    layout_description = asyncio.run(
        generator.generate_and_validate_description(generator_params=permalink.parameters,
                                                    status_update=status_update,
                                                    validate_after_generation=args.validate,
                                                    timeout=None, **extra_args))
    after = time.perf_counter()
    print("Took {} seconds. Hash: {}".format(after - before, layout_description.shareable_hash))
    layout_description.save_to_file(args.output_file)


def generate_from_permalink_logic(args):
    from randovania.layout.permalink import Permalink
    permalink = Permalink.from_str(args.permalink)
    common_generate_logic(args, permalink)


def generate_from_preset_logic(args):
    if args.seed_number is None:
        args.seed_number = 0

    permalink = permalink_command.create_permalink(args)
    print(f"Permalink: {permalink.as_base64_str}")
    common_generate_logic(args, permalink)


def common_generate_arguments(parser: ArgumentParser):
    cli_lib.add_debug_argument(parser)
    cli_lib.add_validate_argument(parser)
    parser.add_argument("--no-retry", default=False, action="store_true", help="Disable retries in the generation.")
    parser.add_argument("--status-update", default=False, action="store_true", help="Print the status updates.")
    parser.add_argument(
        "output_file",
        type=Path,
        help="Where to place the seed log."
    )


def add_generate_commands(sub_parsers):
    parser_permalink: ArgumentParser = sub_parsers.add_parser(
        "generate-from-permalink",
        help="Generate a layout from a permalink."
    )
    common_generate_arguments(parser_permalink)
    parser_permalink.add_argument("--permalink", required=True, type=str, help="The permalink to use")
    parser_permalink.set_defaults(func=generate_from_permalink_logic)

    parser_presets: ArgumentParser = sub_parsers.add_parser(
        "generate-from-presets",
        help="Generate a layout from a list of presets."
    )
    common_generate_arguments(parser_presets)
    permalink_command.add_permalink_arguments(parser_presets)
    parser_presets.set_defaults(func=generate_from_preset_logic)
