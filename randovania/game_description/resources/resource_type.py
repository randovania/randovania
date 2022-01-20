from enum import unique, Enum
from typing import Dict


@unique
class ResourceType(str, Enum):
    ITEM = "items"
    EVENT = "events"
    TRICK = "tricks"
    DAMAGE = "damage"
    VERSION = "versions"
    MISC = "misc"
    _INDEXED = "_indexed"
    PICKUP_INDEX = "pickup_index"
    GATE_INDEX = "gate_index"
    LOGBOOK_INDEX = "logbook_index"
    SHIP_NODE = "ship_node"

    @classmethod
    def indices(cls) -> Dict["ResourceType", int]:
        return {
            ResourceType.ITEM: 0,
            ResourceType.EVENT: 1,
            ResourceType.TRICK: 2,
            ResourceType.DAMAGE: 3,
            ResourceType.VERSION: 4,
            ResourceType.MISC: 5,
            ResourceType._INDEXED: 6,
            ResourceType.PICKUP_INDEX: 7,
            ResourceType.GATE_INDEX: 8,
            ResourceType.LOGBOOK_INDEX: 9,
            ResourceType.SHIP_NODE: 10
        }

    @classmethod
    def from_index(cls, index: int) -> "ResourceType":
        return cls({v: k for k, v in cls.indices().items()}[index])

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

    @property
    def index(self) -> int:
        return self.indices()[self]

    def __lt__(self, other):
        return self.index < other.index
