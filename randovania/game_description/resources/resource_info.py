from __future__ import annotations

import typing
from typing import Union, Tuple, Iterator, Optional

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.game_description.world.node_identifier import NodeIdentifier

if typing.TYPE_CHECKING:
    from randovania.game_description.resources.resource_database import ResourceDatabase

ResourceInfo = Union[SimpleResourceInfo, ItemResourceInfo, TrickResourceInfo,
                     PickupIndex, NodeIdentifier]
ResourceQuantity = Tuple[ResourceInfo, int]
ResourceGainTuple = Tuple[ResourceQuantity, ...]
ResourceGain = Union[Iterator[ResourceQuantity], typing.ItemsView[ResourceInfo, int]]


class ResourceCollection:
    _resources: dict[ResourceInfo, int]
    add_self_as_requirement_to_resources: bool = False

    def __init__(self):
        self._resources = {}

    @classmethod
    def with_database(cls, database: ResourceDatabase) -> ResourceCollection:
        return cls()

    def __getitem__(self, item: ResourceInfo):
        return self._resources.get(item, 0)

    def __str__(self):
        return f"<ResourceCollection with {self.num_resources} resources>"

    @property
    def _comparison_tuple(self):
        return self._resources, self.add_self_as_requirement_to_resources

    def __eq__(self, other):
        return isinstance(other, ResourceCollection) and (
                self._comparison_tuple == other._comparison_tuple
        )

    @property
    def num_resources(self):
        return len(self._resources)

    def has_resource(self, resource: ResourceInfo) -> bool:
        return self[resource] > 0

    def is_resource_set(self, resource: ResourceInfo) -> bool:
        """
        Checks if the given resource has a value explicitly set, instead of using the fallback of 0.
        :param resource:
        :return:
        """
        return resource in self._resources

    def set_resource(self, resource: ResourceInfo, quantity: int):
        self._resources[resource] = quantity

    @classmethod
    def from_dict(cls, resources: dict[ResourceInfo, int]) -> "ResourceCollection":
        result = cls()
        result.add_resource_gain(resources.items())
        return result

    @classmethod
    def from_resource_gain(cls, resource_gain: ResourceGain) -> "ResourceCollection":
        result = cls()
        result.add_resource_gain(resource_gain)
        return result

    def add_resource_gain(self, resource_gain: ResourceGain):
        for resource, quantity in resource_gain:
            self._resources[resource] = self._resources.get(resource, 0) + quantity

    def as_resource_gain(self) -> ResourceGain:
        yield from self._resources.items()

    def remove_resource(self, resource: ResourceInfo):
        self._resources.pop(resource, None)

    def duplicate(self) -> "ResourceCollection":
        result = ResourceCollection()
        result._resources.update(self._resources)
        result.add_self_as_requirement_to_resources = self.add_self_as_requirement_to_resources
        return result
