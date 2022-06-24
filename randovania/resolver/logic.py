from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.world.node import Node
from randovania.layout.base.base_configuration import BaseConfiguration


class Logic:
    """Extra information that persists even after a backtrack, to prevent irrelevant backtracking."""

    game: GameDescription
    configuration: BaseConfiguration
    additional_requirements: list[RequirementSet]

    def __init__(self, game: GameDescription, configuration: BaseConfiguration):
        self.game = game
        self.configuration = configuration
        self.additional_requirements = [RequirementSet.trivial()] * len(game.world_list.all_nodes)

    def get_additional_requirements(self, node: Node) -> RequirementSet:
        return self.additional_requirements[node.node_index]

    def set_additional_requirements(self, node: Node, req: RequirementSet):
        self.additional_requirements[node.node_index] = req

    @property
    def victory_condition(self) -> Requirement:
        return self.game.victory_condition
