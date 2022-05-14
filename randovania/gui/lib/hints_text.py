import collections

from PySide6 import QtWidgets, QtCore

from randovania.game_description import default_database
from randovania.game_description.world.logbook_node import LogbookNode
from randovania.games.game import RandovaniaGame
from randovania.generator.item_pool import pickup_creator


def prime1_hint_text():
    db = default_database.resource_database_for(RandovaniaGame.METROID_PRIME)
    artifact = pickup_creator.create_artifact(0, 0, db)

    result = [(
        "Artifact",
        artifact.item_category,
        artifact.broad_category,
    )]
    return result


def prime2_hint_text():
    db = default_database.resource_database_for(RandovaniaGame.METROID_PRIME_ECHOES)

    result = []

    for temple in range(3):
        key = pickup_creator.create_dark_temple_key(0, temple, db)
        result.append((
            key.name.replace(" 1", "").strip(),
            key.item_category,
            key.broad_category,
        ))

    key = pickup_creator.create_sky_temple_key(0, db)
    result.append((
        "Sky Temple Key",
        key.item_category,
        key.broad_category,
    ))

    return result


def prime3_hint_text():
    db = default_database.resource_database_for(RandovaniaGame.METROID_PRIME_CORRUPTION)
    cell = pickup_creator.create_energy_cell(0, db)

    result = [(
        "Energy Cell",
        cell.item_category,
        cell.broad_category,
    )]
    return result


_GAME_SPECIFIC = {
    RandovaniaGame.METROID_PRIME: prime1_hint_text,
    RandovaniaGame.METROID_PRIME_ECHOES: prime2_hint_text,
    RandovaniaGame.METROID_PRIME_CORRUPTION: prime3_hint_text,
}


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

    for name, item_category, broad_category in _GAME_SPECIFIC.get(game, lambda: [])():
        rows.append((
            name,
            item_category.hint_details[1],
            item_category.general_details[1],
            broad_category.hint_details[1],
        ))

    for ammo in item_database.ammo.values():
        rows.append((
            ammo.name,
            ammo.item_category.hint_details[1],
            ammo.item_category.general_details[1],
            ammo.broad_category.hint_details[1],
        ))

    hint_item_names_tree_widget.setSortingEnabled(False)
    hint_item_names_tree_widget.setRowCount(len(rows))
    for i, elements in enumerate(rows):
        for j, element in enumerate(elements):
            hint_item_names_tree_widget.setItem(i, j, QtWidgets.QTableWidgetItem(element))

    for i in range(4):
        hint_item_names_tree_widget.resizeColumnToContents(i)

    hint_item_names_tree_widget.setSortingEnabled(True)


def update_hint_locations(game: RandovaniaGame,
                          hint_tree_widget: QtWidgets.QTreeWidget):
    game_description = default_database.game_description_for(game)

    used_hint_types = set()

    hint_tree_widget.clear()
    hint_tree_widget.setSortingEnabled(False)

    hint_type_tree = collections.defaultdict(dict)

    # First figure out which areas uses what hints.
    # This lets us use detect which hint types are used
    for world in game_description.world_list.worlds:
        for area in world.areas:
            hint_types = {}

            for node in area.nodes:
                if isinstance(node, LogbookNode):
                    used_hint_types.add(node.lore_type)
                    if node.required_translator is not None:
                        hint_types[node.lore_type] = node.required_translator.short_name
                    else:
                        hint_types[node.lore_type] = "✓"

            if hint_types:
                hint_type_tree[world.correct_name(area.in_dark_aether)][area.name] = hint_types

    number_for_hint_type = {
        hint_type: i + 1
        for i, hint_type in enumerate(sorted(used_hint_types, key=lambda it: it.long_name))
    }

    for world_name, area_hints in hint_type_tree.items():
        world_item = QtWidgets.QTreeWidgetItem(hint_tree_widget)
        world_item.setText(0, world_name)
        world_item.setExpanded(True)

        for area_name, hint_types in area_hints.items():
            area_item = QtWidgets.QTreeWidgetItem(world_item)
            area_item.setText(0, area_name)

            for hint_type, text in hint_types.items():
                area_item.setText(number_for_hint_type[hint_type], text)
                used_hint_types.add(hint_type)

    hint_tree_widget.resizeColumnToContents(0)
    hint_tree_widget.setSortingEnabled(True)
    hint_tree_widget.sortByColumn(0, QtCore.Qt.AscendingOrder)

    for hint_type in used_hint_types:
        hint_tree_widget.headerItem().setText(number_for_hint_type[hint_type], hint_type.long_name)
