import json
from typing import Tuple

from randovania import get_data_path
from randovania.game_description.default_database import default_prime2_item_database
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.major_items_configuration import MajorItemsConfiguration


def get_major_items_configurations_for(mode: str) -> MajorItemsConfiguration:
    item_database = default_prime2_item_database()

    with get_data_path().joinpath("json_data", "configurations", "vanilla.json").open() as open_file:
        data = json.load(open_file)

    return MajorItemsConfiguration.from_json(data["major_items"], item_database)


def get_ammo_configurations_for(mode: str) -> AmmoConfiguration:
    item_database = default_prime2_item_database()

    with get_data_path().joinpath("json_data", "configurations", "vanilla.json").open() as open_file:
        data = json.load(open_file)

    return AmmoConfiguration.from_json(data["ammo"], item_database)
