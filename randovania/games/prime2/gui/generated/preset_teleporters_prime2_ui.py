# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_teleporters_prime2.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QGridLayout,
    QGroupBox, QLabel, QMainWindow, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget)

from randovania.gui.lib.scroll_protected import ScrollProtectedComboBox

class Ui_PresetTeleportersPrime2(object):
    def setupUi(self, PresetTeleportersPrime2):
        if not PresetTeleportersPrime2.objectName():
            PresetTeleportersPrime2.setObjectName(u"PresetTeleportersPrime2")
        PresetTeleportersPrime2.resize(505, 463)
        self.centralWidget = QWidget(PresetTeleportersPrime2)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.teleporter_parent_layout = QVBoxLayout(self.centralWidget)
        self.teleporter_parent_layout.setSpacing(6)
        self.teleporter_parent_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporter_parent_layout.setObjectName(u"teleporter_parent_layout")
        self.teleporter_parent_layout.setContentsMargins(0, 0, 0, 0)
        self.teleporter_scroll_area = QScrollArea(self.centralWidget)
        self.teleporter_scroll_area.setObjectName(u"teleporter_scroll_area")
        self.teleporter_scroll_area.setWidgetResizable(True)
        self.teleporter_scroll_area_contents = QWidget()
        self.teleporter_scroll_area_contents.setObjectName(u"teleporter_scroll_area_contents")
        self.teleporter_scroll_area_contents.setGeometry(QRect(0, 0, 524, 471))
        self.teleporters_layout = QVBoxLayout(self.teleporter_scroll_area_contents)
        self.teleporters_layout.setSpacing(6)
        self.teleporters_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporters_layout.setObjectName(u"teleporters_layout")
        self.teleporters_layout.setContentsMargins(4, 6, 4, 0)
        self.teleporters_combo = ScrollProtectedComboBox(self.teleporter_scroll_area_contents)
        self.teleporters_combo.setObjectName(u"teleporters_combo")

        self.teleporters_layout.addWidget(self.teleporters_combo)

        self.teleporters_description_label = QLabel(self.teleporter_scroll_area_contents)
        self.teleporters_description_label.setObjectName(u"teleporters_description_label")
        self.teleporters_description_label.setScaledContents(True)
        self.teleporters_description_label.setWordWrap(True)

        self.teleporters_layout.addWidget(self.teleporters_description_label)

        self.teleporters_help_sound_bug_label = QLabel(self.teleporter_scroll_area_contents)
        self.teleporters_help_sound_bug_label.setObjectName(u"teleporters_help_sound_bug_label")

        self.teleporters_layout.addWidget(self.teleporters_help_sound_bug_label)

        self.teleporters_line_2 = QFrame(self.teleporter_scroll_area_contents)
        self.teleporters_line_2.setObjectName(u"teleporters_line_2")
        self.teleporters_line_2.setFrameShape(QFrame.Shape.HLine)
        self.teleporters_line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.teleporters_layout.addWidget(self.teleporters_line_2)

        self.skip_final_bosses_check = QCheckBox(self.teleporter_scroll_area_contents)
        self.skip_final_bosses_check.setObjectName(u"skip_final_bosses_check")

        self.teleporters_layout.addWidget(self.skip_final_bosses_check)

        self.skip_final_bosses_label = QLabel(self.teleporter_scroll_area_contents)
        self.skip_final_bosses_label.setObjectName(u"skip_final_bosses_label")
        self.skip_final_bosses_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.skip_final_bosses_label.setWordWrap(True)

        self.teleporters_layout.addWidget(self.skip_final_bosses_label)

        self.teleporters_line_4 = QFrame(self.teleporter_scroll_area_contents)
        self.teleporters_line_4.setObjectName(u"teleporters_line_4")
        self.teleporters_line_4.setFrameShape(QFrame.Shape.HLine)
        self.teleporters_line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.teleporters_layout.addWidget(self.teleporters_line_4)

        self.teleporters_allow_unvisited_names_check = QCheckBox(self.teleporter_scroll_area_contents)
        self.teleporters_allow_unvisited_names_check.setObjectName(u"teleporters_allow_unvisited_names_check")

        self.teleporters_layout.addWidget(self.teleporters_allow_unvisited_names_check)

        self.teleporters_line_3 = QFrame(self.teleporter_scroll_area_contents)
        self.teleporters_line_3.setObjectName(u"teleporters_line_3")
        self.teleporters_line_3.setFrameShape(QFrame.Shape.HLine)
        self.teleporters_line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.teleporters_layout.addWidget(self.teleporters_line_3)

        self.teleporters_help_list_label = QLabel(self.teleporter_scroll_area_contents)
        self.teleporters_help_list_label.setObjectName(u"teleporters_help_list_label")
        self.teleporters_help_list_label.setWordWrap(True)

        self.teleporters_layout.addWidget(self.teleporters_help_list_label)

        self.teleporters_source_group = QGroupBox(self.teleporter_scroll_area_contents)
        self.teleporters_source_group.setObjectName(u"teleporters_source_group")
        self.teleporters_source_layout = QGridLayout(self.teleporters_source_group)
        self.teleporters_source_layout.setSpacing(3)
        self.teleporters_source_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporters_source_layout.setObjectName(u"teleporters_source_layout")
        self.teleporters_source_layout.setContentsMargins(1, 1, 1, 1)

        self.teleporters_layout.addWidget(self.teleporters_source_group)

        self.teleporters_target_group = QGroupBox(self.teleporter_scroll_area_contents)
        self.teleporters_target_group.setObjectName(u"teleporters_target_group")
        self.teleporters_target_layout = QGridLayout(self.teleporters_target_group)
        self.teleporters_target_layout.setSpacing(3)
        self.teleporters_target_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporters_target_layout.setObjectName(u"teleporters_target_layout")
        self.teleporters_target_layout.setContentsMargins(1, 1, 1, 1)

        self.teleporters_layout.addWidget(self.teleporters_target_group)

        self.teleporter_scroll_area.setWidget(self.teleporter_scroll_area_contents)

        self.teleporter_parent_layout.addWidget(self.teleporter_scroll_area)

        PresetTeleportersPrime2.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetTeleportersPrime2)

        QMetaObject.connectSlotsByName(PresetTeleportersPrime2)
    # setupUi

    def retranslateUi(self, PresetTeleportersPrime2):
        PresetTeleportersPrime2.setWindowTitle(QCoreApplication.translate("PresetTeleportersPrime2", u"Elevators", None))
        self.teleporters_description_label.setText(QCoreApplication.translate("PresetTeleportersPrime2", u"<html><head/><body><p>&lt;description generated dynamically&gt;</p></body></html>", None))
        self.teleporters_help_sound_bug_label.setText(QCoreApplication.translate("PresetTeleportersPrime2", u"These settings will cause the teleporter cutscenes to be silent in order to avoid a different game bug.", None))
        self.skip_final_bosses_check.setText(QCoreApplication.translate("PresetTeleportersPrime2", u"Go directly to credits from Sky Temple Gateway", None))
        self.skip_final_bosses_label.setText(QCoreApplication.translate("PresetTeleportersPrime2", u"<html><head/><body><p>Change the light beam in Sky Temple Gateway to go directly to the credits, skipping the final bosses.</p><p>This changes the requirements to <span style=\" font-weight:600;\">not need the final bosses</span>, turning certain items optional such as Screw Attack and Spider Ball.</p></body></html>", None))
        self.teleporters_allow_unvisited_names_check.setText(QCoreApplication.translate("PresetTeleportersPrime2", u"Allow \"Always display room names on map\" when teleporters are shuffled", None))
        self.teleporters_help_list_label.setText(QCoreApplication.translate("PresetTeleportersPrime2", u"<html><head/><body><p>Shuffling Sky Temple Gateway, Sky Temple Energy Controller, Aerie and Aerie Transport Station is possible, but they're not included by default as they behave somewhat differently to other teleporters.</p><p>The teleporter in Aerie Transport Station is only available after you defeat Dark Samus 2.</p><p>When shuffling Sky Temple Energy Controller, you <span style=\" font-weight:600;\">must</span> enter Sky Temple Gateway via an teleporter otherwise the game will crash.</p><p><span style=\" font-style:italic;\">Warning</span>: Entering Sky Temple Energy Controller from elsewhere causes the game to be stuck in a black screen in unknown conditions. The game is still running, so you can blindly use the menu mod to work around this issue.</p></body></html>", None))
        self.teleporters_source_group.setTitle(QCoreApplication.translate("PresetTeleportersPrime2", u"Elevators to randomize", None))
        self.teleporters_target_group.setTitle(QCoreApplication.translate("PresetTeleportersPrime2", u"Valid teleporter targets", None))
    # retranslateUi

