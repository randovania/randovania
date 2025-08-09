# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_patcher_super_patches.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_PresetPatcherSuperPatches(object):
    def setupUi(self, PresetPatcherSuperPatches):
        if not PresetPatcherSuperPatches.objectName():
            PresetPatcherSuperPatches.setObjectName(u"PresetPatcherSuperPatches")
        PresetPatcherSuperPatches.resize(476, 2128)
        self.centralWidget = QWidget(PresetPatcherSuperPatches)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.main_layout = QVBoxLayout(self.centralWidget)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(11, 11, 11, 11)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 472, 2124))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_area_contents.sizePolicy().hasHeightForWidth())
        self.scroll_area_contents.setSizePolicy(sizePolicy)
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_contents)
        self.scroll_area_layout.setSpacing(6)
        self.scroll_area_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_area_layout.setObjectName(u"scroll_area_layout")
        self.scroll_area_layout.setContentsMargins(1, 1, 1, 0)
        self.qol_box = QGroupBox(self.scroll_area_contents)
        self.qol_box.setObjectName(u"qol_box")
        self.gridLayout_4 = QGridLayout(self.qol_box)
        self.gridLayout_4.setSpacing(6)
        self.gridLayout_4.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.backup_saves_label = QLabel(self.qol_box)
        self.backup_saves_label.setObjectName(u"backup_saves_label")
        self.backup_saves_label.setWordWrap(True)

        self.gridLayout_4.addWidget(self.backup_saves_label, 11, 0, 1, 1)

        self.better_decompression_label = QLabel(self.qol_box)
        self.better_decompression_label.setObjectName(u"better_decompression_label")

        self.gridLayout_4.addWidget(self.better_decompression_label, 14, 0, 1, 1)

        self.fast_doors_checkbox = QCheckBox(self.qol_box)
        self.fast_doors_checkbox.setObjectName(u"fast_doors_checkbox")
        self.fast_doors_checkbox.setChecked(True)

        self.gridLayout_4.addWidget(self.fast_doors_checkbox, 7, 0, 1, 1)

        self.instant_g4_checkbox = QCheckBox(self.qol_box)
        self.instant_g4_checkbox.setObjectName(u"instant_g4_checkbox")
        self.instant_g4_checkbox.setChecked(True)

        self.gridLayout_4.addWidget(self.instant_g4_checkbox, 1, 0, 1, 1)

        self.mb_cutscene_tweaks_checkbox = QCheckBox(self.qol_box)
        self.mb_cutscene_tweaks_checkbox.setObjectName(u"mb_cutscene_tweaks_checkbox")
        self.mb_cutscene_tweaks_checkbox.setChecked(True)

        self.gridLayout_4.addWidget(self.mb_cutscene_tweaks_checkbox, 18, 0, 1, 1)

        self.skip_intro_checkbox = QCheckBox(self.qol_box)
        self.skip_intro_checkbox.setObjectName(u"skip_intro_checkbox")
        self.skip_intro_checkbox.setChecked(True)

        self.gridLayout_4.addWidget(self.skip_intro_checkbox, 16, 0, 1, 1)

        self.instant_g4_label = QLabel(self.qol_box)
        self.instant_g4_label.setObjectName(u"instant_g4_label")
        self.instant_g4_label.setWordWrap(True)

        self.gridLayout_4.addWidget(self.instant_g4_label, 2, 0, 1, 1)

        self.fast_doors_label = QLabel(self.qol_box)
        self.fast_doors_label.setObjectName(u"fast_doors_label")

        self.gridLayout_4.addWidget(self.fast_doors_label, 8, 0, 1, 1)

        self.skip_intro_label = QLabel(self.qol_box)
        self.skip_intro_label.setObjectName(u"skip_intro_label")

        self.gridLayout_4.addWidget(self.skip_intro_label, 17, 0, 1, 1)

        self.backup_saves_checkbox = QCheckBox(self.qol_box)
        self.backup_saves_checkbox.setObjectName(u"backup_saves_checkbox")
        self.backup_saves_checkbox.setChecked(True)

        self.gridLayout_4.addWidget(self.backup_saves_checkbox, 10, 0, 1, 1)

        self.mb_cutscene_tweaks_label = QLabel(self.qol_box)
        self.mb_cutscene_tweaks_label.setObjectName(u"mb_cutscene_tweaks_label")
        self.mb_cutscene_tweaks_label.setWordWrap(True)

        self.gridLayout_4.addWidget(self.mb_cutscene_tweaks_label, 19, 0, 1, 1)

        self.better_decompression_checkbox = QCheckBox(self.qol_box)
        self.better_decompression_checkbox.setObjectName(u"better_decompression_checkbox")
        self.better_decompression_checkbox.setChecked(True)

        self.gridLayout_4.addWidget(self.better_decompression_checkbox, 13, 0, 1, 1)


        self.scroll_area_layout.addWidget(self.qol_box)

        self.map_tweak_box = QGroupBox(self.scroll_area_contents)
        self.map_tweak_box.setObjectName(u"map_tweak_box")
        self.gridLayout_3 = QGridLayout(self.map_tweak_box)
        self.gridLayout_3.setSpacing(6)
        self.gridLayout_3.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.red_tower_label = QLabel(self.map_tweak_box)
        self.red_tower_label.setObjectName(u"red_tower_label")
        self.red_tower_label.setWordWrap(True)

        self.gridLayout_3.addWidget(self.red_tower_label, 19, 0, 1, 1)

        self.early_supers_label = QLabel(self.map_tweak_box)
        self.early_supers_label.setObjectName(u"early_supers_label")
        self.early_supers_label.setWordWrap(True)

        self.gridLayout_3.addWidget(self.early_supers_label, 6, 0, 1, 1)

        self.dachora_pit_label = QLabel(self.map_tweak_box)
        self.dachora_pit_label.setObjectName(u"dachora_pit_label")
        self.dachora_pit_label.setWordWrap(True)

        self.gridLayout_3.addWidget(self.dachora_pit_label, 2, 0, 1, 1)

        self.nova_boost_label = QLabel(self.map_tweak_box)
        self.nova_boost_label.setObjectName(u"nova_boost_label")
        self.nova_boost_label.setWordWrap(True)

        self.gridLayout_3.addWidget(self.nova_boost_label, 23, 0, 1, 1)

        self.moat_checkbox = QCheckBox(self.map_tweak_box)
        self.moat_checkbox.setObjectName(u"moat_checkbox")
        self.moat_checkbox.setChecked(True)

        self.gridLayout_3.addWidget(self.moat_checkbox, 11, 0, 1, 1)

        self.pre_spazer_checkbox = QCheckBox(self.map_tweak_box)
        self.pre_spazer_checkbox.setObjectName(u"pre_spazer_checkbox")
        self.pre_spazer_checkbox.setChecked(True)

        self.gridLayout_3.addWidget(self.pre_spazer_checkbox, 14, 0, 1, 1)

        self.moat_label = QLabel(self.map_tweak_box)
        self.moat_label.setObjectName(u"moat_label")
        self.moat_label.setWordWrap(True)

        self.gridLayout_3.addWidget(self.moat_label, 12, 0, 1, 1)

        self.red_tower_checkbox = QCheckBox(self.map_tweak_box)
        self.red_tower_checkbox.setObjectName(u"red_tower_checkbox")
        self.red_tower_checkbox.setChecked(True)

        self.gridLayout_3.addWidget(self.red_tower_checkbox, 18, 0, 1, 1)

        self.dachora_pit_checkbox = QCheckBox(self.map_tweak_box)
        self.dachora_pit_checkbox.setObjectName(u"dachora_pit_checkbox")
        self.dachora_pit_checkbox.setChecked(True)

        self.gridLayout_3.addWidget(self.dachora_pit_checkbox, 1, 0, 1, 1)

        self.pre_hi_jump_checkbox = QCheckBox(self.map_tweak_box)
        self.pre_hi_jump_checkbox.setObjectName(u"pre_hi_jump_checkbox")
        self.pre_hi_jump_checkbox.setChecked(True)

        self.gridLayout_3.addWidget(self.pre_hi_jump_checkbox, 8, 0, 1, 1)

        self.pre_hi_jump_label = QLabel(self.map_tweak_box)
        self.pre_hi_jump_label.setObjectName(u"pre_hi_jump_label")
        self.pre_hi_jump_label.setWordWrap(True)

        self.gridLayout_3.addWidget(self.pre_hi_jump_label, 9, 0, 1, 1)

        self.nova_boost_checkbox = QCheckBox(self.map_tweak_box)
        self.nova_boost_checkbox.setObjectName(u"nova_boost_checkbox")
        self.nova_boost_checkbox.setChecked(True)

        self.gridLayout_3.addWidget(self.nova_boost_checkbox, 22, 0, 1, 1)

        self.early_supers_checkbox = QCheckBox(self.map_tweak_box)
        self.early_supers_checkbox.setObjectName(u"early_supers_checkbox")
        self.early_supers_checkbox.setChecked(True)

        self.gridLayout_3.addWidget(self.early_supers_checkbox, 5, 0, 1, 1)

        self.pre_spazer_label = QLabel(self.map_tweak_box)
        self.pre_spazer_label.setObjectName(u"pre_spazer_label")
        self.pre_spazer_label.setWordWrap(True)

        self.gridLayout_3.addWidget(self.pre_spazer_label, 15, 0, 1, 1)

        self.no_ln_chozo_inventory_check_checkbox = QCheckBox(self.map_tweak_box)
        self.no_ln_chozo_inventory_check_checkbox.setObjectName(u"no_ln_chozo_inventory_check_checkbox")
        self.no_ln_chozo_inventory_check_checkbox.setChecked(True)

        self.gridLayout_3.addWidget(self.no_ln_chozo_inventory_check_checkbox, 24, 0, 1, 1)

        self.no_ln_chozo_inventory_check_label = QLabel(self.map_tweak_box)
        self.no_ln_chozo_inventory_check_label.setObjectName(u"no_ln_chozo_inventory_check_label")
        self.no_ln_chozo_inventory_check_label.setWordWrap(True)

        self.gridLayout_3.addWidget(self.no_ln_chozo_inventory_check_label, 25, 0, 1, 1)


        self.scroll_area_layout.addWidget(self.map_tweak_box)

        self.tweak_box = QGroupBox(self.scroll_area_contents)
        self.tweak_box.setObjectName(u"tweak_box")
        self.gridLayout_5 = QGridLayout(self.tweak_box)
        self.gridLayout_5.setSpacing(6)
        self.gridLayout_5.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.cant_use_supers_on_red_doors_checkbox = QCheckBox(self.tweak_box)
        self.cant_use_supers_on_red_doors_checkbox.setObjectName(u"cant_use_supers_on_red_doors_checkbox")

        self.gridLayout_5.addWidget(self.cant_use_supers_on_red_doors_checkbox, 7, 0, 1, 1)

        self.isj_checkbox = QCheckBox(self.tweak_box)
        self.isj_checkbox.setObjectName(u"isj_checkbox")

        self.gridLayout_5.addWidget(self.isj_checkbox, 16, 0, 1, 1)

        self.mb_rainbow_beam_nerf_checkbox = QCheckBox(self.tweak_box)
        self.mb_rainbow_beam_nerf_checkbox.setObjectName(u"mb_rainbow_beam_nerf_checkbox")
        self.mb_rainbow_beam_nerf_checkbox.setChecked(False)

        self.gridLayout_5.addWidget(self.mb_rainbow_beam_nerf_checkbox, 23, 0, 1, 1)

        self.respin_checkbox = QCheckBox(self.tweak_box)
        self.respin_checkbox.setObjectName(u"respin_checkbox")

        self.gridLayout_5.addWidget(self.respin_checkbox, 1, 0, 1, 1)

        self.speedkeep_label = QLabel(self.tweak_box)
        self.speedkeep_label.setObjectName(u"speedkeep_label")
        self.speedkeep_label.setWordWrap(True)

        self.gridLayout_5.addWidget(self.speedkeep_label, 14, 0, 1, 1)

        self.save_refill_label = QLabel(self.tweak_box)
        self.save_refill_label.setObjectName(u"save_refill_label")
        self.save_refill_label.setWordWrap(True)

        self.gridLayout_5.addWidget(self.save_refill_label, 5, 0, 1, 1)

        self.speedkeep_checkbox = QCheckBox(self.tweak_box)
        self.speedkeep_checkbox.setObjectName(u"speedkeep_checkbox")

        self.gridLayout_5.addWidget(self.speedkeep_checkbox, 13, 0, 1, 1)

        self.save_refills_checkbox = QCheckBox(self.tweak_box)
        self.save_refills_checkbox.setObjectName(u"save_refills_checkbox")

        self.gridLayout_5.addWidget(self.save_refills_checkbox, 4, 0, 1, 1)

        self.cheap_charge_label = QLabel(self.tweak_box)
        self.cheap_charge_label.setObjectName(u"cheap_charge_label")
        self.cheap_charge_label.setWordWrap(True)

        self.gridLayout_5.addWidget(self.cheap_charge_label, 11, 0, 1, 1)

        self.isj_label = QLabel(self.tweak_box)
        self.isj_label.setObjectName(u"isj_label")
        self.isj_label.setWordWrap(True)

        self.gridLayout_5.addWidget(self.isj_label, 17, 0, 1, 1)

        self.cant_use_supers_on_red_doors_label = QLabel(self.tweak_box)
        self.cant_use_supers_on_red_doors_label.setObjectName(u"cant_use_supers_on_red_doors_label")
        self.cant_use_supers_on_red_doors_label.setWordWrap(True)

        self.gridLayout_5.addWidget(self.cant_use_supers_on_red_doors_label, 8, 0, 1, 1)

        self.respin_label = QLabel(self.tweak_box)
        self.respin_label.setObjectName(u"respin_label")
        self.respin_label.setWordWrap(True)

        self.gridLayout_5.addWidget(self.respin_label, 2, 0, 1, 1)

        self.cheap_charge_checkbox = QCheckBox(self.tweak_box)
        self.cheap_charge_checkbox.setObjectName(u"cheap_charge_checkbox")

        self.gridLayout_5.addWidget(self.cheap_charge_checkbox, 10, 0, 1, 1)

        self.mb_rainbow_beam_nerf_label = QLabel(self.tweak_box)
        self.mb_rainbow_beam_nerf_label.setObjectName(u"mb_rainbow_beam_nerf_label")
        self.mb_rainbow_beam_nerf_label.setWordWrap(True)

        self.gridLayout_5.addWidget(self.mb_rainbow_beam_nerf_label, 24, 0, 1, 1)


        self.scroll_area_layout.addWidget(self.tweak_box)

        self.bugfix_box = QGroupBox(self.scroll_area_contents)
        self.bugfix_box.setObjectName(u"bugfix_box")
        self.gridLayout_7 = QGridLayout(self.bugfix_box)
        self.gridLayout_7.setSpacing(6)
        self.gridLayout_7.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_7.setObjectName(u"gridLayout_7")
        self.fix_screw_attack_menu_checkbox = QCheckBox(self.bugfix_box)
        self.fix_screw_attack_menu_checkbox.setObjectName(u"fix_screw_attack_menu_checkbox")
        self.fix_screw_attack_menu_checkbox.setChecked(True)

        self.gridLayout_7.addWidget(self.fix_screw_attack_menu_checkbox, 7, 0, 1, 1)

        self.spacetime_label = QLabel(self.bugfix_box)
        self.spacetime_label.setObjectName(u"spacetime_label")
        self.spacetime_label.setWordWrap(True)

        self.gridLayout_7.addWidget(self.spacetime_label, 2, 0, 1, 1)

        self.fix_spacetime_checkbox = QCheckBox(self.bugfix_box)
        self.fix_spacetime_checkbox.setObjectName(u"fix_spacetime_checkbox")
        self.fix_spacetime_checkbox.setChecked(True)

        self.gridLayout_7.addWidget(self.fix_spacetime_checkbox, 1, 0, 1, 1)

        self.fix_heat_echoes_checkbox = QCheckBox(self.bugfix_box)
        self.fix_heat_echoes_checkbox.setObjectName(u"fix_heat_echoes_checkbox")
        self.fix_heat_echoes_checkbox.setChecked(True)

        self.gridLayout_7.addWidget(self.fix_heat_echoes_checkbox, 4, 0, 1, 1)

        self.no_gt_checkbox = QCheckBox(self.bugfix_box)
        self.no_gt_checkbox.setObjectName(u"no_gt_checkbox")
        self.no_gt_checkbox.setChecked(True)

        self.gridLayout_7.addWidget(self.no_gt_checkbox, 10, 0, 1, 1)

        self.no_gt_code_label = QLabel(self.bugfix_box)
        self.no_gt_code_label.setObjectName(u"no_gt_code_label")
        self.no_gt_code_label.setWordWrap(True)

        self.gridLayout_7.addWidget(self.no_gt_code_label, 11, 0, 1, 1)

        self.item_menu_fix_label = QLabel(self.bugfix_box)
        self.item_menu_fix_label.setObjectName(u"item_menu_fix_label")
        self.item_menu_fix_label.setWordWrap(True)

        self.gridLayout_7.addWidget(self.item_menu_fix_label, 9, 0, 1, 1)

        self.heat_echoes_label = QLabel(self.bugfix_box)
        self.heat_echoes_label.setObjectName(u"heat_echoes_label")
        self.heat_echoes_label.setWordWrap(True)

        self.gridLayout_7.addWidget(self.heat_echoes_label, 6, 0, 1, 1)


        self.scroll_area_layout.addWidget(self.bugfix_box)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.main_layout.addWidget(self.scroll_area)

        PresetPatcherSuperPatches.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetPatcherSuperPatches)

        QMetaObject.connectSlotsByName(PresetPatcherSuperPatches)
    # setupUi

    def retranslateUi(self, PresetPatcherSuperPatches):
        PresetPatcherSuperPatches.setWindowTitle(QCoreApplication.translate("PresetPatcherSuperPatches", u"Game Patches", None))
