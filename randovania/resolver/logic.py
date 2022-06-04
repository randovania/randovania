from typing import Dict

from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements import Requirement, RequirementSet
from randovania.game_description.world.node import Node
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.resolver.state import State


class Logic:
    """Extra information that persists even after a backtrack, to prevent irrelevant backtracking."""

    game: GameDescription
    configuration: BaseConfiguration
    additional_requirements: Dict[Node, RequirementSet]

    def __init__(self, game: GameDescription, configuration: BaseConfiguration):
        self.game = game
        self.configuration = configuration
        self.additional_requirements = {}

    def get_additional_requirements(self, node: Node) -> RequirementSet:
        return self.additional_requirements.get(node, RequirementSet.trivial())
    
    @property
    def victory_condition(self) -> Requirement:
        return self.game.victory_condition
