from __future__ import annotations

import typing

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo

ResourceInfo = SimpleResourceInfo | ItemResourceInfo | TrickResourceInfo | NodeResourceInfo

ResourceQuantity = tuple[ResourceInfo, int]
ResourceGainTuple = tuple[ResourceQuantity, ...]
ResourceGain = typing.Iterable[ResourceQuantity]
