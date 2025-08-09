# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'echoes_cosmetic_patches_dialog.ui'
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
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QSizePolicy,
    QSlider, QSpacerItem, QVBoxLayout, QWidget)

from randovania.gui.lib.foldable import Foldable
from randovania.gui.lib.scroll_protected import ScrollProtectedSlider

class Ui_EchoesCosmeticPatchesDialog(object):
    def setupUi(self, EchoesCosmeticPatchesDialog):
        if not EchoesCosmeticPatchesDialog.objectName():
            EchoesCosmeticPatchesDialog.setObjectName(u"EchoesCosmeticPatchesDialog")
        EchoesCosmeticPatchesDialog.resize(482, 450)
        self.gridLayout = QGridLayout(EchoesCosmeticPatchesDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.reset_button = QPushButton(EchoesCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")

        self.gridLayout.addWidget(self.reset_button, 2, 2, 1, 1)

        self.accept_button = QPushButton(EchoesCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 2, 0, 1, 1)

        self.cancel_button = QPushButton(EchoesCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 2, 1, 1, 1)

        self.scrollArea = QScrollArea(EchoesCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 448, 2361))
        self.verticalLayout = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.game_changes_box = QGroupBox(self.scroll_area_contents)
        self.game_changes_box.setObjectName(u"game_changes_box")
        self.game_changes_layout = QVBoxLayout(self.game_changes_box)
        self.game_changes_layout.setSpacing(6)
        self.game_changes_layout.setContentsMargins(11, 11, 11, 11)
        self.game_changes_layout.setObjectName(u"game_changes_layout")
        self.hud_color_layout = QHBoxLayout()
        self.hud_color_layout.setSpacing(6)
        self.hud_color_layout.setObjectName(u"hud_color_layout")
        self.custom_hud_color = QCheckBox(self.game_changes_box)
        self.custom_hud_color.setObjectName(u"custom_hud_color")

        self.hud_color_layout.addWidget(self.custom_hud_color)

        self.custom_hud_color_button = QPushButton(self.game_changes_box)
        self.custom_hud_color_button.setObjectName(u"custom_hud_color_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.custom_hud_color_button.sizePolicy().hasHeightForWidth())
        self.custom_hud_color_button.setSizePolicy(sizePolicy1)

        self.hud_color_layout.addWidget(self.custom_hud_color_button)

        self.custom_hud_color_square = QFrame(self.game_changes_box)
        self.custom_hud_color_square.setObjectName(u"custom_hud_color_square")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.custom_hud_color_square.sizePolicy().hasHeightForWidth())
        self.custom_hud_color_square.setSizePolicy(sizePolicy2)
        self.custom_hud_color_square.setMinimumSize(QSize(22, 22))
        self.custom_hud_color_square.setAutoFillBackground(False)
        self.custom_hud_color_square.setFrameShape(QFrame.Shape.StyledPanel)
        self.custom_hud_color_square.setFrameShadow(QFrame.Shadow.Raised)
        self.custom_hud_color_square.setLineWidth(1)

        self.hud_color_layout.addWidget(self.custom_hud_color_square)


        self.game_changes_layout.addLayout(self.hud_color_layout)

        self.faster_credits_check = QCheckBox(self.game_changes_box)
        self.faster_credits_check.setObjectName(u"faster_credits_check")

        self.game_changes_layout.addWidget(self.faster_credits_check)

        self.remove_hud_popup_check = QCheckBox(self.game_changes_box)
        self.remove_hud_popup_check.setObjectName(u"remove_hud_popup_check")

        self.game_changes_layout.addWidget(self.remove_hud_popup_check)

        self.pickup_markers_check = QCheckBox(self.game_changes_box)
        self.pickup_markers_check.setObjectName(u"pickup_markers_check")

        self.game_changes_layout.addWidget(self.pickup_markers_check)

        self.open_map_check = QCheckBox(self.game_changes_box)
        self.open_map_check.setObjectName(u"open_map_check")

        self.game_changes_layout.addWidget(self.open_map_check)

        self.unvisited_room_names_check = QCheckBox(self.game_changes_box)
        self.unvisited_room_names_check.setObjectName(u"unvisited_room_names_check")

        self.game_changes_layout.addWidget(self.unvisited_room_names_check)


        self.verticalLayout.addWidget(self.game_changes_box)

        self.suits_foldable = Foldable(self.scroll_area_contents)
        self.suits_foldable.setObjectName(u"suits_foldable")
        self.suits_foldable.setProperty(u"folded", True)
        self.suits_foldable_layout = QVBoxLayout(self.suits_foldable)
        self.suits_foldable_layout.setSpacing(6)
        self.suits_foldable_layout.setContentsMargins(11, 11, 11, 11)
        self.suits_foldable_layout.setObjectName(u"suits_foldable_layout")
        self.experimental_label = QLabel(self.suits_foldable)
        self.experimental_label.setObjectName(u"experimental_label")

        self.suits_foldable_layout.addWidget(self.experimental_label)

        self.simple_suit_box = QWidget(self.suits_foldable)
        self.simple_suit_box.setObjectName(u"simple_suit_box")
        self.horizontalLayout_2 = QHBoxLayout(self.simple_suit_box)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.simple_left_button = QPushButton(self.simple_suit_box)
        self.simple_left_button.setObjectName(u"simple_left_button")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.simple_left_button.sizePolicy().hasHeightForWidth())
        self.simple_left_button.setSizePolicy(sizePolicy3)
        self.simple_left_button.setMaximumSize(QSize(48, 16777215))

        self.horizontalLayout_2.addWidget(self.simple_left_button)

        self.simple_value_box = QGroupBox(self.simple_suit_box)
        self.simple_value_box.setObjectName(u"simple_value_box")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.simple_value_box.sizePolicy().hasHeightForWidth())
        self.simple_value_box.setSizePolicy(sizePolicy4)
        self.simple_value_box.setFlat(False)
        self.verticalLayout_2 = QVBoxLayout(self.simple_value_box)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.simple_name_label = QLabel(self.simple_value_box)
        self.simple_name_label.setObjectName(u"simple_name_label")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.simple_name_label.sizePolicy().hasHeightForWidth())
        self.simple_name_label.setSizePolicy(sizePolicy5)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.simple_name_label.setFont(font)
        self.simple_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.simple_name_label)

        self.simple_img_label = QLabel(self.simple_value_box)
        self.simple_img_label.setObjectName(u"simple_img_label")
        sizePolicy5.setHeightForWidth(self.simple_img_label.sizePolicy().hasHeightForWidth())
        self.simple_img_label.setSizePolicy(sizePolicy5)
        self.simple_img_label.setMinimumSize(QSize(256, 256))
        self.simple_img_label.setMaximumSize(QSize(16777215, 16777215))
        font1 = QFont()
        font1.setBold(False)
        self.simple_img_label.setFont(font1)
        self.simple_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_2.addWidget(self.simple_img_label)


        self.horizontalLayout_2.addWidget(self.simple_value_box)

        self.simple_right_button = QPushButton(self.simple_suit_box)
        self.simple_right_button.setObjectName(u"simple_right_button")
        sizePolicy3.setHeightForWidth(self.simple_right_button.sizePolicy().hasHeightForWidth())
        self.simple_right_button.setSizePolicy(sizePolicy3)
        self.simple_right_button.setMinimumSize(QSize(0, 0))
        self.simple_right_button.setMaximumSize(QSize(48, 16777215))
        self.simple_right_button.setBaseSize(QSize(0, 0))

        self.horizontalLayout_2.addWidget(self.simple_right_button)


        self.suits_foldable_layout.addWidget(self.simple_suit_box)

        self.varia_suit_box = QGroupBox(self.suits_foldable)
        self.varia_suit_box.setObjectName(u"varia_suit_box")
        self.horizontalLayout_3 = QHBoxLayout(self.varia_suit_box)
        self.horizontalLayout_3.setSpacing(6)
        self.horizontalLayout_3.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.varia_left_button = QPushButton(self.varia_suit_box)
        self.varia_left_button.setObjectName(u"varia_left_button")
        sizePolicy3.setHeightForWidth(self.varia_left_button.sizePolicy().hasHeightForWidth())
        self.varia_left_button.setSizePolicy(sizePolicy3)
        self.varia_left_button.setMaximumSize(QSize(48, 16777215))

        self.horizontalLayout_3.addWidget(self.varia_left_button)

        self.varia_value_box = QGroupBox(self.varia_suit_box)
        self.varia_value_box.setObjectName(u"varia_value_box")
        sizePolicy4.setHeightForWidth(self.varia_value_box.sizePolicy().hasHeightForWidth())
        self.varia_value_box.setSizePolicy(sizePolicy4)
        self.varia_value_box.setFlat(False)
        self.verticalLayout_3 = QVBoxLayout(self.varia_value_box)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.varia_name_label = QLabel(self.varia_value_box)
        self.varia_name_label.setObjectName(u"varia_name_label")
        sizePolicy5.setHeightForWidth(self.varia_name_label.sizePolicy().hasHeightForWidth())
        self.varia_name_label.setSizePolicy(sizePolicy5)
        self.varia_name_label.setFont(font)
        self.varia_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.varia_name_label)

        self.varia_img_label = QLabel(self.varia_value_box)
        self.varia_img_label.setObjectName(u"varia_img_label")
        sizePolicy5.setHeightForWidth(self.varia_img_label.sizePolicy().hasHeightForWidth())
        self.varia_img_label.setSizePolicy(sizePolicy5)
        self.varia_img_label.setMinimumSize(QSize(256, 256))
        self.varia_img_label.setMaximumSize(QSize(16777215, 16777215))
        self.varia_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.varia_img_label)


        self.horizontalLayout_3.addWidget(self.varia_value_box)

        self.varia_right_button = QPushButton(self.varia_suit_box)
        self.varia_right_button.setObjectName(u"varia_right_button")
        sizePolicy3.setHeightForWidth(self.varia_right_button.sizePolicy().hasHeightForWidth())
        self.varia_right_button.setSizePolicy(sizePolicy3)
        self.varia_right_button.setMinimumSize(QSize(0, 0))
        self.varia_right_button.setMaximumSize(QSize(48, 16777215))
        self.varia_right_button.setBaseSize(QSize(0, 0))

        self.horizontalLayout_3.addWidget(self.varia_right_button)


        self.suits_foldable_layout.addWidget(self.varia_suit_box)

        self.dark_suit_box = QGroupBox(self.suits_foldable)
        self.dark_suit_box.setObjectName(u"dark_suit_box")
        self.horizontalLayout_4 = QHBoxLayout(self.dark_suit_box)
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.dark_left_button = QPushButton(self.dark_suit_box)
        self.dark_left_button.setObjectName(u"dark_left_button")
        sizePolicy3.setHeightForWidth(self.dark_left_button.sizePolicy().hasHeightForWidth())
        self.dark_left_button.setSizePolicy(sizePolicy3)
        self.dark_left_button.setMaximumSize(QSize(48, 16777215))

        self.horizontalLayout_4.addWidget(self.dark_left_button)

        self.dark_value_box = QGroupBox(self.dark_suit_box)
        self.dark_value_box.setObjectName(u"dark_value_box")
        sizePolicy4.setHeightForWidth(self.dark_value_box.sizePolicy().hasHeightForWidth())
        self.dark_value_box.setSizePolicy(sizePolicy4)
        self.dark_value_box.setFlat(False)
        self.verticalLayout_4 = QVBoxLayout(self.dark_value_box)
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.dark_name_label = QLabel(self.dark_value_box)
        self.dark_name_label.setObjectName(u"dark_name_label")
        sizePolicy5.setHeightForWidth(self.dark_name_label.sizePolicy().hasHeightForWidth())
        self.dark_name_label.setSizePolicy(sizePolicy5)
        font2 = QFont()
        font2.setBold(True)
        self.dark_name_label.setFont(font2)
        self.dark_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_4.addWidget(self.dark_name_label)

        self.dark_img_label = QLabel(self.dark_value_box)
        self.dark_img_label.setObjectName(u"dark_img_label")
        sizePolicy5.setHeightForWidth(self.dark_img_label.sizePolicy().hasHeightForWidth())
        self.dark_img_label.setSizePolicy(sizePolicy5)
        self.dark_img_label.setMinimumSize(QSize(256, 256))
        self.dark_img_label.setMaximumSize(QSize(16777215, 16777215))
        self.dark_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_4.addWidget(self.dark_img_label)


        self.horizontalLayout_4.addWidget(self.dark_value_box)

        self.dark_right_button = QPushButton(self.dark_suit_box)
        self.dark_right_button.setObjectName(u"dark_right_button")
        sizePolicy3.setHeightForWidth(self.dark_right_button.sizePolicy().hasHeightForWidth())
        self.dark_right_button.setSizePolicy(sizePolicy3)
        self.dark_right_button.setMinimumSize(QSize(0, 0))
        self.dark_right_button.setMaximumSize(QSize(48, 16777215))
        self.dark_right_button.setBaseSize(QSize(0, 0))

        self.horizontalLayout_4.addWidget(self.dark_right_button)


        self.suits_foldable_layout.addWidget(self.dark_suit_box)

        self.light_suit_box = QGroupBox(self.suits_foldable)
        self.light_suit_box.setObjectName(u"light_suit_box")
        self.horizontalLayout_5 = QHBoxLayout(self.light_suit_box)
        self.horizontalLayout_5.setSpacing(6)
        self.horizontalLayout_5.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.light_left_button = QPushButton(self.light_suit_box)
        self.light_left_button.setObjectName(u"light_left_button")
        sizePolicy3.setHeightForWidth(self.light_left_button.sizePolicy().hasHeightForWidth())
        self.light_left_button.setSizePolicy(sizePolicy3)
        self.light_left_button.setMaximumSize(QSize(48, 16777215))

        self.horizontalLayout_5.addWidget(self.light_left_button)

        self.light_value_box = QGroupBox(self.light_suit_box)
        self.light_value_box.setObjectName(u"light_value_box")
        sizePolicy4.setHeightForWidth(self.light_value_box.sizePolicy().hasHeightForWidth())
        self.light_value_box.setSizePolicy(sizePolicy4)
        self.light_value_box.setFlat(False)
        self.verticalLayout_5 = QVBoxLayout(self.light_value_box)
        self.verticalLayout_5.setSpacing(6)
        self.verticalLayout_5.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.light_name_label = QLabel(self.light_value_box)
        self.light_name_label.setObjectName(u"light_name_label")
        sizePolicy5.setHeightForWidth(self.light_name_label.sizePolicy().hasHeightForWidth())
        self.light_name_label.setSizePolicy(sizePolicy5)
        self.light_name_label.setFont(font)
        self.light_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_5.addWidget(self.light_name_label)

        self.light_img_label = QLabel(self.light_value_box)
        self.light_img_label.setObjectName(u"light_img_label")
        sizePolicy5.setHeightForWidth(self.light_img_label.sizePolicy().hasHeightForWidth())
        self.light_img_label.setSizePolicy(sizePolicy5)
        self.light_img_label.setMinimumSize(QSize(256, 256))
        self.light_img_label.setMaximumSize(QSize(16777215, 16777215))
        self.light_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_5.addWidget(self.light_img_label)


        self.horizontalLayout_5.addWidget(self.light_value_box)

        self.light_right_button = QPushButton(self.light_suit_box)
        self.light_right_button.setObjectName(u"light_right_button")
        sizePolicy3.setHeightForWidth(self.light_right_button.sizePolicy().hasHeightForWidth())
        self.light_right_button.setSizePolicy(sizePolicy3)
        self.light_right_button.setMinimumSize(QSize(0, 0))
        self.light_right_button.setMaximumSize(QSize(48, 16777215))
        self.light_right_button.setBaseSize(QSize(0, 0))

        self.horizontalLayout_5.addWidget(self.light_right_button)


        self.suits_foldable_layout.addWidget(self.light_suit_box)

        self.advanced_check = QCheckBox(self.suits_foldable)
        self.advanced_check.setObjectName(u"advanced_check")

        self.suits_foldable_layout.addWidget(self.advanced_check)


        self.verticalLayout.addWidget(self.suits_foldable)

        self.options_foldable = Foldable(self.scroll_area_contents)
        self.options_foldable.setObjectName(u"options_foldable")
        self.options_foldable.setProperty(u"folded", True)
        self.options_foldable_layout = QVBoxLayout(self.options_foldable)
        self.options_foldable_layout.setSpacing(6)
        self.options_foldable_layout.setContentsMargins(11, 11, 11, 11)
        self.options_foldable_layout.setObjectName(u"options_foldable_layout")
        self.description_label = QLabel(self.options_foldable)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.options_foldable_layout.addWidget(self.description_label)

        self.visor_box = QGroupBox(self.options_foldable)
        self.visor_box.setObjectName(u"visor_box")
        self.visor_layout = QGridLayout(self.visor_box)
        self.visor_layout.setSpacing(6)
        self.visor_layout.setContentsMargins(11, 11, 11, 11)
        self.visor_layout.setObjectName(u"visor_layout")
        self.hud_lag_check = QCheckBox(self.visor_box)
        self.hud_lag_check.setObjectName(u"hud_lag_check")

        self.visor_layout.addWidget(self.hud_lag_check, 3, 0, 1, 2)

        self.hud_alpha_label = QLabel(self.visor_box)
        self.hud_alpha_label.setObjectName(u"hud_alpha_label")

        self.visor_layout.addWidget(self.hud_alpha_label, 0, 0, 1, 1)

        self.helmet_alpha_slider = ScrollProtectedSlider(self.visor_box)
        self.helmet_alpha_slider.setObjectName(u"helmet_alpha_slider")
        self.helmet_alpha_slider.setOrientation(Qt.Orientation.Horizontal)
        self.helmet_alpha_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.visor_layout.addWidget(self.helmet_alpha_slider, 1, 1, 1, 1)

        self.hud_alpha_value_label = QLabel(self.visor_box)
        self.hud_alpha_value_label.setObjectName(u"hud_alpha_value_label")

        self.visor_layout.addWidget(self.hud_alpha_value_label, 0, 2, 1, 1)

        self.helmet_alpha_label = QLabel(self.visor_box)
        self.helmet_alpha_label.setObjectName(u"helmet_alpha_label")

        self.visor_layout.addWidget(self.helmet_alpha_label, 1, 0, 1, 1)

        self.helmet_alpha_value_label = QLabel(self.visor_box)
        self.helmet_alpha_value_label.setObjectName(u"helmet_alpha_value_label")

        self.visor_layout.addWidget(self.helmet_alpha_value_label, 1, 2, 1, 1)

        self.hud_alpha_slider = ScrollProtectedSlider(self.visor_box)
        self.hud_alpha_slider.setObjectName(u"hud_alpha_slider")
        self.hud_alpha_slider.setOrientation(Qt.Orientation.Horizontal)
        self.hud_alpha_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.visor_layout.addWidget(self.hud_alpha_slider, 0, 1, 1, 1)

        self.checkBox = QCheckBox(self.visor_box)
        self.checkBox.setObjectName(u"checkBox")
        self.checkBox.setEnabled(False)

        self.visor_layout.addWidget(self.checkBox, 4, 0, 1, 2)


        self.options_foldable_layout.addWidget(self.visor_box)

        self.controls_box = QGroupBox(self.options_foldable)
        self.controls_box.setObjectName(u"controls_box")
        self.controls_layout = QGridLayout(self.controls_box)
        self.controls_layout.setSpacing(6)
        self.controls_layout.setContentsMargins(11, 11, 11, 11)
        self.controls_layout.setObjectName(u"controls_layout")
        self.invert_y_axis_check = QCheckBox(self.controls_box)
        self.invert_y_axis_check.setObjectName(u"invert_y_axis_check")

        self.controls_layout.addWidget(self.invert_y_axis_check, 0, 0, 1, 1)

        self.rumble_check = QCheckBox(self.controls_box)
        self.rumble_check.setObjectName(u"rumble_check")

        self.controls_layout.addWidget(self.rumble_check, 1, 0, 1, 1)


        self.options_foldable_layout.addWidget(self.controls_box)

        self.audio_box = QGroupBox(self.options_foldable)
        self.audio_box.setObjectName(u"audio_box")
        self.audio_layout = QGridLayout(self.audio_box)
        self.audio_layout.setSpacing(6)
        self.audio_layout.setContentsMargins(11, 11, 11, 11)
        self.audio_layout.setObjectName(u"audio_layout")
        self.sound_mode_label = QLabel(self.audio_box)
        self.sound_mode_label.setObjectName(u"sound_mode_label")
        self.sound_mode_label.setMaximumSize(QSize(16777215, 20))

        self.audio_layout.addWidget(self.sound_mode_label, 0, 0, 1, 1)

        self.sfx_volume_label = QLabel(self.audio_box)
        self.sfx_volume_label.setObjectName(u"sfx_volume_label")

        self.audio_layout.addWidget(self.sfx_volume_label, 1, 0, 1, 1)

        self.music_volume_label = QLabel(self.audio_box)
        self.music_volume_label.setObjectName(u"music_volume_label")

        self.audio_layout.addWidget(self.music_volume_label, 2, 0, 1, 1)

        self.sound_mode_combo = QComboBox(self.audio_box)
        self.sound_mode_combo.setObjectName(u"sound_mode_combo")

        self.audio_layout.addWidget(self.sound_mode_combo, 0, 1, 1, 1)

        self.sfx_volume_slider = ScrollProtectedSlider(self.audio_box)
        self.sfx_volume_slider.setObjectName(u"sfx_volume_slider")
        self.sfx_volume_slider.setOrientation(Qt.Orientation.Horizontal)
        self.sfx_volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.audio_layout.addWidget(self.sfx_volume_slider, 1, 1, 1, 1)

        self.music_volume_slider = ScrollProtectedSlider(self.audio_box)
        self.music_volume_slider.setObjectName(u"music_volume_slider")
        self.music_volume_slider.setOrientation(Qt.Orientation.Horizontal)
        self.music_volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.audio_layout.addWidget(self.music_volume_slider, 2, 1, 1, 1)

        self.sfx_volume_value_label = QLabel(self.audio_box)
        self.sfx_volume_value_label.setObjectName(u"sfx_volume_value_label")

        self.audio_layout.addWidget(self.sfx_volume_value_label, 1, 2, 1, 1)

        self.music_volume_value_label = QLabel(self.audio_box)
        self.music_volume_value_label.setObjectName(u"music_volume_value_label")

        self.audio_layout.addWidget(self.music_volume_value_label, 2, 2, 1, 1)


        self.options_foldable_layout.addWidget(self.audio_box)

        self.screen_box = QGroupBox(self.options_foldable)
        self.screen_box.setObjectName(u"screen_box")
        self.screen_layout = QGridLayout(self.screen_box)
        self.screen_layout.setSpacing(6)
        self.screen_layout.setContentsMargins(11, 11, 11, 11)
        self.screen_layout.setObjectName(u"screen_layout")
        self.screen_brightness_label = QLabel(self.screen_box)
        self.screen_brightness_label.setObjectName(u"screen_brightness_label")

        self.screen_layout.addWidget(self.screen_brightness_label, 0, 0, 1, 1)

        self.screen_x_offset_label = QLabel(self.screen_box)
        self.screen_x_offset_label.setObjectName(u"screen_x_offset_label")

        self.screen_layout.addWidget(self.screen_x_offset_label, 1, 0, 1, 1)

        self.screen_brightness_slider = ScrollProtectedSlider(self.screen_box)
        self.screen_brightness_slider.setObjectName(u"screen_brightness_slider")
        self.screen_brightness_slider.setOrientation(Qt.Orientation.Horizontal)
        self.screen_brightness_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.screen_layout.addWidget(self.screen_brightness_slider, 0, 1, 1, 1)

        self.screen_y_offset_slider = ScrollProtectedSlider(self.screen_box)
        self.screen_y_offset_slider.setObjectName(u"screen_y_offset_slider")
        self.screen_y_offset_slider.setOrientation(Qt.Orientation.Horizontal)
        self.screen_y_offset_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.screen_layout.addWidget(self.screen_y_offset_slider, 2, 1, 1, 1)

        self.screen_stretch_label = QLabel(self.screen_box)
        self.screen_stretch_label.setObjectName(u"screen_stretch_label")

        self.screen_layout.addWidget(self.screen_stretch_label, 3, 0, 1, 1)

        self.screen_x_offset_slider = ScrollProtectedSlider(self.screen_box)
        self.screen_x_offset_slider.setObjectName(u"screen_x_offset_slider")
        self.screen_x_offset_slider.setOrientation(Qt.Orientation.Horizontal)
        self.screen_x_offset_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.screen_layout.addWidget(self.screen_x_offset_slider, 1, 1, 1, 1)

        self.screen_stretch_slider = ScrollProtectedSlider(self.screen_box)
        self.screen_stretch_slider.setObjectName(u"screen_stretch_slider")
        self.screen_stretch_slider.setOrientation(Qt.Orientation.Horizontal)
        self.screen_stretch_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.screen_layout.addWidget(self.screen_stretch_slider, 3, 1, 1, 1)

        self.screen_y_offset_label = QLabel(self.screen_box)
        self.screen_y_offset_label.setObjectName(u"screen_y_offset_label")

        self.screen_layout.addWidget(self.screen_y_offset_label, 2, 0, 1, 1)

        self.screen_brightness_value_label = QLabel(self.screen_box)
        self.screen_brightness_value_label.setObjectName(u"screen_brightness_value_label")

        self.screen_layout.addWidget(self.screen_brightness_value_label, 0, 2, 1, 1)

        self.screen_x_offset_value_label = QLabel(self.screen_box)
        self.screen_x_offset_value_label.setObjectName(u"screen_x_offset_value_label")

        self.screen_layout.addWidget(self.screen_x_offset_value_label, 1, 2, 1, 1)

        self.screen_y_offset_value_label = QLabel(self.screen_box)
        self.screen_y_offset_value_label.setObjectName(u"screen_y_offset_value_label")

        self.screen_layout.addWidget(self.screen_y_offset_value_label, 2, 2, 1, 1)

        self.screen_stretch_value_label = QLabel(self.screen_box)
        self.screen_stretch_value_label.setObjectName(u"screen_stretch_value_label")

        self.screen_layout.addWidget(self.screen_stretch_value_label, 3, 2, 1, 1)


        self.options_foldable_layout.addWidget(self.screen_box)


        self.verticalLayout.addWidget(self.options_foldable)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scroll_area_contents)

        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 3)


        self.retranslateUi(EchoesCosmeticPatchesDialog)

        self.accept_button.setDefault(True)


        QMetaObject.connectSlotsByName(EchoesCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, EchoesCosmeticPatchesDialog):
        EchoesCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Metroid Prime 2 - Cosmetic Options", None))
        self.reset_button.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Reset to Defaults", None))
        self.accept_button.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Accept", None))
        self.cancel_button.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Cancel", None))
        self.game_changes_box.setTitle(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Game Changes", None))
        self.custom_hud_color.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Use a custom HUD color", None))
        self.custom_hud_color_button.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Set Color...", None))
        self.faster_credits_check.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Faster Credits", None))
        self.remove_hud_popup_check.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Skip Item Acquisition Popups", None))
        self.pickup_markers_check.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Replace Translator icons on map with item icons", None))
        self.open_map_check.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Open map from start", None))
        self.unvisited_room_names_check.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Always display room names on map", None))
        self.suits_foldable.setProperty(u"title", QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Suit Colors", None))
        self.experimental_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Note: requires the experimental patcher to be enabled.", None))
        self.simple_left_button.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"<", None))
        self.simple_name_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Player 1", None))
        self.simple_img_label.setText("")
        self.simple_right_button.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u">", None))
        self.varia_suit_box.setTitle(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Varia Suit", None))
        self.varia_left_button.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"<", None))
        self.varia_name_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Player 1", None))
        self.varia_img_label.setText("")
        self.varia_right_button.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u">", None))
        self.dark_suit_box.setTitle(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Dark Suit", None))
        self.dark_left_button.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"<", None))
        self.dark_name_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Player 1", None))
        self.dark_img_label.setText("")
        self.dark_right_button.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u">", None))
        self.light_suit_box.setTitle(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Light Suit", None))
        self.light_left_button.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"<", None))
        self.light_name_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Player 1", None))
        self.light_img_label.setText("")
        self.light_right_button.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u">", None))
        self.advanced_check.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Use separate suits", None))
        self.options_foldable.setProperty(u"title", QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"In-Game Options", None))
        self.description_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"<html><head/><body><p>What  you choose here will be used as the default values for the in-game options.</p></body></html>", None))
        self.visor_box.setTitle(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Visor", None))
        self.hud_lag_check.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Hud Lag", None))
        self.hud_alpha_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Visor Opacity", None))
        self.hud_alpha_value_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"TextLabel", None))
        self.helmet_alpha_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Helmet Opacity", None))
        self.helmet_alpha_value_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"TextLabel", None))
