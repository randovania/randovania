from __future__ import annotations

import collections

from PySide6 import QtCore, QtWidgets

from randovania.game_description import default_database
from randovania.game_description.db.hint_node import HintNode
from randovania.games.game import RandovaniaGame


def prime1_hint_text():
    db = default_database.resource_database_for(RandovaniaGame.METROID_PRIME)
    from randovania.games.prime1.generator.pickup_pool import artifacts

    artifact = artifacts.create_artifact(0, 0, db)

    result = [
        (
            "Artifact",
            artifact.pickup_category,
            artifact.broad_category,
        )
    ]
    return result


def prime2_hint_text():
    from randovania.games.prime2.generator.pickup_pool import dark_temple_keys, sky_temple_keys

    db = default_database.resource_database_for(RandovaniaGame.METROID_PRIME_ECHOES)

    result = []

    for temple in range(3):
        key = dark_temple_keys.create_dark_temple_key(0, temple, db)
        result.append(
            (
                key.name.replace(" 1", "").strip(),
                key.pickup_category,
                key.broad_category,
            )
        )

    key = sky_temple_keys.create_sky_temple_key(0, db)
    result.append(
        (
            "Sky Temple Key",
            key.pickup_category,
            key.broad_category,
        )
    )

    return result


def prime3_hint_text():
    db = default_database.resource_database_for(RandovaniaGame.METROID_PRIME_CORRUPTION)
    from randovania.games.prime3.generator.pickup_pool import energy_cells

    cell = energy_cells.create_energy_cell(0, db)

    result = [
        (
            "Energy Cell",
            cell.pickup_category,
            cell.broad_category,
        )
    ]
    return result


_GAME_SPECIFIC = {
    RandovaniaGame.METROID_PRIME: prime1_hint_text,
    RandovaniaGame.METROID_PRIME_ECHOES: prime2_hint_text,
    RandovaniaGame.METROID_PRIME_CORRUPTION: prime3_hint_text,
}


def update_hints_text(
    game: RandovaniaGame,
    hint_item_names_tree_widget: QtWidgets.QTableWidget,
):
    pickup_database = default_database.pickup_database_for_game(game)

    rows = []

    for item in pickup_database.standard_pickups.values():
        rows.append(
            (
                item.name,
                item.pickup_category.hint_details[1],
                item.pickup_category.general_details[1],
                item.broad_category.hint_details[1],
            )
        )

    for name, pickup_category, broad_category in _GAME_SPECIFIC.get(game, list)():
        rows.append(
            (
                name,
                pickup_category.hint_details[1],
                pickup_category.general_details[1],
                broad_category.hint_details[1],
            )
        )

    for ammo in pickup_database.ammo_pickups.values():
        rows.append(
            (
                ammo.name,
                ammo.pickup_category.hint_details[1],
                ammo.pickup_category.general_details[1],
                ammo.broad_category.hint_details[1],
            )
        )

    hint_item_names_tree_widget.setSortingEnabled(False)
    hint_item_names_tree_widget.setRowCount(len(rows))
    for i, elements in enumerate(rows):
        for j, element in enumerate(elements):
            hint_item_names_tree_widget.setItem(i, j, QtWidgets.QTableWidgetItem(element))

    for i in range(4):
        hint_item_names_tree_widget.resizeColumnToContents(i)

    hint_item_names_tree_widget.setSortingEnabled(True)


def update_hint_locations(game: RandovaniaGame, hint_tree_widget: QtWidgets.QTreeWidget):
    game_description = default_database.game_description_for(game)

    used_hint_kind = set()

    hint_tree_widget.clear()
    hint_tree_widget.setSortingEnabled(False)

    hint_type_tree = collections.defaultdict(dict)

    # First figure out which areas uses what hints.
    # This lets us use detect which hint types are used
    for region in game_description.region_list.regions:
        for area in region.areas:
            hint_types = {}

            for node in area.nodes:
                if isinstance(node, HintNode):
                    used_hint_kind.add(node.kind)
                    if "translator" in node.extra:
                        hint_types[node.kind] = node.extra["translator"]
                    else:
                        hint_types[node.kind] = "✓"

            if hint_types:
                hint_type_tree[region.correct_name(area.in_dark_aether)][area.name] = hint_types

    number_for_hint_type = {
        hint_type: i + 1 for i, hint_type in enumerate(sorted(used_hint_kind, key=lambda it: it.long_name))
    }

    for region_name, area_hints in hint_type_tree.items():
        region_item = QtWidgets.QTreeWidgetItem(hint_tree_widget)
        region_item.setText(0, region_name)
        region_item.setExpanded(True)

        for area_name, hint_types in area_hints.items():
            area_item = QtWidgets.QTreeWidgetItem(region_item)
            area_item.setText(0, area_name)

            for hint_type, text in hint_types.items():
                area_item.setText(number_for_hint_type[hint_type], text)
                used_hint_kind.add(hint_type)

    hint_tree_widget.resizeColumnToContents(0)
    hint_tree_widget.setSortingEnabled(True)
    hint_tree_widget.sortByColumn(0, QtCore.Qt.AscendingOrder)

    for hint_kind in used_hint_kind:
        hint_tree_widget.headerItem().setText(number_for_hint_type[hint_kind], hint_kind.long_name)
