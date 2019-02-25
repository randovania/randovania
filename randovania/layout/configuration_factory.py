import json
from enum import Enum

from randovania import get_data_path
from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.game_description.default_database import default_prime2_item_database
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.major_items_configuration import MajorItemsConfiguration


class MajorItemsConfigEnum(BitPackEnum, Enum):
    DEFAULT = "default"
    VANILLA = "vanilla"

    @classmethod
    def default(cls) -> "MajorItemsConfigEnum":
        return cls.DEFAULT


class AmmoConfigEnum(BitPackEnum, Enum):
    SPLIT_AMMO = "split-ammo"
    VANILLA = "vanilla"

    @classmethod
    def default(cls) -> "AmmoConfigEnum":
        return cls.SPLIT_AMMO


def get_major_items_configurations_for(mode: MajorItemsConfigEnum) -> MajorItemsConfiguration:
    item_database = default_prime2_item_database()

    with get_data_path().joinpath("json_data", "configurations", "major_items",
                                  "{}.json".format(mode.value)).open() as open_file:
        data = json.load(open_file)

    return MajorItemsConfiguration.from_json(data, item_database)


def get_ammo_configurations_for(mode: AmmoConfigEnum) -> AmmoConfiguration:
    item_database = default_prime2_item_database()

    with get_data_path().joinpath("json_data", "configurations", "ammo",
                                  "{}.json".format(mode.value)).open() as open_file:
        data = json.load(open_file)

    return AmmoConfiguration.from_json(data, item_database)
