from __future__ import annotations

import dataclasses
import typing

from randovania.game_description.resources.resource_type import ResourceType

if typing.TYPE_CHECKING:
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.node import Node, NodeContext


@dataclasses.dataclass(frozen=True, slots=True)
class NodeResourceInfo:
    resource_index: int
    node_identifier: NodeIdentifier
    long_name: str = dataclasses.field(hash=False, repr=False)
    short_name: str = dataclasses.field(hash=False, repr=False)
    resource_type: ResourceType = dataclasses.field(init=False, hash=False, repr=False,
                                                    default=ResourceType.NODE_IDENTIFIER)

    def __str__(self):
        return self.long_name

    @classmethod
    def from_node(cls, node: Node, context: NodeContext) -> NodeResourceInfo:
        result = getattr(node, "cache_node_resource_info", None)
        if result is None:
            result = cls(
                context.database.first_unused_resource_index() + node.node_index,
                node.identifier,
                node.name,
                node.name,
            )
            object.__setattr__(node, "cache_node_resource_info", result)

        return result

    @classmethod
    def from_identifier(cls, identifier: NodeIdentifier, context: NodeContext) -> NodeResourceInfo:
        return cls.from_node(context.node_provider.node_by_identifier(identifier), context)
