from __future__ import annotations

import enum


@enum.unique
class ResourceType(int, enum.Enum):
    ITEM = 0
    EVENT = enum.auto()
    TRICK = enum.auto()
    DAMAGE = enum.auto()
    VERSION = enum.auto()
    MISC = enum.auto()
    NODE_IDENTIFIER = enum.auto()

    @classmethod
    def names(cls) -> dict[ResourceType, str]:
        return {
            ResourceType.ITEM: "items",
            ResourceType.EVENT: "events",
            ResourceType.TRICK: "tricks",
            ResourceType.DAMAGE: "damage",
            ResourceType.VERSION: "versions",
            ResourceType.MISC: "misc",
            ResourceType.NODE_IDENTIFIER: "node_identifier",
        }

    @classmethod
    def from_index(cls, index: int) -> ResourceType:
        return cls(index)

    @property
    def type_index(self) -> int:
        return self.value

    @classmethod
    def from_str(cls, name: str) -> ResourceType:
        return _NAME_TO_TYPE[name]

    @property
    def as_string(self):
        return self.names()[self]

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


_NAME_TO_TYPE = {
    name: resource_type
    for resource_type, name in ResourceType.names().items()
}
