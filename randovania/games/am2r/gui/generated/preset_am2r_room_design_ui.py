# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_am2r_room_design.ui'
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
    QMainWindow, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_PresetAM2RRoomDesign(object):
    def setupUi(self, PresetAM2RRoomDesign):
        if not PresetAM2RRoomDesign.objectName():
            PresetAM2RRoomDesign.setObjectName(u"PresetAM2RRoomDesign")
        PresetAM2RRoomDesign.resize(770, 660)
        self.root_widget = QWidget(PresetAM2RRoomDesign)
        self.root_widget.setObjectName(u"root_widget")
        self.root_widget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(self.root_widget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.scroll_area = QScrollArea(self.root_widget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_contents = QWidget()
        self.scroll_contents.setObjectName(u"scroll_contents")
        self.scroll_contents.setGeometry(QRect(0, 0, 758, 648))
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_layout.setObjectName(u"scroll_layout")
        self.scroll_layout.setContentsMargins(6, 6, 6, 6)
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


        self.scroll_layout.addWidget(self.room_group)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        PresetAM2RRoomDesign.setCentralWidget(self.root_widget)

        self.retranslateUi(PresetAM2RRoomDesign)

        QMetaObject.connectSlotsByName(PresetAM2RRoomDesign)
    # setupUi

    def retranslateUi(self, PresetAM2RRoomDesign):
        PresetAM2RRoomDesign.setWindowTitle(QCoreApplication.translate("PresetAM2RRoomDesign", u"Other", None))
        self.room_group.setTitle(QCoreApplication.translate("PresetAM2RRoomDesign", u"Room Design", None))
        self.septogg_helpers_check.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"Enable Septogg Helpers", None))
        self.septogg_helpers_label.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"<html><head/><body><p>Septoggs will appear in certain rooms, helping you reach higher platforms if you don't have the means to reach them yourself. Due to SR-388's cave structure, this setting is highly recommended.</p></body></html>", None))
        self.grave_grotto_blocks_check.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"Bomb Blocks in Grave Grotto", None))
        self.grave_grotto_blocks_label.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"\"Grave Grotto\" (the cave between Golden Temple and Hydro Station) usually has bomb blocks. Disabling this option removes them.", None))
        self.a3_entrance_blocks_check.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"Bomb Block in Industrial Complex Access", None))
        self.a3_entrance_blocks_label.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"\"Industrial Complex Access\" usually has a bomb block on the way to \"Industrial Complex Exterior\". Disabling this option removes it, allowing sooner access to that area.", None))
        self.softlock_prevention_blocks_check.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"Softlock Prevention Checks", None))
        self.softlock_prevention_blocks_label.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"This option adds checks to some rooms that removes certain blocks in order to minimize softlocks.", None))
        self.screw_blocks_check.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"Screw Attack Blocks near Teleporter Pipes", None))
        self.screw_blocks_label.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"Usually, Teleporter Pipe rooms have Screw Attack Blocks near them. Disabling this option makes them dissapear, allowing sooner usage of them.", None))
        self.respawn_bomb_blocks_check.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"Respawn destructable bomb blocks", None))
        self.respawn_bomb_blocks_label.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"<html><head/><body><p>Makes most destructable bomb blocks respawn. Disabling this will make it easier to traverse certain rooms if you only have Power Bombs.</p></body></html>", None))
        self.nest_pipes_check.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"Add new Teleporter Pipes in final areas", None))
        self.nest_pipes_label.setText(QCoreApplication.translate("PresetAM2RRoomDesign", u"<html><head/><body><p>Adds new Teleporter Pipes to make the final areas less cumbersome to traverse.<br/>The Pipes will be located &quot;Hideout Hub Access East&quot;, &quot;Shinespark Cave East&quot;, &quot;Depths Omega Nest South West Access&quot; and &quot;Waterfall Passage Top&quot;.</p></body></html>", None))
    # retranslateUi

