import multiprocessing
import os
from distutils.version import StrictVersion
from typing import Callable

import nod

from randovania.games.prime import claris_randomizer
from randovania.interface_common.options import validate_game_files_path


def _disc_unpack_process(output_pipe, iso: str, game_files_path: str):
    def progress_callback(path, progress):
        output_pipe.send((False, path, int(progress * 100)))

    def _helper():
        try:
            disc, is_wii = nod.open_disc_from_image(iso)
            data_partition = disc.get_data_partition()
            if not data_partition:
                raise RuntimeError(
                    "Could not find a data partition in '{}'.\nIs it a valid Metroid Prime 2 ISO?".format(
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


def _disable_attract_videos_helper(output_pipe, iso: str, game_files_path: str):
    def progress_update(message: str):
        output_pipe.send((False, message, -1))

    claris_randomizer.disable_echoes_attract_videos(game_files_path, progress_update)

    with open(os.path.join(game_files_path, "files", "attract_videos_disabled.txt"), "w"):
        pass

    output_pipe.send((True, None, -1))


def _disable_attract_videos(game_files_path: str, update: Callable[[str, int], None]) -> None:
    if os.path.exists(os.path.join(game_files_path, "files", "attract_videos_disabled.txt")):
        return

    _shared_process_code(
        target=_disable_attract_videos_helper,
        iso="",
        game_files_path=game_files_path,
        on_finish_message="Finished disabling attract videos.",
        progress_update=update
    )


def pack_iso(iso: str,
             game_files_path: str,
             disable_attract_if_necessary: bool,
             progress_update: Callable[[str, int], None]
             ):

    validate_game_files_path(os.path.join(game_files_path, "files"))

    nod_version = StrictVersion(getattr(nod, "VERSION", "0.0.0"))
    if nod_version < StrictVersion("1.1.0"):
        raise RuntimeError("Installed nod version ({}) is older than required 1.1.0".format(nod_version))

    if disable_attract_if_necessary and nod.DiscBuilderGCN.calculate_total_size_required(game_files_path) is None:
        _disable_attract_videos(game_files_path, progress_update)

    if nod.DiscBuilderGCN.calculate_total_size_required(game_files_path) is None:
        raise RuntimeError("Image built with given directory would pass the maximum size.")

    _shared_process_code(
        target=_disc_pack_process,
        iso=iso,
        game_files_path=game_files_path,
        on_finish_message="Finished packing ISO",
        progress_update=progress_update
    )
