from __future__ import annotations

from randovania.game_description.requirements.array_base import RequirementArrayBase, expand_items, mergeable_array
from randovania.game_description.requirements.base import Requirement


class RequirementAnd(RequirementArrayBase):
    def simplify(self, keep_comments: bool = False) -> Requirement:
        new_items = expand_items(self.items, RequirementAnd, Requirement.trivial(), keep_comments)
        if Requirement.impossible() in new_items and mergeable_array(self, keep_comments):
            return Requirement.impossible()

        if len(new_items) == 1 and mergeable_array(self, keep_comments):
            return new_items[0]

        return RequirementAnd(new_items, comment=self.comment)

    @classmethod
    def combinator(cls) -> str:
        return " and "

    @classmethod
    def _str_no_items(cls) -> str:
        return "Trivial"
