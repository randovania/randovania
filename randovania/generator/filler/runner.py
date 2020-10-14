import copy
import dataclasses
import math
from random import Random
from typing import List, Tuple, Callable, TypeVar, Set, Dict, FrozenSet, Union, Iterator, Optional

from randovania.game_description import node_search
from randovania.game_description.area import Area
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType, PrecisionPair, HintLocationPrecision, HintItemPrecision, \
    HintRelativeAreaName, RelativeDataArea, RelativeDataItem
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import LogbookNode, PickupNode
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world_list import WorldList
from randovania.generator.filler.filler_library import should_have_hint
from randovania.generator.filler.retcon import retcon_playthrough_filler, FillerConfiguration, PlayerState
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.resolver import bootstrap, debug, random_lib

T = TypeVar("T")


def _split_expansions(item_pool: List[PickupEntry]) -> Tuple[List[PickupEntry], List[PickupEntry]]:
    """

    :param item_pool:
    :return:
    """
    major_items = []
    expansions = []

    for pickup in item_pool:
        if pickup.item_category == ItemCategory.EXPANSION:
            expansions.append(pickup)
        else:
            major_items.append(pickup)

    return major_items, expansions


def _create_weighted_list(rng: Random,
                          current: List[T],
                          factory: Callable[[], List[T]],
                          ) -> List[T]:
    """
    Ensures we always have a non-empty list.
    :param rng:
    :param current:
    :param factory:
    :return:
    """
    if not current:
        current = factory()
        rng.shuffle(current)

    return current


def precision_pair_weighted_list() -> List[PrecisionPair]:
    tiers = {
        (HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED): 5,
        (HintLocationPrecision.DETAILED, HintItemPrecision.PRECISE_CATEGORY): 2,
        (HintLocationPrecision.DETAILED, HintItemPrecision.GENERAL_CATEGORY): 1,

        (HintLocationPrecision.WORLD_ONLY, HintItemPrecision.DETAILED): 2,
        (HintLocationPrecision.WORLD_ONLY, HintItemPrecision.PRECISE_CATEGORY): 1,
    }

    hints = []
    for params, quantity in tiers.items():
        hints.extend([PrecisionPair(*params)] * quantity)

    return hints


_MAX_RELATIVE_DISTANCE = 8


def _not_empty(it: Iterator) -> bool:
    return sum(1 for _ in it) > 0


def add_relative_hint(world_list: WorldList,
                      patches: GamePatches,
                      rng: Random,
                      target: PickupIndex,
                      target_precision: HintItemPrecision,
                      relative_type: HintLocationPrecision,
                      precise_distance: bool,
                      precision: Union[HintItemPrecision, HintRelativeAreaName],
                      max_distance: Optional[int] = None,
                      ) -> Optional[Hint]:
    """
    Creates a relative hint.
    :return: Might be None, if no hint could be created.
    """
    if max_distance is None:
        max_distance = _MAX_RELATIVE_DISTANCE
    target_node = node_search.pickup_index_to_node(world_list, target)
    distances = node_search.distances_to_node(world_list, target_node, patches=patches, cutoff=max_distance)

    def _non_expansions(area: Area) -> Iterator[PickupIndex]:
        for index in area.pickup_indices:
            t = patches.pickup_assignment.get(index)
            # FIXME: None should be ok, but this must be called after junk has been filled
            if t is not None and t.pickup.item_category != ItemCategory.EXPANSION:
                yield index

    area_choices = {
        area: 1 / distance
        for area, distance in distances.items()
        if distance > 1 and (relative_type == HintLocationPrecision.RELATIVE_TO_AREA
                             or _not_empty(_non_expansions(area)))
    }
    if not area_choices:
        return None
    area = random_lib.select_element_with_weight(area_choices, rng)

    if relative_type == HintLocationPrecision.RELATIVE_TO_AREA:
        relative = RelativeDataArea(precise_distance, world_list.area_to_area_location(area),
                                    precision)
    elif relative_type == HintLocationPrecision.RELATIVE_TO_INDEX:
        relative = RelativeDataItem(precise_distance, rng.choice(list(_non_expansions(area))), precision)
    else:
        raise ValueError(f"Invalid relative_type: {relative_type}")

    precision_pair = PrecisionPair(relative_type, target_precision, relative)
    return Hint(HintType.LOCATION, precision_pair, target)