#if QT_CONFIG(tooltip)
        PresetPatcherSuperPatches.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.qol_box.setTitle(QCoreApplication.translate("PresetPatcherSuperPatches", u"Quality of Life", None))
        self.backup_saves_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"When saving the game, your previous save is backed up to the unused save slots.", None))
        self.better_decompression_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Improves the efficiency of the game's decompression algorithm.", None))
#if QT_CONFIG(tooltip)
        self.fast_doors_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.fast_doors_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Faster Doors and Elevators", None))
        self.instant_g4_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"G4 Cutscene Skip", None))
#if QT_CONFIG(tooltip)
        self.mb_cutscene_tweaks_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.mb_cutscene_tweaks_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Mother Brain Cutscene Tweaks", None))
        self.skip_intro_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Skip Intro", None))
        self.instant_g4_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Allows the player to enter Tourian immediately upon entering the G4 room once all four bosses have been defeated, skipping the cutscene that plays.", None))
        self.fast_doors_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Increases the speed of doors and elevators.", None))
        self.skip_intro_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Removes Samus' intro monologue.", None))
#if QT_CONFIG(tooltip)
        self.backup_saves_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.backup_saves_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Backup Saves", None))
        self.mb_cutscene_tweaks_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Abbreviates the transition between Mother Brain's glass jar phase and her standing phase.", None))
