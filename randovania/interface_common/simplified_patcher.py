import json
import shutil
from pathlib import Path
from typing import List

from randovania.games.prime import iso_packager, claris_randomizer, patcher_file
from randovania.games.prime.banner_patcher import patch_game_name_and_id
from randovania.interface_common import status_update_lib, echoes
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.options import Options
from randovania.interface_common.status_update_lib import ProgressUpdateCallable, ConstantPercentageCallback
from randovania.layout.layout_description import LayoutDescription


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
                    progress_update: ProgressUpdateCallable,
                    ) -> LayoutDescription:
    """
    Creates a LayoutDescription for the configured permalink
    :param options:
    :param progress_update:
    :return:
    """
    return echoes.generate_layout(
        permalink=options.permalink,
        status_update=ConstantPercentageCallback(progress_update, -1),
        validate_after_generation=options.advanced_validate_seed_after,
        timeout_during_generation=options.advanced_timeout_during_generation,
    )


def apply_layout(layout: LayoutDescription,
                 options: Options,
                 progress_update: ProgressUpdateCallable):
    """
    Applies the given LayoutDescription to the files listed in options
    :param options:
    :param layout:
    :param progress_update:
    :return:
    """
    game_files_path = options.game_files_path
    backup_files_path = options.backup_files_path

    patch_game_name_and_id(game_files_path, "Metroid Prime 2: Randomizer - {}".format(layout.shareable_hash))

    claris_randomizer.apply_layout(description=layout,
                                   cosmetic_patches=options.cosmetic_patches,
                                   backup_files_path=backup_files_path,
                                   progress_update=progress_update,
                                   game_root=game_files_path,
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


def _output_name_for(layout: LayoutDescription) -> str:
    return "Echoes Randomizer - {}".format(layout.shareable_hash)


def _internal_patch_iso(updaters: List[ProgressUpdateCallable],
                        layout: LayoutDescription,
                        options: Options,
                        ):
    output_iso = options.output_directory.joinpath("{}.iso".format(_output_name_for(layout)))

    # Patch ISO
    apply_layout(layout=layout,
                 options=options,
                 progress_update=updaters[0])

    # Pack ISO
    pack_iso(output_iso=output_iso,
             options=options,
             progress_update=updaters[1])

    # Save the layout to a file
    if options.create_spoiler:
        export_layout(layout, options)


def write_patcher_file_to_disk(path: Path, layout: LayoutDescription, cosmetic: CosmeticPatches):
    with path.open("w") as out_file:
        json.dump(patcher_file.create_patcher_file(layout, cosmetic),
                  out_file, indent=4, separators=(',', ': '))


def export_layout(layout: LayoutDescription,
                  options: Options,
                  ):
    """
    Creates a seed log file for the given layout and saves it to the configured path
    :param layout:
    :param options:
    :return:
    """

    output_json = options.output_directory.joinpath("{}.json".format(_output_name_for(layout)))
    write_patcher_file_to_disk(options.output_directory.joinpath("{}-patcher.json".format(_output_name_for(layout))),
                               layout,
                               options.cosmetic_patches)

    # Save the layout to a file
    layout.save_to_file(output_json)


def patch_game_with_existing_layout(progress_update: ProgressUpdateCallable,
                                    layout: LayoutDescription,
                                    options: Options,
                                    ):
    """
    Patches the game with the given layout and exports an ISO
    :param progress_update:
    :param layout:
    :param options:
    :return:
    """
    _internal_patch_iso(
        updaters=status_update_lib.split_progress_update(
            progress_update,
            2
        ),
        layout=layout,
        options=options,
    )


def create_layout_then_export_iso(progress_update: ProgressUpdateCallable,
                                  options: Options,
                                  ) -> LayoutDescription:
    """
    Creates a new layout with the given seed and configured layout, then patches and exports an ISO
    :param progress_update:
    :param options:
    :return:
    """
    updaters = status_update_lib.split_progress_update(
        progress_update,
        3
    )

    # Create a LayoutDescription
    resulting_layout = generate_layout(options=options,
                                       progress_update=updaters[0])

    _internal_patch_iso(
        updaters=updaters[1:],
        layout=resulting_layout,
        options=options,
    )

    return resulting_layout


def create_layout_then_export(progress_update: ProgressUpdateCallable,
                              options: Options,
                              ) -> LayoutDescription:
    """
    Creates a new layout with the given seed and configured layout, then exports that layout
    :param progress_update:
    :param options:
    :return:
    """

    # Create a LayoutDescription
    resulting_layout = generate_layout(options=options,
                                       progress_update=progress_update)
    export_layout(resulting_layout, options)

    return resulting_layout
