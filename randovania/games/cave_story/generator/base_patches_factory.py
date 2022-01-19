from random import Random

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import HintItemPrecision, HintLocationPrecision
from randovania.game_description.world.node import PickupNode
from randovania.game_description.world.world_list import WorldList
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration, CSObjective
from randovania.generator.base_patches_factory import BasePatchesFactory, HintTargetPrecision


class CSBasePatchesFactory(BasePatchesFactory):
    @property
    def num_joke_hints(self) -> int:
        return 0

    def get_specific_location_precisions(self) -> dict[str, HintLocationPrecision]:
        return {
            "Hint - MALCO": (HintLocationPrecision.MALCO, HintItemPrecision.DETAILED),
            "Hint - Mrs. Little": (HintLocationPrecision.LITTLE, HintItemPrecision.DETAILED),
            "Hint - Jenka 1": (HintLocationPrecision.JENKA, HintItemPrecision.DETAILED),
            "Hint - Jenka 2": (HintLocationPrecision.JENKA, HintItemPrecision.DETAILED),
            "Hint - Numahachi 1": (HintLocationPrecision.NUMAHACHI, HintItemPrecision.DETAILED),
            "Hint - Numahachi 2": (HintLocationPrecision.NUMAHACHI, HintItemPrecision.DETAILED)
        }

    def indices_with_hint(self, configuration: CSConfiguration, game: GameDescription, rng: Random,
                          patches: GamePatches, world_list: WorldList) -> list[HintTargetPrecision]:
        return []

        # TODO: assign base hints *after* generation?
        items_with_hint = []
        if configuration.objective == CSObjective.BAD_ENDING:
            items_with_hint.append("Rusty Key")
        else:
            items_with_hint.append("ID Card")
        if patches.starting_location.area_name != "Start Point":
            items_with_hint.append("Arthur's Key")

        already_hinted_indices = [hint.target for hint in patches.hints.values() if hint.target is not None]
        indices_with_hint = [
            (node.pickup_index, HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED)
            for node in world_list.all_nodes
            if isinstance(node, PickupNode)
               and node.pickup_index not in already_hinted_indices
               and patches.pickup_assignment[node.pickup_index].pickup.name in items_with_hint
        ]
        return indices_with_hint
