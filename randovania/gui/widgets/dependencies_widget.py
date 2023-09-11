from __future__ import annotations

import importlib.metadata
from typing import Any

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt


def _get_license(dist: importlib.metadata.Distribution) -> str:
    for classifier in dist.metadata.get_all("Classifier", failobj=[]):
        assert isinstance(classifier, str)
        license = classifier.replace("License :: OSI Approved :: ", "")
        if license.strip() and license != classifier:
            return license

    if dist.metadata.get("License", "unknown").lower() != "unknown":
        return dist.metadata["License"]

    return "Unknown"


class DependenciesModel(QtCore.QAbstractTableModel):
    _headers = ("Dependency", "Version", "License")

    def __init__(self, parent):
        super().__init__(parent)
        self._packages = [(dist.name, dist.version, _get_license(dist)) for dist in importlib.metadata.distributions()]

    def columnCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if role != Qt.DisplayRole:
            return None

        if orientation != Qt.Horizontal:
            return section

        return self._headers[section]

    def rowCount(self, parent: QtCore.QModelIndex = ...) -> int:
        return len(self._packages)

    def data(self, index: QtCore.QModelIndex, role: int = ...) -> Any:
        if role not in {Qt.DisplayRole, Qt.EditRole}:
            return None

        if index.row() < len(self._packages):
            return self._packages[index.row()][index.column()]
        else:
            return ""


class DependenciesWidget(QtWidgets.QTableView):
    def __init__(self):
        super().__init__(None)
        self.root_model = DependenciesModel(self)
        self.proxy_model = QtCore.QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.root_model)
        self.proxy_model.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setModel(self.proxy_model)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)