def _relative(relative_type: HintLocationPrecision,
              precise_distance: bool,
              precision: Union[HintItemPrecision, HintRelativeAreaName],
              ) -> Callable[[PlayerState, GamePatches, Random, PickupIndex], Optional[Hint]]:
    def _wrapper(player_state: PlayerState, patches: GamePatches, rng: Random, target: PickupIndex):
        return add_relative_hint(player_state.game.world_list, patches, rng, target, HintItemPrecision.DETAILED,
                                 relative_type, precise_distance, precision)

    return _wrapper


def _get_relative_hint_providers():
    return [
        _relative(HintLocationPrecision.RELATIVE_TO_AREA, True, HintRelativeAreaName.NAME),
        _relative(HintLocationPrecision.RELATIVE_TO_INDEX, True, HintItemPrecision.DETAILED),
        _relative(HintLocationPrecision.RELATIVE_TO_INDEX, True, HintItemPrecision.PRECISE_CATEGORY),
    ]


def add_hints_precision(player_state: PlayerState,
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

    hints_to_replace: Dict[LogbookAsset, Hint] = {
        asset: hint
        for asset, hint in patches.hints.items()
        if hint.precision is None and hint.hint_type == HintType.LOCATION
    }

    relative_hint_providers = _get_relative_hint_providers()
    asset_ids = list(hints_to_replace.keys())
    rng.shuffle(asset_ids)

    while asset_ids and relative_hint_providers:
        new_hint = relative_hint_providers.pop()(player_state, patches, rng, hints_to_replace[asset_ids[-1]].target)
        if new_hint is not None:
            hints_to_replace[asset_ids.pop()] = new_hint

    # Add random precisions
    precisions = []
    for asset_id in asset_ids:
        precisions = _create_weighted_list(rng, precisions, precision_pair_weighted_list)
        precision = precisions.pop()

        hints_to_replace[asset_id] = dataclasses.replace(hints_to_replace[asset_id], precision=precision)

    # Replace the hints the in the patches
    return dataclasses.replace(patches, hints={
        asset: hints_to_replace.get(asset, hint)
        for asset, hint in patches.hints.items()
    })


def replace_hints_without_precision_with_jokes(patches: GamePatches,
                                               ) -> GamePatches:
    """
    Adds WRONG_GAME precision to all hints that are missing one precision.
    :param patches:
    :return:
    """

    hints_to_replace = {
        asset: dataclasses.replace(hint, hint_type=HintType.JOKE)
        for asset, hint in patches.hints.items()
        if hint.precision is None and hint.hint_type == HintType.LOCATION
    }

    return dataclasses.replace(patches, hints={
        asset: hints_to_replace.get(asset, hint)
        for asset, hint in patches.hints.items()
    })


def fill_unassigned_hints(patches: GamePatches,
                          world_list: WorldList,
                          rng: Random,
                          scan_asset_initial_pickups: Dict[LogbookAsset, FrozenSet[PickupIndex]],
                          ) -> GamePatches:
    new_hints = copy.copy(patches.hints)

    # Get all LogbookAssets from the WorldList
    potential_hint_locations: Set[LogbookAsset] = {
        node.resource()
        for node in world_list.all_nodes
        if isinstance(node, LogbookNode)
    }

    # But remove these that already have hints
    potential_hint_locations -= patches.hints.keys()

    # Get interesting items to place hints for
    possible_indices = set(patches.pickup_assignment.keys())
    possible_indices -= {hint.target for hint in patches.hints.values() if hint.target is not None}
    possible_indices -= {index for index in possible_indices
                         if not should_have_hint(patches.pickup_assignment[index].pickup.item_category)}

    debug.debug_print("fill_unassigned_hints had {} decent indices for {} hint locations".format(
        len(possible_indices), len(potential_hint_locations)))

    if debug.debug_level() > 1:
        print(f"> Num pickups per asset:")
        for asset, pickups in scan_asset_initial_pickups.items():
            print(f"* {asset}: {len(pickups)} pickups")
        print("> Done.")

    # But if we don't have enough hints, just pick randomly from everything
    if len(possible_indices) < len(potential_hint_locations):
        possible_indices = {node.pickup_index
                            for node in world_list.all_nodes
                            if isinstance(node, PickupNode)}

    # Get an stable order then shuffle
    possible_indices = list(sorted(possible_indices))
    rng.shuffle(possible_indices)

    for logbook in sorted(potential_hint_locations):
        new_hints[logbook] = Hint(HintType.LOCATION, None, possible_indices.pop())
        debug.debug_print(f"Added hint at {logbook} for item at {new_hints[logbook].target}")

    return dataclasses.replace(patches, hints=new_hints)


@dataclasses.dataclass(frozen=True)
class PlayerPool:
    game: GameDescription
    configuration: LayoutConfiguration
    patches: GamePatches
    pickups: List[PickupEntry]


@dataclasses.dataclass(frozen=True)
class FillerPlayerResult:
    game: GameDescription
    patches: GamePatches
    unassigned_pickups: List[PickupEntry]


@dataclasses.dataclass(frozen=True)
class FillerResults:
    player_results: Dict[int, FillerPlayerResult]
    action_log: Tuple[str, ...]


def run_filler(rng: Random,
               player_pools: Dict[int, PlayerPool],
               status_update: Callable[[str], None],
               ) -> FillerResults:
    """
    Runs the filler logic for the given configuration and item pool.
    Returns a GamePatches with progression items and hints assigned, along with all items in the pool
    that weren't assigned.

    :param player_pools:
    :param rng:
    :param status_update:
    :return:
    """

    player_states = []
    player_expansions: Dict[int, List[PickupEntry]] = {}

    for index, pool in player_pools.items():
        status_update(f"Creating state for player {index + 1}")
        major_items, player_expansions[index] = _split_expansions(pool.pickups)
        rng.shuffle(major_items)
        rng.shuffle(player_expansions[index])

        new_game, state = bootstrap.logic_bootstrap(pool.configuration, pool.game, pool.patches)
        new_game.patch_requirements(state.resources, pool.configuration.damage_strictness.value)

        major_configuration = pool.configuration.major_items_configuration
        player_states.append(PlayerState(
            index=index,
            game=new_game,
            initial_state=state,
            pickups_left=major_items,
            configuration=FillerConfiguration(
                randomization_mode=pool.configuration.available_locations.randomization_mode,
                minimum_random_starting_items=major_configuration.minimum_random_starting_items,
                maximum_random_starting_items=major_configuration.maximum_random_starting_items,
                indices_to_exclude=pool.configuration.available_locations.excluded_indices,
            ),
        ))

    filler_result, actions_log = retcon_playthrough_filler(rng, player_states, status_update=status_update)

    results = {}

    for player_state, patches in filler_result.items():
        game = player_state.game

        # Since we haven't added expansions yet, these hints will always be for items added by the filler.
        full_hints_patches = fill_unassigned_hints(patches, game.world_list, rng,
                                                   player_state.scan_asset_initial_pickups)

        if player_pools[player_state.index].configuration.hints.item_hints:
            result = add_hints_precision(player_state, full_hints_patches, rng)
        else:
            result = replace_hints_without_precision_with_jokes(full_hints_patches)

        results[player_state.index] = FillerPlayerResult(
            game=game,
            patches=result,
            unassigned_pickups=player_state.pickups_left + player_expansions[player_state.index],
        )

    return FillerResults(results, actions_log)
