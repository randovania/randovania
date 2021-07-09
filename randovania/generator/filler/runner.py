import copy
import dataclasses
from random import Random
from typing import List, Tuple, Callable, TypeVar, Set, Dict, FrozenSet, Union, Iterator, Optional

from randovania.game_description import node_search
from randovania.game_description.world.area import Area
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType, PrecisionPair, HintLocationPrecision, HintItemPrecision, \
    HintRelativeAreaName, RelativeDataArea, RelativeDataItem
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.world.node import LogbookNode, PickupNode
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.generator.filler.filler_configuration import FillerConfiguration
from randovania.generator.filler.filler_library import should_have_hint, UnableToGenerate
from randovania.generator.filler.player_state import PlayerState
from randovania.generator.filler.retcon import retcon_playthrough_filler
from randovania.layout.prime2.echoes_configuration import EchoesConfiguration
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
                      max_distance: int,
                      ) -> Optional[Hint]:
    """
    Creates a relative hint.
    :return: Might be None, if no hint could be created.
    """
    target_node = node_search.pickup_index_to_node(world_list, target)
    target_area = world_list.nodes_to_area(target_node)
    distances = node_search.distances_to_node(world_list, target_node, patches=patches, cutoff=max_distance)

    def _major_pickups(area: Area) -> Iterator[PickupIndex]:
        for index in area.pickup_indices:
            t = patches.pickup_assignment.get(index)
            # FIXME: None should be ok, but this must be called after junk has been filled
            if t is not None:
                cat = t.pickup.item_category
                if cat.is_major_category or (cat != ItemCategory.EXPANSION
                                             and target_precision == HintItemPrecision.DETAILED):
                    yield index

    area_choices = {
        area: 1 / max(distance, 2)
        for area, distance in distances.items()
        if (distance > 0 and area.in_dark_aether == target_area.in_dark_aether
            and (relative_type == HintLocationPrecision.RELATIVE_TO_AREA or _not_empty(_major_pickups(area))))
    }
    if not area_choices:
        return None
    area = random_lib.select_element_with_weight(dict(sorted(area_choices.items(),
                                                             key=lambda a: a[0].area_asset_id)), rng)

    distance_offset = None
    if not precise_distance:
        distance_offset = max_distance - distances[area]

    if relative_type == HintLocationPrecision.RELATIVE_TO_AREA:
        relative = RelativeDataArea(distance_offset, world_list.area_to_area_location(area),
                                    precision)
    elif relative_type == HintLocationPrecision.RELATIVE_TO_INDEX:
        relative = RelativeDataItem(distance_offset, rng.choice(list(_major_pickups(area))), precision)
    else:
        raise ValueError(f"Invalid relative_type: {relative_type}")

    precision_pair = PrecisionPair(relative_type, target_precision, include_owner=False, relative=relative)
    return Hint(HintType.LOCATION, precision_pair, target)


def _relative(relative_type: HintLocationPrecision,
              precise_distance: bool,
              precision: Union[HintItemPrecision, HintRelativeAreaName],
              max_distance: int,
              ) -> Callable[[PlayerState, GamePatches, Random, PickupIndex], Optional[Hint]]:
    def _wrapper(player_state: PlayerState, patches: GamePatches, rng: Random, target: PickupIndex):
        return add_relative_hint(player_state.game.world_list, patches, rng, target, HintItemPrecision.DETAILED,
                                 relative_type, precise_distance, precision, max_distance)

    return _wrapper


def _get_relative_hint_providers():
    return [
        _relative(HintLocationPrecision.RELATIVE_TO_AREA, True, HintRelativeAreaName.NAME, 4),
        _relative(HintLocationPrecision.RELATIVE_TO_AREA, False, HintRelativeAreaName.NAME, 3),
        _relative(HintLocationPrecision.RELATIVE_TO_INDEX, True, HintItemPrecision.DETAILED, 4),
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
        asset: Hint(HintType.JOKE, None)
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
    for logbook in potential_hint_locations:
        if logbook not in scan_asset_initial_pickups:
            scan_asset_initial_pickups[logbook] = frozenset()

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

    # Get an stable order
    ordered_possible_indices = list(sorted(possible_indices))
    ordered_potential_hint_locations = list(sorted(potential_hint_locations))

    num_logbooks: Dict[PickupIndex, int] = {
        index: sum(1 for indices in scan_asset_initial_pickups.values() if index in indices)
        for index in ordered_possible_indices
    }
    max_seen = max(num_logbooks.values())
    pickup_indices_weight: Dict[PickupIndex, int] = {
        index: max_seen - num_logbook
        for index, num_logbook in num_logbooks.items()
    }
    # Ensure all indices are present with at least weight 0
    for index in ordered_possible_indices:
        if index not in pickup_indices_weight:
            pickup_indices_weight[index] = 0

    for logbook in sorted(ordered_potential_hint_locations,
                          key=lambda r: len(scan_asset_initial_pickups[r]),
                          reverse=True):
        try:
            new_index = random_lib.select_element_with_weight(pickup_indices_weight, rng)
        except StopIteration:
            # If everything has weight 0, then just choose randomly.
            new_index = random_lib.random_key(pickup_indices_weight, rng)

        del pickup_indices_weight[new_index]

        new_hints[logbook] = Hint(HintType.LOCATION, None, new_index)
        debug.debug_print(f"Added hint at {logbook} for item at {new_index}")

    return dataclasses.replace(patches, hints=new_hints)


@dataclasses.dataclass(frozen=True)
class PlayerPool:
    game: GameDescription
    configuration: EchoesConfiguration
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


async def run_filler(rng: Random,
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
        if pool.configuration.multi_pickup_placement and False:
            major_items, player_expansions[index] = list(pool.pickups), []
        else:
            major_items, player_expansions[index] = _split_expansions(pool.pickups)
        rng.shuffle(major_items)
        rng.shuffle(player_expansions[index])

        new_game, state = bootstrap.logic_bootstrap(pool.configuration, pool.game, pool.patches)

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
                multi_pickup_placement=pool.configuration.multi_pickup_placement,
            ),
        ))

    try:
        filler_result, actions_log = retcon_playthrough_filler(rng, player_states, status_update=status_update)
    except UnableToGenerate as e:
        message = "{}\n\n{}".format(
            str(e),
            "\n\n".join(
                "#### Player {}\n{}".format(player.index + 1, player.current_state_report())
                for player in player_states
            ),
        )
        debug.debug_print(message)
        raise UnableToGenerate(message) from e

    results = {}

    for player_state, patches in filler_result.items():
        game = player_state.game

        if game.game == RandovaniaGame.METROID_PRIME_ECHOES:
            # Since we haven't added expansions yet, these hints will always be for items added by the filler.
            full_hints_patches = fill_unassigned_hints(patches, game.world_list, rng,
                                                       player_state.scan_asset_initial_pickups)

            if player_pools[player_state.index].configuration.hints.item_hints:
                result = add_hints_precision(player_state, full_hints_patches, rng)
            else:
                result = replace_hints_without_precision_with_jokes(full_hints_patches)
        else:
            result = patches

        results[player_state.index] = FillerPlayerResult(
            game=game,
            patches=result,
            unassigned_pickups=player_state.pickups_left + player_expansions[player_state.index],
        )

    return FillerResults(results, actions_log)
