from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.requirements.array_base import RequirementArrayBase, expand_items, mergeable_array
from randovania.game_description.requirements.base import MAX_DAMAGE, Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_set import RequirementSet

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.requirements.requirement_list import RequirementList


def _halt_damage_on_zero(items: Iterable[Requirement], context: NodeContext) -> Iterator[int]:
    for item in items:
        dmg = item.damage(context)
        yield dmg
        if dmg == 0:
            break


class RequirementOr(RequirementArrayBase):
    def damage(self, context: NodeContext) -> int:
        try:
            return min(_halt_damage_on_zero(self.items, context))
        except ValueError:
            return MAX_DAMAGE

    def satisfied(self, context: NodeContext, current_energy: int) -> bool:
        for item in self.items:
            if item.satisfied(context, current_energy):
                return True
        return False

    def simplify(self, keep_comments: bool = False) -> Requirement:
        new_items = expand_items(self.items, RequirementOr, Requirement.impossible(), keep_comments)
        if Requirement.trivial() in new_items and mergeable_array(self, keep_comments):
            return Requirement.trivial()

        num_and_requirements = 0
        common_requirements: list[Requirement] | None = None
        for item in new_items:
            if isinstance(item, RequirementAnd) and mergeable_array(item, keep_comments):
                num_and_requirements += 1
                if common_requirements is None:
                    common_requirements = list(item.items)
                else:
                    common_requirements = [common for common in common_requirements if common in item.items]

        # Only extract the common requirements if there's more than 1 requirement
        if num_and_requirements >= 2 and common_requirements:
            simplified_items = []
            common_new_or = []

            for item in new_items:
                if isinstance(item, RequirementAnd) and mergeable_array(item, keep_comments):
                    assert set(common_requirements) <= set(item.items)
                    simplified_condition = [it for it in item.items if it not in common_requirements]
                    if simplified_condition:
                        common_new_or.append(
                            RequirementAnd(simplified_condition)
                            if len(simplified_condition) > 1
                            else simplified_condition[0]
                        )
                else:
                    simplified_items.append(item)

            common_requirements.append(RequirementOr(common_new_or))
            simplified_items.append(RequirementAnd(common_requirements))
            final_items = simplified_items

        else:
            final_items = new_items

        if len(final_items) == 1 and mergeable_array(self, keep_comments):
            return final_items[0]

        return RequirementOr(final_items, comment=self.comment)

    def isolate_damage_requirements(self, context: NodeContext) -> Requirement:
        isolated_items = []
        for item in self.items:
            potential_item = item.isolate_damage_requirements(context)
            if potential_item == Requirement.trivial():
                return Requirement.trivial()
            if potential_item != Requirement.impossible():
                isolated_items.append(potential_item)
        return isolated_items[0] if len(isolated_items) == 1 else RequirementOr(isolated_items)

    def as_set(self, context: NodeContext) -> RequirementSet:
        alternatives: set[RequirementList] = set()
        for item in self.items:
            alternatives |= item.as_set(context).alternatives
        return RequirementSet(alternatives)

    @classmethod
    def combinator(cls) -> str:
        return " or "

    @classmethod
    def _str_no_items(cls) -> str:
        return "Impossible"
