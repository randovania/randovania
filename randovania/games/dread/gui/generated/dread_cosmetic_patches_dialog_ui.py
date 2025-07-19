# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dread_cosmetic_patches_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

from randovania.gui.lib.scroll_protected import ScrollProtectedSlider

class Ui_DreadCosmeticPatchesDialog(object):
    def setupUi(self, DreadCosmeticPatchesDialog):
        if not DreadCosmeticPatchesDialog.objectName():
            DreadCosmeticPatchesDialog.setObjectName(u"DreadCosmeticPatchesDialog")
        DreadCosmeticPatchesDialog.resize(421, 368)
        self.gridLayout = QGridLayout(DreadCosmeticPatchesDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.scrollArea = QScrollArea(DreadCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 390, 716))
        self.verticalLayout = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.game_changes_box = QGroupBox(self.scroll_area_contents)
        self.game_changes_box.setObjectName(u"game_changes_box")
        self.game_changes_layout = QVBoxLayout(self.game_changes_box)
        self.game_changes_layout.setSpacing(6)
        self.game_changes_layout.setContentsMargins(11, 11, 11, 11)
        self.game_changes_layout.setObjectName(u"game_changes_layout")
        self.show_boss_life = QCheckBox(self.game_changes_box)
        self.show_boss_life.setObjectName(u"show_boss_life")

        self.game_changes_layout.addWidget(self.show_boss_life)

        self.show_enemy_life = QCheckBox(self.game_changes_box)
        self.show_enemy_life.setObjectName(u"show_enemy_life")

        self.game_changes_layout.addWidget(self.show_enemy_life)

        self.show_enemy_damage = QCheckBox(self.game_changes_box)
        self.show_enemy_damage.setObjectName(u"show_enemy_damage")

        self.game_changes_layout.addWidget(self.show_enemy_damage)

        self.show_player_damage = QCheckBox(self.game_changes_box)
        self.show_player_damage.setObjectName(u"show_player_damage")

        self.game_changes_layout.addWidget(self.show_player_damage)

        self.show_death_counter = QCheckBox(self.game_changes_box)
        self.show_death_counter.setObjectName(u"show_death_counter")

        self.game_changes_layout.addWidget(self.show_death_counter)

        self.enable_auto_tracker = QCheckBox(self.game_changes_box)
        self.enable_auto_tracker.setObjectName(u"enable_auto_tracker")

        self.game_changes_layout.addWidget(self.enable_auto_tracker)

        self.show_room_names = QHBoxLayout()
        self.show_room_names.setSpacing(6)
        self.show_room_names.setObjectName(u"show_room_names")
        self.room_names_label = QLabel(self.game_changes_box)
        self.room_names_label.setObjectName(u"room_names_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.room_names_label.sizePolicy().hasHeightForWidth())
        self.room_names_label.setSizePolicy(sizePolicy)

        self.show_room_names.addWidget(self.room_names_label)

        self.room_names_dropdown = QComboBox(self.game_changes_box)
        self.room_names_dropdown.setObjectName(u"room_names_dropdown")
        self.room_names_dropdown.setEditable(False)

        self.show_room_names.addWidget(self.room_names_dropdown)


        self.game_changes_layout.addLayout(self.show_room_names)

        self.missile_cosmetic = QHBoxLayout()
        self.missile_cosmetic.setSpacing(6)
        self.missile_cosmetic.setObjectName(u"missile_cosmetic")
        self.missile_cosmetic_label = QLabel(self.game_changes_box)
        self.missile_cosmetic_label.setObjectName(u"missile_cosmetic_label")

        self.missile_cosmetic.addWidget(self.missile_cosmetic_label)

        self.missile_cosmetic_dropdown = QComboBox(self.game_changes_box)
        self.missile_cosmetic_dropdown.setObjectName(u"missile_cosmetic_dropdown")

        self.missile_cosmetic.addWidget(self.missile_cosmetic_dropdown)


        self.game_changes_layout.addLayout(self.missile_cosmetic)

        self.music_title_label = QLabel(self.game_changes_box)
        self.music_title_label.setObjectName(u"music_title_label")

        self.game_changes_layout.addWidget(self.music_title_label)

        self.music_group = QHBoxLayout()
        self.music_group.setSpacing(6)
        self.music_group.setObjectName(u"music_group")
        self.music_slider = ScrollProtectedSlider(self.game_changes_box)
        self.music_slider.setObjectName(u"music_slider")
        self.music_slider.setMaximum(100)
        self.music_slider.setSliderPosition(100)
        self.music_slider.setOrientation(Qt.Orientation.Horizontal)

        self.music_group.addWidget(self.music_slider)

        self.music_label = QLabel(self.game_changes_box)
        self.music_label.setObjectName(u"music_label")

        self.music_group.addWidget(self.music_label)


        self.game_changes_layout.addLayout(self.music_group)

        self.sfx_title_label = QLabel(self.game_changes_box)
        self.sfx_title_label.setObjectName(u"sfx_title_label")

        self.game_changes_layout.addWidget(self.sfx_title_label)

        self.sfx_group = QHBoxLayout()
        self.sfx_group.setSpacing(6)
        self.sfx_group.setObjectName(u"sfx_group")
        self.sfx_slider = ScrollProtectedSlider(self.game_changes_box)
        self.sfx_slider.setObjectName(u"sfx_slider")
        self.sfx_slider.setMaximum(100)
        self.sfx_slider.setSliderPosition(100)
        self.sfx_slider.setOrientation(Qt.Orientation.Horizontal)

        self.sfx_group.addWidget(self.sfx_slider)

        self.sfx_label = QLabel(self.game_changes_box)
        self.sfx_label.setObjectName(u"sfx_label")

        self.sfx_group.addWidget(self.sfx_label)


        self.game_changes_layout.addLayout(self.sfx_group)

        self.ambience_title_label = QLabel(self.game_changes_box)
        self.ambience_title_label.setObjectName(u"ambience_title_label")

        self.game_changes_layout.addWidget(self.ambience_title_label)

        self.ambience_group = QHBoxLayout()
        self.ambience_group.setSpacing(6)
        self.ambience_group.setObjectName(u"ambience_group")
        self.ambience_slider = ScrollProtectedSlider(self.game_changes_box)
        self.ambience_slider.setObjectName(u"ambience_slider")
        self.ambience_slider.setMaximum(100)
        self.ambience_slider.setSliderPosition(100)
        self.ambience_slider.setOrientation(Qt.Orientation.Horizontal)

        self.ambience_group.addWidget(self.ambience_slider)

        self.ambience_label = QLabel(self.game_changes_box)
        self.ambience_label.setObjectName(u"ambience_label")

        self.ambience_group.addWidget(self.ambience_label)


        self.game_changes_layout.addLayout(self.ambience_group)


        self.verticalLayout.addWidget(self.game_changes_box)

        self.accessibility_options_box = QGroupBox(self.scroll_area_contents)
        self.accessibility_options_box.setObjectName(u"accessibility_options_box")
        self.game_changes_layout_3 = QVBoxLayout(self.accessibility_options_box)
        self.game_changes_layout_3.setSpacing(6)
        self.game_changes_layout_3.setContentsMargins(11, 11, 11, 11)
        self.game_changes_layout_3.setObjectName(u"game_changes_layout_3")
        self.alt_ice_missile = QCheckBox(self.accessibility_options_box)
        self.alt_ice_missile.setObjectName(u"alt_ice_missile")

        self.game_changes_layout_3.addWidget(self.alt_ice_missile)

        self.alt_storm_missile = QCheckBox(self.accessibility_options_box)
        self.alt_storm_missile.setObjectName(u"alt_storm_missile")

        self.game_changes_layout_3.addWidget(self.alt_storm_missile)

        self.alt_diffusion_beam = QCheckBox(self.accessibility_options_box)
        self.alt_diffusion_beam.setObjectName(u"alt_diffusion_beam")

        self.game_changes_layout_3.addWidget(self.alt_diffusion_beam)

        self.alt_bomb = QCheckBox(self.accessibility_options_box)
        self.alt_bomb.setObjectName(u"alt_bomb")

        self.game_changes_layout_3.addWidget(self.alt_bomb)

        self.alt_cross_bomb = QCheckBox(self.accessibility_options_box)
        self.alt_cross_bomb.setObjectName(u"alt_cross_bomb")

        self.game_changes_layout_3.addWidget(self.alt_cross_bomb)

        self.alt_power_bomb = QCheckBox(self.accessibility_options_box)
        self.alt_power_bomb.setObjectName(u"alt_power_bomb")

        self.game_changes_layout_3.addWidget(self.alt_power_bomb)

        self.alt_closed = QCheckBox(self.accessibility_options_box)
        self.alt_closed.setObjectName(u"alt_closed")

        self.game_changes_layout_3.addWidget(self.alt_closed)


        self.verticalLayout.addWidget(self.accessibility_options_box)

        self.scrollArea.setWidget(self.scroll_area_contents)

        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 3)

        self.reset_button = QPushButton(DreadCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")

        self.gridLayout.addWidget(self.reset_button, 2, 2, 1, 1)

        self.accept_button = QPushButton(DreadCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 2, 0, 1, 1)

        self.cancel_button = QPushButton(DreadCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 2, 1, 1, 1)


        self.retranslateUi(DreadCosmeticPatchesDialog)

        self.accept_button.setDefault(True)


        QMetaObject.connectSlotsByName(DreadCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, DreadCosmeticPatchesDialog):
        DreadCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Metroid Dread - Cosmetic Options", None))
        self.game_changes_box.setTitle(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Config Options", None))
        self.show_boss_life.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Show boss life bars", None))
        self.show_enemy_life.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Show enemy life bars", None))
        self.show_enemy_damage.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Show enemy damage", None))
        self.show_player_damage.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Show player damage", None))
        self.show_death_counter.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Show player death count in HUD", None))
        self.enable_auto_tracker.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Enable automatic item tracker", None))
        self.room_names_label.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Show Room Names On HUD", None))
        self.room_names_dropdown.setCurrentText("")
        self.room_names_dropdown.setPlaceholderText("")
        self.missile_cosmetic_label.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Missile Pack Recolor", None))
        self.music_title_label.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Music Volume:", None))
        self.music_label.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"100%", None))
        self.sfx_title_label.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"SFX Volume:", None))
        self.sfx_label.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"100%", None))
        self.ambience_title_label.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Background Ambience Volume:", None))
        self.ambience_label.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"100%", None))
        self.accessibility_options_box.setTitle(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Accessibility Options", None))
        self.alt_ice_missile.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Alternate Ice Missile shield texture", None))
        self.alt_storm_missile.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Alternate Storm Missile shield texture", None))
        self.alt_diffusion_beam.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Alternate Diffusion Beam shield texture", None))
        self.alt_bomb.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Alternate Bomb shield texture", None))
        self.alt_cross_bomb.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Alternate Cross Bomb shield texture", None))
        self.alt_power_bomb.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Alternate Power Bomb shield texture", None))
        self.alt_closed.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Alternate \"Access Permanently Closed\" shield texture", None))
        self.reset_button.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Reset to Defaults", None))
        self.accept_button.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Accept", None))
        self.cancel_button.setText(QCoreApplication.translate("DreadCosmeticPatchesDialog", u"Cancel", None))
    # retranslateUi

