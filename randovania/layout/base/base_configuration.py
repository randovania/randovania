import dataclasses
from typing import List

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.games import default_data
from randovania.games.game import RandovaniaGame
from randovania.layout.lib import location_list
from randovania.layout.base.ammo_configuration import AmmoConfiguration
from randovania.layout.base.available_locations import AvailableLocationsConfiguration
from randovania.layout.base.damage_strictness import LayoutDamageStrictness
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
from randovania.layout.base.pickup_model import PickupModelStyle, PickupModelDataSource
from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration


class StartingLocationList(location_list.LocationList):
    @classmethod
    def areas_list(cls, game: RandovaniaGame):
        return location_list.area_locations_with_filter(game, lambda area: area.valid_starting_location)


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
    multi_pickup_placement: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        raise NotImplementedError()

    @property
    def game(self):
        return self.game_enum()

    @property
    def game_data(self) -> dict:
        return default_data.read_json_then_binary(self.game)[1]

    @classmethod
    def json_extra_arguments(cls):
        return {
            "game": cls.game_enum(),
        }

    def dangerous_settings(self) -> List[str]:
        result = []
        for field in dataclasses.fields(self):
            f = getattr(self, field.name)
            if hasattr(f, "dangerous_settings"):
                result.extend(f.dangerous_settings())

        if self.multi_pickup_placement:
            result.append("Multi-pickup placement enabled")

        return result
