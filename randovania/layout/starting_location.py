from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Optional, Union

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder, BitPackEnum
from randovania.game_description.area_location import AreaLocation


class StartingLocationConfiguration(BitPackEnum, Enum):
    SHIP = "ship"
    RANDOM_SAVE_STATION = "random-save-station"
    CUSTOM = "custom"


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
                    self._custom_location, self.configuration
                ))

    def bit_pack_format(self) -> Iterator[int]:
        yield from self.configuration.bit_pack_format()
        # TODO: pack the custom location

    def bit_pack_arguments(self) -> Iterator[int]:
        yield from self.configuration.bit_pack_arguments()
        # TODO: pack the custom location

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder) -> "StartingLocation":
        configuration = StartingLocationConfiguration.bit_pack_unpack(decoder)
        # TODO: unpack the custom location
        return cls(configuration, None)

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

