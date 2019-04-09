from typing import NamedTuple

from randovania.game_description.resources.resource_type import ResourceType


class SimpleResourceInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str
    resource_type: ResourceType

    def __str__(self):
        short_resource_name = self.resource_type.short_name
        if short_resource_name is not None:
            return "{}: {}".format(short_resource_name, self.long_name)
        else:
            return self.long_name
