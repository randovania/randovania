from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from randovania.game.generator import GameGenerator
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.generator.filler.player_state import GeneratorHintState
    from randovania.layout.base.available_locations import RandomizationMode
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction


@dataclasses.dataclass(frozen=True)
class FillerConfiguration:
    randomization_mode: RandomizationMode
    minimum_random_starting_pickups: int
    maximum_random_starting_pickups: int
    indices_to_exclude: frozenset[PickupIndex]
    logical_resource_action: LayoutLogicalResourceAction
    first_progression_must_be_local: bool
    minimum_available_locations_for_hint_placement: int
    minimum_location_weight_for_hint_placement: float
    single_set_for_pickups_that_solve: bool
    staggered_multi_pickup_placement: bool
    fallback_to_reweight_with_unsafe: bool
    consider_possible_unsafe_resources: bool

    @classmethod
    def from_configuration(cls, config: BaseConfiguration) -> Self:
        return cls(
            randomization_mode=config.available_locations.randomization_mode,
            minimum_random_starting_pickups=config.standard_pickup_configuration.minimum_random_starting_pickups,
            maximum_random_starting_pickups=config.standard_pickup_configuration.maximum_random_starting_pickups,
            indices_to_exclude=config.available_locations.excluded_indices,
            logical_resource_action=config.logical_resource_action,
            first_progression_must_be_local=config.first_progression_must_be_local,
            minimum_available_locations_for_hint_placement=config.hints.minimum_available_locations_for_hint_placement,
            minimum_location_weight_for_hint_placement=config.hints.minimum_location_weight_for_hint_placement,
            single_set_for_pickups_that_solve=config.single_set_for_pickups_that_solve,
            staggered_multi_pickup_placement=config.staggered_multi_pickup_placement,
            fallback_to_reweight_with_unsafe=False,
            consider_possible_unsafe_resources=config.consider_possible_unsafe_resources,
        )


@dataclasses.dataclass(frozen=True)
class PlayerPool:
    game: GameDescription
    game_generator: GameGenerator
    configuration: BaseConfiguration
    patches: GamePatches
    pickups: list[PickupEntry]
    pickups_in_world: list[PickupEntry]


@dataclasses.dataclass(frozen=True)
class FillerPlayerResult:
    game: GameDescription
    patches: GamePatches
    unassigned_pickups: list[PickupEntry]
    pool: PlayerPool
    hint_state: GeneratorHintState


@dataclasses.dataclass(frozen=True)
class FillerResults:
    player_results: dict[int, FillerPlayerResult]
    action_log: tuple[str, ...]

    @property
    def player_pools(self) -> tuple[PlayerPool, ...]:
        return tuple(result.pool for result in self.player_results.values())
