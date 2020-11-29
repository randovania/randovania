import dataclasses
from enum import Enum
from typing import List

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataClass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_description import default_database
from randovania.games.game import RandovaniaGame
from randovania.games.prime import default_data
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.available_locations import AvailableLocationsConfiguration, RandomizationMode
from randovania.layout.beam_configuration import BeamConfiguration
from randovania.layout.damage_strictness import LayoutDamageStrictness
from randovania.layout.elevators import LayoutElevators
from randovania.layout.hint_configuration import HintConfiguration
from randovania.layout.major_items_configuration import MajorItemsConfiguration
from randovania.layout.pickup_model import PickupModelStyle, PickupModelDataSource
from randovania.layout.starting_location import StartingLocation
from randovania.layout.translator_configuration import TranslatorConfiguration
from randovania.layout.trick_level import TrickLevelConfiguration


class LayoutSkyTempleKeyMode(BitPackEnum, Enum):
    ALL_BOSSES = "all-bosses"
    ALL_GUARDIANS = "all-guardians"
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9

    @classmethod
    def default(cls) -> "LayoutSkyTempleKeyMode":
        return cls.NINE

    @property
    def num_keys(self):
        if self == self.ALL_BOSSES:
            return 9
        elif self == self.ALL_GUARDIANS:
            return 3
        else:
            return self.value


@dataclasses.dataclass(frozen=True)
class LayoutSafeZone(BitPackDataClass, JsonDataclass):
    fully_heal: bool
    prevents_dark_aether: bool
    heal_per_second: float = dataclasses.field(metadata={"min": 0.0, "max": 100.0,
                                                         "if_different": 1.0, "precision": 1.0})


@dataclasses.dataclass(frozen=True)
class EchoesConfiguration(BitPackDataClass, JsonDataclass):
    game: RandovaniaGame
    trick_level: TrickLevelConfiguration
    starting_location: StartingLocation
    available_locations: AvailableLocationsConfiguration
    major_items_configuration: MajorItemsConfiguration
    ammo_configuration: AmmoConfiguration
    damage_strictness: LayoutDamageStrictness
    pickup_model_style: PickupModelStyle
    pickup_model_data_source: PickupModelDataSource

    elevators: LayoutElevators
    sky_temple_keys: LayoutSkyTempleKeyMode
    translator_configuration: TranslatorConfiguration
    hints: HintConfiguration
    beam_configuration: BeamConfiguration
    skip_final_bosses: bool
    energy_per_tank: float = dataclasses.field(metadata={"min": 1.0, "max": 1000.0, "precision": 1.0})
    safe_zone: LayoutSafeZone
    menu_mod: bool
    warp_to_start: bool
    varia_suit_damage: float = dataclasses.field(metadata={"min": 0.0, "max": 60.0, "precision": 2.0})
    dark_suit_damage: float = dataclasses.field(metadata={"min": 0.0, "max": 60.0, "precision": 2.0})

    @property
    def game_data(self) -> dict:
        return default_data.read_json_then_binary(self.game)[1]

    @classmethod
    def from_json(cls, json_dict: dict) -> "EchoesConfiguration":
        game = RandovaniaGame(json_dict["game"])
        item_database = default_database.item_database_for_game(game)

        kwargs = {}
        for field in dataclasses.fields(cls):
            arg = json_dict[field.name]
            if issubclass(field.type, Enum):
                arg = field.type(arg)
            elif hasattr(field.type, "from_json"):
                extra_args = []
                if field.name in ("trick_level", "starting_location"):
                    extra_args.append(game)
                if field.name in ("major_items_configuration", "ammo_configuration"):
                    extra_args.append(item_database)
                arg = field.type.from_json(arg, *extra_args)

            kwargs[field.name] = arg

        return EchoesConfiguration(**kwargs)

    def dangerous_settings(self) -> List[str]:
        result = []
        for field in dataclasses.fields(self):
            f = getattr(self, field.name)
            if hasattr(f, "dangerous_settings"):
                result.extend(f.dangerous_settings())

        if self.elevators == LayoutElevators.ONE_WAY_ANYTHING:
            result.append("One-way anywhere elevators")

        return result
