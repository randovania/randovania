from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from collections.abc import Generator

    from randovania.game_description.requirements.resource_requirement import ResourceRequirement
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.graph.world_graph import WorldGraphNode


class DamageState(ABC):
    """
    Interface responsible for keeping track of all data related to Damage requirements.
    """

    @abstractmethod
    def health_for_damage_requirements(self) -> int:
        """How much health is present for purpose of checking damage requirements."""

    @abstractmethod
    def resources_for_health(self) -> Generator[ItemResourceInfo]:
        """Which items give increases maximum health."""

    @abstractmethod
    def resources_for_general_reduction(self) -> Generator[ItemResourceInfo]:
        """Which items give help with the base damage reduction."""

    @abstractmethod
    def is_better_than(self, other: DamageState | None) -> bool:
        """Is this state strictly better than other, regarding damage requirements.
        Always True when other is None."""

    @abstractmethod
    def apply_damage(self, damage: int) -> Self:
        """
        Applies damage accumulated when visiting a new node.
        :param damage: The damage to be applied, as returned from `Requirements.damage`.
        :return: A new copy with the damage applied.
        """

    @abstractmethod
    def apply_node_heal(self, node: WorldGraphNode, resources: ResourceCollection) -> Self:
        """
        Applies the Node Heal effect, whatever that means for this game.
        Called when visiting a Node with the heal flag set.
        :param node: The visited Node.
        :param resources: The current resources.
        :return: A new copy with the effect applied.
        """

    @abstractmethod
    def debug_string(self, resources: ResourceCollection) -> str:
        """A string that represents this state for purpose of resolver and generator logs."""

    @abstractmethod
    def limited_by_maximum(self, resources: ResourceCollection) -> Self:
        """Applies any resource limit, such as maximum life based on life upgrades."""

    @abstractmethod
    def apply_collected_resource_difference(
        self, new_resources: ResourceCollection, old_resources: ResourceCollection
    ) -> Self:
        """Creates a new state after collecting new resources"""

    @abstractmethod
    def apply_new_starting_resource_difference(
        self, new_resources: ResourceCollection, old_resources: ResourceCollection
    ) -> Self:
        """Creates a new state after new resources were added as if they were starting.
        Common difference: collecting a health upgrade fully heals you. But it won't do it here."""

    @abstractmethod
    def resource_requirements_for_satisfying_damage(
        self, damage: int, resources: ResourceCollection
    ) -> list[list[ResourceRequirement]] | None:
        """
        Determines what are the requirements for satisfying a damage requirement with the given value.
        :param damage:
        :param resources:
        :return: a list containing lists of resource requirements. Each sublist contains a combination of requirements.
        If two resources can be used, the options can be to satisfy the damage with some number of only the first
        resource, some number of only the second resource, or by any combination of the two resources that together
        satisfy the damage requirement. None if the requirements are already satisfied.
        """
