from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Optional, Union, Tuple

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder, BitPackEnum
from randovania.game_description import default_database
from randovania.game_description.area_location import AreaLocation


class StartingLocationConfiguration(BitPackEnum, Enum):
    SHIP = "ship"
    RANDOM_SAVE_STATION = "random-save-station"
    CUSTOM = "custom"


def _areas_list():
    world_list = default_database.default_prime2_game_description(False).world_list
    return world_list, list(world_list.all_areas)


@dataclass(frozen=True)
class StartingLocation(BitPackValue):
    configuration: StartingLocationConfiguration
    _custom_location: Optional[AreaLocation]

    def __post_init__(self):
        if self._custom_location is None:
            if self.configuration == StartingLocationConfiguration.CUSTOM:
                raise ValueError("Configuration is CUSTOM, but not custom_location set")
        else:
            if self.configuration != StartingLocationConfiguration.CUSTOM:
                raise ValueError("custom_location set to {}, but configuration is {} instead of CUSTOM".format(
                    self._custom_location, str(self.configuration)
                ))

    def bit_pack_encode(self) -> Iterator[Tuple[int, int]]:
        yield from self.configuration.bit_pack_encode()

        if self._custom_location is not None:
            world_list, areas = _areas_list()
            area = world_list.area_by_area_location(self._custom_location)

            yield areas.index(area), len(areas)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder) -> "StartingLocation":
        configuration = StartingLocationConfiguration.bit_pack_unpack(decoder)
        location = None

        if configuration == StartingLocationConfiguration.CUSTOM:
            world_list, areas = _areas_list()

            area_index = decoder.decode(len(areas))[0]
            area = areas[area_index]

            location = AreaLocation(world_list.world_with_area(area).world_asset_id,
                                    area.area_asset_id)

        return cls(configuration, location)

    @classmethod
    def default(cls) -> "StartingLocation":
        return cls(StartingLocationConfiguration.SHIP, None)

    @property
    def as_json(self) -> Union[str, dict]:
        if self.configuration != StartingLocationConfiguration.CUSTOM:
            return self.configuration.value
        else:
            return self._custom_location.as_json

    @classmethod
    def from_json(cls, value: Union[str, dict]) -> "StartingLocation":
        if isinstance(value, str):
            return cls(StartingLocationConfiguration(value), None)
        else:
            return cls(StartingLocationConfiguration.CUSTOM, AreaLocation.from_json(value))

    @property
    def custom_location(self) -> AreaLocation:
        if self.configuration != StartingLocationConfiguration.CUSTOM:
            raise ValueError("Attempting to use custom_location of a non-CUSTOM location")
        return self._custom_location
