import json

from randovania import get_data_path
from randovania.game_description.default_database import default_prime2_item_database
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.major_item_state import MajorItemState
from randovania.layout.major_items_configuration import MajorItemsConfiguration


def get_default_major_items_configurations() -> MajorItemsConfiguration:
    item_database = default_prime2_item_database()

    with get_data_path().joinpath("item_database", "default_state", "major-items.json").open() as open_file:
        data = json.load(open_file)

    return MajorItemsConfiguration(
        items_state={
            item_database.major_items[name]: MajorItemState.from_json(state_data)
            for name, state_data in data["items_state"].items()
        }
    )


def get_default_ammo_configurations() -> AmmoConfiguration:
    item_database = default_prime2_item_database()

    with get_data_path().joinpath("item_database", "default_state", "ammo.json").open() as open_file:
        data = json.load(open_file)

    return AmmoConfiguration.from_json(data, item_database)
