from enum import unique, Enum


@unique
class ResourceType(str, Enum):
    ITEM = "items"
    EVENT = "events"
    TRICK = "tricks"
    DAMAGE = "damage"
    VERSION = "versions"
    MISC = "misc"
    PICKUP_INDEX = "pickup_index"
    LOGBOOK_INDEX = "logbook_index"
    NODE_IDENTIFIER = "node_identifier"

    @classmethod
    def indices(cls) -> dict["ResourceType", int]:
        return {
            ResourceType.ITEM: 0,
            ResourceType.EVENT: 1,
            ResourceType.TRICK: 2,
            ResourceType.DAMAGE: 3,
            ResourceType.VERSION: 4,
            ResourceType.MISC: 5,
            ResourceType.PICKUP_INDEX: 7,
            ResourceType.LOGBOOK_INDEX: 9,
            ResourceType.NODE_IDENTIFIER: 10
        }

    @classmethod
    def from_index(cls, index: int) -> "ResourceType":
        return cls({v: k for k, v in cls.indices().items()}[index])

    @property
    def type_index(self) -> int:
        return self.indices()[self]

    @classmethod
    def from_str(cls, name: str) -> "ResourceType":
        return cls(name)

    @property
    def as_string(self):
        return self.value

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
        return self.type_index < other.type_index
