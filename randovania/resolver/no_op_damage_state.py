from __future__ import annotations

from typing import TYPE_CHECKING, Self, override

from randovania.resolver.damage_state import DamageState

if TYPE_CHECKING:
    from randovania.game_description.db.node import Node
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement
    from randovania.game_description.resources.resource_collection import ResourceCollection


class NoOpDamageState(DamageState):
    """A DamageState implementation that does absolutely no damage tracking."""

    @override
    def health_for_damage_requirements(self) -> int:
        return 0

    @override
    def is_better_than(self, other: DamageState | None) -> bool:
        return other is None

    @override
    def apply_damage(self, damage: int) -> Self:
        return self

    @override
    def apply_node_heal(self, node: Node, resources: ResourceCollection) -> Self:
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
