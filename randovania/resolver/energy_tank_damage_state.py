from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Self, override

from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.resolver.damage_state import DamageState

if TYPE_CHECKING:
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase


class EnergyTankDamageState(DamageState):
    _energy: int
    _starting_energy: int
    _energy_per_tank: int
    _energy_tank: ItemResourceInfo
    _resource_database: ResourceDatabase
    _region_list: RegionList

    def __init__(
        self, starting_energy: int, energy_per_tank: int, resource_database: ResourceDatabase, region_list: RegionList
    ):
        self._energy = starting_energy
        self._starting_energy = starting_energy
        self._energy_per_tank = energy_per_tank
        self._energy_tank = resource_database.energy_tank  # TODO: this should be an argument
        self._resource_database = resource_database
        self._region_list = region_list

    @override
    def resource_database(self) -> ResourceDatabase:
        return self._resource_database

    @override
    def region_list(self) -> RegionList:
        return self._region_list

    def _maximum_energy(self, resources: ResourceCollection) -> int:
        num_tanks = resources[self._energy_tank]
        return self._starting_energy + (self._energy_per_tank * num_tanks)

    def _at_maximum_energy(self, resources: ResourceCollection) -> Self:
        result = copy.copy(self)
        result._energy = result._maximum_energy(resources)
        return result

    @override
    def health_for_damage_requirements(self) -> int:
        return self._energy

    @override
    def is_better_than(self, other: DamageState | None) -> bool:
        if other is None:
            return True
        assert isinstance(other, EnergyTankDamageState)
        return self._energy > other._energy

    @override
    def apply_damage(self, damage: int) -> Self:
        result = copy.copy(self)
        result._energy -= damage
        return result

    @override
    def apply_node_heal(self, node: Node, resources: ResourceCollection) -> Self:
        return self._at_maximum_energy(resources)

    @override
    def debug_string(self, resources: ResourceCollection) -> str:
        return f"{self._energy}/{self._maximum_energy(resources)} Energy"

    @override
    def limited_by_maximum(self, resources: ResourceCollection) -> Self:
        result = copy.copy(self)
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
        result = copy.copy(self)
        result._energy += tank_difference * self._energy_per_tank
        return result.limited_by_maximum(new_resources)

    @override
    def resource_requirements_for_satisfying_damage(self, damage: int) -> list[ResourceRequirement]:
        # A requirement for many "Energy Tanks" is added,
        # which is then decreased by how many tanks is in the state by pickups_to_solve_list
        # FIXME: get the required items for reductions (aka suits)
        tank_count = (damage - self._starting_energy) // self._energy_per_tank
        return [ResourceRequirement.create(self._energy_tank, tank_count + 1, False)]
