from typing import NamedTuple

from randovania.game_description.resources.resource_type import ResourceType


class SimpleResourceInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str
    resource_type: ResourceType

    def __str__(self):
        return self.long_name
