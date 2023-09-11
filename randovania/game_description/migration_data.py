from __future__ import annotations

import functools

from randovania.games.game import RandovaniaGame
from randovania.lib import json_lib


@functools.lru_cache
def get_raw_data(game: RandovaniaGame) -> dict:
    return json_lib.read_dict(game.data_path.joinpath("assets", "migration_data.json"))


@functools.lru_cache
def _get_id_to_world_name_mapping(game: RandovaniaGame) -> dict[int, str]:
    world_name_to_id = get_raw_data(game)["world_name_to_id"]
    return {asset_id: name for name, asset_id in world_name_to_id.items()}


@functools.lru_cache
def _get_id_to_area_name_mapping(game: RandovaniaGame, world_name: str) -> dict[int, str]:
    area_name_to_id = get_raw_data(game)["area_name_to_id"][world_name]
    return {asset_id: name for name, asset_id in area_name_to_id.items()}


def get_world_name_from_id(game: RandovaniaGame, asset_id: int) -> str:
    return _get_id_to_world_name_mapping(game)[asset_id]


def get_area_name_from_id(game: RandovaniaGame, world_name: str, asset_id: int) -> str:
    return _get_id_to_area_name_mapping(game, world_name)[asset_id]


def convert_area_loc_id_to_name(game: RandovaniaGame, loc: dict[str, int]) -> dict[str, str]:
    world_name = get_world_name_from_id(game, loc["world_asset_id"])
    return {
        "world_name": world_name,
        "area_name": get_area_name_from_id(game, world_name, loc["area_asset_id"]),
    }


def get_teleporter_area_to_node_mapping() -> dict[str, str]:
    result = {}
    for g in [
        RandovaniaGame.METROID_PRIME,
        RandovaniaGame.METROID_PRIME_ECHOES,
        RandovaniaGame.METROID_PRIME_CORRUPTION,
    ]:
        result.update(get_raw_data(g)["teleporter_mapping"])
    return result


def get_node_name_for_area(game: str, world_name: str, area_name: str) -> str:
    mapping = get_raw_data(RandovaniaGame(game))["start_node_per_area"][world_name]
    return mapping[area_name]


def get_default_dock_lock_settings(game: RandovaniaGame) -> dict:
    return get_raw_data(game)["default_dock_lock_settings"]
