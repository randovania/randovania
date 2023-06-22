import dataclasses
from typing import Iterable

from ppc_asm.dol_file import DolFile
from retro_data_structures.game_check import Game


@dataclasses.dataclass(frozen=True)
class DolVersion:
    game: Game
    description: str
    build_string_address: int
    build_string: bytes
    sda2_base: int
    sda13_base: int


def find_version_for_dol(dol_file: DolFile, all_versions: Iterable[DolVersion]) -> DolVersion:
    dol_file.set_editable(False)
    with dol_file:
        for version in all_versions:
            build_string = dol_file.read(version.build_string_address, len(version.build_string))
            if (build_string[:6], build_string[6 + 16:]) == (version.build_string[:6], version.build_string[6 + 16:]):
                return version

    raise RuntimeError("Unsupported game version")
