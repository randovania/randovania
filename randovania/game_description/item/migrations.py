from randovania.game_description import migration_data
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.game import RandovaniaGame
from randovania.lib import migration_lib

CURRENT_VERSION = 3


def _migrate_v1(data: dict) -> dict:
    game = RandovaniaGame(data["game"])
    for item in data["items"].values():
        item["progression"] = [migration_data.get_resource_name_from_index(game, progression, ResourceType.ITEM) for
                               progression in item["progression"]]
        ammo = item.get("ammo")
        if ammo is not None:
            item["ammo"] = [migration_data.get_resource_name_from_index(game, ammo, ResourceType.ITEM) for ammo in
                            item["ammo"]]
    for ammo in data["ammo"].values():
        ammo["items"] = [migration_data.get_resource_name_from_index(game, item, ResourceType.ITEM) for item in
                         ammo["items"]]
        unlock = ammo.get("unlocked_by")
        if unlock is not None:
            ammo["unlocked_by"] = migration_data.get_resource_name_from_index(game, ammo["unlocked_by"],
                                                                              ResourceType.ITEM)
        temporary = ammo.get("temporary")
        if temporary is not None:
            ammo["temporary"] = migration_data.get_resource_name_from_index(game, ammo["temporary"], ResourceType.ITEM)
    return data


def _migrate_v2(data: dict) -> dict:

    for item in data["items"].values():
        item["must_be_starting"] = item["hide_from_gui"] = item.pop("required")

    return data


_MIGRATIONS = {
    1: _migrate_v1,
    2: _migrate_v2,
}


def migrate_current(data: dict):
    return migration_lib.migrate_to_version(data, CURRENT_VERSION, _MIGRATIONS)
