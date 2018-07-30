import os

import sys


def get_data_path():
    if getattr(sys, "frozen", False):
        file_dir = getattr(sys, "_MEIPASS")
    else:
        file_dir = os.path.dirname(__file__)
    return os.path.join(file_dir, "data")


VERSION = "0.11.0"
