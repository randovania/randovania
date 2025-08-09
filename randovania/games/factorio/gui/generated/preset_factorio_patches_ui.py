# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_factorio_patches.ui'
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
    QMainWindow, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_PresetFactorioPatches(object):
    def setupUi(self, PresetFactorioPatches):
        if not PresetFactorioPatches.objectName():
            PresetFactorioPatches.setObjectName(u"PresetFactorioPatches")
        PresetFactorioPatches.resize(466, 552)
        self.centralWidget = QWidget(PresetFactorioPatches)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.root_layout = QVBoxLayout(self.centralWidget)
        self.root_layout.setSpacing(6)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.root_layout.setContentsMargins(4, 4, 4, 4)
        self.tech_tree_group = QGroupBox(self.centralWidget)
        self.tech_tree_group.setObjectName(u"tech_tree_group")
        self.tech_tree_layout = QVBoxLayout(self.tech_tree_group)
        self.tech_tree_layout.setSpacing(6)
        self.tech_tree_layout.setContentsMargins(11, 11, 11, 11)
        self.tech_tree_layout.setObjectName(u"tech_tree_layout")
        self.full_tech_tree_check = QCheckBox(self.tech_tree_group)
        self.full_tech_tree_check.setObjectName(u"full_tech_tree_check")
        self.full_tech_tree_check.setEnabled(True)

        self.tech_tree_layout.addWidget(self.full_tech_tree_check)

        self.full_tech_tree_label = QLabel(self.tech_tree_group)
        self.full_tech_tree_label.setObjectName(u"full_tech_tree_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.full_tech_tree_label.sizePolicy().hasHeightForWidth())
        self.full_tech_tree_label.setSizePolicy(sizePolicy)
        self.full_tech_tree_label.setMaximumSize(QSize(16777215, 60))
        self.full_tech_tree_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.full_tech_tree_label.setWordWrap(True)
        self.full_tech_tree_label.setOpenExternalLinks(True)

        self.tech_tree_layout.addWidget(self.full_tech_tree_label)


        self.root_layout.addWidget(self.tech_tree_group)

        self.difficulty_group = QGroupBox(self.centralWidget)
        self.difficulty_group.setObjectName(u"difficulty_group")
        self.difficulty_layout = QVBoxLayout(self.difficulty_group)
        self.difficulty_layout.setSpacing(6)
        self.difficulty_layout.setContentsMargins(11, 11, 11, 11)
        self.difficulty_layout.setObjectName(u"difficulty_layout")
        self.allow_productivity_check = QCheckBox(self.difficulty_group)
        self.allow_productivity_check.setObjectName(u"allow_productivity_check")

        self.difficulty_layout.addWidget(self.allow_productivity_check)

        self.allow_productivity_label = QLabel(self.difficulty_group)
        self.allow_productivity_label.setObjectName(u"allow_productivity_label")
        self.allow_productivity_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.allow_productivity_label.setWordWrap(True)

        self.difficulty_layout.addWidget(self.allow_productivity_label)

        self.stronger_solar_check = QCheckBox(self.difficulty_group)
        self.stronger_solar_check.setObjectName(u"stronger_solar_check")

        self.difficulty_layout.addWidget(self.stronger_solar_check)

        self.stronger_solar_label = QLabel(self.difficulty_group)
        self.stronger_solar_label.setObjectName(u"stronger_solar_label")
        self.stronger_solar_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.stronger_solar_label.setWordWrap(True)

        self.difficulty_layout.addWidget(self.stronger_solar_label)


        self.root_layout.addWidget(self.difficulty_group)

        self.freebies_group = QGroupBox(self.centralWidget)
        self.freebies_group.setObjectName(u"freebies_group")
        self.freebies_layout = QVBoxLayout(self.freebies_group)
        self.freebies_layout.setSpacing(6)
        self.freebies_layout.setContentsMargins(11, 11, 11, 11)
        self.freebies_layout.setObjectName(u"freebies_layout")
        self.strict_multiplayer_freebie_check = QCheckBox(self.freebies_group)
        self.strict_multiplayer_freebie_check.setObjectName(u"strict_multiplayer_freebie_check")

        self.freebies_layout.addWidget(self.strict_multiplayer_freebie_check)

        self.strict_multiplayer_freebie_label = QLabel(self.freebies_group)
        self.strict_multiplayer_freebie_label.setObjectName(u"strict_multiplayer_freebie_label")
        self.strict_multiplayer_freebie_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.strict_multiplayer_freebie_label.setWordWrap(True)

        self.freebies_layout.addWidget(self.strict_multiplayer_freebie_label)


        self.root_layout.addWidget(self.freebies_group)

        self.vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.root_layout.addItem(self.vertical_spacer)

        PresetFactorioPatches.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetFactorioPatches)

        QMetaObject.connectSlotsByName(PresetFactorioPatches)
    # setupUi

    def retranslateUi(self, PresetFactorioPatches):
        PresetFactorioPatches.setWindowTitle(QCoreApplication.translate("PresetFactorioPatches", u"Other", None))
        self.tech_tree_group.setTitle(QCoreApplication.translate("PresetFactorioPatches", u"Tech Tree", None))
        self.full_tech_tree_check.setText(QCoreApplication.translate("PresetFactorioPatches", u"Full Tech Tree", None))
        self.full_tech_tree_label.setText(QCoreApplication.translate("PresetFactorioPatches", u"<html><head/><body><p>Include checks for every single tier of the damage and speed upgrades. When unchecked only the first two tiers are used.</p></body></html>", None))
        self.difficulty_group.setTitle(QCoreApplication.translate("PresetFactorioPatches", u"Difficulty", None))
        self.allow_productivity_check.setText(QCoreApplication.translate("PresetFactorioPatches", u"Allow Productivity Modules everywhere", None))
        self.allow_productivity_label.setText(QCoreApplication.translate("PresetFactorioPatches", u"When enabled, all recipes allow the use of Productivity Modules not just intermediates.\n"
"\n"
"Recommended, due the non-intermediates being valid science ingredients.", None))
        self.stronger_solar_check.setText(QCoreApplication.translate("PresetFactorioPatches", u"Stronger Solar Panels and Accumulators", None))
        self.stronger_solar_label.setText(QCoreApplication.translate("PresetFactorioPatches", u"Increases how much power a Solar Panel gives and how much energy an Accumulator holds to 4 times as much.\n"
"\n"
"Recommended, as Solar can be your only source of Electricity and scaling it in early game is very expensive.", None))
        self.freebies_group.setTitle(QCoreApplication.translate("PresetFactorioPatches", u"Freebies", None))
        self.strict_multiplayer_freebie_check.setText(QCoreApplication.translate("PresetFactorioPatches", u"Strict Freebies in Multiplayer", None))
        self.strict_multiplayer_freebie_label.setText(QCoreApplication.translate("PresetFactorioPatches", u"When enabled, guarantee that the total amount of items distributed is not more than in singleplayer, even if it  means some players get nothing.\n"
"\n"
"When disabled, every player is guaranteed at least one, even if you were offline. This includes vehicles and armors.", None))
    # retranslateUi

