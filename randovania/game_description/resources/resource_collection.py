# distutils: language=c++
# cython: profile=False
# pyright: reportPossiblyUnboundVariable=false
# pyright: reportReturnType=false
# mypy: disable-error-code="return"

from __future__ import annotations

import copy
import typing

if typing.TYPE_CHECKING:
    # The package is named `Cython`, so in a case-sensitive system mypy fails to find cython with just `import cython`
    import Cython as cython

    from randovania.game_description.game_database_view import ResourceDatabaseView
    from randovania.game_description.resources.resource_info import ResourceGain, ResourceGainTuple, ResourceInfo
else:
    # However cython's compiler seems to expect the import to be this way, otherwise `cython.compiled` breaks
    import cython

# ruff: noqa: UP046

if cython.compiled:
    if not typing.TYPE_CHECKING:
        from cython.cimports.libcpp.unordered_map import unordered_map
        from cython.cimports.libcpp.vector import vector
        from cython.cimports.randovania.lib.bitmask import Bitmask
else:
    from randovania.lib.bitmask import Bitmask
    from randovania.lib.cython_helper import UnorderedMap as unordered_map
    from randovania.lib.cython_helper import Vector as vector


@cython.final
@cython.cclass
class ResourceCollection:
    # Attributes defined in resource_collection.pxd

    def __init__(self, resource_database: ResourceDatabaseView, resource_array: vector[cython.int]) -> None:
        self.resource_bitmask = Bitmask.create_native()
        self._resource_array = resource_array
        self._existing_resources: dict[int, ResourceInfo] = {}
        self._damage_reduction_cache = unordered_map[cython.size_t, cython.float]()
        self._resource_database = resource_database

    @classmethod
    def with_resource_count(cls, resource_database: ResourceDatabaseView, count: cython.size_t) -> ResourceCollection:
        result = cls(resource_database, vector[cython.int]())
        if cython.compiled:
            result._resize_array_to_fit(count)
        else:
            result._resource_array = vector([0]) * count
        return result

    @cython.ccall
    def _resize_array_to_fit(self, size: cython.size_t) -> cython.void:
        target_size: cython.size_t = self._resource_array.size()
        if target_size < 10:
            target_size = 10
        while target_size < size:
            target_size *= 2
        self._resource_array.resize(target_size, 0)

    def __getitem__(self, item: ResourceInfo) -> int:
        return self.get(item)

    def current_array_size(self) -> cython.size_t:
        return self._resource_array.size()

    @cython.ccall
    def get(self, item: ResourceInfo) -> cython.int:
        resource_index: cython.size_t = item.resource_index
        if resource_index < self._resource_array.size():
            return self._resource_array[resource_index]
        else:
            return 0

    @cython.ccall
    def get_index(self, resource_index: cython.size_t) -> cython.int:
        if resource_index < self._resource_array.size():
            return self._resource_array[resource_index]
        else:
            return 0

    def __str__(self) -> str:
        return f"<ResourceCollection with {self.num_resources} resources>"

    @property
    def _comparison_tuple(self) -> ResourceGainTuple:
        return tuple(self.as_resource_gain())

    def __hash__(self) -> int:
        return hash(self._comparison_tuple)

    def __eq__(self, other: object) -> cython.bint:
        return isinstance(other, ResourceCollection) and (self._comparison_tuple == other._comparison_tuple)

    @property
    def num_resources(self) -> int:
        return len(self._existing_resources)

    @cython.ccall
    @cython.inline
    def has_resource(self, resource: ResourceInfo) -> cython.bint:
        return self.get(resource) > 0

    @cython.ccall
    @cython.inline
    def is_resource_set(self, resource: ResourceInfo) -> cython.bint:
        """
        Checks if the given resource has a value explicitly set, instead of using the fallback of 0.
        :param resource:
        :return:
        """
        return resource.resource_index in self._existing_resources

    def set_resource(self, resource: ResourceInfo, quantity: cython.int) -> cython.void:
        """Sets the quantity of the given resource to be exactly the given value.
        This method should be used in exceptional cases only. For common usage, use `add_resource_gain`.
        """
        quantity = max(quantity, 0)
        resource_index: cython.size_t = resource.resource_index
        self._damage_reduction_cache.clear()
        if self._resource_array.size() <= resource_index:
            self._resize_array_to_fit(resource_index + 1)
        self._resource_array[resource_index] = quantity
        self._existing_resources[resource_index] = resource

        if quantity > 0:
            self.resource_bitmask.set_bit(resource_index)
        else:
            self.resource_bitmask.unset_bit(resource_index)

    @classmethod
    def from_dict(cls, view: ResourceDatabaseView, resources: dict[ResourceInfo, int]) -> ResourceCollection:
        result = view.create_resource_collection()
        result.add_resource_gain(resources.items())
        return result

    @classmethod
    def from_resource_gain(cls, game: ResourceDatabaseView, resource_gain: ResourceGain) -> ResourceCollection:
        result = game.create_resource_collection()
        result.add_resource_gain(resource_gain)
        return result

    @cython.locals(resource=object, quantity=cython.int)
    @cython.ccall
    def add_resource(self, resource: ResourceInfo, quantity: cython.int) -> cython.void:
        self._damage_reduction_cache.clear()

        resource_index: cython.size_t = resource.resource_index
        if self._resource_array.size() <= resource_index:
            self._resize_array_to_fit(resource_index + 1)

        new_amount: cython.int = self._resource_array[resource_index] + quantity
        if new_amount < 0:
            new_amount = 0
        self._resource_array[resource_index] = new_amount
        self._existing_resources[resource_index] = resource

        if new_amount > 0:
            self.resource_bitmask.set_bit(resource_index)
        else:
            self.resource_bitmask.unset_bit(resource_index)

    @cython.locals(resource=object, quantity=cython.int)
    @cython.ccall
    @cython.inline
    def add_resource_gain(self, resource_gain: ResourceGain) -> cython.void:
        for resource, quantity in resource_gain:
            self.add_resource(resource, quantity)

    def as_resource_gain(self) -> ResourceGain:
        for index, resource in self._existing_resources.items():
            yield resource, self._resource_array[index]

    def remove_resource(self, resource: ResourceInfo) -> cython.void:
        """
        Removes the given resource, making `is_resource_set` return False for it.
        This should be used in exceptional cases only. Consider `add_resource_gain` with negative gain instead.
        """
        resource_index: cython.size_t = resource.resource_index
        self._existing_resources.pop(resource_index, None)

        if resource_index < self._resource_array.size():
            self._resource_array[resource_index] = 0

        self.resource_bitmask.unset_bit(resource_index)

    def duplicate(self) -> ResourceCollection:
        result: ResourceCollection = ResourceCollection(self._resource_database, copy.copy(self._resource_array))
        result._existing_resources.update(self._existing_resources)
        result.resource_bitmask = self.resource_bitmask.copy()
        return result

    @cython.ccall
    # @cython.exceptval(check=False)
    def get_damage_reduction(self, resource_index: cython.size_t) -> cython.float:
        if cython.compiled:
            it = self._damage_reduction_cache.find(resource_index)  # type: ignore[attr-defined]
            if it != self._damage_reduction_cache.end():  # type: ignore[attr-defined]
                return cython.operator.dereference(it).second  # type: ignore[attr-defined]
        else:
            if resource_index in self._damage_reduction_cache:
                return self._damage_reduction_cache[resource_index]

        resource: ResourceInfo = getattr(self._resource_database, "_resource_mapping")[resource_index]
        reduction: cython.float = self._resource_database.get_damage_reduction(resource, self)
        self._damage_reduction_cache[resource_index] = reduction
        return reduction

    def __copy__(self) -> ResourceCollection:
        return self.duplicate()
