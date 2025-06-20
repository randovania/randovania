from __future__ import annotations

from typing import TYPE_CHECKING, Self, override

from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from collections.abc import Generator

    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_collection import ResourceCollection


class DreadDamageState(EnergyTankDamageState):
    _use_immediate_energy_parts: bool
    _energy_part_item: ItemResourceInfo

    def __init__(
        self,
        starting_energy: int,
        energy_per_tank: int,
        energy_tank: ItemResourceInfo,
        use_immediate_energy_parts: bool,
        energy_part_item: ItemResourceInfo,
    ):
        super().__init__(starting_energy, energy_per_tank, energy_tank)
        self._use_immediate_energy_parts = use_immediate_energy_parts
        self._energy_part_item = energy_part_item

    def __copy__(self) -> Self:
        return self._duplicate()

    @override
    def resources_for_energy(self) -> Generator[ItemResourceInfo]:
        yield self._energy_tank
        yield self._energy_part_item

    def _maximum_energy(self, resources: ResourceCollection) -> int:
        num_tanks = resources[self._energy_tank]
        num_parts = resources[self._energy_part_item]
        num_whole_tanks = num_tanks + num_parts // 4
        num_partial_parts = num_parts % 4
        energy_from_partial = (self._energy_per_tank * num_partial_parts) // 4

        return self._starting_energy + (self._energy_per_tank * num_whole_tanks) + energy_from_partial

    def _duplicate(self) -> Self:
        result = self.__class__(
            self._starting_energy,
            self._energy_per_tank,
            self._energy_tank,
            self._use_immediate_energy_parts,
            self._energy_part_item,
        )
        result._energy = self._energy
        return result

    def _energy_part_difference(
        self,
        new_resources: ResourceCollection,
        old_resources: ResourceCollection,
    ) -> int:
        return new_resources[self._energy_part_item] - old_resources[self._energy_part_item]

    @override
    def apply_collected_resource_difference(
        self, new_resources: ResourceCollection, old_resources: ResourceCollection
    ) -> Self:
        if self._energy_tank_difference(new_resources, old_resources) > 0:
            # Apply full heal when collecting an Energy Tank
            return self._at_maximum_energy(new_resources)
        elif self._energy_part_difference(new_resources, old_resources) > 0:
            if self._use_immediate_energy_parts:
                # When using immediate energy parts, increase current health by the same amount of energy as the maximum
                # increases by.
                old_max = self._maximum_energy(old_resources)
                new_max = self._maximum_energy(new_resources)

                result = self._duplicate()
                result._energy = self._energy + (new_max - old_max)
                return result
            if (new_resources[self._energy_part_item] // 4) > (old_resources[self._energy_part_item] // 4):
                # When not using immediate energy parts, apply full heal when collecting an energy part that finishes a
                # full set of 4.
                return self._at_maximum_energy(new_resources)
            return self
        else:
            return self

    @override
    def resource_requirements_for_satisfying_damage(self, damage: int) -> list[list[ResourceRequirement]]:
        # A requirement for many "Energy Tanks" is added,
        # which is then decreased by how many tanks is in the state by pickups_to_solve_list
        # FIXME: get the required items for reductions (aka suits)
        tank_count = 1 + (damage - self._starting_energy) // self._energy_per_tank
        part_count = 1 + (damage - self._starting_energy) // (self._energy_per_tank // 4)
        if not self._use_immediate_energy_parts:
            part_count += (4 - (part_count % 4)) % 4
        ret: list[list[ResourceRequirement]] = [
            [ResourceRequirement.create(self._energy_tank, tank_count, False)],
            [ResourceRequirement.create(self._energy_part_item, part_count, False)],
        ]
        tanks = 1
        parts = part_count - 4
        while parts > 0:
            ret.append(
                [
                    ResourceRequirement.create(self._energy_tank, tanks, False),
                    ResourceRequirement.create(self._energy_part_item, parts, False),
                ]
            )
            parts -= 4
            tanks += 1

        return ret
