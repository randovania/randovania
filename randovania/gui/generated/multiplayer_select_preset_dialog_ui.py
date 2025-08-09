# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'multiplayer_select_preset_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

from randovania.gui.widgets.select_preset_widget import *  # type: ignore

class Ui_MultiplayerSelectPresetDialog(object):
    def setupUi(self, MultiplayerSelectPresetDialog):
        if not MultiplayerSelectPresetDialog.objectName():
            MultiplayerSelectPresetDialog.setObjectName(u"MultiplayerSelectPresetDialog")
        MultiplayerSelectPresetDialog.resize(548, 438)
        self.gridLayout = QGridLayout(MultiplayerSelectPresetDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.world_name_edit = QLineEdit(MultiplayerSelectPresetDialog)
        self.world_name_edit.setObjectName(u"world_name_edit")

        self.gridLayout.addWidget(self.world_name_edit, 0, 1, 1, 1)

        self.world_name_label = QLabel(MultiplayerSelectPresetDialog)
        self.world_name_label.setObjectName(u"world_name_label")

        self.gridLayout.addWidget(self.world_name_label, 0, 0, 1, 1)

        self.game_selection_combo = QComboBox(MultiplayerSelectPresetDialog)
        self.game_selection_combo.setObjectName(u"game_selection_combo")

        self.gridLayout.addWidget(self.game_selection_combo, 1, 0, 1, 2)

        self.accept_button = QPushButton(MultiplayerSelectPresetDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 3, 0, 1, 1)

        self.select_preset_widget = SelectPresetWidget(MultiplayerSelectPresetDialog)
        self.select_preset_widget.setObjectName(u"select_preset_widget")

        self.gridLayout.addWidget(self.select_preset_widget, 2, 0, 1, 2)

        self.cancel_button = QPushButton(MultiplayerSelectPresetDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 3, 1, 1, 1)


        self.retranslateUi(MultiplayerSelectPresetDialog)

        QMetaObject.connectSlotsByName(MultiplayerSelectPresetDialog)
    # setupUi

    def retranslateUi(self, MultiplayerSelectPresetDialog):
        MultiplayerSelectPresetDialog.setWindowTitle(QCoreApplication.translate("MultiplayerSelectPresetDialog", u"Select Preset", None))
        self.world_name_edit.setPlaceholderText(QCoreApplication.translate("MultiplayerSelectPresetDialog", u"World name", None))
        self.world_name_label.setText(QCoreApplication.translate("MultiplayerSelectPresetDialog", u"World name", None))
        self.accept_button.setText(QCoreApplication.translate("MultiplayerSelectPresetDialog", u"Accept", None))
        self.cancel_button.setText(QCoreApplication.translate("MultiplayerSelectPresetDialog", u"Cancel", None))
    # retranslateUi

