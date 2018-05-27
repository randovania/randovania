import multiprocessing
import os
from typing import Callable

import nod

from randovania.interface_common.options import validate_game_files_path


def _disc_unpack_process(output_pipe, iso: str, game_files_path: str):
    def progress_callback(path, progress):
        output_pipe.send((False, path, int(progress * 100)))

    def _helper():
        try:
            disc, is_wii = nod.open_disc_from_image(iso)
            data_partition = disc.get_data_partition()
            if not data_partition:
                raise RuntimeError("Could not find a data partition in '{}'.\nIs it a valid Metroid Prime 2 ISO?".format(
                    iso))

            context = nod.ExtractionContext()
            context.set_progress_callback(progress_callback)
            data_partition.extract_to_directory(game_files_path, context)
            return True, None, 100

        except RuntimeError as e:
            return True, str(e), 0
    output_pipe.send(_helper())


def _disc_pack_process(status_queue, iso: str, game_files_path: str):
    def fprogress_callback(progress: float, name: str, bytes: int):
        status_queue.send((False, name, int(progress * 100)))

    def _helper():
        try:
            disc_builder = nod.DiscBuilderGCN(iso, fprogress_callback)
            disc_builder.build_from_directory(game_files_path)
            return True, None, 100

        except RuntimeError as e:
            return True, str(e), 0
    status_queue.send(_helper())


def _shared_process_code(target,
                         iso: str,
                         game_files_path: str,
                         on_finish_message: str,
                         progress_update: Callable[[str, int], None]):

    receiving_pipe, output_pipe = multiprocessing.Pipe(False)
    process = multiprocessing.Process(
        target=target,
        args=(output_pipe, iso, game_files_path)
    )
    process.start()
    try:
        finished = False
        message = ""
        percentage = 0
        while not finished:
            progress_update(message, percentage)
            finished, message, percentage = receiving_pipe.recv()

        if isinstance(message, str):
            raise RuntimeError(message)

        progress_update(on_finish_message, 100)
    finally:
        process.terminate()


def unpack_iso(iso: str, game_files_path: str, progress_update: Callable[[str, int], None]):
    try:
        os.makedirs(game_files_path, exist_ok=True)
    except OSError as e:
        raise RuntimeError("Unable to create files dir {}:\n{}".format(
            game_files_path, e))

    _shared_process_code(
        target=_disc_unpack_process,
        iso=iso,
        game_files_path=game_files_path,
        on_finish_message="Finished extracting ISO",
        progress_update=progress_update
    )


def pack_iso(iso: str, game_files_path: str, progress_update: Callable[[str, int], None]):
    validate_game_files_path(os.path.join(game_files_path, "files"))

    if nod.DiscBuilderGCN.calculate_total_size_required(game_files_path) == -1:
        raise RuntimeError("Image built with given directory would pass the maximum size.")

    _shared_process_code(
        target=_disc_pack_process,
        iso=iso,
        game_files_path=game_files_path,
        on_finish_message="Finished packing ISO",
        progress_update=progress_update
    )
