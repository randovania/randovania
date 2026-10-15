from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.requirements.base import Requirement

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement
    from randovania.game_description.resources.resource_database import ResourceDatabase


class NodeRequirement(Requirement):
    __slots__ = ("node_identifier",)
    node_identifier: NodeIdentifier

    def __copy__(self) -> NodeRequirement:
        return NodeRequirement(self.node_identifier)

    def __reduce__(self) -> tuple[type[NodeRequirement], tuple[NodeIdentifier]]:
        return type(self), (self.node_identifier,)

    def __init__(self, node_identifier: NodeIdentifier):
        self.node_identifier = node_identifier

    def __repr__(self) -> str:
        return f"Req {self.node_identifier}"

    @property
    def is_damage(self) -> bool:
        return False

    def simplify(self, keep_comments: bool = False) -> Requirement:
        return self

    @property
    def pretty_text(self) -> str:
        return str(self.node_identifier)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NodeRequirement):
            return False
        return self.node_identifier == other.node_identifier

    def __lt__(self, other: Requirement) -> bool:
        assert isinstance(other, NodeRequirement)
        return self.node_identifier < other.node_identifier

    def __hash__(self) -> int:
        return hash(self.node_identifier)

    def iterate_resource_requirements(self, database: ResourceDatabase) -> Iterator[ResourceRequirement]:
        yield from []
