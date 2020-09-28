import json
import sys
from pathlib import Path
from typing import Optional

from randovania.version import version

CONFIGURATION_FILE_PATH: Optional[Path] = None


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def get_data_path() -> Path:
    if is_frozen():
        file_dir = Path(getattr(sys, "_MEIPASS"))
    else:
        file_dir = Path(__file__).parent
    return file_dir.joinpath("data")


def _get_default_configuration_path() -> Path:
    return get_data_path().joinpath("configuration.json")


def get_configuration() -> dict:
    file_path = CONFIGURATION_FILE_PATH
    if file_path is None:
        file_path = _get_default_configuration_path()

    try:
        with file_path.open() as file:
            return json.load(file)
    except FileNotFoundError:
        if CONFIGURATION_FILE_PATH is None:
            return {
                "server_address": "http://127.0.0.1:5000",
                "socketio_path": "/socket.io",
            }
        else:
            raise


__version__ = version
VERSION = version
