import functools
import json

from randovania import get_data_path
from randovania.games.game import RandovaniaGame


@functools.lru_cache
def get_raw_data():
    p = get_data_path().joinpath("migration_data.json")
    with p.open() as f:
        return json.load(f)


def get_world_name_to_id_mapping(game: RandovaniaGame) -> dict[str, int]:
    return get_raw_data()[game.value]["world_name_to_id"]


def get_id_to_world_name_mapping(game: RandovaniaGame) -> dict[int, str]:
    return {
        asset_id: name
        for name, asset_id in get_world_name_to_id_mapping(game).items()
    }


def get_world_name_from_id(game: RandovaniaGame, asset_id: int) -> str:
    return get_id_to_world_name_mapping(game)[asset_id]


def get_area_name_to_id_mapping(game: RandovaniaGame, world_name: str) -> dict[str, int]:
    return get_raw_data()[game.value]["area_name_to_id"][world_name]


def get_id_to_area_name_mapping(game: RandovaniaGame, world_name: str) -> dict[int, str]:
    return {
        asset_id: name
        for name, asset_id in get_area_name_to_id_mapping(game, world_name).items()
    }


def get_area_name_from_id(game: RandovaniaGame, world_name: str, asset_id: int) -> str:
    return get_id_to_area_name_mapping(game, world_name)[asset_id]


def convert_area_loc_id_to_name(game: RandovaniaGame, loc: dict[str, int]) -> dict[str, str]:
    world_name = get_world_name_from_id(game, loc["world_asset_id"])
    return {
        "world_name": world_name,
        "area_name": get_area_name_from_id(game, world_name, loc["area_asset_id"]),
    }


def get_teleporter_area_to_node_mapping() -> dict[str, str]:
    return get_raw_data()["teleporter_mapping"]
