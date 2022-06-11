from randovania.game_description.requirements.array_base import RequirementArrayBase, mergeable_array, expand_items
from randovania.game_description.requirements.base import MAX_DAMAGE, Requirement
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection


class RequirementAnd(RequirementArrayBase):
    def damage(self, current_resources: ResourceCollection, database: ResourceDatabase) -> int:
        result = 0
        for item in self.items:
            if item.satisfied(current_resources, MAX_DAMAGE, database):
                result += item.damage(current_resources, database)
            else:
                return MAX_DAMAGE
        return result

    def satisfied(self, current_resources: ResourceCollection, current_energy: int, database: ResourceDatabase) -> bool:
        for item in self.items:
            if not item.satisfied(current_resources, current_energy, database):
                return False

        return True

    def simplify(self, keep_comments: bool = False) -> Requirement:
        new_items = expand_items(self.items, RequirementAnd, Requirement.trivial(), keep_comments)
        if Requirement.impossible() in new_items and mergeable_array(self, keep_comments):
            return Requirement.impossible()

        if len(new_items) == 1 and mergeable_array(self, keep_comments):
            return new_items[0]

        return RequirementAnd(new_items, comment=self.comment)

    def as_set(self, database: ResourceDatabase) -> RequirementSet:
        result = RequirementSet.trivial()
        for item in self.items:
            result = result.union(item.as_set(database))
        return result

    @classmethod
    def combinator(cls):
        return " and "

    @classmethod
    def _str_no_items(cls):
        return "Trivial"
