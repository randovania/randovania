from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.requirements.array_base import RequirementArrayBase, expand_items, mergeable_array
from randovania.game_description.requirements.base import MAX_DAMAGE, Requirement
from randovania.game_description.requirements.requirement_set import RequirementSet

if TYPE_CHECKING:
    from randovania.game_description.db.node import NodeContext


class RequirementAnd(RequirementArrayBase):
    def damage(self, context: NodeContext) -> int:
        result = 0
        for item in self.items:
            result += item.damage(context)
            if result >= MAX_DAMAGE:
                return MAX_DAMAGE
        return result

    def satisfied(self, context: NodeContext, current_energy: int) -> bool:
        for item in self.items:
            if not item.satisfied(context, current_energy):
                return False
            else:
                current_energy -= item.damage(context)

        return True

    def simplify(self, keep_comments: bool = False) -> Requirement:
        new_items = expand_items(self.items, RequirementAnd, Requirement.trivial(), keep_comments)
        if Requirement.impossible() in new_items and mergeable_array(self, keep_comments):
            return Requirement.impossible()

        if len(new_items) == 1 and mergeable_array(self, keep_comments):
            return new_items[0]

        return RequirementAnd(new_items, comment=self.comment)

    def isolate_damage_requirements(self, context: NodeContext) -> Requirement:
        isolated_items = []
        for item in self.items:
            potential_item = item.isolate_damage_requirements(context)
            if potential_item == Requirement.impossible():
                return Requirement.impossible()
            if potential_item != Requirement.trivial():
                isolated_items.append(potential_item)
        return isolated_items[0] if len(isolated_items) == 1 else RequirementAnd(isolated_items)

    def as_set(self, context: NodeContext) -> RequirementSet:
        result = RequirementSet.trivial()
        for item in self.items:
            result = result.union(item.as_set(context))
        return result

    @classmethod
    def combinator(cls) -> str:
        return " and "

    @classmethod
    def _str_no_items(cls) -> str:
        return "Trivial"
