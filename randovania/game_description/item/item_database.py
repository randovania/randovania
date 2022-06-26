from dataclasses import dataclass

from randovania.game_description.item import migrations
from randovania.game_description.item.ammo import Ammo
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.item.major_item import MajorItem
from randovania.games.game import RandovaniaGame


@dataclass(frozen=True)
class ItemDatabase:
    item_categories: dict[str, ItemCategory]
    major_items: dict[str, MajorItem]
    ammo: dict[str, Ammo]
    default_items: dict[ItemCategory, tuple[MajorItem, ...]]

    def get_item_with_name(self, name: str) -> MajorItem | Ammo:
        return self.major_items.get(name) or self.ammo.get(name)


def read_database(database_data: dict, game: RandovaniaGame) -> ItemDatabase:
    """
    :param database_data:
    :param game:
    :return:
    """
    migrations.migrate_current(database_data)

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


def write_database(database: ItemDatabase) -> dict:
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

    return {
        "schema_version": migrations.CURRENT_VERSION,
        "item_categories": item_categories,
        "items": major_items_data,
        "ammo": ammo_data,
        "default_items": default_data,
    }
