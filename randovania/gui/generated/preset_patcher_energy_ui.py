# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_patcher_energy.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QDoubleSpinBox, QFrame, QGridLayout, QGroupBox,
    QLabel, QMainWindow, QScrollArea, QSizePolicy,
    QSpacerItem, QSpinBox, QVBoxLayout, QWidget)

class Ui_PresetPatcherEnergy(object):
    def setupUi(self, PresetPatcherEnergy):
        if not PresetPatcherEnergy.objectName():
            PresetPatcherEnergy.setObjectName(u"PresetPatcherEnergy")
        PresetPatcherEnergy.resize(476, 628)
        self.centralWidget = QWidget(PresetPatcherEnergy)
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
        self.scroll_area_contents.setGeometry(QRect(0, 0, 460, 1151))
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
        self.energy_tank_box = QGroupBox(self.scroll_area_contents)
        self.energy_tank_box.setObjectName(u"energy_tank_box")
        self.gridLayout_2 = QGridLayout(self.energy_tank_box)
        self.gridLayout_2.setSpacing(6)
        self.gridLayout_2.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.energy_tank_capacity_label = QLabel(self.energy_tank_box)
        self.energy_tank_capacity_label.setObjectName(u"energy_tank_capacity_label")

        self.gridLayout_2.addWidget(self.energy_tank_capacity_label, 2, 0, 1, 1)

        self.energy_tank_capacity_spin_box = QSpinBox(self.energy_tank_box)
        self.energy_tank_capacity_spin_box.setObjectName(u"energy_tank_capacity_spin_box")
        self.energy_tank_capacity_spin_box.setMinimum(2)
        self.energy_tank_capacity_spin_box.setMaximum(1000)

        self.gridLayout_2.addWidget(self.energy_tank_capacity_spin_box, 2, 1, 1, 1)

        self.dangerous_tank_check = QCheckBox(self.energy_tank_box)
        self.dangerous_tank_check.setObjectName(u"dangerous_tank_check")

        self.gridLayout_2.addWidget(self.dangerous_tank_check, 4, 0, 1, 2)

        self.line = QFrame(self.energy_tank_box)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_2.addWidget(self.line, 3, 0, 1, 2)

        self.energy_tank_capacity_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.gridLayout_2.addItem(self.energy_tank_capacity_spacer, 1, 0, 1, 2)

        self.energy_tank_capacity_description = QLabel(self.energy_tank_box)
        self.energy_tank_capacity_description.setObjectName(u"energy_tank_capacity_description")
        self.energy_tank_capacity_description.setWordWrap(True)

        self.gridLayout_2.addWidget(self.energy_tank_capacity_description, 0, 0, 1, 2)


        self.scroll_area_layout.addWidget(self.energy_tank_box)

        self.safe_zone_box = QGroupBox(self.scroll_area_contents)
        self.safe_zone_box.setObjectName(u"safe_zone_box")
        self.gridLayout = QGridLayout(self.safe_zone_box)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.safe_zone_regen_spin = QDoubleSpinBox(self.safe_zone_box)
        self.safe_zone_regen_spin.setObjectName(u"safe_zone_regen_spin")
        self.safe_zone_regen_spin.setMaximum(100.000000000000000)
        self.safe_zone_regen_spin.setSingleStep(0.100000000000000)
        self.safe_zone_regen_spin.setValue(1.000000000000000)

        self.gridLayout.addWidget(self.safe_zone_regen_spin, 2, 1, 1, 1)

        self.safe_zone_regen_label = QLabel(self.safe_zone_box)
        self.safe_zone_regen_label.setObjectName(u"safe_zone_regen_label")

        self.gridLayout.addWidget(self.safe_zone_regen_label, 2, 0, 1, 1)

        self.safe_zone_logic_heal_check = QCheckBox(self.safe_zone_box)
        self.safe_zone_logic_heal_check.setObjectName(u"safe_zone_logic_heal_check")
        self.safe_zone_logic_heal_check.setEnabled(False)
        self.safe_zone_logic_heal_check.setChecked(True)

        self.gridLayout.addWidget(self.safe_zone_logic_heal_check, 1, 0, 1, 2)

        self.safe_zone_description = QLabel(self.safe_zone_box)
        self.safe_zone_description.setObjectName(u"safe_zone_description")
        self.safe_zone_description.setWordWrap(True)

        self.gridLayout.addWidget(self.safe_zone_description, 0, 0, 1, 2)


        self.scroll_area_layout.addWidget(self.safe_zone_box)

        self.dark_aether_box = QGroupBox(self.scroll_area_contents)
        self.dark_aether_box.setObjectName(u"dark_aether_box")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.dark_aether_box.sizePolicy().hasHeightForWidth())
        self.dark_aether_box.setSizePolicy(sizePolicy1)
        self.dark_aether_layout_2 = QGridLayout(self.dark_aether_box)
        self.dark_aether_layout_2.setSpacing(6)
        self.dark_aether_layout_2.setContentsMargins(11, 11, 11, 11)
        self.dark_aether_layout_2.setObjectName(u"dark_aether_layout_2")
        self.varia_suit_spin_box = QDoubleSpinBox(self.dark_aether_box)
        self.varia_suit_spin_box.setObjectName(u"varia_suit_spin_box")
        self.varia_suit_spin_box.setMaximum(60.000000000000000)
        self.varia_suit_spin_box.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        self.varia_suit_spin_box.setValue(6.000000000000000)

        self.dark_aether_layout_2.addWidget(self.varia_suit_spin_box, 2, 1, 1, 1)

        self.varia_suit_label = QLabel(self.dark_aether_box)
        self.varia_suit_label.setObjectName(u"varia_suit_label")

        self.dark_aether_layout_2.addWidget(self.varia_suit_label, 2, 0, 1, 1)

        self.dark_suit_label = QLabel(self.dark_aether_box)
        self.dark_suit_label.setObjectName(u"dark_suit_label")

        self.dark_aether_layout_2.addWidget(self.dark_suit_label, 3, 0, 1, 1)

        self.dark_suit_spin_box = QDoubleSpinBox(self.dark_aether_box)
        self.dark_suit_spin_box.setObjectName(u"dark_suit_spin_box")
        self.dark_suit_spin_box.setMaximum(60.000000000000000)
        self.dark_suit_spin_box.setStepType(QAbstractSpinBox.AdaptiveDecimalStepType)
        self.dark_suit_spin_box.setValue(1.200000000000000)

        self.dark_aether_layout_2.addWidget(self.dark_suit_spin_box, 3, 1, 1, 1)

        self.dark_aether_label = QLabel(self.dark_aether_box)
        self.dark_aether_label.setObjectName(u"dark_aether_label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.dark_aether_label.sizePolicy().hasHeightForWidth())
        self.dark_aether_label.setSizePolicy(sizePolicy2)
        self.dark_aether_label.setWordWrap(True)

        self.dark_aether_layout_2.addWidget(self.dark_aether_label, 0, 0, 1, 2)

        self.dark_aether_box_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.dark_aether_layout_2.addItem(self.dark_aether_box_spacer, 1, 0, 1, 2)


        self.scroll_area_layout.addWidget(self.dark_aether_box)

        self.damage_reduction_box = QGroupBox(self.scroll_area_contents)
        self.damage_reduction_box.setObjectName(u"damage_reduction_box")
        self.gridLayout_5 = QGridLayout(self.damage_reduction_box)
        self.gridLayout_5.setSpacing(6)
        self.gridLayout_5.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.damage_reduction_label = QLabel(self.damage_reduction_box)
        self.damage_reduction_label.setObjectName(u"damage_reduction_label")
        self.damage_reduction_label.setWordWrap(True)

        self.gridLayout_5.addWidget(self.damage_reduction_label, 0, 0, 1, 1)

        self.damage_reduction_combo = QComboBox(self.damage_reduction_box)
        self.damage_reduction_combo.addItem("")
        self.damage_reduction_combo.addItem("")
        self.damage_reduction_combo.addItem("")
        self.damage_reduction_combo.setObjectName(u"damage_reduction_combo")

        self.gridLayout_5.addWidget(self.damage_reduction_combo, 1, 0, 1, 1)


        self.scroll_area_layout.addWidget(self.damage_reduction_box)

        self.heated_damage_box = QGroupBox(self.scroll_area_contents)
        self.heated_damage_box.setObjectName(u"heated_damage_box")
        self.gridLayout_3 = QGridLayout(self.heated_damage_box)
        self.gridLayout_3.setSpacing(6)
        self.gridLayout_3.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.heated_damage_spin = QDoubleSpinBox(self.heated_damage_box)
        self.heated_damage_spin.setObjectName(u"heated_damage_spin")
        self.heated_damage_spin.setMaximum(100.000000000000000)
        self.heated_damage_spin.setSingleStep(0.100000000000000)
        self.heated_damage_spin.setValue(1.000000000000000)

        self.gridLayout_3.addWidget(self.heated_damage_spin, 1, 1, 1, 1)

        self.heated_damage_label = QLabel(self.heated_damage_box)
        self.heated_damage_label.setObjectName(u"heated_damage_label")

        self.gridLayout_3.addWidget(self.heated_damage_label, 1, 0, 1, 1)

        self.heated_damage_description = QLabel(self.heated_damage_box)
        self.heated_damage_description.setObjectName(u"heated_damage_description")
        self.heated_damage_description.setWordWrap(True)

        self.gridLayout_3.addWidget(self.heated_damage_description, 0, 0, 1, 2)


        self.scroll_area_layout.addWidget(self.heated_damage_box)

        self.ingame_difficulty_box = QGroupBox(self.scroll_area_contents)
        self.ingame_difficulty_box.setObjectName(u"ingame_difficulty_box")
        self.gridLayout_6 = QGridLayout(self.ingame_difficulty_box)
        self.gridLayout_6.setSpacing(6)
        self.gridLayout_6.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.ingame_difficulty_label = QLabel(self.ingame_difficulty_box)
        self.ingame_difficulty_label.setObjectName(u"ingame_difficulty_label")
        self.ingame_difficulty_label.setWordWrap(True)

        self.gridLayout_6.addWidget(self.ingame_difficulty_label, 0, 0, 1, 1)

        self.ingame_difficulty_combo = QComboBox(self.ingame_difficulty_box)
        self.ingame_difficulty_combo.addItem("")
        self.ingame_difficulty_combo.addItem("")
        self.ingame_difficulty_combo.addItem("")
        self.ingame_difficulty_combo.setObjectName(u"ingame_difficulty_combo")

        self.gridLayout_6.addWidget(self.ingame_difficulty_combo, 1, 0, 1, 1)


        self.scroll_area_layout.addWidget(self.ingame_difficulty_box)

        self.energy_tank_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.energy_tank_spacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.main_layout.addWidget(self.scroll_area)

        PresetPatcherEnergy.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetPatcherEnergy)

        QMetaObject.connectSlotsByName(PresetPatcherEnergy)
    # setupUi

    def retranslateUi(self, PresetPatcherEnergy):
        PresetPatcherEnergy.setWindowTitle(QCoreApplication.translate("PresetPatcherEnergy", u"Energy", None))
        self.energy_tank_box.setTitle(QCoreApplication.translate("PresetPatcherEnergy", u"Energy tank", None))
        self.energy_tank_capacity_label.setText(QCoreApplication.translate("PresetPatcherEnergy", u"Energy per tank", None))
        self.energy_tank_capacity_spin_box.setSuffix(QCoreApplication.translate("PresetPatcherEnergy", u" energy", None))
        self.dangerous_tank_check.setText(QCoreApplication.translate("PresetPatcherEnergy", u"1 HP mode. In this mode, Energy Tanks and Save Stations leave you at 1 HP instead", None))
        self.energy_tank_capacity_description.setText(QCoreApplication.translate("PresetPatcherEnergy", u"<html><head/><body><p>Configure how much energy each Energy Tank you collect will provide. Your base energy is always this quantity, minus 1.</p><p>While logic will respect this value, only the original value (100) has been tested.</p></body></html>", None))
        self.safe_zone_box.setTitle(QCoreApplication.translate("PresetPatcherEnergy", u"Safe zone", None))
        self.safe_zone_regen_spin.setSuffix(QCoreApplication.translate("PresetPatcherEnergy", u" energy/s", None))
        self.safe_zone_regen_label.setText(QCoreApplication.translate("PresetPatcherEnergy", u"Safe Zone healing rate", None))
        self.safe_zone_logic_heal_check.setText(QCoreApplication.translate("PresetPatcherEnergy", u"Logic considers fully healing at every safe zone. This is currently always on.", None))
        self.safe_zone_description.setText(QCoreApplication.translate("PresetPatcherEnergy", u"<html><head/><body><p>Configure how Dark Aether safe zones operate and how logic uses them.</p></body></html>", None))
        self.dark_aether_box.setTitle(QCoreApplication.translate("PresetPatcherEnergy", u"Dark Aether", None))
        self.varia_suit_spin_box.setSuffix(QCoreApplication.translate("PresetPatcherEnergy", u" energy/s", None))
        self.varia_suit_label.setText(QCoreApplication.translate("PresetPatcherEnergy", u"Varia Suit", None))
        self.dark_suit_label.setText(QCoreApplication.translate("PresetPatcherEnergy", u"Dark Suit", None))
        self.dark_suit_spin_box.setSuffix(QCoreApplication.translate("PresetPatcherEnergy", u" energy/s", None))
        self.dark_aether_label.setText(QCoreApplication.translate("PresetPatcherEnergy", u"<html><head/><body><p>Configure how much damage per second you take in Dark Aether, per suit.<br/>Light Suit is always immune.</p></body></html>", None))
        self.damage_reduction_box.setTitle(QCoreApplication.translate("PresetPatcherEnergy", u"Damage reduction", None))
        self.damage_reduction_label.setText(QCoreApplication.translate("PresetPatcherEnergy", u"<html><head/><body><p>Configure how damage reduction is applied, according to what suits you have:</p><p><span style=\" font-weight:704;\">Original:</span> Having Varia Suit reduces damage by 10%, Gravity Suit by 20%, and Phazon Suit by 50%. The highest value suit overrides other suits.</p><p><span style=\" font-weight:704;\">Progressive:</span> Having one suit reduces damage by 10%, two suits by 20%, and having all suits reduces damage by 50%.</p><p><span style=\" font-weight:704;\">Additive:</span> Each suit has a respective damage reduction value, which are added together to determine total damage reduction. Varia and Gravity Suit each add 10% to total damage reduction, and Phazon Suit adds 30%. Phazon and one other suit would reduce damage by 40% total.</p></body></html>", None))
        self.damage_reduction_combo.setItemText(0, QCoreApplication.translate("PresetPatcherEnergy", u"Original", None))
        self.damage_reduction_combo.setItemText(1, QCoreApplication.translate("PresetPatcherEnergy", u"Progressive", None))
        self.damage_reduction_combo.setItemText(2, QCoreApplication.translate("PresetPatcherEnergy", u"Additive", None))

        self.heated_damage_box.setTitle(QCoreApplication.translate("PresetPatcherEnergy", u"Heated rooms", None))
        self.heated_damage_spin.setSuffix(QCoreApplication.translate("PresetPatcherEnergy", u" energy/s", None))
        self.heated_damage_label.setText(QCoreApplication.translate("PresetPatcherEnergy", u"Heated damage rate", None))
        self.heated_damage_description.setText(QCoreApplication.translate("PresetPatcherEnergy", u"<html><head/><body><p>Configure how much damage per second you take in heated rooms, when you don't have proper protection.</p></body></html>", None))
        self.ingame_difficulty_box.setTitle(QCoreApplication.translate("PresetPatcherEnergy", u"In-Game Difficulty", None))
        self.ingame_difficulty_label.setText(QCoreApplication.translate("PresetPatcherEnergy", u"<html><head/><body><p>Control how the in-game difficulty options are presented to the player when starting a new Save Slot in the Main Menu:</p><p><span style=\" font-weight:700;\">Normal: </span>The player is forced to select &quot;Normal&quot; difficulty</p><p><span style=\" font-weight:700;\">Hard: </span>The player is forced to select &quot;Hard&quot; difficulty and the seed will be generated using adjusted damage/energy requirements</p><p><span style=\" font-weight:700;\">Either (Not Recommended): </span>The player may select either the difficulty. If the player chooses to play on &quot;Hard&quot;, the seed may not be completable because of logic differences</p></body></html>", None))
        self.ingame_difficulty_combo.setItemText(0, QCoreApplication.translate("PresetPatcherEnergy", u"Normal", None))
        self.ingame_difficulty_combo.setItemText(1, QCoreApplication.translate("PresetPatcherEnergy", u"Hard", None))
        self.ingame_difficulty_combo.setItemText(2, QCoreApplication.translate("PresetPatcherEnergy", u"Either", None))

    # retranslateUi

