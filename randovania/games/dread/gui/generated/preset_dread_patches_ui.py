# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_dread_patches.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
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
    QMainWindow, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_PresetDreadPatches(object):
    def setupUi(self, PresetDreadPatches):
        if not PresetDreadPatches.objectName():
            PresetDreadPatches.setObjectName(u"PresetDreadPatches")
        PresetDreadPatches.resize(438, 284)
        self.centralWidget = QWidget(PresetDreadPatches)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_contents = QWidget()
        self.scroll_contents.setObjectName(u"scroll_contents")
        self.scroll_contents.setGeometry(QRect(0, 0, 498, 754))
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_layout.setObjectName(u"scroll_layout")
        self.scroll_layout.setContentsMargins(0, 2, 0, 0)
        self.top_spacer = QSpacerItem(20, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.scroll_layout.addItem(self.top_spacer)

        self.unlock_group = QGroupBox(self.scroll_contents)
        self.unlock_group.setObjectName(u"unlock_group")
        self.unlock_layout = QVBoxLayout(self.unlock_group)
        self.unlock_layout.setSpacing(6)
        self.unlock_layout.setContentsMargins(11, 11, 11, 11)
        self.unlock_layout.setObjectName(u"unlock_layout")
        self.hanubia_shortcut_no_grapple_check = QCheckBox(self.unlock_group)
        self.hanubia_shortcut_no_grapple_check.setObjectName(u"hanubia_shortcut_no_grapple_check")

        self.unlock_layout.addWidget(self.hanubia_shortcut_no_grapple_check)

        self.hanubia_shortcut_no_grapple_label = QLabel(self.unlock_group)
        self.hanubia_shortcut_no_grapple_label.setObjectName(u"hanubia_shortcut_no_grapple_label")
        self.hanubia_shortcut_no_grapple_label.setWordWrap(True)

        self.unlock_layout.addWidget(self.hanubia_shortcut_no_grapple_label)

        self.hanubia_easier_path_to_itorash_check = QCheckBox(self.unlock_group)
        self.hanubia_easier_path_to_itorash_check.setObjectName(u"hanubia_easier_path_to_itorash_check")

        self.unlock_layout.addWidget(self.hanubia_easier_path_to_itorash_check)

        self.hanubia_easier_path_to_itorash_label = QLabel(self.unlock_group)
        self.hanubia_easier_path_to_itorash_label.setObjectName(u"hanubia_easier_path_to_itorash_label")

        self.unlock_layout.addWidget(self.hanubia_easier_path_to_itorash_label)


        self.scroll_layout.addWidget(self.unlock_group)

        self.bosses_group = QGroupBox(self.scroll_contents)
        self.bosses_group.setObjectName(u"bosses_group")
        self.raven_beak_damage_table_handling_layout = QVBoxLayout(self.bosses_group)
        self.raven_beak_damage_table_handling_layout.setSpacing(6)
        self.raven_beak_damage_table_handling_layout.setContentsMargins(11, 11, 11, 11)
        self.raven_beak_damage_table_handling_layout.setObjectName(u"raven_beak_damage_table_handling_layout")
        self.raven_beak_damage_table_handling_check = QCheckBox(self.bosses_group)
        self.raven_beak_damage_table_handling_check.setObjectName(u"raven_beak_damage_table_handling_check")

        self.raven_beak_damage_table_handling_layout.addWidget(self.raven_beak_damage_table_handling_check)

        self.raven_beak_damage_table_handling_label = QLabel(self.bosses_group)
        self.raven_beak_damage_table_handling_label.setObjectName(u"raven_beak_damage_table_handling_label")
        self.raven_beak_damage_table_handling_label.setWordWrap(True)

        self.raven_beak_damage_table_handling_layout.addWidget(self.raven_beak_damage_table_handling_label)


        self.scroll_layout.addWidget(self.bosses_group)

        self.x_group = QGroupBox(self.scroll_contents)
        self.x_group.setObjectName(u"x_group")
        self.verticalLayout_2 = QVBoxLayout(self.x_group)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.x_starts_released_check = QCheckBox(self.x_group)
        self.x_starts_released_check.setObjectName(u"x_starts_released_check")

        self.verticalLayout_2.addWidget(self.x_starts_released_check)

        self.x_starts_released_label = QLabel(self.x_group)
        self.x_starts_released_label.setObjectName(u"x_starts_released_label")
        self.x_starts_released_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.x_starts_released_label)


        self.scroll_layout.addWidget(self.x_group)

        self.miscellaneous_group = QGroupBox(self.scroll_contents)
        self.miscellaneous_group.setObjectName(u"miscellaneous_group")
        self.verticalLayout_3 = QVBoxLayout(self.miscellaneous_group)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.nerf_power_bombs_check = QCheckBox(self.miscellaneous_group)
        self.nerf_power_bombs_check.setObjectName(u"nerf_power_bombs_check")

        self.verticalLayout_3.addWidget(self.nerf_power_bombs_check)

        self.nerf_power_bombs_label = QLabel(self.miscellaneous_group)
        self.nerf_power_bombs_label.setObjectName(u"nerf_power_bombs_label")
        self.nerf_power_bombs_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.nerf_power_bombs_label)

        self.skip_item_popups_check = QCheckBox(self.miscellaneous_group)
        self.skip_item_popups_check.setObjectName(u"skip_item_popups_check")

        self.verticalLayout_3.addWidget(self.skip_item_popups_check)

        self.skip_item_popups_label = QLabel(self.miscellaneous_group)
        self.skip_item_popups_label.setObjectName(u"skip_item_popups_label")
        self.skip_item_popups_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.skip_item_popups_label)


        self.scroll_layout.addWidget(self.miscellaneous_group)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        PresetDreadPatches.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetDreadPatches)

        QMetaObject.connectSlotsByName(PresetDreadPatches)
    # setupUi

    def retranslateUi(self, PresetDreadPatches):
        PresetDreadPatches.setWindowTitle(QCoreApplication.translate("PresetDreadPatches", u"Other", None))
        self.unlock_group.setTitle(QCoreApplication.translate("PresetDreadPatches", u"Unlocking access", None))
        self.hanubia_shortcut_no_grapple_check.setText(QCoreApplication.translate("PresetDreadPatches", u"Remove Grapple Blocks in Hanubia - Ferenia Shortcut", None))
        self.hanubia_shortcut_no_grapple_label.setText(QCoreApplication.translate("PresetDreadPatches", u"<html><head/><body><p>Hanubia - Ferenia Shortcut, the room next to the elevator to Ferenia in Hanubia, has two Grapple Blocks that prevents access to Hanubia from this elevator.</p></body></html>", None))
        self.hanubia_easier_path_to_itorash_check.setText(QCoreApplication.translate("PresetDreadPatches", u"Remove Grapple and Wave locks in path to Itorash", None))
        self.hanubia_easier_path_to_itorash_label.setText(QCoreApplication.translate("PresetDreadPatches", u"Removes the Grapple Blocks and Wave Beam door locks on the top of Hanubia.", None))
        self.bosses_group.setTitle(QCoreApplication.translate("PresetDreadPatches", u"Bosses", None))
        self.raven_beak_damage_table_handling_check.setText(QCoreApplication.translate("PresetDreadPatches", u"Use alternate Raven Beak damage resistance", None))
        self.raven_beak_damage_table_handling_label.setText(QCoreApplication.translate("PresetDreadPatches", u"Normally, Raven Beak has a strong resistance to only Wave Beam and Ice Missiles. This setting decides how this inconsistency in damage resistance is addressed.\n"
"\n"
"When unchecked, the damage of all weapons will be reduced by the same factor as Wave Beam and Ice Missiles.\n"
"\n"
"When checked, the damage of Wave Beam and Ice Missiles will be increased to match that of Plasma Beam and Super Missiles, respectively.", None))
        self.x_group.setTitle(QCoreApplication.translate("PresetDreadPatches", u"X Parasites", None))
        self.x_starts_released_check.setText(QCoreApplication.translate("PresetDreadPatches", u"Start game with the X already released", None))
        self.x_starts_released_label.setText(QCoreApplication.translate("PresetDreadPatches", u"The X variant of enemies are stronger, making the game harder. This allows access to Golzuna and Experiment Z-57 without having to visit Elun.", None))
        self.miscellaneous_group.setTitle(QCoreApplication.translate("PresetDreadPatches", u"Miscellaneous", None))
        self.nerf_power_bombs_check.setText(QCoreApplication.translate("PresetDreadPatches", u"Power Bomb Limitations", None))
        self.nerf_power_bombs_label.setText(QCoreApplication.translate("PresetDreadPatches", u"The Power Bomb is one of the most powerful abilities in the game, as it can defeat most enemies and some bosses in one hit, as well as open Charge Beam doors, and destroy Enkies. \n"
"This setting removes the ability to destroy Enkies and open Charge Beam doors, making Ice Missiles and Charge Beam much more valuable. ", None))
        self.skip_item_popups_check.setText(QCoreApplication.translate("PresetDreadPatches", u"Skip Item Acquisition Popups", None))
        self.skip_item_popups_label.setText(QCoreApplication.translate("PresetDreadPatches", u"This setting causes the popup dialogs shown when collecting pickups to be skipped. Instead, a message is shown near the top of the screen for several seconds after collecting an \n"
"item, similar to the messages shown when receiving items in a Multiworld game.\n"
"              ", None))
    # retranslateUi

