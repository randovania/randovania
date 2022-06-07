from __future__ import annotations

import dataclasses
import typing
from typing import Optional

from randovania.game_description.resources.resource_type import ResourceType

if typing.TYPE_CHECKING:
    from randovania.game_description.world.node_identifier import NodeIdentifier
    from randovania.game_description.world.node import Node, NodeContext


@dataclasses.dataclass(frozen=True, order=True, slots=True)
class NodeResourceInfo:
    node_identifier: NodeIdentifier
    long_name: str = dataclasses.field(hash=False, repr=False)
    short_name: str = dataclasses.field(hash=False, repr=False)
    resource_type: ResourceType = dataclasses.field(init=False, hash=False, repr=False,
                                                    default=ResourceType.NODE_IDENTIFIER)
    resource_index: Optional[int] = dataclasses.field(init=False, hash=False, compare=False, default=None)

    def __str__(self):
        return self.long_name

    @classmethod
    def from_node(cls, node: Node, context: NodeContext) -> NodeResourceInfo:
        return cls(
            node.identifier,
            node.name,
            node.name,
        )

    @classmethod
    def from_identifier(cls, identifier: NodeIdentifier, context: NodeContext) -> NodeResourceInfo:
        return cls.from_node(context.node_provider.node_by_identifier(identifier), context)
