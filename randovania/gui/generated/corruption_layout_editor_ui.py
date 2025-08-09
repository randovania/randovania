# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'corruption_layout_editor.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_CorruptionLayoutEditor(object):
    def setupUi(self, CorruptionLayoutEditor):
        if not CorruptionLayoutEditor.objectName():
            CorruptionLayoutEditor.setObjectName(u"CorruptionLayoutEditor")
        CorruptionLayoutEditor.resize(422, 380)
        self.root_layout = QGridLayout(CorruptionLayoutEditor)
        self.root_layout.setSpacing(6)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.root_layout.setContentsMargins(4, -1, 4, -1)
        self.scroll_area = QScrollArea(CorruptionLayoutEditor)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 412, 315))
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_contents)
        self.scroll_area_layout.setSpacing(6)
        self.scroll_area_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_area_layout.setObjectName(u"scroll_area_layout")
        self.scroll_area_layout.setContentsMargins(2, 2, 2, 2)
        self.scroll_area.setWidget(self.scroll_area_contents)

        self.root_layout.addWidget(self.scroll_area, 0, 0, 1, 2)

        self.layout_label = QLabel(CorruptionLayoutEditor)
        self.layout_label.setObjectName(u"layout_label")

        self.root_layout.addWidget(self.layout_label, 1, 0, 1, 1)

        self.layout_edit = QLineEdit(CorruptionLayoutEditor)
        self.layout_edit.setObjectName(u"layout_edit")
        self.layout_edit.setReadOnly(True)

        self.root_layout.addWidget(self.layout_edit, 1, 1, 1, 1)


        self.retranslateUi(CorruptionLayoutEditor)

        QMetaObject.connectSlotsByName(CorruptionLayoutEditor)
    # setupUi

    def retranslateUi(self, CorruptionLayoutEditor):
        CorruptionLayoutEditor.setWindowTitle(QCoreApplication.translate("CorruptionLayoutEditor", u"Layout Editor", None))
        self.layout_label.setText(QCoreApplication.translate("CorruptionLayoutEditor", u"Layout string:", None))
    # retranslateUi

