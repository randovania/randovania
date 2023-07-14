from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from randovania.game_description import data_reader
from randovania.game_description.pickup import pickup_database
from randovania.games import default_data
from randovania.games.game import RandovaniaGame
from randovania.lib import json_lib

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.resource_database import ResourceDatabase


def resource_database_for(game: RandovaniaGame) -> ResourceDatabase:
    return game_description_for(game).resource_database


@functools.lru_cache
def game_description_for(game: RandovaniaGame) -> GameDescription:
    result = data_reader.decode_data(default_data.read_json_then_binary(game)[1])
    if result.game != game:
        raise ValueError(f"Game Description for {game} has game field {result.game}")
    return result


def _read_pickup_database_in_path(path: Path, game: RandovaniaGame) -> pickup_database.PickupDatabase:
    pickup_database_data = json_lib.read_path(path.joinpath("pickup-database.json"))
    return pickup_database.read_database(pickup_database_data, game)


def _write_pickup_database_in_path(pickup_db: pickup_database.PickupDatabase, path: Path):
    data = pickup_database.write_database(pickup_db)
    path.mkdir(parents=True, exist_ok=True)
    json_lib.write_path(path.joinpath("pickup-database.json"), data)


@functools.lru_cache
def pickup_database_for_game(game: RandovaniaGame):
    return _read_pickup_database_in_path(game.data_path.joinpath("pickup_database"),
                                         game)


def write_pickup_database_for_game(pickup_db: pickup_database.PickupDatabase, game: RandovaniaGame):
    _write_pickup_database_in_path(pickup_db, game.data_path.joinpath("pickup_database"))


@functools.lru_cache
def default_prime2_memo_data() -> dict:
    memo_data = json_lib.read_path(
        RandovaniaGame.METROID_PRIME_ECHOES.data_path.joinpath("pickup_database", "memo_data.json")
    )

    temple_keys = ["Dark Agon Key", "Dark Torvus Key", "Ing Hive Key"]

    for i in range(1, 4):
        for temple_key in temple_keys:
            memo_data[f"{temple_key} {i}"] = memo_data[temple_key]

    for temple_key in temple_keys:
        memo_data.pop(temple_key)

    for i in range(1, 10):
        memo_data[f"Sky Temple Key {i}"] = memo_data["Sky Temple Key"]
    memo_data.pop("Sky Temple Key")

    return memo_data
