import functools
import json
from pathlib import Path

from randovania import get_data_path
from randovania.games.prime.binary_data import decode_file_path


def prime2_json_path() -> Path:
    return get_data_path().joinpath("json_data", "prime2.json")


def prime2_human_readable_path() -> Path:
    return prime2_json_path().with_suffix(".txt")


@functools.lru_cache()
def decode_default_prime2() -> dict:
    json_database = prime2_json_path()

    if json_database.exists():
        with json_database.open("r") as open_file:
            return json.load(open_file)

    return decode_file_path(get_data_path().joinpath("binary_data", "prime2.bin"))


@functools.lru_cache()
def decode_randomizer_data() -> dict:
    randomizer_data_path = get_data_path().joinpath("ClarisPrimeRandomizer", "RandomizerData.json")

    with randomizer_data_path.open() as randomizer_data_file:
        return json.load(randomizer_data_file)
