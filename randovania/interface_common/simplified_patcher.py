import os
import shutil
from pathlib import Path
from typing import List

from randovania.games.prime import iso_packager, claris_randomizer, default_data
from randovania.gui.common_qt_lib import application_options
from randovania.interface_common import status_update_lib, echoes
from randovania.interface_common.status_update_lib import ProgressUpdateCallable, ConstantPercentageCallback
from randovania.resolver.layout_description import LayoutDescription


def delete_files_location():
    options = application_options()

    game_files_path = options.game_files_path
    if game_files_path.exists():
        shutil.rmtree(game_files_path)

    backup_files_path = options.backup_files_path
    if backup_files_path.exists():
        shutil.rmtree(backup_files_path)


def unpack_iso(input_iso: Path,
               progress_update: ProgressUpdateCallable,
               ):
    """
    Unpacks the given ISO to the files listed in application_options
    :param input_iso:
    :param progress_update:
    :return:
    """
    game_files_path = application_options().game_files_path

    delete_files_location()
    iso_packager.unpack_iso(
        iso=input_iso,
        game_files_path=game_files_path,
        progress_update=progress_update,
    )


def generate_layout(seed_number: int, progress_update: ProgressUpdateCallable) -> LayoutDescription:
    """
    Creates a LayoutDescription for the given seed_number and the configuration in application_options
    :param seed_number:
    :param progress_update:
    :return:
    """
    layout_configuration = application_options().layout_configuration

    return echoes.generate_layout(
        data=default_data.decode_default_prime2(),
        seed_number=seed_number,
        configuration=layout_configuration,
        status_update=ConstantPercentageCallback(progress_update, -1)
    )


def apply_layout(layout: LayoutDescription, progress_update: ProgressUpdateCallable):
    """
    Applies the given LayoutDescription to the files listed in application_options
    :param layout:
    :param progress_update:
    :return:
    """
    options = application_options()

    game_files_path = options.game_files_path
    backup_files_path = options.backup_files_path
    hud_memo_popup_removal = options.hud_memo_popup_removal
    include_menu_mod = options.include_menu_mod

    claris_randomizer.apply_layout(
        layout=layout,
        hud_memo_popup_removal=hud_memo_popup_removal,
        include_menu_mod=include_menu_mod,
        game_root=game_files_path,
        backup_files_path=backup_files_path,
        progress_update=progress_update
    )


def pack_iso(output_iso: Path,
             progress_update: ProgressUpdateCallable,
             ):
    """
    Unpacks the files listed in application_options to the given path
    :param output_iso:
    :param progress_update:
    :return:
    """
    game_files_path = application_options().game_files_path

    iso_packager.pack_iso(
        iso=output_iso,
        game_files_path=game_files_path,
        disable_attract_if_necessary=True,
        progress_update=progress_update,
    )


def _internal_patch_iso(updaters: List[ProgressUpdateCallable],
                        layout: LayoutDescription,
                        ):
    layout_configuration = layout.configuration

    output_name = "Echoes Randomizer - {}_{}".format(layout_configuration.as_str, layout.seed_number)
    output_directory = application_options().output_directory
    output_iso = output_directory.joinpath("{}.iso".format(output_name))
    output_json = output_directory.joinpath("{}.json".format(output_name))

    # Patch ISO
    apply_layout(layout=layout, progress_update=updaters[0])

    # Pack ISO
    pack_iso(output_iso=output_iso, progress_update=updaters[1])

    # Save the layout to a file
    layout.save_to_file(output_json)


def patch_game_with_existing_layout(progress_update: ProgressUpdateCallable,
                                    layout: LayoutDescription,
                                    ):
    _internal_patch_iso(
        updaters=status_update_lib.split_progress_update(
            progress_update,
            2
        ),
        layout=layout
    )


def create_layout_then_export_iso(progress_update: ProgressUpdateCallable,
                                  seed_number: int,
                                  ) -> LayoutDescription:
    updaters = status_update_lib.split_progress_update(
        progress_update,
        3
    )

    # Create a LayoutDescription
    resulting_layout = generate_layout(seed_number=seed_number, progress_update=updaters[0])

    _internal_patch_iso(
        updaters=updaters[1:],
        layout=resulting_layout
    )

    return resulting_layout
