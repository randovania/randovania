from __future__ import annotations

import dataclasses
from abc import ABC
from collections.abc import Callable
from random import Random
from typing import TYPE_CHECKING

from randovania.game_description.db.hint_node import HintNode, HintNodeKind
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import (
    JokeHint,
    LocationHint,
    PrecisionPair,
    is_unassigned_location,
)
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.filler.filler_library import UnableToGenerate
from randovania.generator.filler.player_state import HintState, PlayerState
from randovania.resolver import debug

if TYPE_CHECKING:
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.generator.filler.filler_configuration import PlayerPool
    from randovania.generator.pre_fill_params import PreFillParams

HintProvider = Callable[[PlayerState, GamePatches, Random, PickupIndex], LocationHint | None]

HintTargetPrecision = tuple[PickupIndex, PrecisionPair]


class HintDistributor(ABC):
    @property
    def num_joke_hints(self) -> int:
        return 0

    def get_generic_hint_nodes(self, prefill: PreFillParams) -> list[NodeIdentifier]:
        return [
            node.identifier
            for node in prefill.game.region_list.iterate_nodes()
            if isinstance(node, HintNode) and node.kind == HintNodeKind.GENERIC
        ]

    async def get_specific_pickup_precision_pairs(self) -> dict[NodeIdentifier, PrecisionPair]:
        return {}

    async def assign_specific_location_hints(self, patches: GamePatches, prefill: PreFillParams) -> GamePatches:
        specific_location_precisions = await self.get_specific_pickup_precision_pairs()

        wl = prefill.game.region_list
        for node in wl.iterate_nodes():
            if isinstance(node, HintNode) and node.kind == HintNodeKind.SPECIFIC_PICKUP:
                identifier = node.identifier
                patches = patches.assign_hint(
                    identifier,
                    LocationHint(
                        specific_location_precisions[identifier],
                        PickupIndex(node.extra["hint_index"]),
                    ),
                )

        return patches

    async def get_guaranteed_hints(self, patches: GamePatches, prefill: PreFillParams) -> list[HintTargetPrecision]:
        return []

    async def assign_guaranteed_indices_hints(
        self, patches: GamePatches, identifiers: list[NodeIdentifier], prefill: PreFillParams
    ) -> GamePatches:
        # Specific Pickup/any HintNode
        indices_with_hint = await self.get_guaranteed_hints(patches, prefill)
        prefill.rng.shuffle(indices_with_hint)

        all_hint_identifiers = [identifier for identifier in identifiers if identifier not in patches.hints]
        prefill.rng.shuffle(all_hint_identifiers)

        for index, precision in indices_with_hint:
            if not all_hint_identifiers:
                break

            identifier = all_hint_identifiers.pop()
            patches = patches.assign_hint(identifier, LocationHint(precision, index))
            identifiers.remove(identifier)

        return patches

    async def assign_other_hints(
        self, patches: GamePatches, identifiers: list[NodeIdentifier], prefill: PreFillParams
    ) -> GamePatches:
        return patches

    async def assign_joke_hints(
        self, patches: GamePatches, identifiers: list[NodeIdentifier], prefill: PreFillParams
    ) -> GamePatches:
        all_hint_identifiers = [identifier for identifier in identifiers if identifier not in patches.hints]
        prefill.rng.shuffle(all_hint_identifiers)

        num_joke = self.num_joke_hints

        while num_joke > 0 and all_hint_identifiers:
            identifier = all_hint_identifiers.pop()
            patches = patches.assign_hint(identifier, JokeHint())
            num_joke -= 1
            identifiers.remove(identifier)

        return patches

    async def assign_pre_filler_hints(
        self, patches: GamePatches, prefill: PreFillParams, rng_required: bool = True
    ) -> GamePatches:
        patches = await self.assign_specific_location_hints(patches, prefill)
        hint_identifiers = self.get_generic_hint_nodes(prefill)
        if rng_required or prefill.rng is not None:
            prefill.rng.shuffle(hint_identifiers)
            patches = await self.assign_guaranteed_indices_hints(patches, hint_identifiers, prefill)
            patches = await self.assign_other_hints(patches, hint_identifiers, prefill)
            patches = await self.assign_joke_hints(patches, hint_identifiers, prefill)
        return patches

    async def assign_post_filler_hints(
        self,
        patches: GamePatches,
        rng: Random,
        player_pool: PlayerPool,
        player_state: PlayerState,
    ) -> GamePatches:
        # Since we haven't added expansions yet, these hints will always be for items added by the filler.
        full_hints_patches = self.fill_unassigned_hints(
            patches,
            player_state.game.region_list,
            rng,
            player_state.hint_state,
        )
        return await self.assign_precision_to_hints(full_hints_patches, rng, player_pool, player_state)

    async def assign_precision_to_hints(
        self, patches: GamePatches, rng: Random, player_pool: PlayerPool, player_state: PlayerState
    ) -> GamePatches:
        """
        Ensures no hints present in `patches` has no precision.
        :param patches:
        :param rng:
        :param player_pool:
        :param player_state:
        :return:
        """
        raise NotImplementedError

    def interesting_pickup_to_hint(self, pickup: PickupEntry) -> bool:
        """Highest priority pickups are those shown in the credits"""
        return pickup.show_in_credits_spoiler and self.less_interesting_pickup_to_hint(pickup)

    def less_interesting_pickup_to_hint(self, pickup: PickupEntry) -> bool:
        """Certain games may want certain pickups to only be hinted as a last resort"""
        return True

    def fill_unassigned_hints(
        self,
        patches: GamePatches,
        region_list: RegionList,
        rng: Random,
        hint_state: HintState,
    ) -> GamePatches:
        """Selects targets for all remaining unassigned generic hint nodes"""
        hinted_pickups = {hint.target for hint in patches.hints.values() if isinstance(hint, LocationHint)}

        def sort_hints(item: tuple[NodeIdentifier, set[PickupIndex]]):
            return (len(item[1] - hinted_pickups), item[0])

        # assign hints with fewest potential targets first to help ensure none of them run out of options
        for hint_node, potential_targets in sorted(hint_state.hint_valid_targets.items(), key=sort_hints):
            if hint_node in patches.hints:
                # hint has already been assigned
                continue

            node = region_list.typed_node_by_identifier(hint_node, HintNode)
            if node.kind != HintNodeKind.GENERIC:
                continue

            debug.debug_print(f"> Choosing hint target for {hint_node.as_string}:")

            # exclude uninteresting pickups (minors, Echoes keys, etc.)
            real_potential_targets = {
                target
                for target in potential_targets
                if self.interesting_pickup_to_hint(patches.pickup_assignment[target].pickup)
            }
            # don't hint things twice
            real_potential_targets -= hinted_pickups

            if not real_potential_targets:
                # no interesting pickups to place - use anything placed by the generator
                real_potential_targets = {
                    pickup
                    for pickup, entry in patches.pickup_assignment.items()
                    if self.less_interesting_pickup_to_hint(entry.pickup)
                }
                real_potential_targets -= hinted_pickups
                debug.debug_print(
                    f"  * No interesting pickups; trying {len(real_potential_targets)} less interesting pickups"
                )

            if not real_potential_targets:
                # STILL no pickups to place - just use *anything* that hasn't been hinted
                real_potential_targets = {
                    node.pickup_index for node in region_list.iterate_nodes() if isinstance(node, PickupNode)
                }
                real_potential_targets -= hinted_pickups
                debug.debug_print(
                    f"  * Still no viable pickups; trying {len(real_potential_targets)} uninteresting pickups"
                )

            if not real_potential_targets:
                raise UnableToGenerate("Not enough PickupNodes in the game to fill all hint locations.")

            target = rng.choice(sorted(real_potential_targets))

            hinted_pickups.add(target)
            debug.debug_print(
                f"  * Placing hint for {patches.pickup_assignment.get(target, target)}"
                f" at {region_list.node_name(region_list.node_from_pickup_index(target))}\n"
            )

            patches = patches.assign_hint(hint_node, LocationHint.unassigned(target))

        return patches

    def replace_hints_without_precision_with_jokes(self, patches: GamePatches) -> GamePatches:
        """
        Assigns a JokeHint to each hint node with unassigned precision
        :param patches:
        :return:
        """

        hints_to_replace = {
            hint_node: JokeHint() for hint_node, hint in patches.hints.items() if is_unassigned_location(hint)
        }

        return dataclasses.replace(
            patches,
            hints={hint_node: hints_to_replace.get(hint_node, hint) for hint_node, hint in patches.hints.items()},
        )

    @property
    def default_precision_pair(self) -> PrecisionPair:
        raise NotImplementedError

    def get_hint_precision(self, hint_node: NodeIdentifier, hint: LocationHint, rng: Random) -> PrecisionPair:
        pass

    def add_hints_precision(
        self,
        player_state: PlayerState,
        patches: GamePatches,
        rng: Random,
    ) -> GamePatches:
        """
        Adds precision to all hints that are missing one.
        :param player_state:
        :param patches:
        :param rng:
        :return:
        """

        hints_to_replace = {
            identifier: hint for identifier, hint in patches.hints.items() if is_unassigned_location(hint)
        }

        unassigned_hints = list(hints_to_replace.items())
        rng.shuffle(unassigned_hints)

        # Add random precisions
        for identifier, hint in unassigned_hints:
            precision = self.get_hint_precision(identifier, hint, rng)
            hints_to_replace[identifier] = dataclasses.replace(hints_to_replace[identifier], precision=precision)

        # Replace the hints in the patches
        return dataclasses.replace(
            patches,
            hints={identifier: hints_to_replace.get(identifier, hint) for identifier, hint in patches.hints.items()},
        )


class AllJokesHintDistributor(HintDistributor):
    async def assign_precision_to_hints(
        self, patches: GamePatches, rng: Random, player_pool: PlayerPool, player_state: PlayerState
    ) -> GamePatches:
        return self.replace_hints_without_precision_with_jokes(patches)
