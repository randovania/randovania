from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum


class RandovaniaGame(BitPackEnum, Enum):
    PRIME1 = "prime1"
    PRIME2 = "prime2"
    PRIME3 = "prime3"
