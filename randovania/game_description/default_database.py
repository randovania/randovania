import functools
import json
from pathlib import Path

from randovania.game_description import data_reader
from randovania.game_description.game_description import GameDescription
from randovania.game_description.item import item_database
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games import default_data
from randovania.games.game import RandovaniaGame


def resource_database_for(game: RandovaniaGame) -> ResourceDatabase:
    return game_description_for(game).resource_database


@functools.lru_cache()
def game_description_for(game: RandovaniaGame) -> GameDescription:
    result = data_reader.decode_data(default_data.read_json_then_binary(game)[1])
    if result.game != game:
        raise ValueError(f"Game Description for {game} has game field {result.game}")
    return result


def _read_item_database_in_path(path: Path, game: RandovaniaGame) -> item_database.ItemDatabase:
    with path.joinpath("item-database.json").open() as database_file:
        item_database_data = json.load(database_file)

    return item_database.read_database(item_database_data, game)


def _write_item_database_in_path(item_db: item_database.ItemDatabase, path: Path):
    data = item_database.write_database(item_db)
    with path.joinpath("item-database.json").open("w") as database_file:
        json.dump(data, database_file, indent=4)


@functools.lru_cache()
def item_database_for_game(game: RandovaniaGame):
    return _read_item_database_in_path(game.data_path.joinpath("item_database"),
                                       game)


def write_item_database_for_game(item_db: item_database, game: RandovaniaGame):
    _write_item_database_in_path(item_db, game.data_path.joinpath("item_database"))


@functools.lru_cache()
def default_prime2_memo_data() -> dict:
    with RandovaniaGame.METROID_PRIME_ECHOES.data_path.joinpath("item_database", "memo_data.json").open(
            "r") as memo_data_file:
        memo_data = json.load(memo_data_file)

    temple_keys = ["Dark Agon Key", "Dark Torvus Key", "Ing Hive Key"]

    for i in range(1, 4):
        for temple_key in temple_keys:
            memo_data["{} {}".format(temple_key, i)] = memo_data[temple_key]

    for temple_key in temple_keys:
        memo_data.pop(temple_key)

    for i in range(1, 10):
        memo_data["Sky Temple Key {}".format(i)] = memo_data["Sky Temple Key"]
    memo_data.pop("Sky Temple Key")

    return memo_data
