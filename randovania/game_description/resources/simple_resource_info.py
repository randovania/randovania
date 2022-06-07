import dataclasses

from frozendict import frozendict

from randovania.game_description.resources.resource_type import ResourceType


@dataclasses.dataclass(frozen=True, order=True, slots=True)
class SimpleResourceInfo:
    long_name: str = dataclasses.field(hash=False)
    short_name: str
    resource_type: ResourceType
    extra: frozendict = dataclasses.field(hash=False, default_factory=frozendict)

    def __str__(self):
        return self.long_name
