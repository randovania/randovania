import functools
import json
from pathlib import Path

from randovania import get_data_path
from randovania.game_description import data_reader
from randovania.game_description.data_reader import read_resource_database
from randovania.game_description.game_description import GameDescription
from randovania.game_description.item import item_database
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.game import RandovaniaGame
from randovania.games.prime import default_data


def default_prime2_game_description() -> GameDescription:
    return game_description_for(RandovaniaGame.PRIME2)


@functools.lru_cache()
def resource_database_for(game: RandovaniaGame) -> ResourceDatabase:
    return read_resource_database(default_data.read_json_then_binary(game)[1]["resource_database"])


def game_description_for(game: RandovaniaGame) -> GameDescription:
    return data_reader.decode_data(default_data.read_json_then_binary(game)[1])


def _read_database_in_path(path: Path) -> item_database.ItemDatabase:
    configuration_path = path.joinpath("configuration")

    with configuration_path.joinpath("major-items.json").open() as major_items_file:
        major_items_data = json.load(major_items_file)

    with configuration_path.joinpath("ammo.json").open() as ammo_file:
        ammo_data = json.load(ammo_file)

    return item_database.read_database(major_items_data, ammo_data)


@functools.lru_cache()
def default_prime1_item_database() -> item_database.ItemDatabase:
    return _read_database_in_path(get_data_path().joinpath("item_database", "prime1"))


@functools.lru_cache()
def default_prime2_item_database() -> item_database.ItemDatabase:
    return _read_database_in_path(get_data_path().joinpath("item_database", "prime2"))


@functools.lru_cache()
def default_prime3_item_database() -> item_database.ItemDatabase:
    return _read_database_in_path(get_data_path().joinpath("item_database", "prime3"))


def item_database_for_game(game: RandovaniaGame):
    if game == RandovaniaGame.PRIME1:
        return default_prime1_item_database()
    elif game == RandovaniaGame.PRIME2:
        return default_prime2_item_database()
    elif game == RandovaniaGame.PRIME3:
        return default_prime3_item_database()
    else:
        raise ValueError(f"Unknown game: {game}")


@functools.lru_cache()
def default_prime2_memo_data() -> dict:
    with get_data_path().joinpath("item_database", "prime2", "memo_data.json").open("r") as memo_data_file:
        memo_data = json.load(memo_data_file)

    item_database.add_memo_data_keys(memo_data)

    return memo_data
