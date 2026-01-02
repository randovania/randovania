from __future__ import annotations

from randovania.game_description.requirements.array_base import RequirementArrayBase, expand_items, mergeable_array
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd


class RequirementOr(RequirementArrayBase):
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

    @classmethod
    def combinator(cls) -> str:
        return " or "

    @classmethod
    def _str_no_items(cls) -> str:
        return "Impossible"
