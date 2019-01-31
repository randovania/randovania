from dataclasses import dataclass
from enum import Enum
from typing import Dict

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataClass
from randovania.game_description.resources import PickupEntry
from randovania.games.prime import default_data
from randovania.layout.pickup_quantities import PickupQuantities
from randovania.layout.starting_location import StartingLocation
from randovania.layout.starting_resources import StartingResources


class LayoutTrickLevel(BitPackEnum, Enum):
    NO_TRICKS = "no-tricks"
    TRIVIAL = "trivial"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    HYPERMODE = "hypermode"
    MINIMAL_RESTRICTIONS = "minimal-restrictions"


class LayoutSkyTempleKeyMode(BitPackEnum, Enum):
    VANILLA = "vanilla"
    ALL_BOSSES = "all-bosses"
    ALL_GUARDIANS = "all-guardians"
    FULLY_RANDOM = "fully-random"


class LayoutRandomizedFlag(BitPackEnum, Enum):
    VANILLA = "vanilla"
    RANDOMIZED = "randomized"


@dataclass(frozen=True)
class LayoutConfiguration(BitPackDataClass):
    trick_level: LayoutTrickLevel
    sky_temple_keys: LayoutSkyTempleKeyMode
    elevators: LayoutRandomizedFlag
    pickup_quantities: PickupQuantities
    starting_location: StartingLocation
    starting_resources: StartingResources

    def quantity_for_pickup(self, pickup: PickupEntry) -> int:
        return self.pickup_quantities.get(pickup)

    @property
    def game_data(self) -> dict:
        return default_data.decode_default_prime2()

    @property
    def as_json(self) -> dict:
        return {
            "game": "mp2-echoes",
            "trick_level": self.trick_level.value,
            "sky_temple_keys": self.sky_temple_keys.value,
            "elevators": self.elevators.value,
            "pickup_quantities": self.pickup_quantities.as_json,
            "starting_location": self.starting_location.as_json,
            "starting_resources": self.starting_resources.as_json,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutConfiguration":
        return cls.from_params(
            trick_level=LayoutTrickLevel(json_dict["trick_level"]),
            sky_temple_keys=LayoutSkyTempleKeyMode(json_dict["sky_temple_keys"]),
            elevators=LayoutRandomizedFlag(json_dict["elevators"]),
            pickup_quantities=json_dict["pickup_quantities"],
            starting_location=StartingLocation.from_json(json_dict["starting_location"]),
            starting_resources=StartingResources.from_json(json_dict["starting_resources"]),
        )

    @classmethod
    def from_params(cls,
                    trick_level: LayoutTrickLevel,
                    sky_temple_keys: LayoutSkyTempleKeyMode,
                    elevators: LayoutRandomizedFlag,
                    pickup_quantities: Dict[str, int],
                    starting_location: StartingLocation,
                    starting_resources: StartingResources,
                    ) -> "LayoutConfiguration":
        return LayoutConfiguration(
            trick_level=trick_level,
            sky_temple_keys=sky_temple_keys,
            elevators=elevators,
            pickup_quantities=PickupQuantities.from_params(pickup_quantities),
            starting_location=starting_location,
            starting_resources=starting_resources,
        )

    @classmethod
    def default(cls) -> "LayoutConfiguration":
        return cls.from_params(
            trick_level=LayoutTrickLevel.NO_TRICKS,
            sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
            elevators=LayoutRandomizedFlag.VANILLA,
            pickup_quantities={},
            starting_location=StartingLocation.default(),
            starting_resources=StartingResources.default(),
        )
