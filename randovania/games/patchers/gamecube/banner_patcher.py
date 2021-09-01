from pathlib import Path

from construct.core import Byte


def patch_game_name_and_id(game_files_path: Path, new_name: str, publisher_id: str):
    b = new_name.encode("ASCII")
    if len(b) > 40:
        raise ValueError("Name '{}' is bigger than 40 bytes".format(new_name))
    
    pid = publisher_id.encode("ASCII")
    if len(pid) != 2:
        raise ValueError("Publisher ID '{}' is not exactly 2 bytes".format(publisher_id))

    with game_files_path.joinpath("sys", "boot.bin").open("r+b") as boot_bin:
        boot_bin.seek(0x4)
        boot_bin.write(pid)
        boot_bin.seek(0x20)
        boot_bin.write(b)

    with game_files_path.joinpath("files", "opening.bnr").open("r+b") as banner:
        banner.seek(0x1860)
        banner.write(b)
