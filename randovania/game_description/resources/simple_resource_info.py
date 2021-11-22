from typing import NamedTuple

from frozendict import frozendict

from randovania.game_description.resources.resource_type import ResourceType


class SimpleResourceInfo(NamedTuple):
    long_name: str
    short_name: str
    resource_type: ResourceType
    extra: frozendict = frozendict()

    def __str__(self):
        return self.long_name