#if QT_CONFIG(tooltip)
        self.checkBox.setToolTip(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"<html><head/><body><p>The in-game Hint System has been removed. The option for it remains, but does nothing.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.checkBox.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Hint System", None))
        self.controls_box.setTitle(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Controls", None))
        self.invert_y_axis_check.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Invert Y Axis", None))
        self.rumble_check.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Rumble", None))
        self.audio_box.setTitle(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Audio", None))
        self.sound_mode_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Sound Mode", None))
        self.sfx_volume_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Sound Volume", None))
        self.music_volume_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Music Volume", None))
        self.sfx_volume_value_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"TextLabel", None))
        self.music_volume_value_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"TextLabel", None))
        self.screen_box.setTitle(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Screen", None))
        self.screen_brightness_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Screen Brightness", None))
        self.screen_x_offset_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Screen X Offset", None))
        self.screen_stretch_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Screen Stretch", None))
        self.screen_y_offset_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"Screen Y Offset", None))
        self.screen_brightness_value_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"TextLabel", None))
        self.screen_x_offset_value_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"TextLabel", None))
        self.screen_y_offset_value_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"TextLabel", None))
        self.screen_stretch_value_label.setText(QCoreApplication.translate("EchoesCosmeticPatchesDialog", u"TextLabel", None))
    # retranslateUi

