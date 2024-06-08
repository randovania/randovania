from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.graph.world_graph import WorldGraphNode

if TYPE_CHECKING:
    from collections.abc import Iterable

ActionStep = WorldGraphNode | PickupEntry


def format_action(action: ActionStep) -> str:
    if isinstance(action, WorldGraphNode):
        # TODO: use full node name
        return f"{type(action.original_node).__name__[0]}: {action.identifier.node}"
    else:
        return f"{type(action).__name__[0]}: {action.name}"


class Action:
    steps: tuple[ActionStep, ...]

    def __init__(self, steps: Iterable[ActionStep]):
        self.steps = tuple(steps)

    def __str__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return "[{}]".format(", ".join(format_action(a) for a in self.steps))

    @property
    def num_pickups(self) -> int:
        return sum(1 for p in self.steps if isinstance(p, PickupEntry))

    @property
    def num_steps(self) -> int:
        return len(self.steps)

    def split_pickups(self) -> tuple[list[WorldGraphNode], list[PickupEntry]]:
        pickups = []
        resources = []
        for step in self.steps:
            if isinstance(step, PickupEntry):
                pickups.append(step)
            else:
                resources.append(step)
        return resources, pickups
