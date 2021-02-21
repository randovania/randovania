from PySide2 import QtWidgets, QtCore

from randovania.game_description import default_database
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import LogbookNode, LoreType
from randovania.games.game import RandovaniaGame
from randovania.games.prime.echoes_items import DARK_TEMPLE_KEY_NAMES


def update_hints_text(game: RandovaniaGame,
                      hint_item_names_tree_widget: QtWidgets.QTableWidget,
                      ):
    item_database = default_database.item_database_for_game(game)

    rows = []

    for item in item_database.major_items.values():
        rows.append((
            item.name,
            item.item_category.hint_details[1],
            item.item_category.general_details[1],
            item.broad_category.hint_details[1],
        ))

    if game == RandovaniaGame.PRIME2:
        for dark_temple_key in DARK_TEMPLE_KEY_NAMES:
            rows.append((
                dark_temple_key.format("").strip(),
                ItemCategory.TEMPLE_KEY.hint_details[1],
                ItemCategory.TEMPLE_KEY.general_details[1],
                ItemCategory.KEY.hint_details[1],
            ))

        rows.append((
            "Sky Temple Key",
            ItemCategory.SKY_TEMPLE_KEY.hint_details[1],
            ItemCategory.SKY_TEMPLE_KEY.general_details[1],
            ItemCategory.KEY.hint_details[1],
        ))

    for item in item_database.ammo.values():
        rows.append((
            item.name,
            ItemCategory.EXPANSION.hint_details[1],
            ItemCategory.EXPANSION.general_details[1],
            item.broad_category.hint_details[1],
        ))

    hint_item_names_tree_widget.setRowCount(len(rows))
    for i, elements in enumerate(rows):
        for j, element in enumerate(elements):
            hint_item_names_tree_widget.setItem(i, j, QtWidgets.QTableWidgetItem(element))

    for i in range(4):
        hint_item_names_tree_widget.resizeColumnToContents(i)


def update_hint_locations(game: RandovaniaGame,
                          hint_tree_widget: QtWidgets.QTreeWidget):
    game_description = default_database.game_description_for(game)

    number_for_hint_type = {
        hint_type: i + 1
        for i, hint_type in enumerate(LoreType)
    }
    used_hint_types = set()

    hint_tree_widget.clear()
    hint_tree_widget.setSortingEnabled(False)

    # TODO: This ignores the Dark World names. But there's currently no logbook nodes in Dark World.
    for world in game_description.world_list.worlds:

        world_item = QtWidgets.QTreeWidgetItem(hint_tree_widget)
        world_item.setText(0, world.name)
        world_item.setExpanded(True)

        for area in world.areas:
            hint_types = {}

            for node in area.nodes:
                if isinstance(node, LogbookNode):
                    if node.required_translator is not None:
                        hint_types[node.lore_type] = node.required_translator.short_name
                    else:
                        hint_types[node.lore_type] = "✓"

            if hint_types:
                area_item = QtWidgets.QTreeWidgetItem(world_item)
                area_item.setText(0, area.name)

                for hint_type, text in hint_types.items():
                    area_item.setText(number_for_hint_type[hint_type], text)
                    used_hint_types.add(hint_type)

    hint_tree_widget.resizeColumnToContents(0)
    hint_tree_widget.setSortingEnabled(True)
    hint_tree_widget.sortByColumn(0, QtCore.Qt.AscendingOrder)

    for hint_type in used_hint_types:
        hint_tree_widget.headerItem().setText(number_for_hint_type[hint_type], hint_type.long_name)
