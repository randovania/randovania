import shutil
from pathlib import Path
from typing import Optional

from randovania.games.patchers.gamecube import iso_packager
from randovania.interface_common import echoes
from randovania.interface_common.options import Options
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


def generate_layout(options: Options,
                    permalink: Permalink,
                    progress_update: ProgressUpdateCallable,
                    retries: Optional[int] = None,
                    ) -> LayoutDescription:
    """
    Creates a LayoutDescription for the configured permalink
    :param options:
    :param permalink:
    :param progress_update:
    :param retries:
    :return:
    """
    return echoes.generate_description(
        permalink=permalink,
        status_update=ConstantPercentageCallback(progress_update, -1),
        validate_after_generation=options.advanced_validate_seed_after,
        timeout_during_generation=options.advanced_timeout_during_generation,
        attempts=retries,
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
