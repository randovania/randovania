# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_prime_chaos.ui'
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
    QHBoxLayout, QLabel, QMainWindow, QScrollArea,
    QSizePolicy, QSlider, QSpacerItem, QVBoxLayout,
    QWidget)

from randovania.gui.lib.scroll_protected import ScrollProtectedSlider

class Ui_PresetPrimeChaos(object):
    def setupUi(self, PresetPrimeChaos):
        if not PresetPrimeChaos.objectName():
            PresetPrimeChaos.setObjectName(u"PresetPrimeChaos")
        PresetPrimeChaos.resize(503, 687)
        self.centralWidget = QWidget(PresetPrimeChaos)
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
        self.scroll_contents.setGeometry(QRect(0, 0, 487, 1190))
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_layout.setObjectName(u"scroll_layout")
        self.scroll_layout.setContentsMargins(0, 2, 0, 0)
        self.top_spacer = QSpacerItem(20, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.scroll_layout.addItem(self.top_spacer)

        self.chaos_label = QLabel(self.scroll_contents)
        self.chaos_label.setObjectName(u"chaos_label")
        self.chaos_label.setWordWrap(True)

        self.scroll_layout.addWidget(self.chaos_label)

        self.legacy_mode_group = QGroupBox(self.scroll_contents)
        self.legacy_mode_group.setObjectName(u"legacy_mode_group")
        self.verticalLayout_9 = QVBoxLayout(self.legacy_mode_group)
        self.verticalLayout_9.setSpacing(6)
        self.verticalLayout_9.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(9, 9, 9, 9)
        self.legacy_mode_check = QCheckBox(self.legacy_mode_group)
        self.legacy_mode_check.setObjectName(u"legacy_mode_check")
        self.legacy_mode_check.setEnabled(True)

        self.verticalLayout_9.addWidget(self.legacy_mode_check)

        self.legacy_mode_label = QLabel(self.legacy_mode_group)
        self.legacy_mode_label.setObjectName(u"legacy_mode_label")
        self.legacy_mode_label.setWordWrap(True)

        self.verticalLayout_9.addWidget(self.legacy_mode_label)


        self.scroll_layout.addWidget(self.legacy_mode_group)

        self.room_rando_group = QGroupBox(self.scroll_contents)
        self.room_rando_group.setObjectName(u"room_rando_group")
        self.verticalLayout_5 = QVBoxLayout(self.room_rando_group)
        self.verticalLayout_5.setSpacing(6)
        self.verticalLayout_5.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.room_rando_combo = QComboBox(self.room_rando_group)
        self.room_rando_combo.addItem("")
        self.room_rando_combo.addItem("")
        self.room_rando_combo.addItem("")
        self.room_rando_combo.setObjectName(u"room_rando_combo")

        self.verticalLayout_5.addWidget(self.room_rando_combo)

        self.room_rando_label = QLabel(self.room_rando_group)
        self.room_rando_label.setObjectName(u"room_rando_label")
        self.room_rando_label.setWordWrap(True)

        self.verticalLayout_5.addWidget(self.room_rando_label)


        self.scroll_layout.addWidget(self.room_rando_group)

        self.groupBox = QGroupBox(self.scroll_contents)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_6 = QVBoxLayout(self.groupBox)
        self.verticalLayout_6.setSpacing(6)
        self.verticalLayout_6.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.small_samus_check = QCheckBox(self.groupBox)
        self.small_samus_check.setObjectName(u"small_samus_check")

        self.verticalLayout_6.addWidget(self.small_samus_check)

        self.small_samus_label = QLabel(self.groupBox)
        self.small_samus_label.setObjectName(u"small_samus_label")
        self.small_samus_label.setWordWrap(True)

        self.verticalLayout_6.addWidget(self.small_samus_label)

        self.large_samus_check = QCheckBox(self.groupBox)
        self.large_samus_check.setObjectName(u"large_samus_check")

        self.verticalLayout_6.addWidget(self.large_samus_check)

        self.large_samus_label = QLabel(self.groupBox)
        self.large_samus_label.setObjectName(u"large_samus_label")
        self.large_samus_label.setWordWrap(True)

        self.verticalLayout_6.addWidget(self.large_samus_label)


        self.scroll_layout.addWidget(self.groupBox)

        self.random_boss_sizes_group = QGroupBox(self.scroll_contents)
        self.random_boss_sizes_group.setObjectName(u"random_boss_sizes_group")
        self.verticalLayout_8 = QVBoxLayout(self.random_boss_sizes_group)
        self.verticalLayout_8.setSpacing(6)
        self.verticalLayout_8.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.random_boss_sizes_check = QCheckBox(self.random_boss_sizes_group)
        self.random_boss_sizes_check.setObjectName(u"random_boss_sizes_check")

        self.verticalLayout_8.addWidget(self.random_boss_sizes_check)

        self.random_boss_sizes_label = QLabel(self.random_boss_sizes_group)
        self.random_boss_sizes_label.setObjectName(u"random_boss_sizes_label")
        self.random_boss_sizes_label.setWordWrap(True)

        self.verticalLayout_8.addWidget(self.random_boss_sizes_label)


        self.scroll_layout.addWidget(self.random_boss_sizes_group)

        self.items_group = QGroupBox(self.scroll_contents)
        self.items_group.setObjectName(u"items_group")
        self.verticalLayout_7 = QVBoxLayout(self.items_group)
        self.verticalLayout_7.setSpacing(6)
        self.verticalLayout_7.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.shuffle_item_pos_check = QCheckBox(self.items_group)
        self.shuffle_item_pos_check.setObjectName(u"shuffle_item_pos_check")

        self.verticalLayout_7.addWidget(self.shuffle_item_pos_check)

        self.shuffle_item_pos_label = QLabel(self.items_group)
        self.shuffle_item_pos_label.setObjectName(u"shuffle_item_pos_label")
        self.shuffle_item_pos_label.setWordWrap(True)

        self.verticalLayout_7.addWidget(self.shuffle_item_pos_label)

        self.items_every_room_check = QCheckBox(self.items_group)
        self.items_every_room_check.setObjectName(u"items_every_room_check")

        self.verticalLayout_7.addWidget(self.items_every_room_check)

        self.items_every_room_label = QLabel(self.items_group)
        self.items_every_room_label.setObjectName(u"items_every_room_label")
        self.items_every_room_label.setWordWrap(True)

        self.verticalLayout_7.addWidget(self.items_every_room_label)


        self.scroll_layout.addWidget(self.items_group)

        self.shuffle_item_pos_group = QGroupBox(self.scroll_contents)
        self.shuffle_item_pos_group.setObjectName(u"shuffle_item_pos_group")
        self.verticalLayout_4 = QVBoxLayout(self.shuffle_item_pos_group)
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.superheated_label = QLabel(self.shuffle_item_pos_group)
        self.superheated_label.setObjectName(u"superheated_label")
        self.superheated_label.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.superheated_label)

        self.superheated_slider_layout = QHBoxLayout()
        self.superheated_slider_layout.setSpacing(6)
        self.superheated_slider_layout.setObjectName(u"superheated_slider_layout")
        self.superheated_slider = ScrollProtectedSlider(self.shuffle_item_pos_group)
        self.superheated_slider.setObjectName(u"superheated_slider")
        self.superheated_slider.setMaximum(1000)
        self.superheated_slider.setPageStep(2)
        self.superheated_slider.setOrientation(Qt.Horizontal)
        self.superheated_slider.setTickPosition(QSlider.TicksBelow)

        self.superheated_slider_layout.addWidget(self.superheated_slider)

        self.superheated_slider_label = QLabel(self.shuffle_item_pos_group)
        self.superheated_slider_label.setObjectName(u"superheated_slider_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.superheated_slider_label.sizePolicy().hasHeightForWidth())
        self.superheated_slider_label.setSizePolicy(sizePolicy)
        self.superheated_slider_label.setMinimumSize(QSize(20, 0))
        self.superheated_slider_label.setAlignment(Qt.AlignCenter)

        self.superheated_slider_layout.addWidget(self.superheated_slider_label)


        self.verticalLayout_4.addLayout(self.superheated_slider_layout)

        self.submerged_label = QLabel(self.shuffle_item_pos_group)
        self.submerged_label.setObjectName(u"submerged_label")
        self.submerged_label.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.submerged_label)

        self.submerged_slider_layout = QHBoxLayout()
        self.submerged_slider_layout.setSpacing(6)
        self.submerged_slider_layout.setObjectName(u"submerged_slider_layout")
        self.submerged_slider = ScrollProtectedSlider(self.shuffle_item_pos_group)
        self.submerged_slider.setObjectName(u"submerged_slider")
        self.submerged_slider.setMaximum(1000)
        self.submerged_slider.setPageStep(2)
        self.submerged_slider.setOrientation(Qt.Horizontal)
        self.submerged_slider.setTickPosition(QSlider.TicksBelow)

        self.submerged_slider_layout.addWidget(self.submerged_slider)

        self.submerged_slider_label = QLabel(self.shuffle_item_pos_group)
        self.submerged_slider_label.setObjectName(u"submerged_slider_label")
        sizePolicy.setHeightForWidth(self.submerged_slider_label.sizePolicy().hasHeightForWidth())
        self.submerged_slider_label.setSizePolicy(sizePolicy)
        self.submerged_slider_label.setMinimumSize(QSize(20, 0))
        self.submerged_slider_label.setAlignment(Qt.AlignCenter)

        self.submerged_slider_layout.addWidget(self.submerged_slider_label)


        self.verticalLayout_4.addLayout(self.submerged_slider_layout)


        self.scroll_layout.addWidget(self.shuffle_item_pos_group)

        self.scroll_area.setWidget(self.scroll_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        PresetPrimeChaos.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetPrimeChaos)

        QMetaObject.connectSlotsByName(PresetPrimeChaos)
    # setupUi

    def retranslateUi(self, PresetPrimeChaos):
        PresetPrimeChaos.setWindowTitle(QCoreApplication.translate("PresetPrimeChaos", u"Other", None))
        self.chaos_label.setText(QCoreApplication.translate("PresetPrimeChaos", u"<html><head/><body><p>This page contains experimental settings which do not yet have (or will never have) logic support. This means that games generated with anything other than this tab's default settings may result in incompletable seeds.</p></body></html>", None))
        self.legacy_mode_group.setTitle(QCoreApplication.translate("PresetPrimeChaos", u"Legacy Mode", None))
        self.legacy_mode_check.setText(QCoreApplication.translate("PresetPrimeChaos", u"Enable Legacy Mode", None))
        self.legacy_mode_label.setText(QCoreApplication.translate("PresetPrimeChaos", u"<html><head/><body><p>Check this box to skip various patches, resulting in gameplay as close to the vanilla experience as possible. This includes:</p><p>Fixed crashes, Fixed softlocks, Fast item acquisition, Better pickup scans, Undo non-NTSC sequence break patches, Varia-only heat protection and &quot;General&quot; QoL</p></body></html>", None))
        self.room_rando_group.setTitle(QCoreApplication.translate("PresetPrimeChaos", u"Room Rando", None))
        self.room_rando_combo.setItemText(0, QCoreApplication.translate("PresetPrimeChaos", u"None", None))
        self.room_rando_combo.setItemText(1, QCoreApplication.translate("PresetPrimeChaos", u"One-way", None))
        self.room_rando_combo.setItemText(2, QCoreApplication.translate("PresetPrimeChaos", u"Two-way", None))

        self.room_rando_label.setText(QCoreApplication.translate("PresetPrimeChaos", u"<html><head/><body>These options shuffle how rooms within an area are connected completely smashing randovania's delicately balanced logic.<p><span style=\" font-weight:600;\">None</span>: No changes are made.</p><p><span style=\" font-weight:600;\">One-way</span>: Doors are patched to lead to another random door in the same world. That door most likely does not lead back to the previous room. Scan doors to see where they lead.</p><p><span style=\" font-weight:600;\">Two-way</span>: Like One-way, but doors will always lead back to the previous room.</p></body></html>", None))
        self.groupBox.setTitle(QCoreApplication.translate("PresetPrimeChaos", u"Player Size", None))
        self.small_samus_check.setText(QCoreApplication.translate("PresetPrimeChaos", u"Enable Small Samus", None))
        self.small_samus_label.setText(QCoreApplication.translate("PresetPrimeChaos", u"<html><head/><body><p>Makes the player 30% of their original size. This includes hitbox size, camera height, morph ball size and step-up height but not movement speed or jump height.</p></body></html>", None))
        self.large_samus_check.setText(QCoreApplication.translate("PresetPrimeChaos", u"Enable Large Samus", None))
        self.large_samus_label.setText(QCoreApplication.translate("PresetPrimeChaos", u"<html><head/><body><p>Like above, but makes the player 175% of the original size. Morph ball stays the same to avoid frequent soft-locks.</p></body></html>", None))
        self.random_boss_sizes_group.setTitle(QCoreApplication.translate("PresetPrimeChaos", u"Boss Size", None))
        self.random_boss_sizes_check.setText(QCoreApplication.translate("PresetPrimeChaos", u"Random Boss Sizes", None))
        self.random_boss_sizes_label.setText(QCoreApplication.translate("PresetPrimeChaos", u"<html><head/><body><p>Makes each of the bosses (and mini-bosses) a random size ranging from \"tiny bug\" to \"barely fits in the room\".</p></body></html>", None))
        self.items_group.setTitle(QCoreApplication.translate("PresetPrimeChaos", u"Pickup Locations", None))
        self.shuffle_item_pos_check.setText(QCoreApplication.translate("PresetPrimeChaos", u"Shuffle Pickup Position", None))
        self.shuffle_item_pos_label.setText(QCoreApplication.translate("PresetPrimeChaos", u"<html><head/><body><p>Item locations are randomized within the rooms they reside in. There is no checking to ensure items are placed inbounds so seeds are not garunteed to be logical or even completable. Item scan points are adjusted in this mode to be larger and can be seen through walls.</p></body></html>", None))
        self.items_every_room_check.setText(QCoreApplication.translate("PresetPrimeChaos", u"Pickups in Every Room", None))
        self.items_every_room_label.setText(QCoreApplication.translate("PresetPrimeChaos", u"<html><head/><body><p>Like above, but adds 1 additional item spawn locations in each room which normally do not contain an item. Be sure to visit the item pool tab to fill the pool with items to use in the newly added location. These extra locations are always filled with filler items, unless playing on minimum logic.</p></body></html>", None))
        self.shuffle_item_pos_group.setTitle(QCoreApplication.translate("PresetPrimeChaos", u"Room Attributes", None))
        self.superheated_label.setText(QCoreApplication.translate("PresetPrimeChaos", u"<html><head/><body><p><br/>Superheated Probability: Probability that any room is superheated. If non-zero, rooms which are normally superheated will have their superheated state re-rolled. Completely ignores heat-run logic.</p></body></html>", None))
        self.superheated_slider_label.setText(QCoreApplication.translate("PresetPrimeChaos", u"0", None))
        self.submerged_label.setText(QCoreApplication.translate("PresetPrimeChaos", u"<html><head/><body><p><br/>Submerged Probability: Probability that any room is fully submerged in water. Completely ignores underwater movement logic.</p></body></html>", None))
        self.submerged_slider_label.setText(QCoreApplication.translate("PresetPrimeChaos", u"0", None))
    # retranslateUi

