# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'corruption_cosmetic_patches_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_CorruptionCosmeticPatchesDialog(object):
    def setupUi(self, CorruptionCosmeticPatchesDialog):
        if not CorruptionCosmeticPatchesDialog.objectName():
            CorruptionCosmeticPatchesDialog.setObjectName(u"CorruptionCosmeticPatchesDialog")
        CorruptionCosmeticPatchesDialog.resize(396, 246)
        self.gridLayout = QGridLayout(CorruptionCosmeticPatchesDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.reset_button = QPushButton(CorruptionCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")

        self.gridLayout.addWidget(self.reset_button, 2, 2, 1, 1)

        self.accept_button = QPushButton(CorruptionCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 2, 0, 1, 1)

        self.cancel_button = QPushButton(CorruptionCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 2, 1, 1, 1)

        self.scrollArea = QScrollArea(CorruptionCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 376, 198))
        self.verticalLayout = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.game_changes_box = QGroupBox(self.scroll_area_contents)
        self.game_changes_box.setObjectName(u"game_changes_box")
        self.verticalLayout_2 = QVBoxLayout(self.game_changes_box)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.random_door_colors_check = QCheckBox(self.game_changes_box)
        self.random_door_colors_check.setObjectName(u"random_door_colors_check")

        self.verticalLayout_2.addWidget(self.random_door_colors_check)

        self.random_welding_colors_check = QCheckBox(self.game_changes_box)
        self.random_welding_colors_check.setObjectName(u"random_welding_colors_check")

        self.verticalLayout_2.addWidget(self.random_welding_colors_check)

        self.suit_layout = QHBoxLayout()
        self.suit_layout.setSpacing(6)
        self.suit_layout.setObjectName(u"suit_layout")
        self.suit_label = QLabel(self.game_changes_box)
        self.suit_label.setObjectName(u"suit_label")

        self.suit_layout.addWidget(self.suit_label)

        self.suit_combo = QComboBox(self.game_changes_box)
        self.suit_combo.setObjectName(u"suit_combo")

        self.suit_layout.addWidget(self.suit_combo)


        self.verticalLayout_2.addLayout(self.suit_layout)


        self.verticalLayout.addWidget(self.game_changes_box)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scroll_area_contents)

        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 3)


        self.retranslateUi(CorruptionCosmeticPatchesDialog)

        QMetaObject.connectSlotsByName(CorruptionCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, CorruptionCosmeticPatchesDialog):
        CorruptionCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("CorruptionCosmeticPatchesDialog", u"Metroid Prime 3 - Cosmetic Options", None))
        self.reset_button.setText(QCoreApplication.translate("CorruptionCosmeticPatchesDialog", u"Reset to Defaults", None))
        self.accept_button.setText(QCoreApplication.translate("CorruptionCosmeticPatchesDialog", u"Accept", None))
        self.cancel_button.setText(QCoreApplication.translate("CorruptionCosmeticPatchesDialog", u"Cancel", None))
        self.game_changes_box.setTitle(QCoreApplication.translate("CorruptionCosmeticPatchesDialog", u"Game Changes", None))
        self.random_door_colors_check.setText(QCoreApplication.translate("CorruptionCosmeticPatchesDialog", u"Random door colors", None))
        self.random_welding_colors_check.setText(QCoreApplication.translate("CorruptionCosmeticPatchesDialog", u"Random welding colors", None))
        self.suit_label.setText(QCoreApplication.translate("CorruptionCosmeticPatchesDialog", u"Initial suit", None))
    # retranslateUi

