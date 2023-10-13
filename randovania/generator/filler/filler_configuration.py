import dataclasses

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import GameGenerator
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


@dataclasses.dataclass(frozen=True)
class PlayerPool:
    game: GameDescription
    game_generator: GameGenerator
    configuration: BaseConfiguration
    patches: GamePatches
    pickups: list[PickupEntry]


@dataclasses.dataclass(frozen=True)
class FillerPlayerResult:
    game: GameDescription
    patches: GamePatches
    unassigned_pickups: list[PickupEntry]


@dataclasses.dataclass(frozen=True)
class FillerResults:
    player_results: dict[int, FillerPlayerResult]
    action_log: tuple[str, ...]
