from enum import unique, Enum
from typing import Optional


@unique
class ResourceType(Enum):
    ITEM = 0
    EVENT = 1
    TRICK = 2
    DAMAGE = 3
    VERSION = 4
    MISC = 5
    DIFFICULTY = 6
    PICKUP_INDEX = 7
    GATE_INDEX = 8
    LOGBOOK_INDEX = 9

    @property
    def is_usable_for_requirement(self) -> bool:
        return self not in _TYPES_NO_FOR_REQUIREMENT

    @property
    def short_name(self) -> Optional[str]:
        if self == ResourceType.ITEM:
            return "I"
        elif self == ResourceType.EVENT:
            return "E"
        elif self == ResourceType.TRICK:
            return "T"
        else:
            return None

    def __lt__(self, other):
        return self.value < other.value


_TYPES_NO_FOR_REQUIREMENT = {
    ResourceType.PICKUP_INDEX,
    ResourceType.GATE_INDEX,
    ResourceType.LOGBOOK_INDEX,
}
