from __future__ import annotations

import dataclasses
import typing

from randovania.game_description.db.resource_node import ResourceNode

if typing.TYPE_CHECKING:
    from randovania.game_description.requirements.base import Requirement


@dataclasses.dataclass(frozen=True, slots=True)
class TeleporterNetworkNode(ResourceNode):
    """
    Represents a node that belongs to a set, where you can freely move between if some conditions are satisfied.
    - can only teleport *to* if `is_unlocked` is satisfied
    - can only teleport *from* if the node has been activated

    A TeleporterNetworkNode being activated is implemented as being collected, with this class being a ResourceNode.
    There are three methods of activating a TeleporterNetworkNode:

    Method 1:
    - Be the starting node

    Method 2:
    - Collecting a TeleporterNetworkNode also collects all other nodes in the same network with satisfied `is_unlocked`

    Method 3:
    - Collect the node normally by reaching it, with `is_unlocked` satisfied and one of:
      - `requirement_to_activate` is satisfied
      - this node was already collected
    """

    is_unlocked: Requirement
    network: str
    requirement_to_activate: Requirement
