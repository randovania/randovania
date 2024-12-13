from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.requirements.resource_requirement import ResourceRequirement
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase


class DamageState(ABC):
    """
    Interface responsible for keeping track of all data related to Damage requirements.
    """

    def resource_database(self) -> ResourceDatabase:
        """The ResourceDatabase."""

    def region_list(self) -> RegionList:
        """The preprocessed RegionList."""

    def health_for_damage_requirements(self) -> int:
        """How much health is present for purpose of checking damage requirements."""

    def is_better_than(self, other: DamageState | None) -> bool:
        """Is this state strictly better than other, regarding damage requirements.
        Always True when other is None."""

    def apply_damage(self, damage: int) -> Self:
        """
        Applies damage accumulated when visiting a new node.
        :param damage: The damage to be applied, as returned from `Requirements.damage`.
        :return: A new copy with the damage applied.
        """

    def apply_node_heal(self, node: Node, resources: ResourceCollection) -> Self:
        """
        Applies the Node Heal effect, whatever that means for this game.
        Called when visiting a Node with the heal flag set.
        :param node: The visited Node.
        :param resources: The current resources.
        :return: A new copy with the effect applied.
        """

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
