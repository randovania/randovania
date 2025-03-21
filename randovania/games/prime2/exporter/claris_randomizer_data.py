from __future__ import annotations

import functools
import typing

from randovania import get_data_path
from randovania.lib import json_lib


@functools.lru_cache
def decode_randomizer_data() -> dict:
    randomizer_data_path = get_data_path().joinpath("ClarisPrimeRandomizer", "RandomizerData.json")
    return typing.cast("dict", json_lib.read_path(randomizer_data_path))
