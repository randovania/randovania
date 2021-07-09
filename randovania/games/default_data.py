import functools
import json
from pathlib import Path
from typing import Tuple

from randovania import get_data_path
from randovania.game_description import data_reader
from randovania.games.game import RandovaniaGame
from randovania.games.binary_data import decode_file_path


@functools.lru_cache()
def read_json_then_binary(game: RandovaniaGame) -> Tuple[Path, dict]:
    dir_path = get_data_path().joinpath("json_data", f"{game.value}")
    if dir_path.exists():
        return dir_path, data_reader.read_split_file(dir_path)

    json_path = get_data_path().joinpath("json_data", f"{game.value}.json")
    if json_path.exists():
        with json_path.open("r") as open_file:
            return json_path, json.load(open_file)

    binary_path = get_data_path().joinpath("binary_data", f"{game.value}.bin")
    return binary_path, decode_file_path(binary_path)
