from __future__ import annotations

import dataclasses
import typing

from randovania.game_description.resources.resource_type import ResourceType

if typing.TYPE_CHECKING:
    from randovania.game_description.db.node_identifier import NodeIdentifier


@dataclasses.dataclass(frozen=True, slots=True)
class NodeResourceInfo:
    resource_index: int
    node_identifier: NodeIdentifier
    long_name: str = dataclasses.field(hash=False, repr=False)
    short_name: str = dataclasses.field(hash=False, repr=False)
    resource_type: ResourceType = dataclasses.field(
        init=False, hash=False, repr=False, default=ResourceType.NODE_IDENTIFIER
    )

    def __str__(self) -> str:
        return self.long_name

    @property
    def extra(self) -> dict:
        return {}
