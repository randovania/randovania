from pathlib import Path


def patch_game_name_and_id(game_files_path: Path, new_name: str):
    b = new_name.encode("ASCII")
    if len(b) > 40:
        raise ValueError("Name '{}' is bigger than 40 bytes".format(new_name))

    with game_files_path.joinpath("sys", "boot.bin").open("r+b") as boot_bin:
        boot_bin.seek(0x0)
        boot_bin.write(b"G2ME0R")
        boot_bin.seek(0x20)
        boot_bin.write(b)

    with game_files_path.joinpath("files", "opening.bnr").open("r+b") as banner:
        banner.seek(0x1860)
        banner.write(b)
