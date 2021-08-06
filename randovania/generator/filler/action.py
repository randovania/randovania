from typing import Union

from randovania.game_description.world.node import ResourceNode
from randovania.generator.filler.pickup_list import PickupCombination

Action = Union[ResourceNode, PickupCombination]


def action_name(action: Action) -> str:
    if isinstance(action, tuple):
        return "[{}]".format(", ".join(a.name for a in action))
    else:
        return f"({type(action).__name__}) {action.name}"
