from __future__ import annotations

import copy
import dataclasses
from abc import ABC
from collections.abc import Callable, Iterator
from random import Random
from typing import TYPE_CHECKING

from randovania.game_description import node_search
from randovania.game_description.db.hint_node import HintNode, HintNodeKind
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import (
    Hint,
    HintItemPrecision,
    HintLocationPrecision,
    HintRelativeAreaName,
    HintType,
    PrecisionPair,
    RelativeData,
    RelativeDataArea,
    RelativeDataItem,
)
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.filler.filler_library import UnableToGenerate
from randovania.generator.filler.player_state import PlayerState
from randovania.lib import random_lib
from randovania.resolver import debug

if TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.generator.filler.filler_configuration import PlayerPool
    from randovania.generator.pre_fill_params import PreFillParams

HintProvider = Callable[[PlayerState, GamePatches, Random, PickupIndex], Hint | None]


def _not_empty(it: Iterator) -> bool:
    return sum(1 for _ in it) > 0


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

    async def get_specific_pickup_precision_pair_overrides(
        self, patches: GamePatches, prefill: PreFillParams
    ) -> dict[NodeIdentifier, PrecisionPair]:
        return {}

    async def assign_specific_location_hints(self, patches: GamePatches, prefill: PreFillParams) -> GamePatches:
        specific_location_precisions = await self.get_specific_pickup_precision_pair_overrides(patches, prefill)

        # TODO: this is an Echoes default. Should not have a default and all nodes have one in the DB.
        default_precision = PrecisionPair(
            HintLocationPrecision.KEYBEARER, HintItemPrecision.BROAD_CATEGORY, include_owner=True
        )

        wl = prefill.game.region_list
        for node in wl.iterate_nodes():
            if isinstance(node, HintNode) and node.kind == HintNodeKind.SPECIFIC_PICKUP:
                identifier = node.identifier
                patches = patches.assign_hint(
                    identifier,
                    Hint(
                        HintType.LOCATION,
                        specific_location_precisions.get(identifier, default_precision),
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
            patches = patches.assign_hint(identifier, Hint(HintType.LOCATION, precision, index))
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
            patches = patches.assign_hint(identifier, Hint(HintType.JOKE, None))
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
            player_state.hint_initial_pickups,
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
        return pickup.pickup_category.hinted_as_major

    def fill_unassigned_hints(
        self,
        patches: GamePatches,
        region_list: RegionList,
        rng: Random,
        hint_initial_pickups: dict[NodeIdentifier, frozenset[PickupIndex]],
    ) -> GamePatches:
        new_hints = copy.copy(patches.hints)

        debug.debug_print(f"fill_unassigned_hints: hint_initial_pickups has {len(hint_initial_pickups)} elements")

        # Get all Hint's NodeIdentifiers from the RegionList
        potential_hint_locations: set[NodeIdentifier] = {
            node.identifier for node in region_list.iterate_nodes() if isinstance(node, HintNode)
        }
        for hint in potential_hint_locations:
            if hint not in hint_initial_pickups:
                hint_initial_pickups[hint] = frozenset()

        # But remove these that already have hints
        potential_hint_locations -= patches.hints.keys()

        # We try our best to not hint the same thing twice
        hinted_indices: set[PickupIndex] = {hint.target for hint in patches.hints.values() if hint.target is not None}

        # Get interesting items to place hints for
        possible_indices: set[PickupIndex] = {
            index
            for index, target in patches.pickup_assignment.items()
            if self.interesting_pickup_to_hint(target.pickup)
        }
        possible_indices -= hinted_indices

        debug.debug_print(
            f"fill_unassigned_hints had {len(possible_indices)} decent indices "
            f"for {len(potential_hint_locations)} hint locations"
        )

        if debug.debug_level() > 1:
            print("> Num pickups per asset:")
            for asset, pickups in hint_initial_pickups.items():
                print(f"* {asset}: {len(pickups)} pickups")
            print("> Done.")

        all_pickup_indices = [node.pickup_index for node in region_list.iterate_nodes() if isinstance(node, PickupNode)]
        rng.shuffle(all_pickup_indices)

        # If there isn't enough indices, use unhinted non-majors placed by generator
        if (num_indices_needed := len(potential_hint_locations) - len(possible_indices)) > 0:
            potential_indices = [
                index for index in all_pickup_indices if index not in possible_indices and index not in hinted_indices
            ]
            debug.debug_print(
                f"Had only {len(possible_indices)} hintable indices, but needed {len(potential_hint_locations)}."
                f" Found {len(potential_indices)} less desirable locations."
            )
            possible_indices |= set(potential_indices[:num_indices_needed])

        # But if we don't have enough hints, just pick randomly from everything
        while len(possible_indices) < len(potential_hint_locations):
            debug.debug_print(
                f"Still only {len(possible_indices)} indices out of {len(potential_hint_locations)} target."
                f"Desperate pool has {len(all_pickup_indices)} left."
            )
            try:
                possible_indices.add(all_pickup_indices.pop())
            except IndexError:
                raise UnableToGenerate("Not enough PickupNodes in the game to fill all hint locations.")

        # Get an stable order
        ordered_possible_indices = sorted(possible_indices)
        ordered_potential_hint_locations = sorted(potential_hint_locations)

        num_hints: dict[PickupIndex, int] = {
            index: sum(1 for indices in hint_initial_pickups.values() if index in indices)
            for index in ordered_possible_indices
        }
        max_seen = max(num_hints.values()) if num_hints else 0
        pickup_indices_weight: dict[PickupIndex, int] = {
            index: max_seen - num_hint for index, num_hint in num_hints.items()
        }
        # Ensure all indices are present with at least weight 0
        for index in ordered_possible_indices:
            if index not in pickup_indices_weight:
                pickup_indices_weight[index] = 0

        for hint in sorted(ordered_potential_hint_locations, key=lambda r: len(hint_initial_pickups[r]), reverse=True):
            try:
                new_index = random_lib.select_element_with_weight(pickup_indices_weight, rng)
            except StopIteration:
                # If everything has weight 0, then just choose randomly.
                new_index = random_lib.random_key(pickup_indices_weight, rng)

            del pickup_indices_weight[new_index]

            new_hints[hint] = Hint(HintType.LOCATION, None, new_index)
            debug.debug_print(
                f"Added hint at {hint} for item at "
                f"{region_list.node_name(region_list.node_from_pickup_index(new_index))}"
            )

        return dataclasses.replace(patches, hints=new_hints)

    def replace_hints_without_precision_with_jokes(self, patches: GamePatches) -> GamePatches:
        """
        Adds WRONG_GAME precision to all hints that are missing one precision.
        :param patches:
        :return:
        """

        hints_to_replace = {
            asset: Hint(HintType.JOKE, None)
            for asset, hint in patches.hints.items()
            if hint.precision is None and hint.hint_type == HintType.LOCATION
        }

        return dataclasses.replace(
            patches, hints={asset: hints_to_replace.get(asset, hint) for asset, hint in patches.hints.items()}
        )

    def precision_pair_weighted_list(self) -> list[PrecisionPair]:
        raise NotImplementedError

    def add_relative_hint(
        self,
        region_list: RegionList,
        patches: GamePatches,
        rng: Random,
        target: PickupIndex,
        target_precision: HintItemPrecision,
        relative_type: HintLocationPrecision,
        precise_distance: bool,
        precision: HintItemPrecision | HintRelativeAreaName,
        max_distance: int,
    ) -> Hint | None:
        """
        Creates a relative hint.
        :return: Might be None, if no hint could be created.
        """
        target_node = node_search.pickup_index_to_node(region_list, target)
        target_area = region_list.nodes_to_area(target_node)
        dock_types_to_ignore = patches.game.dock_weakness_database.all_ignore_hints_dock_types
        distances = node_search.distances_to_node(
            region_list, target_node, dock_types_to_ignore, patches=patches, cutoff=max_distance
        )

        def _major_pickups(area: Area) -> Iterator[PickupIndex]:
            for index in area.pickup_indices:
                t = patches.pickup_assignment.get(index)
                # FIXME: None should be ok, but this must be called after junk has been filled
                if t is not None:
                    cat = t.pickup.pickup_category
                    if cat.hinted_as_major or (not cat.is_expansion and target_precision == HintItemPrecision.DETAILED):
                        yield index

        area_choices = {
            area: 1 / max(distance, 2)
            for area, distance in distances.items()
            if (
                distance > 0
                and area.in_dark_aether == target_area.in_dark_aether
                and (relative_type == HintLocationPrecision.RELATIVE_TO_AREA or _not_empty(_major_pickups(area)))
            )
        }
        if not area_choices:
            return None

        area = random_lib.select_element_with_weight(dict(sorted(area_choices.items(), key=lambda a: a[0].name)), rng)

        distance_offset = None
        if not precise_distance:
            distance_offset = max_distance - distances[area]

        relative: RelativeData

        if relative_type == HintLocationPrecision.RELATIVE_TO_AREA:
            assert isinstance(precision, HintRelativeAreaName)
            relative = RelativeDataArea(distance_offset, region_list.identifier_for_area(area), precision)

        elif relative_type == HintLocationPrecision.RELATIVE_TO_INDEX:
            assert isinstance(precision, HintItemPrecision)
            relative = RelativeDataItem(distance_offset, rng.choice(list(_major_pickups(area))), precision)
        else:
            raise ValueError(f"Invalid relative_type: {relative_type}")

        precision_pair = PrecisionPair(relative_type, target_precision, include_owner=False, relative=relative)
        return Hint(HintType.LOCATION, precision_pair, target)

    def _relative(
        self,
        relative_type: HintLocationPrecision,
        precise_distance: bool,
        precision: HintItemPrecision | HintRelativeAreaName,
        max_distance: int,
    ) -> HintProvider:
        def _wrapper(player_state: PlayerState, patches: GamePatches, rng: Random, target: PickupIndex) -> Hint | None:
            return self.add_relative_hint(
                player_state.game.region_list,
                patches,
                rng,
                target,
                HintItemPrecision.DETAILED,
                relative_type,
                precise_distance,
                precision,
                max_distance,
            )

        return _wrapper

    def _get_relative_hint_providers(self) -> list[HintProvider]:
        raise NotImplementedError

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

        hints_to_replace: dict[NodeIdentifier, Hint] = {
            identifier: hint
            for identifier, hint in patches.hints.items()
            if hint.precision is None and hint.hint_type == HintType.LOCATION
        }

        relative_hint_providers = self._get_relative_hint_providers()
        identifiers = list(hints_to_replace.keys())
        rng.shuffle(identifiers)

        while identifiers and relative_hint_providers:
            hint_target = hints_to_replace[identifiers[-1]].target
            assert hint_target is not None
            new_hint = relative_hint_providers.pop()(player_state, patches, rng, hint_target)
            if new_hint is not None:
                hints_to_replace[identifiers.pop()] = new_hint

        # Add random precisions
        precisions: list[PrecisionPair] = []
        for identifier in identifiers:
            precisions = random_lib.create_weighted_list(rng, precisions, self.precision_pair_weighted_list)
            precision = precisions.pop()

            hints_to_replace[identifier] = dataclasses.replace(hints_to_replace[identifier], precision=precision)

        # Replace the hints the in the patches
        return dataclasses.replace(
            patches,
            hints={identifier: hints_to_replace.get(identifier, hint) for identifier, hint in patches.hints.items()},
        )


class AllJokesHintDistributor(HintDistributor):
    async def assign_precision_to_hints(
        self, patches: GamePatches, rng: Random, player_pool: PlayerPool, player_state: PlayerState
    ) -> GamePatches:
        return self.replace_hints_without_precision_with_jokes(patches)
