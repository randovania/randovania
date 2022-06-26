from randovania.game_description.requirements.array_base import RequirementArrayBase, mergeable_array, expand_items
from randovania.game_description.requirements.base import MAX_DAMAGE, Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection


class RequirementOr(RequirementArrayBase):
    def damage(self, current_resources: ResourceCollection, database: ResourceDatabase) -> int:
        try:
            return min(
                item.damage(current_resources, database)
                for item in self.items
                if item.satisfied(current_resources, MAX_DAMAGE, database)
            )
        except ValueError:
            return MAX_DAMAGE

    def satisfied(self, current_resources: ResourceCollection, current_energy: int, database: ResourceDatabase) -> bool:
        for item in self.items:
            if item.satisfied(current_resources, current_energy, database):
                return True
        return False

    def simplify(self, keep_comments: bool = False) -> Requirement:
        new_items = expand_items(self.items, RequirementOr, Requirement.impossible(), keep_comments)
        if Requirement.trivial() in new_items and mergeable_array(self, keep_comments):
            return Requirement.trivial()

        num_and_requirements = 0
        common_requirements = None
        for item in new_items:
            if isinstance(item, RequirementAnd) and mergeable_array(item, keep_comments):
                num_and_requirements += 1
                if common_requirements is None:
                    common_requirements = item.items
                else:
                    common_requirements = [
                        common
                        for common in common_requirements
                        if common in item.items
                    ]

        # Only extract the common requirements if there's more than 1 requirement
        if num_and_requirements >= 2 and common_requirements:
            simplified_items = []
            common_new_or = []

            for item in new_items:
                if isinstance(item, RequirementAnd) and mergeable_array(item, keep_comments):
                    assert set(common_requirements) <= set(item.items)
                    simplified_condition = [it for it in item.items if it not in common_requirements]
                    if simplified_condition:
                        common_new_or.append(RequirementAnd(simplified_condition) if len(simplified_condition) > 1
                                             else simplified_condition[0])
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

    def as_set(self, database: ResourceDatabase) -> "RequirementSet":
        alternatives = set()
        for item in self.items:
            alternatives |= item.as_set(database).alternatives
        return RequirementSet(alternatives)

    @classmethod
    def combinator(cls):
        return " or "

    @classmethod
    def _str_no_items(cls):
        return "Impossible"
