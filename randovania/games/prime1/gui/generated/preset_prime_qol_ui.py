# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_prime_qol.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGroupBox,
    QLabel, QMainWindow, QScrollArea, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_PresetPrimeQol(object):
    def setupUi(self, PresetPrimeQol):
        if not PresetPrimeQol.objectName():
            PresetPrimeQol.setObjectName(u"PresetPrimeQol")
        PresetPrimeQol.resize(503, 687)
        self.centralWidget = QWidget(PresetPrimeQol)
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
        self.scroll_contents.setGeometry(QRect(0, 0, 487, 976))
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_layout.setObjectName(u"scroll_layout")
        self.scroll_layout.setContentsMargins(0, 2, 0, 0)
        self.top_spacer = QSpacerItem(20, 8, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.scroll_layout.addItem(self.top_spacer)

        self.description_label = QLabel(self.scroll_contents)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)
        self.description_label.setOpenExternalLinks(True)

        self.scroll_layout.addWidget(self.description_label)

        self.warp_to_start_group = QGroupBox(self.scroll_contents)
        self.warp_to_start_group.setObjectName(u"warp_to_start_group")
        self.verticalLayout_6 = QVBoxLayout(self.warp_to_start_group)
        self.verticalLayout_6.setSpacing(6)
        self.verticalLayout_6.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.warp_to_start_check = QCheckBox(self.warp_to_start_group)
        self.warp_to_start_check.setObjectName(u"warp_to_start_check")

        self.verticalLayout_6.addWidget(self.warp_to_start_check)

        self.warp_to_start_label = QLabel(self.warp_to_start_group)
        self.warp_to_start_label.setObjectName(u"warp_to_start_label")
        self.warp_to_start_label.setWordWrap(True)

        self.verticalLayout_6.addWidget(self.warp_to_start_label)


        self.scroll_layout.addWidget(self.warp_to_start_group)

        self.logical_group = QGroupBox(self.scroll_contents)
        self.logical_group.setObjectName(u"logical_group")
        self.verticalLayout_3 = QVBoxLayout(self.logical_group)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.logical_label = QLabel(self.logical_group)
        self.logical_label.setObjectName(u"logical_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.logical_label.sizePolicy().hasHeightForWidth())
        self.logical_label.setSizePolicy(sizePolicy)
        self.logical_label.setMaximumSize(QSize(16777215, 90))
        self.logical_label.setWordWrap(True)
        self.logical_label.setOpenExternalLinks(True)

        self.verticalLayout_3.addWidget(self.logical_label)

        self.main_plaza_door_check = QCheckBox(self.logical_group)
        self.main_plaza_door_check.setObjectName(u"main_plaza_door_check")

        self.verticalLayout_3.addWidget(self.main_plaza_door_check)

        self.main_plaza_door_label = QLabel(self.logical_group)
        self.main_plaza_door_label.setObjectName(u"main_plaza_door_label")
        self.main_plaza_door_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.main_plaza_door_label)

        self.backwards_frigate_check = QCheckBox(self.logical_group)
        self.backwards_frigate_check.setObjectName(u"backwards_frigate_check")

        self.verticalLayout_3.addWidget(self.backwards_frigate_check)

        self.backwards_frigate_label = QLabel(self.logical_group)
        self.backwards_frigate_label.setObjectName(u"backwards_frigate_label")
        self.backwards_frigate_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.backwards_frigate_label)

        self.backwards_labs_check = QCheckBox(self.logical_group)
        self.backwards_labs_check.setObjectName(u"backwards_labs_check")

        self.verticalLayout_3.addWidget(self.backwards_labs_check)

        self.backwards_labs_label = QLabel(self.logical_group)
        self.backwards_labs_label.setObjectName(u"backwards_labs_label")
        self.backwards_labs_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.backwards_labs_label)

        self.remove_bars_great_tree_hall_check = QCheckBox(self.logical_group)
        self.remove_bars_great_tree_hall_check.setObjectName(u"remove_bars_great_tree_hall_check")

        self.verticalLayout_3.addWidget(self.remove_bars_great_tree_hall_check)

        self.remove_bars_great_tree_hall_label = QLabel(self.logical_group)
        self.remove_bars_great_tree_hall_label.setObjectName(u"remove_bars_great_tree_hall_label")
        self.remove_bars_great_tree_hall_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.remove_bars_great_tree_hall_label)

        self.backwards_upper_mines_check = QCheckBox(self.logical_group)
        self.backwards_upper_mines_check.setObjectName(u"backwards_upper_mines_check")

        self.verticalLayout_3.addWidget(self.backwards_upper_mines_check)

        self.backwards_upper_mines_label = QLabel(self.logical_group)
        self.backwards_upper_mines_label.setObjectName(u"backwards_upper_mines_label")
        self.backwards_upper_mines_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.backwards_upper_mines_label)

        self.backwards_lower_mines_check = QCheckBox(self.logical_group)
        self.backwards_lower_mines_check.setObjectName(u"backwards_lower_mines_check")

        self.verticalLayout_3.addWidget(self.backwards_lower_mines_check)

        self.backwards_lower_mines_label = QLabel(self.logical_group)
        self.backwards_lower_mines_label.setObjectName(u"backwards_lower_mines_label")
        self.backwards_lower_mines_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.backwards_lower_mines_label)

        self.phazon_elite_without_dynamo_check = QCheckBox(self.logical_group)
        self.phazon_elite_without_dynamo_check.setObjectName(u"phazon_elite_without_dynamo_check")

        self.verticalLayout_3.addWidget(self.phazon_elite_without_dynamo_check)

        self.phazon_elite_without_dynamo_label = QLabel(self.logical_group)
        self.phazon_elite_without_dynamo_label.setObjectName(u"phazon_elite_without_dynamo_label")
        self.phazon_elite_without_dynamo_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.phazon_elite_without_dynamo_label)


        self.scroll_layout.addWidget(self.logical_group)

        self.cutscene_group = QGroupBox(self.scroll_contents)
        self.cutscene_group.setObjectName(u"cutscene_group")
        self.verticalLayout_5 = QVBoxLayout(self.cutscene_group)
        self.verticalLayout_5.setSpacing(6)
        self.verticalLayout_5.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.cutscene_combo = QComboBox(self.cutscene_group)
        self.cutscene_combo.addItem("")
        self.cutscene_combo.addItem("")
        self.cutscene_combo.addItem("")
        self.cutscene_combo.addItem("")
        self.cutscene_combo.setObjectName(u"cutscene_combo")

        self.verticalLayout_5.addWidget(self.cutscene_combo)

        self.cutscene_label = QLabel(self.cutscene_group)
        self.cutscene_label.setObjectName(u"cutscene_label")
        self.cutscene_label.setWordWrap(True)

        self.verticalLayout_5.addWidget(self.cutscene_label)


        self.scroll_layout.addWidget(self.cutscene_group)

        self.spring_ball_group = QGroupBox(self.scroll_contents)
        self.spring_ball_group.setObjectName(u"spring_ball_group")
        self.verticalLayout_9 = QVBoxLayout(self.spring_ball_group)
        self.verticalLayout_9.setSpacing(6)
        self.verticalLayout_9.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(9, 9, 9, 9)
        self.spring_ball_check = QCheckBox(self.spring_ball_group)
        self.spring_ball_check.setObjectName(u"spring_ball_check")

        self.verticalLayout_9.addWidget(self.spring_ball_check)

        self.spring_ball_label = QLabel(self.spring_ball_group)
        self.spring_ball_label.setObjectName(u"spring_ball_label")
        self.spring_ball_label.setWordWrap(True)

        self.verticalLayout_9.addWidget(self.spring_ball_label)


        self.scroll_layout.addWidget(self.spring_ball_group)

        self.scroll_area.setWidget(self.scroll_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        PresetPrimeQol.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetPrimeQol)

        QMetaObject.connectSlotsByName(PresetPrimeQol)
    # setupUi

    def retranslateUi(self, PresetPrimeQol):
        PresetPrimeQol.setWindowTitle(QCoreApplication.translate("PresetPrimeQol", u"Other", None))
        self.description_label.setText(QCoreApplication.translate("PresetPrimeQol", u"<html><head/><body><p>This tab offers various impovements over the base game to better suit it for randomization and frequent playing. Some improvements included with the randomizer are always enabled and thus not presented here.</p></body></html>", None))
        self.warp_to_start_group.setTitle(QCoreApplication.translate("PresetPrimeQol", u"Warp to Start", None))
        self.warp_to_start_check.setText(QCoreApplication.translate("PresetPrimeQol", u"Add warping to starting location from save stations", None))
        self.warp_to_start_label.setText(QCoreApplication.translate("PresetPrimeQol", u"<html><head/><body><p>Refusing to save at any Save Station while holding L+R will warp you to the starting location (by default, Samus' ship in Landing Site).</p></body></html>", None))
        self.logical_group.setTitle(QCoreApplication.translate("PresetPrimeQol", u"Logical changes", None))
        self.logical_label.setText(QCoreApplication.translate("PresetPrimeQol", u"<html><head/><body><p>These quality of life options affect the game world and therefore might affect the logical path the generator expects the player to traverse.</p></body></html>", None))
        self.main_plaza_door_check.setText(QCoreApplication.translate("PresetPrimeQol", u"Main Plaza Vault Door", None))
        self.main_plaza_door_label.setText(QCoreApplication.translate("PresetPrimeQol", u"Allow access to Vault from Main Plaza", None))
        self.backwards_frigate_check.setText(QCoreApplication.translate("PresetPrimeQol", u"Backwards Frigate", None))
        self.backwards_frigate_label.setText(QCoreApplication.translate("PresetPrimeQol", u"Power door in Main Ventilation Shaft Section B when approached from behind", None))
        self.backwards_labs_check.setText(QCoreApplication.translate("PresetPrimeQol", u"Backwards Labs", None))
        self.backwards_labs_label.setText(QCoreApplication.translate("PresetPrimeQol", u"Scan through barrier of Research Lab Hydra when approached from deep labs", None))
        self.remove_bars_great_tree_hall_check.setText(QCoreApplication.translate("PresetPrimeQol", u"Remove Bars in Great Tree Hall", None))
        self.remove_bars_great_tree_hall_label.setText(QCoreApplication.translate("PresetPrimeQol", u"Removes the Boost Ball bars obstacle in Tallon Overworld's Great Tree Hall allowing free movement between the lower and upper levels of the room", None))
        self.backwards_upper_mines_check.setText(QCoreApplication.translate("PresetPrimeQol", u"Backwards Upper Mines", None))
        self.backwards_upper_mines_label.setText(QCoreApplication.translate("PresetPrimeQol", u"Disable Main Quarry barrier automatically when approached from Mine Security Station", None))
        self.backwards_lower_mines_check.setText(QCoreApplication.translate("PresetPrimeQol", u"Backwards Lower Mines", None))
        self.backwards_lower_mines_label.setText(QCoreApplication.translate("PresetPrimeQol", u"Remove PCA locks and allow passing through lower mines scan barriers from the back", None))
        self.phazon_elite_without_dynamo_check.setText(QCoreApplication.translate("PresetPrimeQol", u"Phazon Elite without Dynamo", None))
        self.phazon_elite_without_dynamo_label.setText(QCoreApplication.translate("PresetPrimeQol", u"Removes the Central Dynamo item requirement for activating the Phazon Elite boss fight", None))
        self.cutscene_group.setTitle(QCoreApplication.translate("PresetPrimeQol", u"Cutscene Mode", None))
        self.cutscene_combo.setItemText(0, QCoreApplication.translate("PresetPrimeQol", u"Original", None))
        self.cutscene_combo.setItemText(1, QCoreApplication.translate("PresetPrimeQol", u"Skippable", None))
        self.cutscene_combo.setItemText(2, QCoreApplication.translate("PresetPrimeQol", u"Competitive", None))
        self.cutscene_combo.setItemText(3, QCoreApplication.translate("PresetPrimeQol", u"Major [Deprecated]", None))

        self.cutscene_label.setText(QCoreApplication.translate("PresetPrimeQol", u"<html><head/><body><p><span style=\" font-weight:600;\">Original</span>: No changes to the cutscenes are made.</p><p><span style=\" font-weight:700;\">Skippable</span>: Keeps all of the cutscenes in the game, but makes it so that they can be skipped with the START button.</p><p><span style=\" font-weight:700;\">Competitive</span>: Removes some cutscenes from the game which hinder the flow of competitive play. All others are skippable.</p></body></html>", None))
        self.spring_ball_group.setTitle(QCoreApplication.translate("PresetPrimeQol", u"Spring Ball", None))
        self.spring_ball_check.setText(QCoreApplication.translate("PresetPrimeQol", u"Enable Spring Ball", None))
        self.spring_ball_label.setText(QCoreApplication.translate("PresetPrimeQol", u"<html><head/><body><p>Restores the Spring Ball feature from Metroid Prime Trilogy.<br/>Use C-Stick Up while being morphed to use Spring Ball.<br/><br/><span style=\" font-weight:600;\">Warning:</span> You need Morph Ball Bombs to use Spring Ball just like in Metroid Prime Trilogy.</p></body></html>", None))
    # retranslateUi

