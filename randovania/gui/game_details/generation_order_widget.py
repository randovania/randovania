import re

from PySide6 import QtCore, QtGui, QtWidgets

from randovania.layout.layout_description import LayoutDescription

_player_re = re.compile(r"[pP]layer (\d+)")


class GenerationOrderWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None, description: LayoutDescription, players: list[str]):
        super().__init__(parent)
        self.root_layout = QtWidgets.QVBoxLayout(self)

        numbered_players = [f"Player {i + 1}" for i in range(description.world_count)]

        self.filter_edit = QtWidgets.QLineEdit(self)
        self.filter_edit.setPlaceholderText("Type here to filter the log below")
        self.root_layout.addWidget(self.filter_edit)

        self.item_model = QtGui.QStandardItemModel(0, 1, self)

        self.list_view = QtWidgets.QListView(self)
        self.root_layout.addWidget(self.list_view)

        def get_name(m: re.Match):
            return players[int(m.group(1)) - 1]

        for item_order in description.item_order:
            # update player names in the generation order
            if numbered_players != players:
                item_order = _player_re.sub(get_name, item_order)

            self.item_model.appendRow(QtGui.QStandardItem(item_order))

        self.proxy_model = QtCore.QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.item_model)
        self.filter_edit.textChanged.connect(self.proxy_model.setFilterRegularExpression)
        self.list_view.setModel(self.proxy_model)
