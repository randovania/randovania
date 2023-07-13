import datetime

from PySide6 import QtCore, QtGui


def create_int_item(value: int) -> QtGui.QStandardItem:
    item = QtGui.QStandardItem()
    item.setData(value, QtCore.Qt.ItemDataRole.DisplayRole)
    return item


def create_date_item(date: datetime.datetime) -> QtGui.QStandardItem:
    item = QtGui.QStandardItem()
    item.setData(QtCore.QDateTime.fromSecsSinceEpoch(int(date.timestamp())),
                 QtCore.Qt.ItemDataRole.DisplayRole)
    return item
