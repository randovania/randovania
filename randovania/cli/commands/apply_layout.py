import asyncio
from argparse import ArgumentParser
from pathlib import Path


def randomize_command_logic(args):
    return asyncio.run(randomize_command_logic_async(args))


async def randomize_command_logic_async(args):
    from randovania.patching.patcher_provider import PatcherProvider
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.layout_description import LayoutDescription
    from randovania.interface_common.options import Options

    def status_update(s):
        if args.verbose:
            print(s)

    layout_description = LayoutDescription.from_file(args.log_file)
    players_config = PlayersConfiguration(args.player_index,
                                          {i: f"Player {i + 1}"
                                           for i in range(layout_description.player_count)})
    preset = layout_description.get_preset(players_config.player_index)

    internal_copies_path = Options.with_default_data_dir().internal_copies_path
    patcher_provider = PatcherProvider()
    cosmetic_patches = preset.game.data.layout.cosmetic_patches.default()
    patcher = patcher_provider.patcher_for_game(preset.game)

    patch_data = patcher.create_patch_data(layout_description, players_config, cosmetic_patches)
    patcher.patch_game(args.input_file, args.output_file, patch_data, internal_copies_path,
                       lambda x, _: status_update(x))


def add_apply_layout_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "apply-layout",
        help="Exports the modified game."
    )
    parser.add_argument("--layout-file", type=Path, help="The rdvgame file to use")
    parser.add_argument("--verbose", action="store_true", help="Prints progress",
                        default=False)
    parser.add_argument("--player-index", type=int, default=0,
                        help="Number of the player to export, for multiworld games. 0-indexed")

    parser.add_argument(
        "--input-file",
        type=Path,
        help="File to use to randomize the game.")
    parser.add_argument(
        "output_file",
        type=Path,
        help="Output file.")
    parser.set_defaults(func=randomize_command_logic)
