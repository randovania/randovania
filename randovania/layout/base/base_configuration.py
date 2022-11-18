import dataclasses

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.games.game import RandovaniaGame
from randovania.layout.base.ammo_configuration import AmmoConfiguration
from randovania.layout.base.available_locations import AvailableLocationsConfiguration
from randovania.layout.base.damage_strictness import LayoutDamageStrictness
from randovania.layout.base.dock_rando_configuration import DockRandoConfiguration
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
from randovania.layout.base.pickup_model import PickupModelStyle, PickupModelDataSource
from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration
from randovania.layout.lib import location_list


class StartingLocationList(location_list.LocationList):
    @classmethod
    def areas_list(cls, game: RandovaniaGame):
        return location_list.area_locations_with_filter(game, lambda area: area.valid_starting_location)


def _collect_from_fields(obj, field_name: str):
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
    major_items_configuration: MajorItemsConfiguration
    ammo_configuration: AmmoConfiguration
    damage_strictness: LayoutDamageStrictness
    pickup_model_style: PickupModelStyle
    pickup_model_data_source: PickupModelDataSource
    logical_resource_action: LayoutLogicalResourceAction
    first_progression_must_be_local: bool
    minimum_available_locations_for_hint_placement: int = dataclasses.field(metadata={"min": 0, "max": 99})
    minimum_location_weight_for_hint_placement: float = dataclasses.field(metadata={
        "min": 0, "max": 5.0, "precision": 0.1,
    })
    dock_rando: DockRandoConfiguration

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        raise NotImplementedError()

    @property
    def game(self):
        return self.game_enum()

    @classmethod
    def json_extra_arguments(cls):
        return {
            "game": cls.game_enum(),
        }

    def active_layers(self) -> set[str]:
        return {"default"}

    def dangerous_settings(self) -> list[str]:
        result = _collect_from_fields(self, "dangerous_settings")

        if self.first_progression_must_be_local:
            result.append("Requiring first progression to be local causes increased generation failure.")

        return result

    def settings_incompatible_with_multiworld(self) -> list[str]:
        return _collect_from_fields(self, "settings_incompatible_with_multiworld")

    def unsupported_features(self) -> list[str]:
        return _collect_from_fields(self, "unsupported_features")
