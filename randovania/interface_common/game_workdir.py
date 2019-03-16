from pathlib import Path
from typing import Optional, Tuple


def discover_game(game_files_path: Path) -> Optional[Tuple[str, str]]:
    if not game_files_path.is_dir():
        return None

    boot_bin = game_files_path / "sys" / "boot.bin"
    try:
        header_bytes = boot_bin.read_bytes()

        game_id = header_bytes[0:6].decode("UTF-8")
        game_title = header_bytes[0x20:(0x20 + 40)].split(b"\x00")[0].decode("UTF-8")
        return game_id, game_title

    except FileNotFoundError:
        return None


def validate_game_files_path(game_files_path: Path):
    if not game_files_path.is_dir():
        raise ValueError("Not a directory")

    required_files = ["default.dol", "FrontEnd.pak", "Metroid1.pak", "Metroid2.pak"]
    missing_files = [(game_files_path / required_file).is_file()
                     for required_file in required_files]

    if not all(missing_files):
        raise ValueError("Is not a valid game folder. Missing files: {}".format([
            filename for filename, exists in zip(required_files, missing_files)
            if not exists
        ]))
