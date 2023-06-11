import re

from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QGridLayout
)

from randovania.game_description import pretty_print
from randovania.game_description.requirements.base import Requirement


def create_tree_items_for_requirement(
        tree: QtWidgets.QTreeWidget,
        root: QtWidgets.QTreeWidget | QtWidgets.QTreeWidgetItem,
        requirement: Requirement,
) -> QtWidgets.QTreeWidgetItem:
    parents: list[QtWidgets.QTreeWidget | QtWidgets.QTreeWidgetItem] = [root]

    result = None

    for depth, text in pretty_print.pretty_print_requirement(requirement):
        item = QtWidgets.QTreeWidgetItem(parents[depth])
        item.setExpanded(True)

        if result is None:
            result = item

        if "of the following" in text:
            item.setText(0, text)
            if len(parents) == depth + 1:
                parents.append(item)
            else:
                parents[depth + 1] = item
        else:
            label = QtWidgets.QLabel()

            if text.startswith("# "):
                text = re.sub(r"(https?://[^\s]+)", r'<a href="\1">\1</a>', text[2:])
                label.setStyleSheet("font-weight: bold; color: green")
                label.setOpenExternalLinks(True)
            else:
                max_size = 100
                if len(text) > max_size:
                    lines = [text]
                    while len(lines[-1]) > max_size:
                        and_i = lines[-1].rfind(" and ", 0, max_size)
                        or_i = lines[-1].rfind(" or ", 0, max_size)
                        i = max(and_i, or_i)
                        if i == -1:
                            break
                        lines.append(lines[-1][i:])
                        lines[-2] = lines[-2][:i]
                    text = "\n".join(lines)

            label.setText(text)
            tree.setItemWidget(item, 0, label)

    return result


class ConnectionsVisualizer:
    parent: QWidget
    grid_layout: QGridLayout

    def __init__(self, parent: QWidget, grid_layout: QGridLayout, requirement: Requirement):
        self.parent = parent
        self.grid_layout = grid_layout
        self._tree = QtWidgets.QTreeWidget(self.parent)
        self._tree.header().setVisible(False)
        self.grid_layout.addWidget(self._tree)

        self._add_widget_for_requirement_array(requirement)

    def _add_widget_for_requirement_array(self, requirement: Requirement):
        self.grid_layout.setAlignment(Qt.AlignTop)
        create_tree_items_for_requirement(self._tree, self._tree, requirement)
        self._tree.updateGeometries()

    def deleteLater(self):
        self._tree.deleteLater()
