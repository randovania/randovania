from typing import List

from randovania.patching.patcher import Patcher


class SuperDuperMetroidPatcher(Patcher):
    def default_output_file(self, seed_hash: str) -> str:
        """
        Provides a output file name with the given seed hash.
        :param seed_hash:
        :return:
        """
        return "SM Randomizer - {}".format(seed_hash)

    @property
    def valid_input_file_types(self) -> List[str]:
        return ["smc", "sfc"]

    @property
    def valid_output_file_types(self) -> List[str]:
        return ["smc", "sfc"]
