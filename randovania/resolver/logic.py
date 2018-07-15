import collections
from typing import Dict, Set

from randovania.resolver.game_description import GameDescription
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.layout_configuration import LayoutConfiguration
from randovania.resolver.node import Node
from randovania.resolver.requirements import RequirementSet
from randovania.resolver.resources import CurrentResources, ResourceDatabase


class Logic:
    """Extra information that persists even after a backtrack, to prevent irrelevant backtracking."""

    game: GameDescription
    configuration: LayoutConfiguration
    patches: GamePatches
    additional_requirements: Dict[Node, RequirementSet]
    node_sightings: Dict[Node, int]

    def __init__(self, game: GameDescription, configuration: LayoutConfiguration, patches: GamePatches):
        self.game = game
        self.configuration = configuration
        self.patches = patches
        self.additional_requirements = {}
        self.node_sightings = collections.defaultdict(int)

    def get_additional_requirements(self, node: Node) -> RequirementSet:
        return self.additional_requirements.get(node, RequirementSet.trivial())


def build_static_resources(difficulty_level: int,
                           tricks_enabled: Set[int],
                           resource_database: ResourceDatabase) -> CurrentResources:
    static_resources = {}

    for trick in resource_database.trick:
        if trick.index in tricks_enabled:
            static_resources[trick] = 1
        else:
            static_resources[trick] = 0

    for difficulty in resource_database.difficulty:
        static_resources[difficulty] = difficulty_level

    return static_resources
