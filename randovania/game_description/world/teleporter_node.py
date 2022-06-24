import dataclasses
import typing

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node import Node, NodeContext


@dataclasses.dataclass(frozen=True, slots=True)
class TeleporterNode(Node):
    default_connection: AreaIdentifier
    keep_name_when_vanilla: bool
    editable: bool

    def __repr__(self):
        return f"TeleporterNode({self.name!r} -> {self.default_connection})"

    def connections_from(self, context: NodeContext) -> typing.Iterator[tuple[Node, Requirement]]:
        target_area_identifier = context.patches.get_elevator_connection_for(self)
        if target_area_identifier is None:
            return

        yield context.node_provider.default_node_for_area(target_area_identifier), Requirement.trivial()
