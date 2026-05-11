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
    QGroupBox, QLabel, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_HuntersCosmeticPatchesDialog(object):
    def setupUi(self, HuntersCosmeticPatchesDialog):
        if not HuntersCosmeticPatchesDialog.objectName():
            HuntersCosmeticPatchesDialog.setObjectName(u"HuntersCosmeticPatchesDialog")
        HuntersCosmeticPatchesDialog.resize(396, 246)
        self.gridLayout = QGridLayout(HuntersCosmeticPatchesDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.scrollArea = QScrollArea(HuntersCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 376, 199))
        self.gridLayout_2 = QGridLayout(self.scroll_area_contents)
        self.gridLayout_2.setSpacing(6)
        self.gridLayout_2.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.cosmetic_patches_box = QGroupBox(self.scroll_area_contents)
        self.cosmetic_patches_box.setObjectName(u"cosmetic_patches_box")
        self.verticalLayout = QVBoxLayout(self.cosmetic_patches_box)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.shuffle_hunter_colors_check = QCheckBox(self.cosmetic_patches_box)
        self.shuffle_hunter_colors_check.setObjectName(u"shuffle_hunter_colors_check")

        self.verticalLayout.addWidget(self.shuffle_hunter_colors_check)

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

        self.verticalLayout.addWidget(self.shuffle_hunter_colors_label)


        self.gridLayout_2.addWidget(self.cosmetic_patches_box, 0, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_2.addItem(self.verticalSpacer, 1, 0, 1, 1)

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
        self.reset_button.setText(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u"Reset to Defaults", None))
        self.cancel_button.setText(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u"Cancel", None))
        self.accept_button.setText(QCoreApplication.translate("HuntersCosmeticPatchesDialog", u"Accept", None))
    # retranslateUi

