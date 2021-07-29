from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum


class RandovaniaGame(BitPackEnum, Enum):
    METROID_PRIME = "prime1"
    METROID_PRIME_ECHOES = "prime2"
    METROID_PRIME_CORRUPTION = "prime3"

    @property
    def short_name(self) -> str:
        return SHORT_NAME[self]

    @property
    def long_name(self) -> str:
        return LONG_NAME[self]

    @property
    def is_experimental(self) -> bool:
        return self in EXPERIMENTAL


SHORT_NAME = {
    RandovaniaGame.METROID_PRIME: "Prime",
    RandovaniaGame.METROID_PRIME_ECHOES: "Echoes",
    RandovaniaGame.METROID_PRIME_CORRUPTION: "Corruption"
}

LONG_NAME = {
    RandovaniaGame.METROID_PRIME: "Metroid Prime",
    RandovaniaGame.METROID_PRIME_ECHOES: "Metroid Prime 2: Echoes",
    RandovaniaGame.METROID_PRIME_CORRUPTION: "Metroid Prime 3: Corruption"
}

EXPERIMENTAL = {
    RandovaniaGame.METROID_PRIME_CORRUPTION,
}
