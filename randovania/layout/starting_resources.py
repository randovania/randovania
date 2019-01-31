from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Dict, Union, List

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder, BitPackEnum
from randovania.game_description import default_database
from randovania.game_description.resources import SimpleResourceInfo, ResourceGain

_vanilla_item_loss_enabled_items = {
    0: 1,  # Power Beam
    8: 1,  # Combat Visor
    9: 1,  # Scan Visor
    12: 1,  # Varia Suit
    15: 1,  # Morph Ball
    22: 1,  # Charge Beam
}

_vanilla_item_loss_disabled_items: Dict[int, int] = {
    0: 1,  # Power Beam
    8: 1,  # Combat Visor
    9: 1,  # Scan Visor
    12: 1,  # Varia Suit
    15: 1,  # Morph Ball
    16: 1,  # Boost Ball
    17: 1,  # Spider Ball
    18: 1,  # Morph Ball Bomb
    22: 1,  # Charge Beam
    24: 1,  # Space Jump Boots
    44: 5,  # Missile
}

_items_with_custom_maximum = {
    42: 12,  # Energy Tank
    43: 10,  # Power Bomb
    44: 255,  # Missile
    45: 250,  # Dark Ammo
    46: 250,  # Light Ammo
}


class StartingResourcesConfiguration(BitPackEnum, Enum):
    VANILLA_ITEM_LOSS_ENABLED = "vanilla-item-loss-enabled"
    VANILLA_ITEM_LOSS_DISABLED = "vanilla-item-loss-disabled"
    CUSTOM = "custom"


_reference_starting_equipment = {
    StartingResourcesConfiguration.VANILLA_ITEM_LOSS_ENABLED: _vanilla_item_loss_enabled_items,
    StartingResourcesConfiguration.VANILLA_ITEM_LOSS_DISABLED: _vanilla_item_loss_disabled_items,
}


@dataclass(frozen=True)
class StartingResources(BitPackValue):
    """
    This class contains configuration for what items you chose to start the game with, no random involved.
    """
    configuration: StartingResourcesConfiguration
    _resources: Dict[SimpleResourceInfo, int]

    def __post_init__(self):
        database = default_database.default_prime2_resource_database()
        missing_items = [item.long_name for item in database.item if item not in self._resources]
        if missing_items:
            raise ValueError("resources {} has missing items: {}".format(
                self._resources, missing_items
            ))

        for item, quantity in self._resources.items():
            maximum = _items_with_custom_maximum.get(item.index, 1)
            if quantity > maximum:
                raise ValueError("Item {} has a maximum of {}, got {}".format(item, maximum, quantity))

    def bit_pack_format(self) -> Iterator[int]:
        yield from self.configuration.bit_pack_format()

        if self.configuration == StartingResourcesConfiguration.CUSTOM:
            database = default_database.default_prime2_resource_database()
            for item in database.item:
                yield _items_with_custom_maximum.get(item.index, 1) + 1

    def bit_pack_arguments(self) -> Iterator[int]:
        yield from self.configuration.bit_pack_arguments()

        if self.configuration == StartingResourcesConfiguration.CUSTOM:
            database = default_database.default_prime2_resource_database()
            for item in database.item:
                yield self._resources[item]

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder) -> "StartingResources":
        configuration = StartingResourcesConfiguration.bit_pack_unpack(decoder)

        if configuration != StartingResourcesConfiguration.CUSTOM:
            return cls.from_non_custom_configuration(configuration)

        database = default_database.default_prime2_resource_database()

        items = {}
        for item in database.item:
            maximum = _items_with_custom_maximum.get(item.index, 1)
            items[item] = decoder.decode(maximum + 1)[0]

        return cls(configuration, items)

    @classmethod
    def from_non_custom_configuration(cls, configuration: StartingResourcesConfiguration) -> "StartingResources":
        if configuration == StartingResourcesConfiguration.CUSTOM:
            raise ValueError("from_non_custom_configuration shouldn't receive CUSTOM configuration")

        reference_items = _reference_starting_equipment[configuration]
        database = default_database.default_prime2_resource_database()

        items = {}
        for item in database.item:
            items[item] = reference_items.get(item.index, 0)

        return cls(configuration, items)

    @classmethod
    def from_item_loss(cls, item_loss_enabled: bool) -> "StartingResources":
        if item_loss_enabled:
            resource_config = StartingResourcesConfiguration.VANILLA_ITEM_LOSS_ENABLED
        else:
            resource_config = StartingResourcesConfiguration.VANILLA_ITEM_LOSS_DISABLED
        return cls.from_non_custom_configuration(resource_config)

    @classmethod
    def default(cls) -> "StartingResources":
        return cls.from_non_custom_configuration(StartingResourcesConfiguration.VANILLA_ITEM_LOSS_ENABLED)

    @property
    def as_json(self) -> Union[str, List[int]]:
        if self.configuration != StartingResourcesConfiguration.CUSTOM:
            return self.configuration.value
        else:
            return list(self._resources.values())

    @classmethod
    def from_json(cls, value: Union[str, List[int]]) -> "StartingResources":
        if isinstance(value, str):
            return cls.from_non_custom_configuration(StartingResourcesConfiguration(value))
        else:
            database = default_database.default_prime2_resource_database()
            return cls(StartingResourcesConfiguration.CUSTOM, dict(zip(database.item, value)))

    @property
    def resource_gain(self) -> ResourceGain:
        yield from self._resources.items()
