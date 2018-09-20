import os
import shutil
from typing import List

from randovania.games.prime import iso_packager, claris_randomizer, binary_data
from randovania.gui.common_qt_lib import application_options
from randovania.interface_common import status_update_lib
from randovania.interface_common.status_update_lib import ProgressUpdateCallable, ConstantPercentageCallback
from randovania.resolver import echoes
from randovania.resolver.layout_description import LayoutDescription


def _delete_files_location(game_files_path: str):
    if os.path.exists(game_files_path):
        shutil.rmtree(game_files_path)


def unpack_iso(input_iso: str, progress_update: ProgressUpdateCallable):
    """
    Unpacks the given ISO to the files listed in application_options
    :param input_iso:
    :param progress_update:
    :return:
    """
    game_files_path = application_options().game_files_path

    _delete_files_location(game_files_path)
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
        data=binary_data.decode_default_prime2(),
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
    hud_memo_popup_removal = options.hud_memo_popup_removal

    claris_randomizer.apply_layout(
        layout=layout,
        hud_memo_popup_removal=hud_memo_popup_removal,
        game_root=game_files_path,
        status_update=status_update_lib.create_progress_update_from_successive_messages(progress_update, 100)
    )


def pack_iso(output_iso: str, progress_update: ProgressUpdateCallable):
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
                        input_iso: str,
                        layout: LayoutDescription,
                        ):
    layout_configuration = layout.configuration

    output_name = "Echoes Randomizer - {}_{}".format(layout_configuration.as_str, layout.seed_number)
    base_directory = os.path.dirname(input_iso)
    output_iso = os.path.join(base_directory, "{}.iso".format(output_name))
    output_json = os.path.join(base_directory, "{}.json".format(output_name))

    # Unpack ISO
    unpack_iso(input_iso=input_iso, progress_update=updaters[0])

    # Patch ISO
    apply_layout(layout=layout, progress_update=updaters[1])

    # Pack ISO
    pack_iso(output_iso=output_iso, progress_update=updaters[2])

    # Save the layout to a file
    layout.save_to_file(output_json)


def patch_iso_with_existing_layout(progress_update: ProgressUpdateCallable,
                                   input_iso: str,
                                   layout: LayoutDescription,
                                   ):
    _internal_patch_iso(
        updaters=status_update_lib.split_progress_update(
            progress_update,
            3
        ),
        input_iso=input_iso,
        layout=layout
    )


def create_layout_then_patch_iso(progress_update: ProgressUpdateCallable,
                                 input_iso: str,
                                 seed_number: int,
                                 ) -> LayoutDescription:
    updaters = status_update_lib.split_progress_update(
        progress_update,
        4
    )

    # Create a LayoutDescription
    resulting_layout = generate_layout(seed_number=seed_number, progress_update=updaters[0])

    _internal_patch_iso(
        updaters=updaters[1:],
        input_iso=input_iso,
        layout=resulting_layout
    )

    return resulting_layout
