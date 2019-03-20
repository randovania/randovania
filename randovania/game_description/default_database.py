import functools
import json

from randovania import get_data_path
from randovania.game_description import data_reader
from randovania.game_description.data_reader import read_resource_database
from randovania.game_description.game_description import GameDescription
from randovania.game_description.item import item_database
from randovania.game_description.resources import ResourceDatabase
from randovania.games.prime import default_data


@functools.lru_cache()
def default_prime2_resource_database() -> ResourceDatabase:
    return read_resource_database(default_data.decode_default_prime2()["resource_database"])


def default_prime2_game_description(add_self_as_requirement_to_resources: bool = True,
                                    ) -> GameDescription:
    return data_reader.decode_data(default_data.decode_default_prime2(), add_self_as_requirement_to_resources)


@functools.lru_cache()
def default_prime2_item_database() -> item_database.ItemDatabase:
    configuration_path = get_data_path().joinpath("item_database", "configuration")

    with configuration_path.joinpath("major-items.json").open() as major_items_file:
        major_items_data = json.load(major_items_file)

    with configuration_path.joinpath("ammo.json").open() as ammo_file:
        ammo_data = json.load(ammo_file)

    return item_database.read_database(major_items_data, ammo_data)


@functools.lru_cache()
def default_prime2_memo_data() -> dict:
    with get_data_path().joinpath("item_database", "memo_data.json").open("r") as memo_data_file:
        memo_data = json.load(memo_data_file)

    item_database.add_memo_data_keys(memo_data)

    return memo_data
