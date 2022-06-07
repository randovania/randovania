import dataclasses

from frozendict import frozendict

from randovania.game_description.resources.resource_type import ResourceType


@dataclasses.dataclass(frozen=True, order=True, slots=True)
class ItemResourceInfo:
    long_name: str
    short_name: str
    max_capacity: int
    extra: frozendict = dataclasses.field(hash=False, default_factory=frozendict)
    resource_type: ResourceType = dataclasses.field(init=False, hash=False, repr=False, default=ResourceType.ITEM)

    def __str__(self):
        return self.long_name
