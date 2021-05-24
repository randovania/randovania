from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum


class LayoutArtifactMode(BitPackEnum, Enum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    ELEVEN = 11
    TWELVE = 12

    @property
    def num_artifacts(self):
        return self.value
