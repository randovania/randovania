from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum


class RandovaniaGame(BitPackEnum, Enum):
    PRIME1 = "prime1"
    PRIME2 = "prime2"
    PRIME3 = "prime3"

    @property
    def short_name(self) -> str:
        return SHORT_NAME[self]

    @property
    def long_name(self) -> str:
        return LONG_NAME[self]


SHORT_NAME = {
    RandovaniaGame.PRIME1: "Prime",
    RandovaniaGame.PRIME2: "Echoes",
    RandovaniaGame.PRIME3: "Corruption"
}

LONG_NAME = {
    RandovaniaGame.PRIME1: "Metroid Prime",
    RandovaniaGame.PRIME2: "Metroid Prime 2: Echoes",
    RandovaniaGame.PRIME3: "Metroid Prime 3: Corruption"
}
