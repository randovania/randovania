from random import Random

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import (
    HintLocationPrecision, HintRelativeAreaName, HintItemPrecision,
    PrecisionPair, HintDarkTemple, Hint, HintType
)
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.node import LogbookNode
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.generator.filler.player_state import PlayerState
from randovania.generator.filler.runner import PlayerPool
from randovania.generator.hint_distributor import HintDistributor, PreFillParams, HintTargetPrecision
from randovania.lib import enum_lib


class EchoesHintDistributor(HintDistributor):
    # Pre Filler
    @property
    def num_joke_hints(self) -> int:
        return 2

    async def get_guranteed_hints(self, patches: GamePatches, prefill: PreFillParams) -> list[HintTargetPrecision]:
        def g(index, loc):
            return (
                PickupIndex(index),
                PrecisionPair(loc, HintItemPrecision.DETAILED, include_owner=False),
            )

        return [
            g(24, HintLocationPrecision.LIGHT_SUIT_LOCATION),  # Light Suit
            g(43, HintLocationPrecision.GUARDIAN),  # Dark Suit (Amorbis)
            g(79, HintLocationPrecision.GUARDIAN),  # Dark Visor (Chykka)
            g(115, HintLocationPrecision.GUARDIAN),  # Annihilator Beam (Quadraxis)
        ]

    async def assign_other_hints(self, patches: GamePatches, nodes: list[LogbookNode],
                                 prefill: PreFillParams) -> GamePatches:
        all_logbook_nodes = [node for node in nodes if node.resource() not in patches.hints]
        prefill.rng.shuffle(all_logbook_nodes)

        # Dark Temple hints
        temple_hints = list(enum_lib.iterate_enum(HintDarkTemple))
        while all_logbook_nodes and temple_hints:
            logbook_asset = (node := all_logbook_nodes.pop()).resource()
            patches = patches.assign_hint(logbook_asset, Hint(HintType.RED_TEMPLE_KEY_SET, None,
                                                              dark_temple=temple_hints.pop(0)))
            nodes.remove(node)

        return patches

    # Post Filler

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