#if QT_CONFIG(tooltip)
        self.better_decompression_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.better_decompression_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Better Decompression", None))
        self.map_tweak_box.setTitle(QCoreApplication.translate("PresetPatcherSuperPatches", u"Map Tweaks", None))
        self.red_tower_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Moves platforms in Red Tower, allowing it to be traversed without a jump item more easily.", None))
        self.early_supers_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Replaces a segment of the Early Supers Bridge with a shot block to prevent softlocks.", None))
        self.dachora_pit_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Changes the speed blocks in Dachora Pit not to respawn after being broken.", None))
        self.nova_boost_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Moves platforms in the Nova Boost Room, allowing it to be traversed without a jump item more easily.", None))
#if QT_CONFIG(tooltip)
        self.moat_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.moat_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Moat Tweaks", None))
#if QT_CONFIG(tooltip)
        self.pre_spazer_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.pre_spazer_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Pre Spazer Tweaks", None))
        self.moat_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Replaces the bomb block underneath the center post with a shot block.", None))
#if QT_CONFIG(tooltip)
        self.red_tower_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.red_tower_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Red Tower Tweaks", None))
#if QT_CONFIG(tooltip)
        self.dachora_pit_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.dachora_pit_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Dachora Pit Tweaks", None))
#if QT_CONFIG(tooltip)
        self.pre_hi_jump_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.pre_hi_jump_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Pre Hi-Jump Tweaks", None))
        self.pre_hi_jump_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Replaces the bomb blocks at the top of the room with shot blocks.", None))
