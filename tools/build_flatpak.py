from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

_here = Path(__file__).parent
_production_id = "io.github.randovania.Randovania"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("executable_tar", help="Path to the PyInstaller linux executable", type=Path)
    args = parser.parse_args()

    executable_tar: Path = args.executable_tar
    repository: Path = args.repository
    flatpak_id = _production_id

    if flatpak_id != _production_id:
        _here.joinpath(f"flatpak/{flatpak_id}.yml").write_text(
            _here.joinpath(f"flatpak/{_production_id}.yml")
            .read_text()
            .replace(
                _production_id,
                flatpak_id,
            )
        )

    shutil.move(
        executable_tar,
        os.fspath(_here.joinpath("flatpak/randovania-linux.tar.gz")),
    )
    subprocess.run(
        [
            "flatpak-builder",
            f"--repo={os.fspath(repository.absolute())}",
            "./flatpak-build-dir",
            os.fspath(_here.joinpath(f"flatpak/{flatpak_id}.yml")),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
