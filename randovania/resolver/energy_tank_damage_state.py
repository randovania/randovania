from __future__ import annotations

from typing import TYPE_CHECKING, Self, override

from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.resolver.damage_state import DamageState

if TYPE_CHECKING:
    from collections.abc import Generator

    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.graph.world_graph import WorldGraphNode


class EnergyTankDamageState(DamageState):
    __slots__ = ("_energy", "_starting_energy", "_energy_per_tank", "_energy_tank", "_damage_reduction_items")
    _energy: int
    _starting_energy: int
    _energy_per_tank: int
    _energy_tank: ItemResourceInfo
    _damage_reduction_items: list[ItemResourceInfo]

    def __init__(
        self,
        starting_energy: int,
        energy_per_tank: int,
        energy_tank: ItemResourceInfo,
        damage_reduction_items: list[ItemResourceInfo],
    ):
        self._energy = starting_energy
        self._starting_energy = starting_energy
        self._energy_per_tank = energy_per_tank
        self._energy_tank = energy_tank
        self._damage_reduction_items = damage_reduction_items

    def __copy__(self) -> Self:
        return self._duplicate()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}[{self._energy}]"

    @override
    def health_for_damage_requirements(self) -> int:
        return self._energy

    @override
    def resources_for_health(self) -> Generator[ItemResourceInfo]:
        yield self._energy_tank

    @override
    def resources_for_general_reduction(self) -> Generator[ItemResourceInfo]:
        yield from self._damage_reduction_items

    def _maximum_energy(self, resources: ResourceCollection) -> int:
        num_tanks = resources[self._energy_tank]
        return self._starting_energy + (self._energy_per_tank * num_tanks)

    def _duplicate(self) -> Self:
        result = self.__class__(
            self._starting_energy,
            self._energy_per_tank,
            self._energy_tank,
            self._damage_reduction_items,
        )
        result._energy = self._energy
        return result

    def _at_maximum_energy(self, resources: ResourceCollection) -> Self:
        maximum_energy = self._maximum_energy(resources)
        if maximum_energy == self._energy:
            return self
        else:
            result = self._duplicate()
            result._energy = maximum_energy
            return result

    @override
    def is_better_than(self, other: int) -> bool:
        return self._energy > other

    @override
    def with_health(self, health: int) -> Self:
        result = self._duplicate()
        result._energy = health
        return result

    @override
    def apply_damage(self, damage: float) -> Self:
        if damage <= 0:
            return self
        result = self._duplicate()
        result._energy -= int(damage)
        return result

    @override
    def apply_node_heal(self, node: WorldGraphNode, resources: ResourceCollection) -> Self:
        return self._at_maximum_energy(resources)

    @override
    def debug_string(self, resources: ResourceCollection) -> str:
        return f"{self._energy}/{self._maximum_energy(resources)} Energy"

    @override
    def limited_by_maximum(self, resources: ResourceCollection) -> Self:
        result = self._duplicate()
        result._energy = min(result._energy, result._maximum_energy(resources))
        return result

    def _energy_tank_difference(
        self,
        new_resources: ResourceCollection,
        old_resources: ResourceCollection,
    ) -> int:
        return new_resources[self._energy_tank] - old_resources[self._energy_tank]

    @override
    def apply_collected_resource_difference(
        self, new_resources: ResourceCollection, old_resources: ResourceCollection
    ) -> Self:
        if self._energy_tank_difference(new_resources, old_resources) > 0:
            return self._at_maximum_energy(new_resources)
        else:
            return self

    @override
    def apply_new_starting_resource_difference(
        self, new_resources: ResourceCollection, old_resources: ResourceCollection
    ) -> Self:
        tank_difference = self._energy_tank_difference(new_resources, old_resources)
        result = self._duplicate()
        result._energy += tank_difference * self._energy_per_tank
        return result.limited_by_maximum(new_resources)

    @override
    def resource_requirements_for_satisfying_damage(
        self, damage: int, resources: ResourceCollection
    ) -> list[list[ResourceRequirement]] | None:
        # A requirement for many "Energy Tanks" is added,
        # which is then decreased by how many tanks is in the state by pickups_to_solve_list
        # FIXME: get the required items for reductions (aka suits)
        tank_count = (damage - self._starting_energy) // self._energy_per_tank
        return [[ResourceRequirement.create(self._energy_tank, tank_count + 1, False)]]
