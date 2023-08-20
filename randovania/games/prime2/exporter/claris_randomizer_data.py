from __future__ import annotations

import functools

from randovania import get_data_path
from randovania.lib import json_lib


@functools.lru_cache
def decode_randomizer_data() -> dict:
    randomizer_data_path = get_data_path().joinpath("ClarisPrimeRandomizer", "RandomizerData.json")
    return json_lib.read_path(randomizer_data_path)
