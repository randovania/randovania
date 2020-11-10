import functools
import json
from pathlib import Path
from typing import Tuple

from randovania import get_data_path
from randovania.games.game import RandovaniaGame
from randovania.games.prime.binary_data import decode_file_path


@functools.lru_cache()
def read_json_then_binary(game: RandovaniaGame) -> Tuple[Path, dict]:
    json_path = get_data_path().joinpath("json_data", f"{game.value}.json")
    if json_path.exists():
        with json_path.open("r") as open_file:
            return json_path, json.load(open_file)

    binary_path = get_data_path().joinpath("binary_data", f"{game.value}.bin")
    return binary_path, decode_file_path(binary_path)


def decode_default_prime2() -> dict:
    return read_json_then_binary(RandovaniaGame.PRIME2)[1]


def decode_default_prime3() -> dict:
    return read_json_then_binary(RandovaniaGame.PRIME3)[1]


@functools.lru_cache()
def decode_randomizer_data() -> dict:
    randomizer_data_path = get_data_path().joinpath("ClarisPrimeRandomizer", "RandomizerData.json")

    with randomizer_data_path.open() as randomizer_data_file:
        return json.load(randomizer_data_file)
