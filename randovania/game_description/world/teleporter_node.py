import dataclasses

from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node import Node


@dataclasses.dataclass(frozen=True)
class TeleporterNode(Node):
    default_connection: AreaIdentifier
    keep_name_when_vanilla: bool
    editable: bool

    def __repr__(self):
        return "TeleporterNode({!r} -> {})".format(self.name, self.default_connection)
