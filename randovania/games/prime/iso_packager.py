import multiprocessing
from distutils.version import StrictVersion
from pathlib import Path

try:
    import nod
except ImportError:
    nod = None

from randovania.games.prime import claris_randomizer
from randovania.interface_common.game_workdir import validate_game_files_path
from randovania.interface_common.status_update_lib import ProgressUpdateCallable


def _disc_unpack_process(output_pipe,
                         iso: Path,
                         game_files_path: Path,
                         ):
    def progress_callback(path, progress):
        output_pipe.send((False, path, progress))

    def _helper():
        try:
            disc, is_wii = nod.open_disc_from_image(str(iso))
            data_partition = disc.get_data_partition()
            if not data_partition:
                raise RuntimeError(
                    "Could not find a data partition in '{}'.\nIs it a valid Metroid Prime 2 ISO?".format(
                        iso))

            context = nod.ExtractionContext()
            context.set_progress_callback(progress_callback)
            data_partition.extract_to_directory(str(game_files_path), context)
            return True, None, 100

        except RuntimeError as e:
            return True, str(e), 0

    output_pipe.send(_helper())


def _disc_pack_process(status_queue,
                       iso: Path,
                       game_files_path: Path,
                       ):
    def fprogress_callback(progress: float, name: str, bytes: int):
        status_queue.send((False, name, progress))

    def _helper():
        try:
            disc_builder = nod.DiscBuilderGCN(str(iso), fprogress_callback)
            disc_builder.build_from_directory(str(game_files_path))
            return True, None, 100

        except RuntimeError as e:
            return True, str(e), 0

    status_queue.send(_helper())


def _shared_process_code(target,
                         iso: Path,
                         game_files_path: Path,
                         on_finish_message: str,
                         progress_update: ProgressUpdateCallable):
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

        progress_update(on_finish_message, 1)
    finally:
        process.terminate()


def unpack_iso(iso: Path,
               game_files_path: Path,
               progress_update: ProgressUpdateCallable,
               ):
    try:
        game_files_path.mkdir(parents=True, exist_ok=True)
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


def pack_iso(iso: Path,
             game_files_path: Path,
             progress_update: ProgressUpdateCallable
             ):
    validate_game_files_path(game_files_path.joinpath("files"))

    nod_version = StrictVersion(getattr(nod, "VERSION", "0.0.0"))
    if nod_version < StrictVersion("1.1.0"):
        raise RuntimeError("Installed nod version ({}) is older than required 1.1.0".format(nod_version))

    if nod.DiscBuilderGCN.calculate_total_size_required(str(game_files_path)) is None:
        raise RuntimeError("Image built with given directory would pass the maximum size.")

    _shared_process_code(
        target=_disc_pack_process,
        iso=iso,
        game_files_path=game_files_path,
        on_finish_message="Finished packing ISO",
        progress_update=progress_update
    )


def can_process_iso() -> bool:
    return nod is not None
