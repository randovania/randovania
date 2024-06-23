from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace, _SubParsersAction


def patcher_data_command_logic(args: Namespace) -> None:
    return asyncio.run(patcher_data_command_logic_async(args))


async def patcher_data_command_logic_async(args: Namespace) -> None:
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.layout_description import LayoutDescription

    layout_description = LayoutDescription.from_file(args.layout_file)
    players_config = PlayersConfiguration(
        args.player_index,
        {i: f"Player {i + 1}" for i in range(layout_description.world_count)},
    )
    preset = layout_description.get_preset(players_config.player_index)

    cosmetic_patches = preset.game.data.layout.cosmetic_patches.default()
    data_factory = preset.game.patch_data_factory(layout_description, players_config, cosmetic_patches)
    patch_data = data_factory.create_data()

    output = json.dumps(
        patch_data,
        indent=4,
    )
    if args.output is not None:
        args.output.write_text(output)
    else:
        print(output)


def add_patcher_data_command(sub_parsers: _SubParsersAction) -> None:
    parser: ArgumentParser = sub_parsers.add_parser("patcher-data", help="Exports the patcher data.")
    parser.add_argument("--layout-file", type=Path, required=True, help="The rdvgame file to use")
    parser.add_argument(
        "--player-index", type=int, default=0, help="Number of the player to export, for multiworld games. 0-indexed"
    )
    parser.add_argument("--output", type=Path, help="Where to write the output. Defaults to stdout.")
    parser.set_defaults(func=patcher_data_command_logic)
