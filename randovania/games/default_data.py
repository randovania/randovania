import functools
from pathlib import Path

from randovania import get_data_path
from randovania.game_description import data_reader
from randovania.games import binary_data
from randovania.games.game import RandovaniaGame


@functools.lru_cache()
def read_json_then_binary(game: RandovaniaGame) -> tuple[Path, dict]:
    dir_path = game.data_path.joinpath("json_data")
    if dir_path.exists():
        return dir_path, data_reader.read_split_file(dir_path)

    json_path = dir_path.joinpath(f"{game.value}.json")
    if json_path.exists():
        with json_path.open("r") as open_file:
            return json_path, data_reader.read_json_file(open_file)

    binary_path = get_data_path().joinpath("binary_data", f"{game.value}.bin")
    return binary_path, binary_data.decode_file_path(binary_path)
