# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'corruption_game_export_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_CorruptionGameExportDialog(object):
    def setupUi(self, CorruptionGameExportDialog):
        if not CorruptionGameExportDialog.objectName():
            CorruptionGameExportDialog.setObjectName(u"CorruptionGameExportDialog")
        CorruptionGameExportDialog.resize(787, 315)
        self.gridLayout = QGridLayout(CorruptionGameExportDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.commands_label = QLabel(CorruptionGameExportDialog)
        self.commands_label.setObjectName(u"commands_label")
        self.commands_label.setWordWrap(False)
        self.commands_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.gridLayout.addWidget(self.commands_label, 2, 0, 1, 2)

        self.description_label = QLabel(CorruptionGameExportDialog)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.gridLayout.addWidget(self.description_label, 1, 0, 1, 2)

        self.cancel_button = QPushButton(CorruptionGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 3, 0, 1, 2)


        self.retranslateUi(CorruptionGameExportDialog)

        QMetaObject.connectSlotsByName(CorruptionGameExportDialog)
    # setupUi

    def retranslateUi(self, CorruptionGameExportDialog):
        CorruptionGameExportDialog.setWindowTitle(QCoreApplication.translate("CorruptionGameExportDialog", u"Game Patching", None))
        self.commands_label.setText(QCoreApplication.translate("CorruptionGameExportDialog", u"Replaced by code", None))
        self.description_label.setText(QCoreApplication.translate("CorruptionGameExportDialog", u"<html><head/><body><p>There is no integrated patcher for Metroid Prime 3: Corruption games.</p><p>Download the randomizer for it from #corruption-general in the Metroid Prime Randomizer Discord, and use the following commands as a seed.</p><p><br/></p><p><br/></p></body></html>", None))
        self.cancel_button.setText(QCoreApplication.translate("CorruptionGameExportDialog", u"Cancel", None))
    # retranslateUi

