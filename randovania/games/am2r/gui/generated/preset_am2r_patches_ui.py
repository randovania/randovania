# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_am2r_patches.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_PresetAM2RPatches(object):
    def setupUi(self, PresetAM2RPatches):
        if not PresetAM2RPatches.objectName():
            PresetAM2RPatches.setObjectName(u"PresetAM2RPatches")
        PresetAM2RPatches.resize(770, 660)
        self.root_widget = QWidget(PresetAM2RPatches)
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
        self.scroll_contents.setGeometry(QRect(0, 0, 745, 1066))
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
        self.septogg_helpers_check = QCheckBox(self.room_group)
        self.septogg_helpers_check.setObjectName(u"septogg_helpers_check")

        self.unlock_layout.addWidget(self.septogg_helpers_check)

        self.septogg_helpers_label = QLabel(self.room_group)
        self.septogg_helpers_label.setObjectName(u"septogg_helpers_label")
        self.septogg_helpers_label.setWordWrap(True)

        self.unlock_layout.addWidget(self.septogg_helpers_label)

        self.grave_grotto_blocks_check = QCheckBox(self.room_group)
        self.grave_grotto_blocks_check.setObjectName(u"grave_grotto_blocks_check")

        self.unlock_layout.addWidget(self.grave_grotto_blocks_check)

        self.grave_grotto_blocks_label = QLabel(self.room_group)
        self.grave_grotto_blocks_label.setObjectName(u"grave_grotto_blocks_label")
        self.grave_grotto_blocks_label.setWordWrap(True)

        self.unlock_layout.addWidget(self.grave_grotto_blocks_label)

        self.a3_entrance_blocks_check = QCheckBox(self.room_group)
        self.a3_entrance_blocks_check.setObjectName(u"a3_entrance_blocks_check")

        self.unlock_layout.addWidget(self.a3_entrance_blocks_check)

        self.a3_entrance_blocks_label = QLabel(self.room_group)
        self.a3_entrance_blocks_label.setObjectName(u"a3_entrance_blocks_label")
        self.a3_entrance_blocks_label.setWordWrap(True)

        self.unlock_layout.addWidget(self.a3_entrance_blocks_label)

        self.softlock_prevention_blocks_check = QCheckBox(self.room_group)
        self.softlock_prevention_blocks_check.setObjectName(u"softlock_prevention_blocks_check")

        self.unlock_layout.addWidget(self.softlock_prevention_blocks_check)

        self.softlock_prevention_blocks_label = QLabel(self.room_group)
        self.softlock_prevention_blocks_label.setObjectName(u"softlock_prevention_blocks_label")
        self.softlock_prevention_blocks_label.setWordWrap(True)

        self.unlock_layout.addWidget(self.softlock_prevention_blocks_label)

        self.screw_blocks_check = QCheckBox(self.room_group)
        self.screw_blocks_check.setObjectName(u"screw_blocks_check")

        self.unlock_layout.addWidget(self.screw_blocks_check)

        self.screw_blocks_label = QLabel(self.room_group)
        self.screw_blocks_label.setObjectName(u"screw_blocks_label")
        self.screw_blocks_label.setWordWrap(True)

        self.unlock_layout.addWidget(self.screw_blocks_label)

        self.respawn_bomb_blocks_check = QCheckBox(self.room_group)
        self.respawn_bomb_blocks_check.setObjectName(u"respawn_bomb_blocks_check")

        self.unlock_layout.addWidget(self.respawn_bomb_blocks_check)

        self.respawn_bomb_blocks_label = QLabel(self.room_group)
        self.respawn_bomb_blocks_label.setObjectName(u"respawn_bomb_blocks_label")
        self.respawn_bomb_blocks_label.setWordWrap(True)

        self.unlock_layout.addWidget(self.respawn_bomb_blocks_label)

        self.nest_pipes_check = QCheckBox(self.room_group)
        self.nest_pipes_check.setObjectName(u"nest_pipes_check")

        self.unlock_layout.addWidget(self.nest_pipes_check)

        self.nest_pipes_label = QLabel(self.room_group)
        self.nest_pipes_label.setObjectName(u"nest_pipes_label")
        self.nest_pipes_label.setWordWrap(True)

        self.unlock_layout.addWidget(self.nest_pipes_label)

        self.blue_save_doors_check = QCheckBox(self.room_group)
        self.blue_save_doors_check.setObjectName(u"blue_save_doors_check")

        self.unlock_layout.addWidget(self.blue_save_doors_check)

        self.blue_save_doors_label = QLabel(self.room_group)
        self.blue_save_doors_label.setObjectName(u"blue_save_doors_label")
        self.blue_save_doors_label.setWordWrap(True)

        self.unlock_layout.addWidget(self.blue_save_doors_label)

        self.force_blue_labs_check = QCheckBox(self.room_group)
        self.force_blue_labs_check.setObjectName(u"force_blue_labs_check")

        self.unlock_layout.addWidget(self.force_blue_labs_check)

        self.force_blue_labs_check_2 = QLabel(self.room_group)
        self.force_blue_labs_check_2.setObjectName(u"force_blue_labs_check_2")
        self.force_blue_labs_check_2.setWordWrap(True)

        self.unlock_layout.addWidget(self.force_blue_labs_check_2)


        self.scroll_layout.addWidget(self.room_group)

        self.misc_group = QGroupBox(self.scroll_contents)
        self.misc_group.setObjectName(u"misc_group")
        self.raven_beak_damage_table_handling_layout = QVBoxLayout(self.misc_group)
        self.raven_beak_damage_table_handling_layout.setSpacing(6)
        self.raven_beak_damage_table_handling_layout.setContentsMargins(11, 11, 11, 11)
        self.raven_beak_damage_table_handling_layout.setObjectName(u"raven_beak_damage_table_handling_layout")
        self.skip_cutscenes_check = QCheckBox(self.misc_group)
        self.skip_cutscenes_check.setObjectName(u"skip_cutscenes_check")

        self.raven_beak_damage_table_handling_layout.addWidget(self.skip_cutscenes_check)

        self.skip_cutscenes_label = QLabel(self.misc_group)
        self.skip_cutscenes_label.setObjectName(u"skip_cutscenes_label")
        self.skip_cutscenes_label.setWordWrap(True)

        self.raven_beak_damage_table_handling_layout.addWidget(self.skip_cutscenes_label)

        self.skip_save_cutscene_check = QCheckBox(self.misc_group)
        self.skip_save_cutscene_check.setObjectName(u"skip_save_cutscene_check")

        self.raven_beak_damage_table_handling_layout.addWidget(self.skip_save_cutscene_check)

        self.skip_save_cutscene_label = QLabel(self.misc_group)
        self.skip_save_cutscene_label.setObjectName(u"skip_save_cutscene_label")
        self.skip_save_cutscene_label.setWordWrap(True)

        self.raven_beak_damage_table_handling_layout.addWidget(self.skip_save_cutscene_label)

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

        self.fusion_mode_check = QCheckBox(self.misc_group)
        self.fusion_mode_check.setObjectName(u"fusion_mode_check")

        self.raven_beak_damage_table_handling_layout.addWidget(self.fusion_mode_check)

        self.fusion_mode_label = QLabel(self.misc_group)
        self.fusion_mode_label.setObjectName(u"fusion_mode_label")
        self.fusion_mode_label.setWordWrap(True)

        self.raven_beak_damage_table_handling_layout.addWidget(self.fusion_mode_label)


        self.scroll_layout.addWidget(self.misc_group)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        PresetAM2RPatches.setCentralWidget(self.root_widget)

        self.retranslateUi(PresetAM2RPatches)

        QMetaObject.connectSlotsByName(PresetAM2RPatches)
    # setupUi

    def retranslateUi(self, PresetAM2RPatches):
        PresetAM2RPatches.setWindowTitle(QCoreApplication.translate("PresetAM2RPatches", u"Other", None))
        self.room_group.setTitle(QCoreApplication.translate("PresetAM2RPatches", u"Room Design", None))
        self.septogg_helpers_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Enable Septogg Helpers", None))
        self.septogg_helpers_label.setText(QCoreApplication.translate("PresetAM2RPatches", u"<html><head/><body><p>Septoggs will appear in certain rooms, helping you reach higher platforms if you don't have the means to reach them yourself. Due to SR-388's cave structure, this setting is highly recommended.</p></body></html>", None))
        self.grave_grotto_blocks_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Bomb Blocks in Grave Grotto", None))
        self.grave_grotto_blocks_label.setText(QCoreApplication.translate("PresetAM2RPatches", u"\"Grave Grotto\" (the cave between Golden Temple and Hydro Station) usually has bomb blocks. Disabling this option removes them.", None))
        self.a3_entrance_blocks_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Bomb Block in Industrial Complex Access", None))
        self.a3_entrance_blocks_label.setText(QCoreApplication.translate("PresetAM2RPatches", u"\"Industrial Complex Access\" usually has a bomb block on the way to \"Industrial Complex Exterior\". Disabling this option removes it, allowing sooner access to that area.", None))
        self.softlock_prevention_blocks_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Softlock Prevention Checks", None))
        self.softlock_prevention_blocks_label.setText(QCoreApplication.translate("PresetAM2RPatches", u"This option adds checks to some rooms that removes certain blocks in order to minimize softlocks.", None))
        self.screw_blocks_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Screw Attack Blocks near Teleporter Pipes", None))
        self.screw_blocks_label.setText(QCoreApplication.translate("PresetAM2RPatches", u"Usually, Teleporter Pipe rooms have Screw Attack Blocks near them. Disabling this option makes them dissapear, allowing sooner usage of them.", None))
        self.respawn_bomb_blocks_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Respawn destructable bomb blocks", None))
        self.respawn_bomb_blocks_label.setText(QCoreApplication.translate("PresetAM2RPatches", u"<html><head/><body><p>Makes most destructable bomb blocks respawn. Disabling this will make it easier to traverse certain rooms if you only have Power Bombs.</p></body></html>", None))
        self.nest_pipes_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Add new Teleporter Pipes in final areas", None))
        self.nest_pipes_label.setText(QCoreApplication.translate("PresetAM2RPatches", u"<html><head/><body><p>Adds new Teleporter Pipes to make the final areas less cumbersome to traverse.<br/>The Pipes will be located &quot;Hideout Hub Access East&quot;, &quot;Shinespark Cave East&quot;, &quot;Depths Omega Nest South West Access&quot; and &quot;Waterfall Passage Top&quot;.</p></body></html>", None))
        self.blue_save_doors_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Unlock Save Station Doors", None))
        self.blue_save_doors_label.setText(QCoreApplication.translate("PresetAM2RPatches", u"Ensures all Save Station doors are normal (blue) doors, even with door lock rando enabled.", None))
        self.force_blue_labs_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Unlock Genetics Laboratory Doors", None))
        self.force_blue_labs_check_2.setText(QCoreApplication.translate("PresetAM2RPatches", u"Ensures that the doors in the later parts of Genetics Laboratory are normal (blue) doors, even with door lock rando enabled.\n"
"To be more precise, all rooms after \"Hatchling Room Underside\" will have their doors changed.", None))
        self.misc_group.setTitle(QCoreApplication.translate("PresetAM2RPatches", u"Miscellaneous", None))
        self.skip_cutscenes_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Skip gameplay cutscenes", None))
        self.skip_cutscenes_label.setText(QCoreApplication.translate("PresetAM2RPatches", u"<html><head/><body><p>Enabling this will skip most gameplay related cutscenes, such as the Drill Sequence, the cutscenes you'll see when viewing a Metroid for the first time and similar.</p></body></html>", None))
        self.skip_save_cutscene_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Skip Save Station cutscene", None))
        self.skip_save_cutscene_label.setText(QCoreApplication.translate("PresetAM2RPatches", u"Enabling this will skip the short cutscene that appears when saving at a Save Station.", None))
        self.skip_item_cutscenes_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Skip item acquisition cutscenes", None))
        self.skip_item_cutscenes_label.setText(QCoreApplication.translate("PresetAM2RPatches", u"Enabling this will skip item related cutscenes, such as the pause when collecting an item or the cutscene that plays when collecting a suit.", None))
        self.supers_on_missile_doors_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Open Missile Doors with Super Missiles", None))
        self.supers_on_missile_doors_label.setText(QCoreApplication.translate("PresetAM2RPatches", u"Determines whether Super Missiles can be used to open Missile Doors.", None))
        self.fusion_mode_check.setText(QCoreApplication.translate("PresetAM2RPatches", u"Enable Fusion Mode", None))
        self.fusion_mode_label.setText(QCoreApplication.translate("PresetAM2RPatches", u"<html><head/><body><p>Fusion Mode enables the Fusion Suit for Samus, makes organic enemies drop X, makes bosses spawn Core-X and makes Metroids move faster.</p></body></html>", None))
    # retranslateUi

