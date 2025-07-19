# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'select_preset_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QGridLayout, QHeaderView,
    QLabel, QScrollArea, QSizePolicy, QTreeWidgetItem,
    QVBoxLayout, QWidget)

from randovania.gui.lib.preset_tree_widget import PresetTreeWidget

class Ui_SelectPresetWidget(object):
    def setupUi(self, SelectPresetWidget):
        if not SelectPresetWidget.objectName():
            SelectPresetWidget.setObjectName(u"SelectPresetWidget")
        SelectPresetWidget.resize(409, 312)
        self.create_layout = QGridLayout(SelectPresetWidget)
        self.create_layout.setSpacing(6)
        self.create_layout.setContentsMargins(11, 11, 11, 11)
        self.create_layout.setObjectName(u"create_layout")
        self.create_layout.setContentsMargins(0, 0, 0, 0)
        self.create_scroll_area = QScrollArea(SelectPresetWidget)
        self.create_scroll_area.setObjectName(u"create_scroll_area")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.create_scroll_area.sizePolicy().hasHeightForWidth())
        self.create_scroll_area.setSizePolicy(sizePolicy)
        self.create_scroll_area.setWidgetResizable(True)
        self.create_scroll_area_contents = QWidget()
        self.create_scroll_area_contents.setObjectName(u"create_scroll_area_contents")
        self.create_scroll_area_contents.setGeometry(QRect(0, 0, 147, 310))
        self.create_scroll_area_layout = QVBoxLayout(self.create_scroll_area_contents)
        self.create_scroll_area_layout.setSpacing(6)
        self.create_scroll_area_layout.setContentsMargins(11, 11, 11, 11)
        self.create_scroll_area_layout.setObjectName(u"create_scroll_area_layout")
        self.create_scroll_area_layout.setContentsMargins(4, 4, 4, 4)
        self.create_preset_description = QLabel(self.create_scroll_area_contents)
        self.create_preset_description.setObjectName(u"create_preset_description")
        self.create_preset_description.setMinimumSize(QSize(0, 40))
        self.create_preset_description.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.create_preset_description.setWordWrap(True)

        self.create_scroll_area_layout.addWidget(self.create_preset_description)

        self.create_scroll_area.setWidget(self.create_scroll_area_contents)

        self.create_layout.addWidget(self.create_scroll_area, 2, 2, 1, 2)

        self.create_preset_tree = PresetTreeWidget(SelectPresetWidget)
        __qtreewidgetitem = QTreeWidgetItem(self.create_preset_tree)
        __qtreewidgetitem1 = QTreeWidgetItem(__qtreewidgetitem)
        QTreeWidgetItem(__qtreewidgetitem1)
        QTreeWidgetItem(self.create_preset_tree)
        self.create_preset_tree.setObjectName(u"create_preset_tree")
        self.create_preset_tree.setMinimumSize(QSize(200, 0))
        self.create_preset_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.create_preset_tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.create_preset_tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.create_preset_tree.setAlternatingRowColors(False)
        self.create_preset_tree.setRootIsDecorated(False)

        self.create_layout.addWidget(self.create_preset_tree, 2, 0, 1, 2)


        self.retranslateUi(SelectPresetWidget)

        QMetaObject.connectSlotsByName(SelectPresetWidget)
    # setupUi

    def retranslateUi(self, SelectPresetWidget):
        self.create_preset_description.setText(QCoreApplication.translate("SelectPresetWidget", u"<html><head/><body><p>This content should have been replaced by code.</p></body></html>", None))
        ___qtreewidgetitem = self.create_preset_tree.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("SelectPresetWidget", u"Presets (Right click for actions)", None));

        __sortingEnabled = self.create_preset_tree.isSortingEnabled()
        self.create_preset_tree.setSortingEnabled(False)
        ___qtreewidgetitem1 = self.create_preset_tree.topLevelItem(0)
        ___qtreewidgetitem1.setText(0, QCoreApplication.translate("SelectPresetWidget", u"Metroid Prime", None));
        ___qtreewidgetitem2 = ___qtreewidgetitem1.child(0)
        ___qtreewidgetitem2.setText(0, QCoreApplication.translate("SelectPresetWidget", u"Default Preset", None));
        ___qtreewidgetitem3 = ___qtreewidgetitem2.child(0)
        ___qtreewidgetitem3.setText(0, QCoreApplication.translate("SelectPresetWidget", u"Your Custom Preset", None));
        ___qtreewidgetitem4 = self.create_preset_tree.topLevelItem(1)
        ___qtreewidgetitem4.setText(0, QCoreApplication.translate("SelectPresetWidget", u"Metroid Prime 2", None));
        self.create_preset_tree.setSortingEnabled(__sortingEnabled)

        pass
    # retranslateUi

