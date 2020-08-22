import json
import sys
from pathlib import Path

from randovania.version import version


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
        with get_data_path().joinpath("configuration.json").open() as file:
            return json.load(file)
    except FileNotFoundError:
        return {
            "server_address": "http://127.0.0.1:5000",
            "socketio_path": "/socket.io",
        }


__version__ = version
VERSION = version
