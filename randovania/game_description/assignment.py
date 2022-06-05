from typing import NamedTuple

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.dock import DockWeakness
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.node_identifier import NodeIdentifier


class PickupTarget(NamedTuple):
    pickup: PickupEntry
    player: int


PickupAssignment = dict[PickupIndex, PickupTarget]
PickupTargetAssociation = tuple[PickupIndex, PickupTarget]
NodeConfigurationAssociation = tuple[NodeIdentifier, Requirement]
DockWeaknessAssociation = tuple[DockNode, DockWeakness]
