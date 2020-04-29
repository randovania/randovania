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


__version__ = version
VERSION = version
