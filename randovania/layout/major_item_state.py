from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum


class MajorItemState(BitPackEnum, Enum):
    SHUFFLED = "shuffled"
    ORIGINAL_LOCATION = "original-location"
    STARTING_ITEM = "starting-item"
    REMOVED = "removed"
