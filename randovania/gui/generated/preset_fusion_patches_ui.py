# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_fusion_patches.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_PresetFusionPatches(object):
    def setupUi(self, PresetFusionPatches):
        if not PresetFusionPatches.objectName():
            PresetFusionPatches.setObjectName(u"PresetFusionPatches")
        PresetFusionPatches.resize(770, 660)
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

        self.scroll_layout.addWidget(self.room_group)

        self.misc_group = QGroupBox(self.scroll_contents)
        self.misc_group.setObjectName(u"misc_group")
        self.instant_transitions_layout = QVBoxLayout(self.misc_group)
        self.instant_transitions_layout.setSpacing(6)
        self.instant_transitions_layout.setContentsMargins(11, 11, 11, 11)
        self.instant_transitions_layout.setObjectName(u"instant_transitions_layout")
        self.instant_transitions_check = QCheckBox(self.misc_group)
        self.instant_transitions_check.setObjectName(u"instant_transitions_check")

        self.instant_transitions_layout.addWidget(self.instant_transitions_check)

        self.instant_transitions_label = QLabel(self.misc_group)
        self.instant_transitions_label.setObjectName(u"instant_transitions_label")
        self.instant_transitions_label.setWordWrap(True)

        self.instant_transitions_layout.addWidget(self.instant_transitions_label)


        self.scroll_layout.addWidget(self.misc_group)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        PresetFusionPatches.setCentralWidget(self.root_widget)

        self.retranslateUi(PresetFusionPatches)

        QMetaObject.connectSlotsByName(PresetFusionPatches)
    # setupUi

    def retranslateUi(self, PresetFusionPatches):
        PresetFusionPatches.setWindowTitle(QCoreApplication.translate("PresetFusionPatches", u"Other", None))
        self.room_group.setTitle(QCoreApplication.translate("PresetFusionPatches", u"Room Design", None))
        self.misc_group.setTitle(QCoreApplication.translate("PresetFusionPatches", u"Miscellaneous", None))
        self.instant_transitions_check.setText(QCoreApplication.translate("PresetFusionPatches", u"Enable Instant Hatch Transitions", None))
        self.instant_transitions_label.setText(QCoreApplication.translate("PresetFusionPatches", u"<html><head/><body><p>Enabling this will skip the transition animation for hatches.</p></body></html>", None))
    # retranslateUi

