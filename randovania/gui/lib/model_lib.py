import datetime

from PySide6 import QtCore, QtGui


def create_int_item(value: int) -> QtGui.QStandardItem:
    item = QtGui.QStandardItem()
    item.setData(value, QtCore.Qt.ItemDataRole.DisplayRole)
    return item


def create_date_item(date: datetime.datetime) -> QtGui.QStandardItem:
    item = QtGui.QStandardItem()
    item.setData(QtCore.QDateTime.fromSecsSinceEpoch(int(date.timestamp())), QtCore.Qt.ItemDataRole.DisplayRole)
    return item


def get_texts(model: QtCore.QAbstractProxyModel, *, max_rows: int | None = None) -> list[list[str]] | list[str]:
    column_count = model.columnCount()
    row_count = model.rowCount()
    if max_rows is not None:
        row_count = min(max_rows, row_count)

    if column_count == 1:
        return [model.data(model.index(row, 0)) for row in range(row_count)]
    else:
        return [[model.data(model.index(row, col)) for col in range(column_count)] for row in range(row_count)]
