# /// script
# dependencies = [
#   "PySide6-Essentials"
# ]
# ///

import argparse
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--git-add", action="store_true")
    parser.add_argument("paths", type=Path, nargs="+")
    args = parser.parse_args()
    paths: list[Path] = args.paths
    new_paths: list[str] = []

    try:

        def process_file(path: Path):
            new_file = os.fspath(path.parents[1].joinpath("generated").joinpath(path.stem + "_ui.py"))
            new_paths.append(new_file)
            subprocess.check_call(
                [
                    "pyside6-uic",
                    "--absolute-imports",
                    "-o",
                    new_file,
                    os.fspath(path),
                ]
            )

        with ThreadPoolExecutor() as executor:
            for path_to_process in paths:
                executor.submit(process_file, path_to_process)

        if args.git_add:
            subprocess.check_call(
                ["git", "add"] + new_paths,
            )
    except subprocess.CalledProcessError as e:
        raise SystemExit(e.returncode)


if __name__ == "__main__":
    main()
