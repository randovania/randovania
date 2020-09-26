from enum import unique, Enum


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
    def negated_prefix(self) -> str:
        if self is ResourceType.EVENT:
            return "Before "
        elif self is ResourceType.MISC:
            return "Disabled "
        else:
            return "No "

    @property
    def non_negated_prefix(self) -> str:
        if self is ResourceType.EVENT:
            return "After "
        elif self is ResourceType.MISC:
            return "Enabled "
        else:
            return ""

    def __lt__(self, other):
        return self.value < other.value


_TYPES_NO_FOR_REQUIREMENT = {
    ResourceType.PICKUP_INDEX,
    ResourceType.GATE_INDEX,
    ResourceType.LOGBOOK_INDEX,
}
