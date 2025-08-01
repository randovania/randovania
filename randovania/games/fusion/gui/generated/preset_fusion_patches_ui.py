# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_fusion_patches.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QScrollArea, QSizePolicy,
    QSpacerItem, QSpinBox, QVBoxLayout, QWidget)

class Ui_PresetFusionPatches(object):
    def setupUi(self, PresetFusionPatches):
        if not PresetFusionPatches.objectName():
            PresetFusionPatches.setObjectName(u"PresetFusionPatches")
        PresetFusionPatches.resize(725, 408)
        self.root_widget = QWidget(PresetFusionPatches)
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
        self.scroll_contents.setGeometry(QRect(0, 0, 709, 422))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_contents.sizePolicy().hasHeightForWidth())
        self.scroll_contents.setSizePolicy(sizePolicy)
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_layout.setObjectName(u"scroll_layout")
        self.scroll_layout.setContentsMargins(0, 2, 0, 0)
        self.top_spacer = QSpacerItem(20, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.scroll_layout.addItem(self.top_spacer)

        self.energy_group = QGroupBox(self.scroll_contents)
        self.energy_group.setObjectName(u"energy_group")
        self.verticalLayout_2 = QVBoxLayout(self.energy_group)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.etank_description_label = QLabel(self.energy_group)
        self.etank_description_label.setObjectName(u"etank_description_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.etank_description_label.sizePolicy().hasHeightForWidth())
        self.etank_description_label.setSizePolicy(sizePolicy1)
        self.etank_description_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.etank_description_label)

        self.etank_layout = QHBoxLayout()
        self.etank_layout.setSpacing(6)
        self.etank_layout.setObjectName(u"etank_layout")
        self.etank_layout.setContentsMargins(-1, 0, -1, -1)
        self.etank_capacity_label = QLabel(self.energy_group)
        self.etank_capacity_label.setObjectName(u"etank_capacity_label")
        self.etank_capacity_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.etank_layout.addWidget(self.etank_capacity_label)

        self.etank_capacity_spin_box = QSpinBox(self.energy_group)
        self.etank_capacity_spin_box.setObjectName(u"etank_capacity_spin_box")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.etank_capacity_spin_box.sizePolicy().hasHeightForWidth())
        self.etank_capacity_spin_box.setSizePolicy(sizePolicy2)
        self.etank_capacity_spin_box.setMinimum(1)
        self.etank_capacity_spin_box.setMaximum(1000)

        self.etank_layout.addWidget(self.etank_capacity_spin_box)


        self.verticalLayout_2.addLayout(self.etank_layout)


        self.scroll_layout.addWidget(self.energy_group)

        self.room_group = QGroupBox(self.scroll_contents)
        self.room_group.setObjectName(u"room_group")
        self.unlock_layout = QVBoxLayout(self.room_group)
        self.unlock_layout.setSpacing(6)
        self.unlock_layout.setContentsMargins(11, 11, 11, 11)
        self.unlock_layout.setObjectName(u"unlock_layout")
        self.anti_softlock_check = QCheckBox(self.room_group)
        self.anti_softlock_check.setObjectName(u"anti_softlock_check")

        self.unlock_layout.addWidget(self.anti_softlock_check)

        self.anti_softlock_label = QLabel(self.room_group)
        self.anti_softlock_label.setObjectName(u"anti_softlock_label")
        sizePolicy1.setHeightForWidth(self.anti_softlock_label.sizePolicy().hasHeightForWidth())
        self.anti_softlock_label.setSizePolicy(sizePolicy1)
        self.anti_softlock_label.setWordWrap(True)

        self.unlock_layout.addWidget(self.anti_softlock_label)


        self.scroll_layout.addWidget(self.room_group)

        self.gameplay_group = QGroupBox(self.scroll_contents)
        self.gameplay_group.setObjectName(u"gameplay_group")
        self.instant_transitions_layout = QVBoxLayout(self.gameplay_group)
        self.instant_transitions_layout.setSpacing(6)
        self.instant_transitions_layout.setContentsMargins(11, 11, 11, 11)
        self.instant_transitions_layout.setObjectName(u"instant_transitions_layout")
        self.instant_transitions_check = QCheckBox(self.gameplay_group)
        self.instant_transitions_check.setObjectName(u"instant_transitions_check")

        self.instant_transitions_layout.addWidget(self.instant_transitions_check)

        self.instant_transitions_label = QLabel(self.gameplay_group)
        self.instant_transitions_label.setObjectName(u"instant_transitions_label")
        sizePolicy1.setHeightForWidth(self.instant_transitions_label.sizePolicy().hasHeightForWidth())
        self.instant_transitions_label.setSizePolicy(sizePolicy1)
        self.instant_transitions_label.setWordWrap(True)

        self.instant_transitions_layout.addWidget(self.instant_transitions_label)

        self.short_intro_text_check = QCheckBox(self.gameplay_group)
        self.short_intro_text_check.setObjectName(u"short_intro_text_check")

        self.instant_transitions_layout.addWidget(self.short_intro_text_check)

        self.short_intro_text_label = QLabel(self.gameplay_group)
        self.short_intro_text_label.setObjectName(u"short_intro_text_label")
        sizePolicy1.setHeightForWidth(self.short_intro_text_label.sizePolicy().hasHeightForWidth())
        self.short_intro_text_label.setSizePolicy(sizePolicy1)
        self.short_intro_text_label.setWordWrap(True)

        self.instant_transitions_layout.addWidget(self.short_intro_text_label)


        self.scroll_layout.addWidget(self.gameplay_group)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        PresetFusionPatches.setCentralWidget(self.root_widget)

        self.retranslateUi(PresetFusionPatches)

        QMetaObject.connectSlotsByName(PresetFusionPatches)
    # setupUi

    def retranslateUi(self, PresetFusionPatches):
        PresetFusionPatches.setWindowTitle(QCoreApplication.translate("PresetFusionPatches", u"Gameplay", None))
        self.energy_group.setTitle(QCoreApplication.translate("PresetFusionPatches", u"Energy", None))
        self.etank_description_label.setText(QCoreApplication.translate("PresetFusionPatches", u"Configure how much energy each Energy Tank you collect will provide. Your base energy is always this quantity, minus 1.\n"
"While logic will respect this value, only the original value (100) has been tested.", None))
        self.etank_capacity_label.setText(QCoreApplication.translate("PresetFusionPatches", u"Energy per tank:", None))
        self.room_group.setTitle(QCoreApplication.translate("PresetFusionPatches", u"Room Design", None))
        self.anti_softlock_check.setText(QCoreApplication.translate("PresetFusionPatches", u"Enable Anti-Softlock Room Edits", None))
        self.anti_softlock_label.setText(QCoreApplication.translate("PresetFusionPatches", u"Enabling this will modify certain rooms to prevent potential softlocks for the player.", None))
        self.gameplay_group.setTitle(QCoreApplication.translate("PresetFusionPatches", u"Other", None))
        self.instant_transitions_check.setText(QCoreApplication.translate("PresetFusionPatches", u"Enable Instant Hatch Transitions", None))
        self.instant_transitions_label.setText(QCoreApplication.translate("PresetFusionPatches", u"<html><head/><body><p>Enabling this will skip the transition animation for hatches.</p></body></html>", None))
        self.short_intro_text_check.setText(QCoreApplication.translate("PresetFusionPatches", u"Enable Short Intro Text", None))
        self.short_intro_text_label.setText(QCoreApplication.translate("PresetFusionPatches", u"Enabling this considerably shortens Adam's intro text. This setting is only recommended to players familiar with the randomizer and its settings.", None))
    # retranslateUi