#if QT_CONFIG(tooltip)
        self.nova_boost_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.nova_boost_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Nova Boost Tweaks", None))
#if QT_CONFIG(tooltip)
        self.early_supers_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.early_supers_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Early Supers Bridge Tweaks", None))
        self.pre_spazer_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Replaces a bomb block in the room before Spazer Beam with a shot block.", None))
        self.no_ln_chozo_inventory_check_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Lower Norfair Acid Statue Room Tweaks", None))
        self.no_ln_chozo_inventory_check_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Allows the Chozo Statue in Acid Statue Room to not require Space Jump to be activated.", None))
        self.tweak_box.setTitle(QCoreApplication.translate("PresetPatcherSuperPatches", u"Gameplay Tweaks", None))
#if QT_CONFIG(tooltip)
        self.cant_use_supers_on_red_doors_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.cant_use_supers_on_red_doors_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Can't Use Supers on Red Doors", None))
#if QT_CONFIG(tooltip)
        self.isj_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.isj_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Infinite Space Jump", None))
#if QT_CONFIG(tooltip)
        self.mb_rainbow_beam_nerf_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.mb_rainbow_beam_nerf_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Mother Brain Rainbow Beam Nerf", None))
#if QT_CONFIG(tooltip)
        self.respin_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.respin_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Respin", None))
        self.speedkeep_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Samus maintains her air speed when landing.", None))
        self.save_refill_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Save Stations refill Samus' energy and ammo when used.", None))
