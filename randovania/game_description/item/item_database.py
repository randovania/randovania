from dataclasses import dataclass
from typing import Dict, Tuple

from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.major_item import MajorItem


@dataclass(frozen=True)
class ItemDatabase:
    major_items: Dict[str, MajorItem]
    ammo: Dict[str, Ammo]


def read_database(major_items_data: Dict,
                  ammo_data: Dict,
                  ) -> ItemDatabase:
    """

    :param major_items_data:
    :param ammo_data:
    :return:
    """
    major_items = {
        name: MajorItem.from_json(name, value)
        for name, value in major_items_data.items()
    }

    ammo = {
        name: Ammo.from_json(name, value)
        for name, value in ammo_data.items()
    }

    return ItemDatabase(major_items, ammo)


def write_database(database: ItemDatabase,
                   ) -> Tuple[Dict, Dict]:
    """

    :param database:
    :return:
    """
    major_items_data = {
        name: item.as_json
        for name, item in database.major_items.items()
    }

    ammo_data = {
        name: ammo.as_json
        for name, ammo in database.ammo.items()
    }

    return major_items_data, ammo_data


_TEMPLE_KEYS = ["Dark Agon Key", "Dark Torvus Key", "Ing Hive Key"]


def add_memo_data_keys(data: dict):
    for i in range(1, 4):
        for temple_key in _TEMPLE_KEYS:
            data["{} {}".format(temple_key, i)] = data[temple_key]

    for temple_key in _TEMPLE_KEYS:
        data.pop(temple_key)

    for i in range(1, 10):
        data["Sky Temple Key {}".format(i)] = data["Sky Temple Key"]
    data.pop("Sky Temple Key")
