import os
import shutil
from typing import Optional, Callable

from randovania.games.prime import iso_packager, claris_randomizer, binary_data
from randovania.gui.common_qt_lib import application_options
from randovania.interface_common import status_update_lib
from randovania.interface_common.status_update_lib import ProgressUpdateCallable, ConstantPercentageCallback
from randovania.resolver import echoes
from randovania.resolver.layout_configuration import LayoutConfiguration
from randovania.resolver.layout_description import LayoutDescription


def delete_files_location(game_files_path: str):
    if os.path.exists(game_files_path):
        shutil.rmtree(game_files_path)


def randomize_iso(status_update: ProgressUpdateCallable,
                  input_iso: str,
                  seed_number: int,
                  layout_reporter: Optional[Callable[[LayoutDescription], None]],
                  exception_reporter: Optional[Callable[[Exception], None]],
                  ):
    options = application_options()

    base_directory = os.path.dirname(input_iso)
    game_files_path = options.game_files_path
    hud_memo_popup_removal = options.hud_memo_popup_removal
    layout_configuration = options.layout_configuration

    output_name = "Echoes Randomizer - {}-{}".format(layout_configuration.as_str, seed_number)
    output_iso = os.path.join(base_directory, "{}.iso".format(output_name))
    output_json = os.path.join(base_directory, "{}.json".format(output_name))

    updaters = status_update_lib.split_progress_update(
        status_update,
        4
    )

    # Create a LayoutDescription
    resulting_layout = echoes.generate_layout(
        data=binary_data.decode_default_prime2(),
        seed_number=seed_number,
        configuration=layout_configuration,
        status_update=ConstantPercentageCallback(updaters[0], -1)
    )
    if isinstance(resulting_layout, Exception):
        if exception_reporter is not None:
            exception_reporter(resulting_layout)
        status_update("Error: {}".format(resulting_layout), 1)
        return
    else:
        status_update("Success!", 1)

    # Unpack ISO
    delete_files_location(game_files_path)
    iso_packager.unpack_iso(
        iso=input_iso,
        game_files_path=game_files_path,
        progress_update=updaters[1],
    )

    # Patch ISO
    claris_randomizer.apply_layout(
        layout=resulting_layout,
        hud_memo_popup_removal=hud_memo_popup_removal,
        game_root=game_files_path,
        status_update=status_update_lib.create_progress_update_from_successive_messages(
            updaters[2], 100
        )
    )

    # Pack ISO
    iso_packager.pack_iso(
        iso=output_iso,
        game_files_path=game_files_path,
        disable_attract_if_necessary=True,
        progress_update=updaters[3],
    )

    resulting_layout.save_to_file(output_json)

    if layout_reporter is not None:
        layout_reporter(resulting_layout)
