from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.pickup.pickup_entry import PickupEntry

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.graph.state import GraphOrResourceNode

    type ActionStep = GraphOrResourceNode | PickupEntry


def format_action(action: ActionStep) -> str:
    if isinstance(action, PickupEntry):
        # TODO: could combine both sides by always using `name`
        # But maybe instead change how with WorldGraphNode the first letter is always W no matter the kind of node.
        return f"{type(action).__name__[0]}: {action.name}"
    else:
        return f"{type(action).__name__[0]}: {action.identifier}"


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

    def split_pickups(self) -> tuple[list[GraphOrResourceNode], list[PickupEntry]]:
        pickups = []
        resources = []
        for step in self.steps:
            if isinstance(step, PickupEntry):
                pickups.append(step)
            else:
                resources.append(step)
        return resources, pickups
