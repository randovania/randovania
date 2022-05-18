import dataclasses
import typing

from randovania.game_description.requirements import Requirement
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node import Node, NodeContext


@dataclasses.dataclass(frozen=True, slots=True)
class TeleporterNode(Node):
    default_connection: AreaIdentifier
    keep_name_when_vanilla: bool
    editable: bool

    def __repr__(self):
        return "TeleporterNode({!r} -> {})".format(self.name, self.default_connection)

    def connections_from(self, context: NodeContext) -> typing.Iterator[tuple[Node, Requirement]]:
        target_area_identifier = context.patches.elevator_connection.get(
            context.node_provider.identifier_for_node(self),
            self.default_connection,
        )
        if target_area_identifier is None:
            return

        yield context.node_provider.default_node_for_area(target_area_identifier), Requirement.trivial()
