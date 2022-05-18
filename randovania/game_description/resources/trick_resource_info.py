import dataclasses

from frozendict import frozendict

from randovania.game_description.resources.resource_type import ResourceType


@dataclasses.dataclass(frozen=True, order=True, slots=True)
class TrickResourceInfo:
    long_name: str
    short_name: str
    description: str
    extra: frozendict = dataclasses.field(default_factory=frozendict)

    def __str__(self):
        return self.long_name

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.TRICK
