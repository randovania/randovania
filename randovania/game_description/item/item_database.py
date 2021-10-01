from dataclasses import dataclass
from typing import Dict, Tuple

from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.item.major_item import MajorItem
from randovania.games.game import RandovaniaGame


@dataclass(frozen=True)
class ItemDatabase:
    item_categories: Dict[str, ItemCategory]
    major_items: Dict[str, MajorItem]
    ammo: Dict[str, Ammo]
    default_items: Dict[ItemCategory, Tuple[MajorItem, ...]]


def read_database(database_data: Dict, game: RandovaniaGame) -> ItemDatabase:
    """
    :param database_data:
    :param game:
    :return:
    """
    item_categories = {
        name: ItemCategory.from_json(name, value)
        for name, value in database_data["item_categories"].items()
    }

    major_items = {
        name: MajorItem.from_json(name, value, game, item_categories)
        for name, value in database_data["items"].items()
    }

    ammo = {
        name: Ammo.from_json(name, value, game, item_categories)
        for name, value in database_data["ammo"].items()
    }

    default_items = {
        item_categories[category_name]: tuple(major_items[item_name] for item_name in value)
        for category_name, value in database_data["default_items"].items()
    }

    return ItemDatabase(item_categories, major_items, ammo, default_items)


def write_database(database: ItemDatabase) -> Dict:
    """

    :param database:
    :return:
    """
    item_categories = {
        name: item_category.as_json
        for name, item_category in database.item_categories.items()    
    }

    major_items_data = {
        name: item.as_json
        for name, item in database.major_items.items()
    }

    ammo_data = {
        name: ammo.as_json
        for name, ammo in database.ammo.items()
    }

    default_data = {
        category.name: [item.name for item in items]
        for category, items in database.default_items.items()
    }

    return {"item_categories": item_categories, "items": major_items_data, "ammo": ammo_data, "default_items": default_data}
