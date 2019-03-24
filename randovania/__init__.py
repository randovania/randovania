import os

import sys
from pathlib import Path


def get_data_path() -> Path:
    if getattr(sys, "frozen", False):
        file_dir = Path(getattr(sys, "_MEIPASS"))
    else:
        file_dir = Path(__file__).parent
    return file_dir.joinpath("data")


VERSION = "0.25.0"
