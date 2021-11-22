from typing import NamedTuple, Optional

from frozendict import frozendict

from randovania.game_description.resources.resource_type import ResourceType


class ItemResourceInfo(NamedTuple):
    long_name: str
    short_name: str
    max_capacity: int
    extra: frozendict = frozendict()

    def __str__(self):
        return self.long_name

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.ITEM
