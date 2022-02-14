from random import Random

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import (
    HintLocationPrecision, HintRelativeAreaName, HintItemPrecision,
    PrecisionPair
)
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.generator.filler.player_state import PlayerState
from randovania.generator.filler.runner import PlayerPool
from randovania.generator.hint_distributor import HintDistributor


class EchoesHintDistributor(HintDistributor):
    def precision_pair_weighted_list(self) -> list[PrecisionPair]:
        tiers = {
            (HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED, False): 3,
            (HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED, True): 2,
            (HintLocationPrecision.DETAILED, HintItemPrecision.PRECISE_CATEGORY, True): 2,
            (HintLocationPrecision.DETAILED, HintItemPrecision.GENERAL_CATEGORY, True): 1,

            (HintLocationPrecision.WORLD_ONLY, HintItemPrecision.DETAILED, False): 2,
            (HintLocationPrecision.WORLD_ONLY, HintItemPrecision.PRECISE_CATEGORY, True): 1,
        }

        hints = []
        for params, quantity in tiers.items():
            hints.extend([PrecisionPair(*params)] * quantity)

        return hints

    def _get_relative_hint_providers(self):
        return [
            self._relative(HintLocationPrecision.RELATIVE_TO_AREA, True, HintRelativeAreaName.NAME, 4),
            self._relative(HintLocationPrecision.RELATIVE_TO_AREA, False, HintRelativeAreaName.NAME, 3),
            self._relative(HintLocationPrecision.RELATIVE_TO_INDEX, True, HintItemPrecision.DETAILED, 4),
        ]

    async def assign_precision_to_hints(self, patches: GamePatches, rng: Random,
                                        player_pool: PlayerPool, player_state: PlayerState) -> GamePatches:
        assert isinstance(player_pool.configuration, EchoesConfiguration)
        if player_pool.configuration.hints.item_hints:
            return self.add_hints_precision(player_state, patches, rng)
        else:
            return self.replace_hints_without_precision_with_jokes(patches)
