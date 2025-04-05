from __future__ import annotations

import collections
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets

from randovania.game_description import default_database
from randovania.game_description.db.hint_node import HintNode, HintNodeKind

if TYPE_CHECKING:
    from randovania.game.game_enum import RandovaniaGame


def update_hint_locations(game: RandovaniaGame, hint_tree_widget: QtWidgets.QTreeWidget) -> None:
    game_description = default_database.game_description_for(game)

    used_hint_kind = set()

    hint_tree_widget.clear()
    hint_tree_widget.setSortingEnabled(False)

    hint_type_tree: collections.defaultdict[str, dict[str, dict[HintNodeKind, str]]] = collections.defaultdict(dict)

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
                hint_type_tree[region.name][area.name] = hint_types

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
    hint_tree_widget.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)

    for hint_kind in used_hint_kind:
        hint_tree_widget.headerItem().setText(number_for_hint_type[hint_kind], hint_kind.long_name)
