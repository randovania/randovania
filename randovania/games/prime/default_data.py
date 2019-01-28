import functools
import json

from randovania import get_data_path
from randovania.games.prime.binary_data import decode_file_path


@functools.lru_cache()
def decode_default_prime2() -> dict:
    json_database = get_data_path().joinpath("json_data", "prime2.json")

    if json_database.exists():
        with json_database.open("r") as open_file:
            return json.load(open_file)

    return decode_file_path(
        get_data_path().joinpath("binary_data", "prime2.bin"),
        get_data_path().joinpath("binary_data", "prime2_extra.json")
    )
