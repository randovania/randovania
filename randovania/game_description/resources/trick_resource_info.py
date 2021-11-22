from typing import NamedTuple

from frozendict import frozendict

from randovania.game_description.resources.resource_type import ResourceType


class TrickResourceInfo(NamedTuple):
    long_name: str
    short_name: str
    description: str
    extra: frozendict = frozendict()

    def __str__(self):
        return self.long_name

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.TRICK