#if QT_CONFIG(tooltip)
        self.speedkeep_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.speedkeep_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Speedkeep", None))
#if QT_CONFIG(tooltip)
        self.save_refills_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.save_refills_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Save Station Refills", None))
        self.cheap_charge_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Samus has access to a weakened version of the Charge Beam before finding it.", None))
        self.isj_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Makes it easier to chain Space Jumps together.", None))
        self.cant_use_supers_on_red_doors_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Super Missiles can no longer be used to open red doors.", None))
        self.respin_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"While performing a jump, Samus can press Jump in mid-air to change her jump into a spin jump.", None))
#if QT_CONFIG(tooltip)
        self.cheap_charge_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.cheap_charge_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Cheap Charge", None))
        self.mb_rainbow_beam_nerf_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Mother Brain's rainbow beam attack deals less damage, allowing the game to be completed without any Energy Tanks.", None))
        self.bugfix_box.setTitle(QCoreApplication.translate("PresetPatcherSuperPatches", u"Bug Fixes", None))
#if QT_CONFIG(tooltip)
        self.fix_screw_attack_menu_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.fix_screw_attack_menu_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Fix Item Menu", None))
        self.spacetime_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Removes the glitch that allows Samus to equip the Spazer and Plasma beams simultaneously.", None))
#if QT_CONFIG(tooltip)
        self.fix_spacetime_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.fix_spacetime_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Fix Spacetime Glitch", None))
#if QT_CONFIG(tooltip)
        self.fix_heat_echoes_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.fix_heat_echoes_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Fix Heat Echoes", None))
#if QT_CONFIG(tooltip)
        self.no_gt_checkbox.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.no_gt_checkbox.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"No GT Code", None))
        self.no_gt_code_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Disables the GT code, a leftover debug function which allows Samus to gain most of her inventory by holding certain buttons while entering Golden Torizo's room.", None))
        self.item_menu_fix_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Fixes unintuitive menu behavior when the player has certain equipment unlocked, particularly the Screw Attack.", None))
        self.heat_echoes_label.setText(QCoreApplication.translate("PresetPatcherSuperPatches", u"Fixes a bug causing heat damage to remove Samus' speed echoes, causing her to collide with enemies and cancel the speed boost entirely instead of instantly killing them.", None))
    # retranslateUi

