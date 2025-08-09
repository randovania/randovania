# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_planets_zebeth_patches.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_PresetMetroidPatches(object):
    def setupUi(self, PresetMetroidPatches):
        if not PresetMetroidPatches.objectName():
            PresetMetroidPatches.setObjectName(u"PresetMetroidPatches")
        PresetMetroidPatches.resize(770, 660)
        self.root_widget = QWidget(PresetMetroidPatches)
        self.root_widget.setObjectName(u"root_widget")
        self.root_widget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.root_widget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self.root_widget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_contents = QWidget()
        self.scroll_contents.setObjectName(u"scroll_contents")
        self.scroll_contents.setGeometry(QRect(0, 0, 768, 658))
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_layout.setObjectName(u"scroll_layout")
        self.scroll_layout.setContentsMargins(0, 2, 0, 0)
        self.top_spacer = QSpacerItem(20, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.scroll_layout.addItem(self.top_spacer)

        self.room_group = QGroupBox(self.scroll_contents)
        self.room_group.setObjectName(u"room_group")
        self.unlock_layout = QVBoxLayout(self.room_group)
        self.unlock_layout.setSpacing(6)
        self.unlock_layout.setContentsMargins(11, 11, 11, 11)
        self.unlock_layout.setObjectName(u"unlock_layout")
        self.softlock_prevention_blocks_check = QCheckBox(self.room_group)
        self.softlock_prevention_blocks_check.setObjectName(u"softlock_prevention_blocks_check")

        self.unlock_layout.addWidget(self.softlock_prevention_blocks_check)

        self.softlock_prevention_blocks_label = QLabel(self.room_group)
        self.softlock_prevention_blocks_label.setObjectName(u"softlock_prevention_blocks_label")
        self.softlock_prevention_blocks_label.setWordWrap(True)

        self.unlock_layout.addWidget(self.softlock_prevention_blocks_label)


        self.scroll_layout.addWidget(self.room_group)

        self.misc_group = QGroupBox(self.scroll_contents)
        self.misc_group.setObjectName(u"misc_group")
        self.raven_beak_damage_table_handling_layout = QVBoxLayout(self.misc_group)
        self.raven_beak_damage_table_handling_layout.setSpacing(6)
        self.raven_beak_damage_table_handling_layout.setContentsMargins(11, 11, 11, 11)
        self.raven_beak_damage_table_handling_layout.setObjectName(u"raven_beak_damage_table_handling_layout")
        self.skip_item_cutscenes_check = QCheckBox(self.misc_group)
        self.skip_item_cutscenes_check.setObjectName(u"skip_item_cutscenes_check")

        self.raven_beak_damage_table_handling_layout.addWidget(self.skip_item_cutscenes_check)

        self.skip_item_cutscenes_label = QLabel(self.misc_group)
        self.skip_item_cutscenes_label.setObjectName(u"skip_item_cutscenes_label")
        self.skip_item_cutscenes_label.setWordWrap(True)

        self.raven_beak_damage_table_handling_layout.addWidget(self.skip_item_cutscenes_label)

        self.supers_on_missile_doors_check = QCheckBox(self.misc_group)
        self.supers_on_missile_doors_check.setObjectName(u"supers_on_missile_doors_check")

        self.raven_beak_damage_table_handling_layout.addWidget(self.supers_on_missile_doors_check)

        self.supers_on_missile_doors_label = QLabel(self.misc_group)
        self.supers_on_missile_doors_label.setObjectName(u"supers_on_missile_doors_label")
        self.supers_on_missile_doors_label.setWordWrap(True)

        self.raven_beak_damage_table_handling_layout.addWidget(self.supers_on_missile_doors_label)


        self.scroll_layout.addWidget(self.misc_group)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        PresetMetroidPatches.setCentralWidget(self.root_widget)

        self.retranslateUi(PresetMetroidPatches)

        QMetaObject.connectSlotsByName(PresetMetroidPatches)
    # setupUi

    def retranslateUi(self, PresetMetroidPatches):
        PresetMetroidPatches.setWindowTitle(QCoreApplication.translate("PresetMetroidPatches", u"Other", None))
        self.room_group.setTitle(QCoreApplication.translate("PresetMetroidPatches", u"Room Design", None))
        self.softlock_prevention_blocks_check.setText(QCoreApplication.translate("PresetMetroidPatches", u"Softlock Prevention Checks", None))
        self.softlock_prevention_blocks_label.setText(QCoreApplication.translate("PresetMetroidPatches", u"This option adds checks to some rooms that removes certain blocks in order to minimize softlocks.", None))
        self.misc_group.setTitle(QCoreApplication.translate("PresetMetroidPatches", u"Miscellaneous", None))
        self.skip_item_cutscenes_check.setText(QCoreApplication.translate("PresetMetroidPatches", u"Non modal item acquisition text", None))
        self.skip_item_cutscenes_label.setText(QCoreApplication.translate("PresetMetroidPatches", u"<html><head/><body><p>Instead of pausing for a few seconds and rendering a message box with the text just render the text and don't pause.</p></body></html>", None))
        self.supers_on_missile_doors_check.setText(QCoreApplication.translate("PresetMetroidPatches", u"Open Missile Doors with 1 missile", None))
        self.supers_on_missile_doors_label.setText(QCoreApplication.translate("PresetMetroidPatches", u"<html><head/><body><p>Use only 1 missile to open Missile Doors rather than 5.</p></body></html>", None))
    # retranslateUi

