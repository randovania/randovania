# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'prime_hunters_cosmetic_patches_dialog.ui'
##
## Created by: tools/uic_wrapper.py
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

class Ui_HuntersCosmeticPatchesDialog(object):
    def setupUi(self, HuntersCosmeticPatchesDialog):
        if not HuntersCosmeticPatchesDialog.objectName():
            HuntersCosmeticPatchesDialog.setObjectName(u"HuntersCosmeticPatchesDialog")
        HuntersCosmeticPatchesDialog.resize(483, 568)
        self.gridLayout = QGridLayout(HuntersCosmeticPatchesDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.scrollArea = QScrollArea(HuntersCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 463, 521))
        self.verticalLayout = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.cosmetic_patches_box = QGroupBox(self.scroll_area_contents)
        self.cosmetic_patches_box.setObjectName(u"cosmetic_patches_box")
        self.verticalLayout_4 = QVBoxLayout(self.cosmetic_patches_box)
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.shuffle_hunter_colors_check = QCheckBox(self.cosmetic_patches_box)
        self.shuffle_hunter_colors_check.setObjectName(u"shuffle_hunter_colors_check")

        self.verticalLayout_4.addWidget(self.shuffle_hunter_colors_check)

        self.shuffle_hunter_colors_label = QLabel(self.cosmetic_patches_box)
        self.shuffle_hunter_colors_label.setObjectName(u"shuffle_hunter_colors_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.shuffle_hunter_colors_label.sizePolicy().hasHeightForWidth())
        self.shuffle_hunter_colors_label.setSizePolicy(sizePolicy)
        self.shuffle_hunter_colors_label.setMinimumSize(QSize(0, 0))
        font = QFont()
        font.setKerning(True)
        self.shuffle_hunter_colors_label.setFont(font)
        self.shuffle_hunter_colors_label.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.shuffle_hunter_colors_label)

        self.suit_box = QGroupBox(self.cosmetic_patches_box)
        self.suit_box.setObjectName(u"suit_box")
        self.horizontalLayout_5 = QHBoxLayout(self.suit_box)
        self.horizontalLayout_5.setSpacing(6)
        self.horizontalLayout_5.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.left_button = QPushButton(self.suit_box)
        self.left_button.setObjectName(u"left_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.left_button.sizePolicy().hasHeightForWidth())
        self.left_button.setSizePolicy(sizePolicy1)
        self.left_button.setMaximumSize(QSize(48, 16777215))

        self.horizontalLayout_5.addWidget(self.left_button)

        self.value_box = QGroupBox(self.suit_box)
        self.value_box.setObjectName(u"value_box")
        sizePolicy.setHeightForWidth(self.value_box.sizePolicy().hasHeightForWidth())
        self.value_box.setSizePolicy(sizePolicy)
        self.value_box.setFlat(False)
        self.verticalLayout_6 = QVBoxLayout(self.value_box)
        self.verticalLayout_6.setSpacing(6)
        self.verticalLayout_6.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.name_label = QLabel(self.value_box)
        self.name_label.setObjectName(u"name_label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.name_label.sizePolicy().hasHeightForWidth())
        self.name_label.setSizePolicy(sizePolicy2)
        font1 = QFont()
        font1.setBold(True)
        self.name_label.setFont(font1)

        self.verticalLayout_6.addWidget(self.name_label)

        self.img_label = QLabel(self.value_box)
        self.img_label.setObjectName(u"img_label")
        sizePolicy2.setHeightForWidth(self.img_label.sizePolicy().hasHeightForWidth())
        self.img_label.setSizePolicy(sizePolicy2)
        self.img_label.setMinimumSize(QSize(256, 256))
        self.img_label.setMaximumSize(QSize(16777215, 16777215))

        self.verticalLayout_6.addWidget(self.img_label)


        self.horizontalLayout_5.addWidget(self.value_box)

        self.right_button = QPushButton(self.suit_box)
        self.right_button.setObjectName(u"right_button")
        sizePolicy1.setHeightForWidth(self.right_button.sizePolicy().hasHeightForWidth())
        self.right_button.setSizePolicy(sizePolicy1)
        self.right_button.setMinimumSize(QSize(0, 0))
        self.right_button.setMaximumSize(QSize(48, 16777215))
        self.right_button.setBaseSize(QSize(0, 0))

        self.horizontalLayout_5.addWidget(self.right_button)


        self.verticalLayout_4.addWidget(self.suit_box)


        self.verticalLayout.addWidget(self.cosmetic_patches_box)

        self.scrollArea.setWidget(self.scroll_area_contents)

        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 3)

        self.reset_button = QPushButton(HuntersCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")

        self.gridLayout.addWidget(self.reset_button, 2, 2, 1, 1)

        self.cancel_button = QPushButton(HuntersCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 2, 1, 1, 1)

        self.accept_button = QPushButton(HuntersCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 2, 0, 1, 1)


        self.retranslateUi(HuntersCosmeticPatchesDialog)

        self.accept_button.setDefault(True)


        QMetaObject.connectSlotsByName(HuntersCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, HuntersCosmeticPatchesDialog):
        HuntersCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u"Hunters Game - Cosmetic Options", None))
        self.cosmetic_patches_box.setTitle(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u"Cosmetic Patches", None))
        self.shuffle_hunter_colors_check.setText(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u"Shuffle Hunter Colors", None))
        self.shuffle_hunter_colors_label.setText(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u"This changes how the Hunters appear in game by using alternate textures from multiplayer.", None))
        self.suit_box.setTitle(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u"Suit Color", None))
        self.left_button.setText(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u"<", None))
        self.name_label.setText(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u"Player 1", None))
        self.img_label.setText("")
        self.right_button.setText(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u">", None))
        self.reset_button.setText(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u"Reset to Defaults", None))
        self.cancel_button.setText(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u"Cancel", None))
        self.accept_button.setText(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u"Accept", None))
    # retranslateUi

