from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from frozendict import frozendict

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_type import ResourceType


@dataclasses.dataclass(frozen=True, slots=True)
class SimpleResourceInfo:
    resource_index: int
    long_name: str = dataclasses.field(hash=False)
    short_name: str = dataclasses.field(hash=False)
    resource_type: ResourceType
    extra: frozendict = dataclasses.field(hash=False, default_factory=frozendict)

    def __str__(self) -> str:
        return self.long_name
