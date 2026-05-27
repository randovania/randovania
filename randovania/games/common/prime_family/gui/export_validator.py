from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import nod

from randovania.gui.dialog.game_export_dialog import is_file_validator

if TYPE_CHECKING:
    from pathlib import Path


def discover_game(iso_path: Path) -> tuple[str, str] | None:
    """Identifies which GameCube/Wii game belongs to the target ISO file.
    Returns:
        - None, if incompatible file
        - game id, game title tuple
    """
    if not iso_path.is_file():
        return None

    try:
        disc, is_wii = nod.open_disc_from_image(iso_path)
        data_partition: nod.Partition = disc.get_data_partition()
        header: nod.DolHeader = data_partition.get_header()
    except RuntimeError as e:
        logging.warning("Unable to parse %s: %s", str(iso_path), str(e))
        return None

    return header.game_id.decode("UTF-8"), header.game_title.split(b"\x00")[0].decode("UTF-8")


def is_prime1_iso_validator(file: Path | None, *, iso_required: bool = False) -> bool:
    """Validates if the given path is a proper input for Metroid Prime.
    - If input doesn't exist, returns True
    - If input is ISO or iso_required is set, return False if it's Metroid Prime otherwise True
    - If input is not ISO, returns False.
    """
    if is_file_validator(file):
        return True

    # Check if correct game, but only for ISO files (as we can't for them).
    if file.suffix.lower() == ".iso" or iso_required:
        iso_details = discover_game(file)
        if iso_details is None:
            return True
        return not iso_details[0].startswith("GM8")

    return False


def is_prime2_iso_validator(file: Path | None) -> bool:
    """Returns False when the given path exists and is a Prime 2 ISO, True otherwise"""
    if is_file_validator(file):
        return True

    # Echoes only support ISO, so we can always identify the game
    iso_details = discover_game(file)
    if iso_details is None:
        return True

    return not iso_details[0].startswith("G2M")
