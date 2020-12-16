import dataclasses
from enum import Enum
from typing import List

from randovania.bitpacking.bitpacking import BitPackDataClass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_description import default_database
from randovania.games.game import RandovaniaGame
from randovania.games.prime import default_data
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.available_locations import AvailableLocationsConfiguration
from randovania.layout.damage_strictness import LayoutDamageStrictness
from randovania.layout.major_items_configuration import MajorItemsConfiguration
from randovania.layout.pickup_model import PickupModelStyle, PickupModelDataSource
from randovania.layout.starting_location import StartingLocation
from randovania.layout.trick_level import TrickLevelConfiguration


@dataclasses.dataclass(frozen=True)
class BaseConfiguration(BitPackDataClass, JsonDataclass):
    trick_level: TrickLevelConfiguration
    starting_location: StartingLocation
    available_locations: AvailableLocationsConfiguration
    major_items_configuration: MajorItemsConfiguration
    ammo_configuration: AmmoConfiguration
    damage_strictness: LayoutDamageStrictness
    pickup_model_style: PickupModelStyle
    pickup_model_data_source: PickupModelDataSource

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
    def from_json(cls, json_dict: dict) -> "BaseConfiguration":
        game = cls.game_enum()
        item_database = default_database.item_database_for_game(game)

        kwargs = {}
        for field in dataclasses.fields(cls):
            try:
                arg = json_dict[field.name]
            except KeyError as e:
                raise KeyError(f"Missing field {e}") from e

            try:
                if issubclass(field.type, Enum):
                    arg = field.type(arg)
                elif hasattr(field.type, "from_json"):
                    extra_args = []
                    if field.name in ("trick_level", "starting_location"):
                        extra_args.append(game)
                    if field.name in ("major_items_configuration", "ammo_configuration"):
                        extra_args.append(item_database)
                    arg = field.type.from_json(arg, *extra_args)
            except ValueError as e:
                raise ValueError(f"Error in field {field.name}: {e}") from e

            kwargs[field.name] = arg

        return cls(**kwargs)

    def dangerous_settings(self) -> List[str]:
        result = []
        for field in dataclasses.fields(self):
            f = getattr(self, field.name)
            if hasattr(f, "dangerous_settings"):
                result.extend(f.dangerous_settings())

        return result
