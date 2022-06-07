import dataclasses

from frozendict import frozendict

from randovania.game_description.resources.resource_type import ResourceType


@dataclasses.dataclass(frozen=True, order=True, slots=True)
class TrickResourceInfo:
    long_name: str = dataclasses.field(hash=False)
    short_name: str
    description: str = dataclasses.field(hash=False)
    extra: frozendict = dataclasses.field(hash=False, default_factory=frozendict)
    resource_type: ResourceType = dataclasses.field(init=False, hash=False, repr=False, default=ResourceType.TRICK)

    def __str__(self):
        return self.long_name
