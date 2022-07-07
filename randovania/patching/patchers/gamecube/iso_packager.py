from pathlib import Path

import nod
import os

from randovania.interface_common.game_workdir import validate_game_files_path
from randovania.lib.status_update_lib import ProgressUpdateCallable


def unpack_iso(iso: Path,
               game_files_path: Path,
               progress_update: ProgressUpdateCallable,
               ):
    try:
        game_files_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError("Unable to create files dir {}:\n{}".format(
            game_files_path, e))

    disc, is_wii = nod.open_disc_from_image(iso)
    data_partition = disc.get_data_partition()
    if not data_partition:
        raise RuntimeError(
            f"Could not find a data partition in '{iso}'.\nIs it a valid Metroid Prime 2 ISO?"
        )

    context = nod.ExtractionContext()
    context.set_progress_callback(progress_update)
    data_partition.extract_to_directory(os.fspath(game_files_path), context)

    progress_update("Finished extracting ISO", 1)


def pack_iso(iso: Path,
             game_files_path: Path,
             progress_update: ProgressUpdateCallable
             ):
    validate_game_files_path(game_files_path.joinpath("files"))

    if nod.DiscBuilderGCN.calculate_total_size_required(game_files_path) is None:
        raise RuntimeError("Image built with given directory would pass the maximum size.")

    def fprogress_callback(progress: float, name: str, byte_count: int):
        progress_update(name, progress)

    disc_builder = nod.DiscBuilderGCN(iso, fprogress_callback)
    disc_builder.build_from_directory(game_files_path)

    progress_update("Finished packing ISO", 1)
