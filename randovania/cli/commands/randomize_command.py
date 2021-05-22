import asyncio
from argparse import ArgumentParser
from pathlib import Path


def randomize_command_logic(args):
    return asyncio.run(randomize_command_logic_async(args))


async def randomize_command_logic_async(args):
    from randovania.games.patcher_provider import PatcherProvider
    from randovania.generator import generator
    from randovania.interface_common.cosmetic_patches import CosmeticPatches
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.layout_description import LayoutDescription
    from randovania.layout.permalink import Permalink
    from randovania.interface_common.options import Options

    def status_update(s):
        if args.verbose:
            print(s)

    if args.permalink is not None:
        permalink = Permalink.from_str(args.permalink)
        layout_description = await generator.generate_and_validate_description(
            permalink=permalink,
            status_update=status_update,
            validate_after_generation=True,
        )
    else:
        layout_description = LayoutDescription.from_file(args.log_file)

    cosmetic_patches = CosmeticPatches(
        disable_hud_popup=args.disable_hud_popup,
        speed_up_credits=args.speed_up_credits)

    players_config = PlayersConfiguration(args.player_index,
                                          {i: f"Player {i + 1}"
                                           for i in range(layout_description.permalink.player_count)})
    preset = layout_description.permalink.get_preset(players_config.player_index)

    game_files_path = Options.with_default_data_dir().game_files_path
    patcher_provider = PatcherProvider()
    patcher = patcher_provider.patcher_for_game(preset.game)

    patch_data = patcher.create_patch_data(layout_description, players_config, cosmetic_patches)
    patcher.patch_game(args.input_file, args.output_file, patch_data, game_files_path, lambda x, _: status_update(x))


def add_randomize_command(sub_parsers):
    parser: ArgumentParser = sub_parsers.add_parser(
        "randomize",
        help="Randomizes a game files path."
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--permalink", type=str, help="The permalink to use")
    group.add_argument("--log-file", type=Path, help="A seed log file to use")

    parser.add_argument("--disable-hud-popup", action="store_true", help="Remove the HUD popup", default=False)
    parser.add_argument("--speed-up-credits", action="store_true", help="Speeds ups the credits sequence",
                        default=False)
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
