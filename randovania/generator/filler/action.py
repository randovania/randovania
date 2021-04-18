from typing import Union, Tuple

from randovania.game_description.node import ResourceNode
from randovania.game_description.resources.pickup_entry import PickupEntry

Action = Union[ResourceNode, Tuple[PickupEntry, ...]]


def action_name(action: Action) -> str:
    if isinstance(action, tuple):
        return "[{}]".format(", ".join(a.name for a in action))
    return action.name
