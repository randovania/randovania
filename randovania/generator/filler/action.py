from typing import Union, Iterable

from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.world.resource_node import ResourceNode

ActionStep = Union[ResourceNode, PickupEntry]


class Action:
    steps: tuple[ActionStep, ...]

    def __init__(self, steps: Iterable[ActionStep]):
        self.steps = tuple(steps)

    @property
    def name(self) -> str:
        return "[{}]".format(", ".join(
            f"{type(a).__name__[0]}: {a.name}"
            for a in self.steps
        ))

    @property
    def num_pickups(self) -> int:
        return sum(1 for p in self.steps if isinstance(p, PickupEntry))

    @property
    def num_steps(self):
        return len(self.steps)

    def split_pickups(self) -> tuple[list[ResourceNode], list[PickupEntry]]:
        pickups = []
        resources = []
        for step in self.steps:
            if isinstance(step, PickupEntry):
                pickups.append(step)
            else:
                resources.append(step)
        return resources, pickups
