# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_msr_patches.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGroupBox, QLabel,
    QLayout, QMainWindow, QScrollArea, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_PresetMSRPatches(object):
    def setupUi(self, PresetMSRPatches):
        if not PresetMSRPatches.objectName():
            PresetMSRPatches.setObjectName(u"PresetMSRPatches")
        PresetMSRPatches.setEnabled(True)
        PresetMSRPatches.resize(642, 535)
        self.root_widget = QWidget(PresetMSRPatches)
        self.root_widget.setObjectName(u"root_widget")
        self.root_widget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.root_widget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self.root_widget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setMinimumSize(QSize(0, 0))
        self.scroll_area.setWidgetResizable(True)
        self.scroll_contents = QWidget()
        self.scroll_contents.setObjectName(u"scroll_contents")
        self.scroll_contents.setGeometry(QRect(0, 0, 626, 681))
        self.scroll_contents.setMinimumSize(QSize(0, 469))
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_layout.setObjectName(u"scroll_layout")
        self.scroll_layout.setContentsMargins(6, 6, 6, 6)
        self.environment_group = QGroupBox(self.scroll_contents)
        self.environment_group.setObjectName(u"environment_group")
        self.verticalLayout_3 = QVBoxLayout(self.environment_group)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.area3_interior_shortcut_no_grapple_check = QCheckBox(self.environment_group)
        self.area3_interior_shortcut_no_grapple_check.setObjectName(u"area3_interior_shortcut_no_grapple_check")

        self.verticalLayout_3.addWidget(self.area3_interior_shortcut_no_grapple_check)

        self.area3_interior_shortcut_no_grapple_label = QLabel(self.environment_group)
        self.area3_interior_shortcut_no_grapple_label.setObjectName(u"area3_interior_shortcut_no_grapple_label")
        self.area3_interior_shortcut_no_grapple_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.area3_interior_shortcut_no_grapple_label)

        self.elevator_grapple_blocks_check = QCheckBox(self.environment_group)
        self.elevator_grapple_blocks_check.setObjectName(u"elevator_grapple_blocks_check")

        self.verticalLayout_3.addWidget(self.elevator_grapple_blocks_check)

        self.elevator_grapple_blocks_label = QLabel(self.environment_group)
        self.elevator_grapple_blocks_label.setObjectName(u"elevator_grapple_blocks_label")
        self.elevator_grapple_blocks_label.setMouseTracking(True)
        self.elevator_grapple_blocks_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.elevator_grapple_blocks_label)

        self.surface_crumbles_check = QCheckBox(self.environment_group)
        self.surface_crumbles_check.setObjectName(u"surface_crumbles_check")

        self.verticalLayout_3.addWidget(self.surface_crumbles_check)

        self.surface_crumbles_label = QLabel(self.environment_group)
        self.surface_crumbles_label.setObjectName(u"surface_crumbles_label")
        self.surface_crumbles_label.setMouseTracking(True)
        self.surface_crumbles_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.surface_crumbles_label)

        self.area1_crumbles_check = QCheckBox(self.environment_group)
        self.area1_crumbles_check.setObjectName(u"area1_crumbles_check")

        self.verticalLayout_3.addWidget(self.area1_crumbles_check)

        self.area1_crumbles_label = QLabel(self.environment_group)
        self.area1_crumbles_label.setObjectName(u"area1_crumbles_label")
        self.area1_crumbles_label.setMouseTracking(True)
        self.area1_crumbles_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.area1_crumbles_label)

        self.reverse_area8_check = QCheckBox(self.environment_group)
        self.reverse_area8_check.setObjectName(u"reverse_area8_check")

        self.verticalLayout_3.addWidget(self.reverse_area8_check)

        self.reverse_area8_label = QLabel(self.environment_group)
        self.reverse_area8_label.setObjectName(u"reverse_area8_label")
        self.reverse_area8_label.setMouseTracking(True)
        self.reverse_area8_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.reverse_area8_label)


        self.scroll_layout.addWidget(self.environment_group)

        self.misc_group = QGroupBox(self.scroll_contents)
        self.misc_group.setObjectName(u"misc_group")
        self.verticalLayout_2 = QVBoxLayout(self.misc_group)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.charge_door_buff_check = QCheckBox(self.misc_group)
        self.charge_door_buff_check.setObjectName(u"charge_door_buff_check")

        self.verticalLayout_2.addWidget(self.charge_door_buff_check)

        self.charge_door_buff_label = QLabel(self.misc_group)
        self.charge_door_buff_label.setObjectName(u"charge_door_buff_label")
        self.charge_door_buff_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.charge_door_buff_label)

        self.beam_door_buff_check = QCheckBox(self.misc_group)
        self.beam_door_buff_check.setObjectName(u"beam_door_buff_check")

        self.verticalLayout_2.addWidget(self.beam_door_buff_check)

        self.beam_door_buff_label = QLabel(self.misc_group)
        self.beam_door_buff_label.setObjectName(u"beam_door_buff_label")
        self.beam_door_buff_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.beam_door_buff_label)

        self.beam_burst_buff_check = QCheckBox(self.misc_group)
        self.beam_burst_buff_check.setObjectName(u"beam_burst_buff_check")

        self.verticalLayout_2.addWidget(self.beam_burst_buff_check)

        self.beam_burst_buff_label = QLabel(self.misc_group)
        self.beam_burst_buff_label.setObjectName(u"beam_burst_buff_label")
        self.beam_burst_buff_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.beam_burst_buff_label)

        self.nerf_super_missiles_check = QCheckBox(self.misc_group)
        self.nerf_super_missiles_check.setObjectName(u"nerf_super_missiles_check")

        self.verticalLayout_2.addWidget(self.nerf_super_missiles_check)

        self.nerf_super_missiles_label = QLabel(self.misc_group)
        self.nerf_super_missiles_label.setObjectName(u"nerf_super_missiles_label")
        self.nerf_super_missiles_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.nerf_super_missiles_label)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.scroll_layout.addWidget(self.misc_group)

        self.scroll_area.setWidget(self.scroll_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        PresetMSRPatches.setCentralWidget(self.root_widget)

        self.retranslateUi(PresetMSRPatches)

        QMetaObject.connectSlotsByName(PresetMSRPatches)
    # setupUi

    def retranslateUi(self, PresetMSRPatches):
        PresetMSRPatches.setWindowTitle(QCoreApplication.translate("PresetMSRPatches", u"Other", None))
        self.environment_group.setTitle(QCoreApplication.translate("PresetMSRPatches", u"Room Changes", None))
        self.area3_interior_shortcut_no_grapple_check.setText(QCoreApplication.translate("PresetMSRPatches", u"Grapple Block in Area 3 Factory Interior - Gamma Arena && Transport to Metroid Caverns East", None))
        self.area3_interior_shortcut_no_grapple_label.setText(QCoreApplication.translate("PresetMSRPatches", u"<html><head/><body><p>Removes the Grapple Block next to the elevator, allowing earlier access from this side.</p></body></html>", None))
        self.elevator_grapple_blocks_check.setText(QCoreApplication.translate("PresetMSRPatches", u"Grapple Blocks leaving areas", None))
        self.elevator_grapple_blocks_label.setText(QCoreApplication.translate("PresetMSRPatches", u"<html><head/><body><p>Removes the Grapple Blocks that are near the exit elevators of certain areas. These include:</p><ul style=\"margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;\"><li style=\" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Area 4 Central Caves to Area 4 Crystal Mines</li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Area 5 Tower Lobby to Area 6 </li><li style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Area 6 to Area 7 </li><li style=\" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Area 7 to Area 8 </li></ul><p>If Diggernaut is the final boss, the block in Area 6 will always be removed even if this option is unchecked.</p></body></html>", None))
        self.surface_crumbles_check.setText(QCoreApplication.translate("PresetMSRPatches", u"Crumble Blocks in Surface East - Cavern Cavity", None))
        self.surface_crumbles_label.setText(QCoreApplication.translate("PresetMSRPatches", u"Changes the Crumble Blocks to Power Beam Blocks, allowing for a two-way path through the room. This makes this section less dangerous without Charge Beam.", None))
        self.area1_crumbles_check.setText(QCoreApplication.translate("PresetMSRPatches", u"Crumble Blocks in Area 1 - Transport to Surface and Area 2", None))
        self.area1_crumbles_label.setText(QCoreApplication.translate("PresetMSRPatches", u"Changes the Crumble Blocks leaving Area 1 to Power Beam Blocks, allowing for earlier access to Area 2 with only Morph Ball. This helps make item placement less restrictive.", None))
        self.reverse_area8_check.setText(QCoreApplication.translate("PresetMSRPatches", u"Reverse Area 8", None))
        self.reverse_area8_label.setText(QCoreApplication.translate("PresetMSRPatches", u"<html><head/><body><p>Removes the wall between the Queen Arena and Hatchling Room, allowing for earlier access into Area 8 by entering the area backwards.</p><p>If the Metroid Queen is the final boss, the wall will always be removed even if this option is unchecked.</p></body></html>", None))
        self.misc_group.setTitle(QCoreApplication.translate("PresetMSRPatches", u"Item Changes", None))
        self.charge_door_buff_check.setText(QCoreApplication.translate("PresetMSRPatches", u"Buff Charge Beam Doors", None))
        self.charge_door_buff_label.setText(QCoreApplication.translate("PresetMSRPatches", u"Makes Charge Doors invulnerable to Power Bombs. Beam Burst is unaffected.", None))
        self.beam_door_buff_check.setText(QCoreApplication.translate("PresetMSRPatches", u"Buff Beam Doors", None))
        self.beam_door_buff_label.setText(QCoreApplication.translate("PresetMSRPatches", u"Makes Beam Doors invulnerable to Power Bombs.", None))
        self.beam_burst_buff_check.setText(QCoreApplication.translate("PresetMSRPatches", u"Buff Beam Burst", None))
        self.beam_burst_buff_label.setText(QCoreApplication.translate("PresetMSRPatches", u"Makes Blob Throwers and Steel Orbs invulnerable to Power Bombs.", None))
        self.nerf_super_missiles_check.setText(QCoreApplication.translate("PresetMSRPatches", u"Buff Missile Doors", None))
        self.nerf_super_missiles_label.setText(QCoreApplication.translate("PresetMSRPatches", u"Makes Missile Doors invulnerable to Super Missiles. Missile blocks are unaffected.", None))
    # retranslateUi

