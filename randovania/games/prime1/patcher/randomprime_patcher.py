from typing import List

from randovania.patching.patcher import Patcher


class RandomprimePatcher(Patcher):
    def default_output_file(self, seed_hash: str) -> str:
        return "Prime Randomizer - {}".format(seed_hash)

    @property
    def valid_input_file_types(self) -> List[str]:
        return ["iso"]

    @property
    def valid_output_file_types(self) -> List[str]:
        return ["iso", "ciso", "gcz"]
