from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.resource_node import ResourceNode

if TYPE_CHECKING:
    from randovania.game_description.db.node_identifier import NodeIdentifier


@dataclasses.dataclass(frozen=True, slots=True)
class RemoteCollectionNode(ResourceNode):
    remote_node: NodeIdentifier

    def __repr__(self) -> str:
        return f"RemoteCollectionNode({self.name!r})"
