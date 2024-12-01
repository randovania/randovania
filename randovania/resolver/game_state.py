from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Self

from typing_extensions import override

from randovania.game_description.requirements.resource_requirement import ResourceRequirement

if TYPE_CHECKING:
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase


class GameState:
    """
    Represents whatever game specific resource that is consumed during gameplay.
    """

    def resource_database(self) -> ResourceDatabase:
        """The ResourceDatabase."""

    def region_list(self) -> RegionList:
        """The preprocessed RegionList."""

    def health_for_damage_requirements(self) -> int:
        """How much health is present for purpose of checking damage requirements."""

    def is_better_than(self, other: GameState | None) -> bool:
        """Is this state strictly better than other, regarding damage requirements.
        Always True when other is None."""

    def apply_damage(self, damage: int) -> Self:
        """Applies the given damage, returned from a Requirements.damage. Returns a new copy."""

    def apply_node_heal(self, resources: ResourceCollection) -> Self:
        """Applies whatever is considered the Node heal."""

    def debug_string(self, resources: ResourceCollection) -> str:
        """A string that represents this state for purpose of resolver and generator logs."""

    def limited_by_maximum(self, resources: ResourceCollection) -> Self:
        """Applies any resource limit, such as maximum life based on life upgrades."""

    def apply_collected_resource_difference(
        self, new_resources: ResourceCollection, old_resources: ResourceCollection
    ) -> Self:
        """Creates a new state after collecting new resources"""

    def apply_new_starting_resource_difference(
        self, new_resources: ResourceCollection, old_resources: ResourceCollection
    ) -> Self:
        """Creates a new state after new resources were added as if they were starting.
        Common difference: collecting a health upgrade fully heals you. But it won't do it here."""

    def resource_requirements_for_satisfying_damage(self, damage: int) -> list[ResourceRequirement]:
        """
        Determines what are the requirements for satisfying a damage requirement with the given value.
        :param damage:
        :return: a list of resource requirements
        """


class NoDamageGameState(GameState):
    def __init__(self, resource_database: ResourceDatabase, region_list: RegionList):
        self._resource_database = resource_database
        self._region_list = region_list

    @override
    def resource_database(self) -> ResourceDatabase:
        return self._resource_database

    @override
    def region_list(self) -> RegionList:
        return self._region_list

    @override
    def health_for_damage_requirements(self) -> int:
        return 0

    @override
    def is_better_than(self, other: GameState | None) -> bool:
        return other is None

    @override
    def apply_damage(self, damage: int) -> Self:
        return self

    @override
    def apply_node_heal(self, resources: ResourceCollection) -> Self:
        return self

    @override
    def debug_string(self, resources: ResourceCollection) -> str:
        return ""

    @override
    def limited_by_maximum(self, resources: ResourceCollection) -> Self:
        return self

    @override
    def apply_collected_resource_difference(
        self, new_resources: ResourceCollection, old_resources: ResourceCollection
    ) -> Self:
        return self

    @override
    def apply_new_starting_resource_difference(
        self, new_resources: ResourceCollection, old_resources: ResourceCollection
    ) -> Self:
        return self

    @override
    def resource_requirements_for_satisfying_damage(self, damage: int) -> list[ResourceRequirement]:
        return []


class EnergyTankGameState(GameState):
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
        self._energy_tank = resource_database.energy_tank
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

    @override
    def health_for_damage_requirements(self) -> int:
        return self._energy

    @override
    def is_better_than(self, other: GameState | None) -> bool:
        if other is None:
            return True
        assert isinstance(other, EnergyTankGameState)
        return self._energy > other._energy

    @override
    def apply_damage(self, damage: int) -> Self:
        result = copy.copy(self)
        result._energy -= damage
        return result

    @override
    def apply_node_heal(self, resources: ResourceCollection) -> Self:
        return self.limited_by_maximum(resources)

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
            return self.limited_by_maximum(new_resources)
        else:
            return self

    @override
    def apply_new_starting_resource_difference(
        self, new_resources: ResourceCollection, old_resources: ResourceCollection
    ) -> Self:
        tank_difference = self._energy_tank_difference(new_resources, old_resources)
        result = copy.copy(self)
        result._energy += tank_difference * self._energy_per_tank
        return result

    @override
    def resource_requirements_for_satisfying_damage(self, damage: int) -> list[ResourceRequirement]:
        # A requirement for many "Energy Tanks" is added,
        # which is then decreased by how many tanks is in the state by pickups_to_solve_list
        # FIXME: get the required items for reductions (aka suits)
        tank_count = (damage - self._starting_energy) // self._energy_per_tank
        return [ResourceRequirement.create(self._energy_tank, tank_count + 1, False)]
