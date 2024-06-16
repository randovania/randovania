from __future__ import annotations

import asyncio
import random
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.games.game import RandovaniaGame
from randovania.layout.versioned_preset import VersionedPreset

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction

    from randovania.layout.permalink import Permalink


def _error(msg: str) -> None:
    print(msg)
    raise SystemExit(1)


def create_permalink(args: Namespace) -> Permalink:
    from randovania.interface_common.preset_manager import PresetManager
    from randovania.layout.generator_parameters import GeneratorParameters
    from randovania.layout.permalink import Permalink

    preset_manager = PresetManager(None)
    presets = []

    for combined_name in args.name:
        try:
            game_value, preset_name = combined_name.split("/", 1)
        except ValueError:
            _error(f"Name {combined_name} does not match format <Game Name>/<Preset Name>")

        try:
            game = RandovaniaGame(game_value)
        except ValueError:
            _error(f"{game_value} is not a known RandovaniaGame")

        versioned = preset_manager.included_preset_with(game, preset_name)
        if versioned is None:
            options = [preset.name for preset in preset_manager.included_presets.values() if preset.game == game]
            _error(f"Unknown included preset '{preset_name}' for game {game.long_name}. Valid options are: {options}")
        assert versioned is not None
        presets.append(versioned.get_preset())

    for preset_file in args.file:
        versioned = VersionedPreset.from_file_sync(preset_file)
        presets.append(versioned.get_preset())

    folder: Path | None = args.folder
    if folder is not None:
        for preset_file in folder.glob(f"*.{VersionedPreset.file_extension()}"):
            versioned = VersionedPreset.from_file_sync(preset_file)
            presets.append(versioned.get_preset())

    seed = args.seed_number
    if seed is None:
        seed = random.randint(0, 2**31)

    return Permalink.from_parameters(
        GeneratorParameters(
            seed,
            spoiler=not args.race,
            development=args.development,
            presets=presets,
        ),
    )


async def permalink_command_body(args: Namespace) -> None:
    from randovania.layout.permalink import Permalink

    permalink = create_permalink(args)
    print(permalink.as_base64_str)
    Permalink.from_str(permalink.as_base64_str)


def permalink_command(args: Namespace) -> None:
    asyncio.run(permalink_command_body(args))


def add_permalink_arguments(parser: ArgumentParser) -> None:
    parser.add_argument("--seed-number", type=int, help="The seed number. Defaults to 0.")
    parser.add_argument(
        "--name",
        type=str,
        action="append",
        help="The name of the presets to use. Should be named <game>/<name>. Can be specified multiple times.",
        default=[],
    )
    parser.add_argument(
        "--file",
        type=Path,
        action="append",
        help="The path of preset file to use. Can be specified multiple times.",
        default=[],
    )
    parser.add_argument("--folder", type=Path, help="Use all presets in the folder")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--race", default=False, action="store_true", help="Make a race permalink (without spoiler).")
    group.add_argument(
        "--development",
        default=False,
        action="store_true",
        help="Disables features that maximize randomness in order to make easier to investigate bugs.",
    )


def add_permalink_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser("permalink", help="Creates a permalink")
    add_permalink_arguments(parser)
    parser.set_defaults(func=permalink_command)
