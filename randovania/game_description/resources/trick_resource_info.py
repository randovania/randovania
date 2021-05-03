from typing import NamedTuple

from randovania.game_description.resources.resource_type import ResourceType


class TrickResourceInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str
    description: str

    def __str__(self):
        return self.long_name

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.TRICK
