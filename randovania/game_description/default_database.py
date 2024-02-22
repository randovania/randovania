from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from randovania.game_description import data_reader
from randovania.game_description.pickup import pickup_database
from randovania.games import default_data
from randovania.lib import json_lib

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.games.game import RandovaniaGame


def resource_database_for(game: RandovaniaGame) -> ResourceDatabase:
    return game_description_for(game).resource_database


@functools.lru_cache
def game_description_for(game: RandovaniaGame) -> GameDescription:
    result = data_reader.decode_data(default_data.read_json_then_binary(game)[1])
    if result.game != game:
        raise ValueError(f"Game Description for {game} has game field {result.game}")
    return result


def _read_pickup_database_in_path(path: Path, game: RandovaniaGame) -> pickup_database.PickupDatabase:
    pickup_database_data = json_lib.read_dict(path.joinpath("pickup-database.json"))
    return pickup_database.read_database(pickup_database_data, game)


def _write_pickup_database_in_path(pickup_db: pickup_database.PickupDatabase, path: Path) -> None:
    data = pickup_database.write_database(pickup_db)
    path.mkdir(parents=True, exist_ok=True)
    json_lib.write_path(path.joinpath("pickup-database.json"), data)


@functools.lru_cache
def pickup_database_for_game(game: RandovaniaGame) -> pickup_database.PickupDatabase:
    return _read_pickup_database_in_path(game.data_path.joinpath("pickup_database"), game)


def write_pickup_database_for_game(pickup_db: pickup_database.PickupDatabase, game: RandovaniaGame) -> None:
    _write_pickup_database_in_path(pickup_db, game.data_path.joinpath("pickup_database"))
