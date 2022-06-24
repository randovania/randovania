import dataclasses

from frozendict import frozendict

from randovania.game_description.resources.resource_type import ResourceType


@dataclasses.dataclass(frozen=True, slots=True)
class ItemResourceInfo:
    resource_index: int
    long_name: str = dataclasses.field(hash=False)
    short_name: str = dataclasses.field(hash=False)
    max_capacity: int
    extra: frozendict = dataclasses.field(hash=False, default_factory=frozendict)
    resource_type: ResourceType = dataclasses.field(init=False, hash=False, repr=False, default=ResourceType.ITEM)

    def __str__(self):
        return self.long_name
