import argparse
import os
import shutil
import subprocess
from pathlib import Path


# Version field is the specification version, not the app's
_executable_metadata = """
[Desktop Entry]
Version=1.0
Name={NAME}
GenericName={NAME}
Comment={DESCRIPTION}
Exec=/app/share/randovania/randovania
StartupNotify=true
Terminal=false
Icon={ICON}
Type=Application
Categories=Game
"""

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
            _here.joinpath(f"flatpak/{_production_id}.yml").read_text().replace(
                _production_id,
                flatpak_id,
            )
        )

    metadata = _executable_metadata.format(
        NAME="Randovania",
        DESCRIPTION="A randomizer platform for a multitude of games.",
        ICON=flatpak_id,
    )
    _here.joinpath(f"flatpak/{flatpak_id}.desktop").write_text(metadata)

    shutil.move(
        executable_tar,
        os.fspath(_here.joinpath("flatpak/randovania-linux.tar.gz")),
    )
    shutil.copy2(
        os.fspath(_here.joinpath("icons/sky_temple_key.png")),
        os.fspath(_here.joinpath(f"flatpak/{flatpak_id}.png")),
    )
    subprocess.run([
        "flatpak-builder",
        f"--repo={os.fspath(repository.absolute())}",
        "./flatpak-build-dir",
        os.fspath(_here.joinpath(f"flatpak/{flatpak_id}.yml")),
    ], check=True)


if __name__ == '__main__':
    main()
