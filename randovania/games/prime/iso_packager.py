import multiprocessing
import os
from typing import Callable

import nod

from randovania.interface_common.options import validate_game_files_path


def _disc_extract_process(status_queue, input_file: str, output_directory: str):
    def progress_callback(path, progress):
        status_queue.put_nowait((False, path, int(progress * 100)))

    def _helper():
        try:
            disc, is_wii = nod.open_disc_from_image(input_file)
            data_partition = disc.get_data_partition()
            if not data_partition:
                raise RuntimeError("Could not find a data partition in '{}'.\nIs it a valid Metroid Prime 2 ISO?".format(
                    input_file))

            context = nod.ExtractionContext()
            context.set_progress_callback(progress_callback)
            data_partition.extract_to_directory(output_directory, context)
            return True, None, 100

        except RuntimeError as e:
            return True, str(e), 0

    status_queue.put_nowait(_helper())


def unpack_iso(iso: str, game_files_path: str, progress_update: Callable[[str, int], None]):
    try:
        os.makedirs(game_files_path, exist_ok=True)
    except OSError as e:
        raise RuntimeError("Unable to create files dir {}:\n{}".format(
            game_files_path, e))

    output_queue = multiprocessing.Queue()

    process = multiprocessing.Process(
        target=_disc_extract_process,
        args=(output_queue, iso, game_files_path)
    )
    process.start()
    try:
        finished = False
        message = ""
        percentage = 0
        while not finished:
            progress_update(message, percentage)
            finished, message, percentage = output_queue.get()

        if isinstance(message, str):
            raise RuntimeError(message)

        progress_update("Finished extracting ISO", 100)
    finally:
        process.terminate()


def pack_iso(iso: str, game_files_path: str, progress_update: Callable[[str, int], None]):
    validate_game_files_path(os.path.join(game_files_path, "files"))

    if nod.DiscBuilderGCN.calculate_total_size_required(game_files_path) == -1:
        raise RuntimeError("Image built with given directory would pass the maximum size.")

    def fprogress_callback(progress: float, name: str, bytes: int):
        progress_update(name, int(progress * 100))

    disc_builder = nod.DiscBuilderGCN(iso, fprogress_callback)
    disc_builder.build_from_directory(game_files_path)
    progress_update("Finished packing ISO", 100)
