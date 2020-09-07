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


def get_configuration() -> dict:
    try:
        if CONFIGURATION_FILE_PATH is None:
            raise FileNotFoundError()

        with CONFIGURATION_FILE_PATH.open() as file:
            return json.load(file)
    except FileNotFoundError:
        return {
            "server_address": "http://127.0.0.1:5000",
            "socketio_path": "/socket.io",
        }


__version__ = version
VERSION = version
