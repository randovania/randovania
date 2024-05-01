from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from randovania.game_description.db.dock import DockWeakness
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.resources.pickup_index import PickupIndex

if TYPE_CHECKING:
    from randovania.game_description.pickup.pickup_entry import PickupEntry


class PickupTarget(NamedTuple):
    pickup: PickupEntry
    player: int


PickupAssignment = dict[PickupIndex, PickupTarget]
PickupTargetAssociation = tuple[PickupIndex, PickupTarget]
DockWeaknessAssociation = tuple[DockNode, DockWeakness]
