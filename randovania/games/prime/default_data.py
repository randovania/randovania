import functools
import os

from randovania import get_data_path
from randovania.games.prime.binary_data import decode_file_path


@functools.lru_cache()
def decode_default_prime2() -> dict:
    return decode_file_path(
        os.path.join(get_data_path(), "prime2.bin"),
        os.path.join(get_data_path(), "prime2_extra.json")
    )
