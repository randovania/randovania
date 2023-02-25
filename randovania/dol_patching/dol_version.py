import dataclasses
from typing import Iterable

from randovania.dol_patching.dol_file import DolFile
from randovania.games.game import RandovaniaGame


@dataclasses.dataclass(frozen=True)
class DolVersion:
    game: RandovaniaGame
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
            if build_string == version.build_string:
                return version

    raise RuntimeError(f"Unsupported game version")
