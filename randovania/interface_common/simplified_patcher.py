import shutil
from pathlib import Path

from randovania.game_description.echoes_game_specific import EchoesGameSpecific
from randovania.games.prime import iso_packager, claris_randomizer
from randovania.games.prime.banner_patcher import patch_game_name_and_id
from randovania.interface_common import echoes
from randovania.interface_common.options import Options
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.interface_common.status_update_lib import ProgressUpdateCallable, ConstantPercentageCallback
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink

export_busy = False


def delete_files_location(options: Options, ):
    """
    Deletes an extracted game in given options.
    :param options:
    :return:
    """
    game_files_path = options.game_files_path
    if game_files_path.exists():
        shutil.rmtree(game_files_path)

    backup_files_path = options.backup_files_path
    if backup_files_path.exists():
        shutil.rmtree(backup_files_path)


def unpack_iso(input_iso: Path,
               options: Options,
               progress_update: ProgressUpdateCallable,
               ):
    """
    Unpacks the given ISO to the files listed in options
    :param input_iso:
    :param options:
    :param progress_update:
    :return:
    """
    game_files_path = options.game_files_path

    delete_files_location(options)
    iso_packager.unpack_iso(
        iso=input_iso,
        game_files_path=game_files_path,
        progress_update=progress_update,
    )


def generate_layout(options: Options,
                    permalink: Permalink,
                    progress_update: ProgressUpdateCallable,
                    ) -> LayoutDescription:
    """
    Creates a LayoutDescription for the configured permalink
    :param options:
    :param permalink:
    :param progress_update:
    :return:
    """
    return echoes.generate_layout(
        permalink=permalink,
        status_update=ConstantPercentageCallback(progress_update, -1),
        validate_after_generation=options.advanced_validate_seed_after,
        timeout_during_generation=options.advanced_timeout_during_generation,
    )


def apply_layout(layout: LayoutDescription,
                 options: Options,
                 players_config: PlayersConfiguration,
                 progress_update: ProgressUpdateCallable):
    """
    Applies the given LayoutDescription to the files listed in options
    :param options:
    :param layout:
    :param players_config:
    :param progress_update:
    :return:
    """
    game_files_path = options.game_files_path
    backup_files_path = options.backup_files_path

    patch_game_name_and_id(game_files_path, "Metroid Prime 2: Randomizer - {}".format(layout.shareable_hash))

    claris_randomizer.apply_layout(description=layout,
                                   players_config=players_config,
                                   cosmetic_patches=options.cosmetic_patches,
                                   backup_files_path=backup_files_path,
                                   progress_update=progress_update,
                                   game_root=game_files_path,
                                   )


def apply_patcher_file(patcher_file: dict,
                       game_specific: EchoesGameSpecific,
                       shareable_hash: str,
                       options: Options,
                       progress_update: ProgressUpdateCallable):
    """
    Applies the given LayoutDescription to the files listed in options
    :param options:
    :param patcher_file:
    :param game_specific:
    :param shareable_hash:
    :param progress_update:
    :return:
    """
    game_files_path = options.game_files_path
    backup_files_path = options.backup_files_path

    patch_game_name_and_id(game_files_path, "Metroid Prime 2: Randomizer - {}".format(shareable_hash))

    claris_randomizer.apply_patcher_file(
        game_root=game_files_path,
        backup_files_path=backup_files_path,
        patcher_data=patcher_file,
        game_specific=game_specific,
        progress_update=progress_update,
    )


def pack_iso(output_iso: Path,
             options: Options,
             progress_update: ProgressUpdateCallable,
             ):
    """
    Unpacks the files listed in options to the given path
    :param output_iso:
    :param options:
    :param progress_update:
    :return:
    """
    game_files_path = options.game_files_path

    iso_packager.pack_iso(
        iso=output_iso,
        game_files_path=game_files_path,
        progress_update=progress_update,
    )
