from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from typing_extensions import TypeVar

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.layout.base.ammo_pickup_configuration import AmmoPickupConfiguration
from randovania.layout.base.available_locations import AvailableLocationsConfiguration
from randovania.layout.base.damage_strictness import LayoutDamageStrictness
from randovania.layout.base.dock_rando_configuration import DockRandoConfiguration, DockRandoMode
from randovania.layout.base.hint_configuration import HintConfiguration
from randovania.layout.base.logical_pickup_placement_configuration import LogicalPickupPlacementConfiguration
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction
from randovania.layout.base.pickup_model import PickupModelDataSource, PickupModelStyle
from randovania.layout.base.standard_pickup_configuration import StandardPickupConfiguration
from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration
from randovania.layout.lib import location_list

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.db.node_identifier import NodeIdentifier


class StartingLocationList(location_list.LocationList):
    @classmethod
    def nodes_list(cls, game: RandovaniaGame) -> list[NodeIdentifier]:
        return location_list.node_locations_with_filter(game, lambda node: node.valid_starting_location)


def _collect_from_fields(obj: DataclassInstance, field_name: str) -> list[str]:
    result = []

    for field in dataclasses.fields(obj):
        f = getattr(obj, field.name)
        if hasattr(f, field_name):
            result.extend(getattr(f, field_name)())

    return result


@dataclasses.dataclass(frozen=True)
class BaseConfiguration(BitPackDataclass, JsonDataclass, DataclassPostInitTypeCheck):
    trick_level: TrickLevelConfiguration
    starting_location: StartingLocationList
    available_locations: AvailableLocationsConfiguration
    standard_pickup_configuration: StandardPickupConfiguration
    ammo_pickup_configuration: AmmoPickupConfiguration
    damage_strictness: LayoutDamageStrictness
    pickup_model_style: PickupModelStyle
    pickup_model_data_source: PickupModelDataSource
    logical_resource_action: LayoutLogicalResourceAction
    first_progression_must_be_local: bool
    two_sided_door_lock_search: bool
    dock_rando: DockRandoConfiguration
    single_set_for_pickups_that_solve: bool
    staggered_multi_pickup_placement: bool
    check_if_beatable_after_base_patches: bool
    logical_pickup_placement: LogicalPickupPlacementConfiguration
    consider_possible_unsafe_resources: bool
    hints: HintConfiguration

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        raise NotImplementedError

    @property
    def game(self) -> RandovaniaGame:
        return self.game_enum()

    @classmethod
    def json_extra_arguments(cls) -> dict:
        return {
            "game": cls.game_enum(),
        }

    def active_layers(self) -> set[str]:
        return {"default"}

    def dangerous_settings(self) -> list[str]:
        result = _collect_from_fields(self, "dangerous_settings")

        if self.first_progression_must_be_local:
            result.append("Requiring first progression to be local causes increased generation failure.")

        if self.consider_possible_unsafe_resources:
            result.append("Considering possible unsafe resources will increase generation time.")

        return result

    def settings_incompatible_with_multiworld(self) -> list[str]:
        return _collect_from_fields(self, "settings_incompatible_with_multiworld")

    def unsupported_features(self) -> list[str]:
        return _collect_from_fields(self, "unsupported_features")

    def should_hide_generation_log(self) -> bool:
        """Certain settings makes the generation log full of nonsense. It should be hidden in these cases."""
        return self.dock_rando.mode == DockRandoMode.DOCKS


ConfigurationT_co = TypeVar("ConfigurationT_co", bound=BaseConfiguration, default=BaseConfiguration, covariant=True)
