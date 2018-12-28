import functools
import os

from randovania import get_data_path
from randovania.games.prime.binary_data import decode_file_path


@functools.lru_cache()
def decode_default_prime2() -> dict:
    return decode_file_path(
        get_data_path().joinpath("prime2.bin"),
        get_data_path().joinpath("prime2_extra.json")
    )
