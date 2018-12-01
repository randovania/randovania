from pathlib import Path

from appdirs import AppDirs

dirs = AppDirs("Randovania", False)


def user_data_dir() -> Path:
    return Path(dirs.user_data_dir)
