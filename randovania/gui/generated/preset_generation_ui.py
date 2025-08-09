# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_generation.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QMainWindow,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

class Ui_PresetGeneration(object):
    def setupUi(self, PresetGeneration):
        if not PresetGeneration.objectName():
            PresetGeneration.setObjectName(u"PresetGeneration")
        PresetGeneration.resize(568, 561)
        self.centralWidget = QWidget(PresetGeneration)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(5, 5, 5, 5)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_contents = QWidget()
        self.scroll_contents.setObjectName(u"scroll_contents")
        self.scroll_contents.setGeometry(QRect(0, 0, 542, 1033))
        self.verticalLayout_3 = QVBoxLayout(self.scroll_contents)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 6, 0, 0)
        self.game_specific_group = QGroupBox(self.scroll_contents)
        self.game_specific_group.setObjectName(u"game_specific_group")
        self.verticalLayout_5 = QVBoxLayout(self.game_specific_group)
        self.verticalLayout_5.setSpacing(6)
        self.verticalLayout_5.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.game_specific_layout = QVBoxLayout()
        self.game_specific_layout.setSpacing(6)
        self.game_specific_layout.setObjectName(u"game_specific_layout")

        self.verticalLayout_5.addLayout(self.game_specific_layout)


        self.verticalLayout_3.addWidget(self.game_specific_group)

        self.randomization_mode_group = QGroupBox(self.scroll_contents)
        self.randomization_mode_group.setObjectName(u"randomization_mode_group")
        self.verticalLayout_2 = QVBoxLayout(self.randomization_mode_group)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.check_major_minor = QCheckBox(self.randomization_mode_group)
        self.check_major_minor.setObjectName(u"check_major_minor")

        self.verticalLayout_2.addWidget(self.check_major_minor)

        self.major_minor_label = QLabel(self.randomization_mode_group)
        self.major_minor_label.setObjectName(u"major_minor_label")
        self.major_minor_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.major_minor_label)

        self.line_2 = QFrame(self.randomization_mode_group)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.line_2)

        self.local_first_progression_check = QCheckBox(self.randomization_mode_group)
        self.local_first_progression_check.setObjectName(u"local_first_progression_check")

        self.verticalLayout_2.addWidget(self.local_first_progression_check)

        self.local_first_progression_label = QLabel(self.randomization_mode_group)
        self.local_first_progression_label.setObjectName(u"local_first_progression_label")
        self.local_first_progression_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.local_first_progression_label)

        self.logical_pickup_placement_line = QFrame(self.randomization_mode_group)
        self.logical_pickup_placement_line.setObjectName(u"logical_pickup_placement_line")
        self.logical_pickup_placement_line.setFrameShape(QFrame.Shape.HLine)
        self.logical_pickup_placement_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.logical_pickup_placement_line)

        self.logical_pickup_placement_layout = QHBoxLayout()
        self.logical_pickup_placement_layout.setSpacing(6)
        self.logical_pickup_placement_layout.setObjectName(u"logical_pickup_placement_layout")
        self.logical_pickup_placement_label = QLabel(self.randomization_mode_group)
        self.logical_pickup_placement_label.setObjectName(u"logical_pickup_placement_label")

        self.logical_pickup_placement_layout.addWidget(self.logical_pickup_placement_label)

        self.logical_pickup_placement_combo = QComboBox(self.randomization_mode_group)
        self.logical_pickup_placement_combo.addItem("")
        self.logical_pickup_placement_combo.addItem("")
        self.logical_pickup_placement_combo.addItem("")
        self.logical_pickup_placement_combo.setObjectName(u"logical_pickup_placement_combo")

        self.logical_pickup_placement_layout.addWidget(self.logical_pickup_placement_combo)


        self.verticalLayout_2.addLayout(self.logical_pickup_placement_layout)

        self.logical_pickup_placement_description = QLabel(self.randomization_mode_group)
        self.logical_pickup_placement_description.setObjectName(u"logical_pickup_placement_description")
        self.logical_pickup_placement_description.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.logical_pickup_placement_description)


        self.verticalLayout_3.addWidget(self.randomization_mode_group)

        self.logic_group = QGroupBox(self.scroll_contents)
        self.logic_group.setObjectName(u"logic_group")
        self.verticalLayout_4 = QVBoxLayout(self.logic_group)
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.dangerous_layout = QHBoxLayout()
        self.dangerous_layout.setSpacing(6)
        self.dangerous_layout.setObjectName(u"dangerous_layout")
        self.dangerous_label = QLabel(self.logic_group)
        self.dangerous_label.setObjectName(u"dangerous_label")

        self.dangerous_layout.addWidget(self.dangerous_label)

        self.dangerous_combo = QComboBox(self.logic_group)
        self.dangerous_combo.addItem("")
        self.dangerous_combo.addItem("")
        self.dangerous_combo.setObjectName(u"dangerous_combo")

        self.dangerous_layout.addWidget(self.dangerous_combo)


        self.verticalLayout_4.addLayout(self.dangerous_layout)

        self.dangerous_description = QLabel(self.logic_group)
        self.dangerous_description.setObjectName(u"dangerous_description")
        self.dangerous_description.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.dangerous_description)

        self.experimental_generator_line = QFrame(self.logic_group)
        self.experimental_generator_line.setObjectName(u"experimental_generator_line")
        self.experimental_generator_line.setFrameShape(QFrame.Shape.HLine)
        self.experimental_generator_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_4.addWidget(self.experimental_generator_line)

        self.check_if_beatable_after_base_patches_check = QCheckBox(self.logic_group)
        self.check_if_beatable_after_base_patches_check.setObjectName(u"check_if_beatable_after_base_patches_check")

        self.verticalLayout_4.addWidget(self.check_if_beatable_after_base_patches_check)

        self.consider_unsafe_line = QFrame(self.logic_group)
        self.consider_unsafe_line.setObjectName(u"consider_unsafe_line")
        self.consider_unsafe_line.setFrameShape(QFrame.Shape.HLine)
        self.consider_unsafe_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_4.addWidget(self.consider_unsafe_line)

        self.consider_unsafe_check = QCheckBox(self.logic_group)
        self.consider_unsafe_check.setObjectName(u"consider_unsafe_check")

        self.verticalLayout_4.addWidget(self.consider_unsafe_check)

        self.consider_unsafe_description = QLabel(self.logic_group)
        self.consider_unsafe_description.setObjectName(u"consider_unsafe_description")
        self.consider_unsafe_description.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.consider_unsafe_description)

        self.minimal_logic_line = QFrame(self.logic_group)
        self.minimal_logic_line.setObjectName(u"minimal_logic_line")
        self.minimal_logic_line.setFrameShape(QFrame.Shape.HLine)
        self.minimal_logic_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_4.addWidget(self.minimal_logic_line)

        self.trick_level_minimal_logic_check = QCheckBox(self.logic_group)
        self.trick_level_minimal_logic_check.setObjectName(u"trick_level_minimal_logic_check")

        self.verticalLayout_4.addWidget(self.trick_level_minimal_logic_check)

        self.trick_level_minimal_logic_label = QLabel(self.logic_group)
        self.trick_level_minimal_logic_label.setObjectName(u"trick_level_minimal_logic_label")
        self.trick_level_minimal_logic_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.trick_level_minimal_logic_label.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.trick_level_minimal_logic_label)


        self.verticalLayout_3.addWidget(self.logic_group)

        self.damage_strictness_group = QGroupBox(self.scroll_contents)
        self.damage_strictness_group.setObjectName(u"damage_strictness_group")
        self.damage_strictness_layout = QVBoxLayout(self.damage_strictness_group)
        self.damage_strictness_layout.setSpacing(6)
        self.damage_strictness_layout.setContentsMargins(11, 11, 11, 11)
        self.damage_strictness_layout.setObjectName(u"damage_strictness_layout")
        self.damage_strictness_label = QLabel(self.damage_strictness_group)
        self.damage_strictness_label.setObjectName(u"damage_strictness_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.damage_strictness_label.sizePolicy().hasHeightForWidth())
        self.damage_strictness_label.setSizePolicy(sizePolicy)
        self.damage_strictness_label.setWordWrap(True)

        self.damage_strictness_layout.addWidget(self.damage_strictness_label)

        self.damage_strictness_combo = QComboBox(self.damage_strictness_group)
        self.damage_strictness_combo.addItem("")
        self.damage_strictness_combo.addItem("")
        self.damage_strictness_combo.addItem("")
        self.damage_strictness_combo.setObjectName(u"damage_strictness_combo")

        self.damage_strictness_layout.addWidget(self.damage_strictness_combo)


        self.verticalLayout_3.addWidget(self.damage_strictness_group)

        self.scroll_area.setWidget(self.scroll_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        PresetGeneration.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetGeneration)

        QMetaObject.connectSlotsByName(PresetGeneration)
    # setupUi

    def retranslateUi(self, PresetGeneration):
        PresetGeneration.setWindowTitle(QCoreApplication.translate("PresetGeneration", u"Generation", None))
        self.game_specific_group.setTitle(QCoreApplication.translate("PresetGeneration", u"Game-specific Settings", None))
        self.randomization_mode_group.setTitle(QCoreApplication.translate("PresetGeneration", u"Item Placement", None))
        self.check_major_minor.setText(QCoreApplication.translate("PresetGeneration", u"Enable major/minor split", None))
        self.major_minor_label.setText(QCoreApplication.translate("PresetGeneration", u"<html><head/><body><p>If this setting is enabled, major items (e.g., major upgrades and keys to new areas) and minor items (i.e, ammo expansions) will be shuffled separately.<br/>Minor items in excess of the number of minor locations will be placed in major locations, but major items won't be placed in minor locations.</p></body></html>", None))
        self.local_first_progression_check.setText(QCoreApplication.translate("PresetGeneration", u"[Experimental] Require first progression to be local", None))
        self.local_first_progression_label.setText(QCoreApplication.translate("PresetGeneration", u"<html><head/><body><p>Ensures that that your first progression is placed in your own world, ensuring you always have something to do before potentially having to wait for progression.</p><p>This only changes anything in multiworld sessions.</p><p><span style=\" font-weight:700;\">Warning:</span> This will make generation fail more frequently. Use with caution in sessions with many players and random starting locations.</p></body></html>", None))
        self.logical_pickup_placement_label.setText(QCoreApplication.translate("PresetGeneration", u"[Experimental] Logical pickup placement:", None))
        self.logical_pickup_placement_combo.setItemText(0, QCoreApplication.translate("PresetGeneration", u"Minimal", None))
        self.logical_pickup_placement_combo.setItemText(1, QCoreApplication.translate("PresetGeneration", u"Major pickups", None))
        self.logical_pickup_placement_combo.setItemText(2, QCoreApplication.translate("PresetGeneration", u"All pickups", None))

        self.logical_pickup_placement_description.setText(QCoreApplication.translate("PresetGeneration", u"<html><head/><body><p><span style=\" font-weight:700;\">Minimal</span>: Only the pickups required to beat the game are guaranteed to be obtainable.</p></body></html>", None))
        self.logic_group.setTitle(QCoreApplication.translate("PresetGeneration", u"Logic Settings", None))
        self.dangerous_label.setText(QCoreApplication.translate("PresetGeneration", u"Dangerous actions:", None))
        self.dangerous_combo.setItemText(0, QCoreApplication.translate("PresetGeneration", u"Randomly", None))
        self.dangerous_combo.setItemText(1, QCoreApplication.translate("PresetGeneration", u"Last Resort", None))

        self.dangerous_description.setText(QCoreApplication.translate("PresetGeneration", u"<html><head/><body><p>A dangerous action is the act of moving past a lock without the appropriate items needed to head backwards, or doing an action that can only be done once.</p><p><span style=\" font-weight:600;\">Randomly</span>: Dangerous actions might be required by logic.</p><p><span style=\" font-weight:600;\">Last Resort</span>: Only allows dangerous actions to be required if no other option is available for progression.<br/>Warning: Due to how item placement works, certain locations will have progression extremely less often or even never.</p></body></html>", None))
        self.check_if_beatable_after_base_patches_check.setText(QCoreApplication.translate("PresetGeneration", u"[Experimental] Verify if game is beatable after deciding starting location, elevator, etc.", None))
        self.consider_unsafe_check.setText(QCoreApplication.translate("PresetGeneration", u"[Experimental] Consider possible unsafe resources", None))
        self.consider_unsafe_description.setText(QCoreApplication.translate("PresetGeneration", u"When determining weights for an action, check to see if the action can collect additional resources by passing through some dangerous connections. This improves the results of generation, but increases generation time.", None))
        self.trick_level_minimal_logic_check.setText(QCoreApplication.translate("PresetGeneration", u"Use Minimal Logic", None))
        self.trick_level_minimal_logic_label.setText(QCoreApplication.translate("PresetGeneration", u"<html><head/><body></p><p>Minimal Logic is a setting that checks for the bare minimum items to create an almost pure random layout. This setting assumes the player has extensive knowledge of the game and will likely require major glitches (e.g. breaking out of bounds) to complete.</p><p>There are no guarantees that a seed will be possible in this case.</p><p>{game_specific_text}</body></html>", None))
        self.damage_strictness_group.setTitle(QCoreApplication.translate("PresetGeneration", u"Damage strictness", None))
        self.damage_strictness_label.setText(QCoreApplication.translate("PresetGeneration", u"<html><head/><body><p>Certain locations, such as rooms with bosses or passive damage over time, require you to be able to take a certain amount of damage.</p><p>This setting controls how much energy the logic will expect you to have to reach these locations.</p></body></html>", None))
        self.damage_strictness_combo.setItemText(0, QCoreApplication.translate("PresetGeneration", u"Strict (1\u00d7)", None))
        self.damage_strictness_combo.setItemText(1, QCoreApplication.translate("PresetGeneration", u"Medium (1.5\u00d7)", None))
        self.damage_strictness_combo.setItemText(2, QCoreApplication.translate("PresetGeneration", u"Lenient (2\u00d7)", None))

        self.damage_strictness_combo.setCurrentText(QCoreApplication.translate("PresetGeneration", u"Strict (1\u00d7)", None))
    # retranslateUi

