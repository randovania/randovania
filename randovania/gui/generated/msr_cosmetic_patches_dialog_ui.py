# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'msr_cosmetic_patches_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_MSRCosmeticPatchesDialog(object):
    def setupUi(self, MSRCosmeticPatchesDialog):
        if not MSRCosmeticPatchesDialog.objectName():
            MSRCosmeticPatchesDialog.setObjectName(u"MSRCosmeticPatchesDialog")
        MSRCosmeticPatchesDialog.resize(524, 439)
        self.gridLayout = QGridLayout(MSRCosmeticPatchesDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.cancel_button = QPushButton(MSRCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 2, 1, 1, 1)

        self.reset_button = QPushButton(MSRCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")

        self.gridLayout.addWidget(self.reset_button, 2, 2, 1, 1)

        self.accept_button = QPushButton(MSRCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 2, 0, 1, 1)

        self.scrollArea = QScrollArea(MSRCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 504, 392))
        self.verticalLayout = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.game_changes_box = QGroupBox(self.scroll_area_contents)
        self.game_changes_box.setObjectName(u"game_changes_box")
        self.horizontalLayout = QHBoxLayout(self.game_changes_box)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.custom_laser_color_check = QCheckBox(self.game_changes_box)
        self.custom_laser_color_check.setObjectName(u"custom_laser_color_check")

        self.horizontalLayout.addWidget(self.custom_laser_color_check)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setSpacing(6)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.custom_laser_unlocked_color_button = QPushButton(self.game_changes_box)
        self.custom_laser_unlocked_color_button.setObjectName(u"custom_laser_unlocked_color_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.custom_laser_unlocked_color_button.sizePolicy().hasHeightForWidth())
        self.custom_laser_unlocked_color_button.setSizePolicy(sizePolicy)

        self.gridLayout_3.addWidget(self.custom_laser_unlocked_color_button, 0, 2, 1, 1)

        self.custom_laser_unlocked_color_square = QFrame(self.game_changes_box)
        self.custom_laser_unlocked_color_square.setObjectName(u"custom_laser_unlocked_color_square")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.custom_laser_unlocked_color_square.sizePolicy().hasHeightForWidth())
        self.custom_laser_unlocked_color_square.setSizePolicy(sizePolicy1)
        self.custom_laser_unlocked_color_square.setMinimumSize(QSize(22, 22))
        self.custom_laser_unlocked_color_square.setAutoFillBackground(False)
        self.custom_laser_unlocked_color_square.setFrameShape(QFrame.StyledPanel)
        self.custom_laser_unlocked_color_square.setFrameShadow(QFrame.Raised)
        self.custom_laser_unlocked_color_square.setLineWidth(1)

        self.gridLayout_3.addWidget(self.custom_laser_unlocked_color_square, 0, 3, 1, 1)

        self.custom_grapple_laser_unlocked_color_button = QPushButton(self.game_changes_box)
        self.custom_grapple_laser_unlocked_color_button.setObjectName(u"custom_grapple_laser_unlocked_color_button")
        sizePolicy.setHeightForWidth(self.custom_grapple_laser_unlocked_color_button.sizePolicy().hasHeightForWidth())
        self.custom_grapple_laser_unlocked_color_button.setSizePolicy(sizePolicy)

        self.gridLayout_3.addWidget(self.custom_grapple_laser_unlocked_color_button, 2, 2, 1, 1)

        self.custom_laser_locked_color_square = QFrame(self.game_changes_box)
        self.custom_laser_locked_color_square.setObjectName(u"custom_laser_locked_color_square")
        sizePolicy1.setHeightForWidth(self.custom_laser_locked_color_square.sizePolicy().hasHeightForWidth())
        self.custom_laser_locked_color_square.setSizePolicy(sizePolicy1)
        self.custom_laser_locked_color_square.setMinimumSize(QSize(22, 22))
        self.custom_laser_locked_color_square.setAutoFillBackground(False)
        self.custom_laser_locked_color_square.setFrameShape(QFrame.StyledPanel)
        self.custom_laser_locked_color_square.setFrameShadow(QFrame.Raised)
        self.custom_laser_locked_color_square.setLineWidth(1)

        self.gridLayout_3.addWidget(self.custom_laser_locked_color_square, 1, 3, 1, 1)

        self.custom_laser_locked_color_button = QPushButton(self.game_changes_box)
        self.custom_laser_locked_color_button.setObjectName(u"custom_laser_locked_color_button")
        sizePolicy.setHeightForWidth(self.custom_laser_locked_color_button.sizePolicy().hasHeightForWidth())
        self.custom_laser_locked_color_button.setSizePolicy(sizePolicy)

        self.gridLayout_3.addWidget(self.custom_laser_locked_color_button, 1, 2, 1, 1)

        self.custom_grapple_laser_locked_color_button = QPushButton(self.game_changes_box)
        self.custom_grapple_laser_locked_color_button.setObjectName(u"custom_grapple_laser_locked_color_button")
        sizePolicy.setHeightForWidth(self.custom_grapple_laser_locked_color_button.sizePolicy().hasHeightForWidth())
        self.custom_grapple_laser_locked_color_button.setSizePolicy(sizePolicy)

        self.gridLayout_3.addWidget(self.custom_grapple_laser_locked_color_button, 3, 2, 1, 1)

        self.custom_grapple_laser_unlocked_color_square = QFrame(self.game_changes_box)
        self.custom_grapple_laser_unlocked_color_square.setObjectName(u"custom_grapple_laser_unlocked_color_square")
        sizePolicy1.setHeightForWidth(self.custom_grapple_laser_unlocked_color_square.sizePolicy().hasHeightForWidth())
        self.custom_grapple_laser_unlocked_color_square.setSizePolicy(sizePolicy1)
        self.custom_grapple_laser_unlocked_color_square.setMinimumSize(QSize(22, 22))
        self.custom_grapple_laser_unlocked_color_square.setAutoFillBackground(False)
        self.custom_grapple_laser_unlocked_color_square.setFrameShape(QFrame.StyledPanel)
        self.custom_grapple_laser_unlocked_color_square.setFrameShadow(QFrame.Raised)
        self.custom_grapple_laser_unlocked_color_square.setLineWidth(1)

        self.gridLayout_3.addWidget(self.custom_grapple_laser_unlocked_color_square, 2, 3, 1, 1)

        self.custom_grapple_laser_locked_color_square = QFrame(self.game_changes_box)
        self.custom_grapple_laser_locked_color_square.setObjectName(u"custom_grapple_laser_locked_color_square")
        sizePolicy1.setHeightForWidth(self.custom_grapple_laser_locked_color_square.sizePolicy().hasHeightForWidth())
        self.custom_grapple_laser_locked_color_square.setSizePolicy(sizePolicy1)
        self.custom_grapple_laser_locked_color_square.setMinimumSize(QSize(22, 22))
        self.custom_grapple_laser_locked_color_square.setAutoFillBackground(False)
        self.custom_grapple_laser_locked_color_square.setFrameShape(QFrame.StyledPanel)
        self.custom_grapple_laser_locked_color_square.setFrameShadow(QFrame.Raised)
        self.custom_grapple_laser_locked_color_square.setLineWidth(1)

        self.gridLayout_3.addWidget(self.custom_grapple_laser_locked_color_square, 3, 3, 1, 1)


        self.horizontalLayout.addLayout(self.gridLayout_3)


        self.verticalLayout.addWidget(self.game_changes_box)

        self.groupBox = QGroupBox(self.scroll_area_contents)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setSpacing(6)
        self.gridLayout_2.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.aeion_bar_color_layout = QHBoxLayout()
        self.aeion_bar_color_layout.setSpacing(6)
        self.aeion_bar_color_layout.setObjectName(u"aeion_bar_color_layout")
        self.custom_aeion_bar_color_check = QCheckBox(self.groupBox)
        self.custom_aeion_bar_color_check.setObjectName(u"custom_aeion_bar_color_check")

        self.aeion_bar_color_layout.addWidget(self.custom_aeion_bar_color_check)

        self.custom_aeion_bar_color_button = QPushButton(self.groupBox)
        self.custom_aeion_bar_color_button.setObjectName(u"custom_aeion_bar_color_button")
        sizePolicy.setHeightForWidth(self.custom_aeion_bar_color_button.sizePolicy().hasHeightForWidth())
        self.custom_aeion_bar_color_button.setSizePolicy(sizePolicy)

        self.aeion_bar_color_layout.addWidget(self.custom_aeion_bar_color_button)

        self.custom_aeion_bar_color_square = QFrame(self.groupBox)
        self.custom_aeion_bar_color_square.setObjectName(u"custom_aeion_bar_color_square")
        sizePolicy1.setHeightForWidth(self.custom_aeion_bar_color_square.sizePolicy().hasHeightForWidth())
        self.custom_aeion_bar_color_square.setSizePolicy(sizePolicy1)
        self.custom_aeion_bar_color_square.setMinimumSize(QSize(22, 22))
        self.custom_aeion_bar_color_square.setAutoFillBackground(False)
        self.custom_aeion_bar_color_square.setFrameShape(QFrame.StyledPanel)
        self.custom_aeion_bar_color_square.setFrameShadow(QFrame.Raised)
        self.custom_aeion_bar_color_square.setLineWidth(1)

        self.aeion_bar_color_layout.addWidget(self.custom_aeion_bar_color_square)


        self.gridLayout_2.addLayout(self.aeion_bar_color_layout, 2, 0, 1, 2)

        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 2, Qt.AlignHCenter)

        self.room_names_dropdown = QComboBox(self.groupBox)
        self.room_names_dropdown.setObjectName(u"room_names_dropdown")
        self.room_names_dropdown.setEditable(False)

        self.gridLayout_2.addWidget(self.room_names_dropdown, 4, 1, 1, 1)

        self.room_names_label = QLabel(self.groupBox)
        self.room_names_label.setObjectName(u"room_names_label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.room_names_label.sizePolicy().hasHeightForWidth())
        self.room_names_label.setSizePolicy(sizePolicy2)

        self.gridLayout_2.addWidget(self.room_names_label, 4, 0, 1, 1)

        self.energy_tank_color_layout = QHBoxLayout()
        self.energy_tank_color_layout.setSpacing(6)
        self.energy_tank_color_layout.setObjectName(u"energy_tank_color_layout")
        self.custom_energy_tank_color_check = QCheckBox(self.groupBox)
        self.custom_energy_tank_color_check.setObjectName(u"custom_energy_tank_color_check")

        self.energy_tank_color_layout.addWidget(self.custom_energy_tank_color_check)

        self.custom_energy_tank_color_button = QPushButton(self.groupBox)
        self.custom_energy_tank_color_button.setObjectName(u"custom_energy_tank_color_button")
        sizePolicy.setHeightForWidth(self.custom_energy_tank_color_button.sizePolicy().hasHeightForWidth())
        self.custom_energy_tank_color_button.setSizePolicy(sizePolicy)

        self.energy_tank_color_layout.addWidget(self.custom_energy_tank_color_button)

        self.custom_energy_tank_color_square = QFrame(self.groupBox)
        self.custom_energy_tank_color_square.setObjectName(u"custom_energy_tank_color_square")
        sizePolicy1.setHeightForWidth(self.custom_energy_tank_color_square.sizePolicy().hasHeightForWidth())
        self.custom_energy_tank_color_square.setSizePolicy(sizePolicy1)
        self.custom_energy_tank_color_square.setMinimumSize(QSize(22, 22))
        self.custom_energy_tank_color_square.setAutoFillBackground(False)
        self.custom_energy_tank_color_square.setFrameShape(QFrame.StyledPanel)
        self.custom_energy_tank_color_square.setFrameShadow(QFrame.Raised)
        self.custom_energy_tank_color_square.setLineWidth(1)

        self.energy_tank_color_layout.addWidget(self.custom_energy_tank_color_square)


        self.gridLayout_2.addLayout(self.energy_tank_color_layout, 1, 0, 1, 2)

        self.ammo_hud_color_layout = QHBoxLayout()
        self.ammo_hud_color_layout.setSpacing(6)
        self.ammo_hud_color_layout.setObjectName(u"ammo_hud_color_layout")
        self.custom_ammo_hud_color_check = QCheckBox(self.groupBox)
        self.custom_ammo_hud_color_check.setObjectName(u"custom_ammo_hud_color_check")

        self.ammo_hud_color_layout.addWidget(self.custom_ammo_hud_color_check)

        self.custom_ammo_hud_color_button = QPushButton(self.groupBox)
        self.custom_ammo_hud_color_button.setObjectName(u"custom_ammo_hud_color_button")
        sizePolicy.setHeightForWidth(self.custom_ammo_hud_color_button.sizePolicy().hasHeightForWidth())
        self.custom_ammo_hud_color_button.setSizePolicy(sizePolicy)

        self.ammo_hud_color_layout.addWidget(self.custom_ammo_hud_color_button)

        self.custom_ammo_hud_color_square = QFrame(self.groupBox)
        self.custom_ammo_hud_color_square.setObjectName(u"custom_ammo_hud_color_square")
        sizePolicy1.setHeightForWidth(self.custom_ammo_hud_color_square.sizePolicy().hasHeightForWidth())
        self.custom_ammo_hud_color_square.setSizePolicy(sizePolicy1)
        self.custom_ammo_hud_color_square.setMinimumSize(QSize(22, 22))
        self.custom_ammo_hud_color_square.setAutoFillBackground(False)
        self.custom_ammo_hud_color_square.setFrameShape(QFrame.StyledPanel)
        self.custom_ammo_hud_color_square.setFrameShadow(QFrame.Raised)
        self.custom_ammo_hud_color_square.setLineWidth(1)

        self.ammo_hud_color_layout.addWidget(self.custom_ammo_hud_color_square)


        self.gridLayout_2.addLayout(self.ammo_hud_color_layout, 3, 0, 1, 2)


        self.verticalLayout.addWidget(self.groupBox)

        self.scrollArea.setWidget(self.scroll_area_contents)

        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 3)


        self.retranslateUi(MSRCosmeticPatchesDialog)

        QMetaObject.connectSlotsByName(MSRCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, MSRCosmeticPatchesDialog):
        MSRCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Metroid: Samus Returns - Cosmetic Options", None))
        self.cancel_button.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Cancel", None))
        self.reset_button.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Reset to Defaults", None))
        self.accept_button.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Accept", None))
        self.game_changes_box.setTitle(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Samus Changes", None))
        self.custom_laser_color_check.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Use custom Laser Aim colors", None))
        self.custom_laser_unlocked_color_button.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Set Standard Free-Aim Color...", None))
        self.custom_grapple_laser_unlocked_color_button.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Set Grapple Free-Aim Color...", None))
        self.custom_laser_locked_color_button.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Set Standard Target-Aim Color...", None))
        self.custom_grapple_laser_locked_color_button.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Set Grapple Target-Aim Color...", None))
        self.groupBox.setTitle(QCoreApplication.translate("MSRCosmeticPatchesDialog", u" HUD Changes", None))
        self.custom_aeion_bar_color_check.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Use a custom Aeion Bar color", None))
        self.custom_aeion_bar_color_button.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Set Color...", None))
        self.label.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Color choices may appear differently in-game than what is selected.", None))
        self.room_names_dropdown.setCurrentText("")
        self.room_names_dropdown.setPlaceholderText("")
        self.room_names_label.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Show Room Names On HUD", None))
        self.custom_energy_tank_color_check.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Use a custom Energy Tank color", None))
        self.custom_energy_tank_color_button.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Set Color...", None))
        self.custom_ammo_hud_color_check.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Use a custom Ammo color", None))
        self.custom_ammo_hud_color_button.setText(QCoreApplication.translate("MSRCosmeticPatchesDialog", u"Set Color...", None))
    # retranslateUi

