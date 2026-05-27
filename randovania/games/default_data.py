from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from randovania import get_data_path
from randovania.game_description import binary_data, data_reader

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.game.game_enum import RandovaniaGame


@functools.lru_cache
def read_json_then_binary(game: RandovaniaGame) -> tuple[Path, dict]:
    dir_path = game.data_path.joinpath("logic_database")
    if dir_path.exists():
        return dir_path, data_reader.read_split_file(dir_path)

    binary_path = get_data_path().joinpath("binary_data", f"{game.value}.bin")
    return binary_path, binary_data.decode_file_path(binary_path)
