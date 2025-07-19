# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'cs_cosmetic_patches_dialog.ui'
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

class Ui_CSCosmeticPatchesDialog(object):
    def setupUi(self, CSCosmeticPatchesDialog):
        if not CSCosmeticPatchesDialog.objectName():
            CSCosmeticPatchesDialog.setObjectName(u"CSCosmeticPatchesDialog")
        CSCosmeticPatchesDialog.resize(424, 421)
        self.gridLayout = QGridLayout(CSCosmeticPatchesDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.reset_button = QPushButton(CSCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")

        self.gridLayout.addWidget(self.reset_button, 2, 2, 1, 1)

        self.accept_button = QPushButton(CSCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 2, 0, 1, 1)

        self.cancel_button = QPushButton(CSCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 2, 1, 1, 1)

        self.scrollArea = QScrollArea(CSCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 390, 390))
        self.verticalLayout = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.mychar_box = QGroupBox(self.scroll_area_contents)
        self.mychar_box.setObjectName(u"mychar_box")
        self.gridLayout_2 = QGridLayout(self.mychar_box)
        self.gridLayout_2.setSpacing(6)
        self.gridLayout_2.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.mychar_value_box = QGroupBox(self.mychar_box)
        self.mychar_value_box.setObjectName(u"mychar_value_box")
        self.mychar_value_box.setFlat(False)
        self.mychar_value_layout = QHBoxLayout(self.mychar_value_box)
        self.mychar_value_layout.setSpacing(6)
        self.mychar_value_layout.setContentsMargins(11, 11, 11, 11)
        self.mychar_value_layout.setObjectName(u"mychar_value_layout")
        self.mychar_img_label = QLabel(self.mychar_value_box)
        self.mychar_img_label.setObjectName(u"mychar_img_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mychar_img_label.sizePolicy().hasHeightForWidth())
        self.mychar_img_label.setSizePolicy(sizePolicy)
        self.mychar_img_label.setMinimumSize(QSize(64, 32))
        self.mychar_img_label.setMaximumSize(QSize(16777215, 16777215))
        self.mychar_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.mychar_value_layout.addWidget(self.mychar_img_label)

        self.mychar_name_label = QLabel(self.mychar_value_box)
        self.mychar_name_label.setObjectName(u"mychar_name_label")
        sizePolicy.setHeightForWidth(self.mychar_name_label.sizePolicy().hasHeightForWidth())
        self.mychar_name_label.setSizePolicy(sizePolicy)
        self.mychar_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.mychar_value_layout.addWidget(self.mychar_name_label)


        self.gridLayout_2.addWidget(self.mychar_value_box, 0, 1, 1, 1)

        self.mychar_right_button = QPushButton(self.mychar_box)
        self.mychar_right_button.setObjectName(u"mychar_right_button")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.mychar_right_button.sizePolicy().hasHeightForWidth())
        self.mychar_right_button.setSizePolicy(sizePolicy1)
        self.mychar_right_button.setMinimumSize(QSize(0, 0))
        self.mychar_right_button.setMaximumSize(QSize(48, 16777215))
        self.mychar_right_button.setBaseSize(QSize(0, 0))

        self.gridLayout_2.addWidget(self.mychar_right_button, 0, 2, 1, 1)

        self.mychar_left_button = QPushButton(self.mychar_box)
        self.mychar_left_button.setObjectName(u"mychar_left_button")
        sizePolicy1.setHeightForWidth(self.mychar_left_button.sizePolicy().hasHeightForWidth())
        self.mychar_left_button.setSizePolicy(sizePolicy1)
        self.mychar_left_button.setMaximumSize(QSize(48, 16777215))

        self.gridLayout_2.addWidget(self.mychar_left_button, 0, 0, 1, 1)

        self.mychar_description_label = QLabel(self.mychar_box)
        self.mychar_description_label.setObjectName(u"mychar_description_label")
        self.mychar_description_label.setTextFormat(Qt.TextFormat.MarkdownText)

        self.gridLayout_2.addWidget(self.mychar_description_label, 1, 0, 1, 3)


        self.verticalLayout.addWidget(self.mychar_box)

        self.music_box = QGroupBox(self.scroll_area_contents)
        self.music_box.setObjectName(u"music_box")
        self.music_layout = QGridLayout(self.music_box)
        self.music_layout.setSpacing(6)
        self.music_layout.setContentsMargins(11, 11, 11, 11)
        self.music_layout.setObjectName(u"music_layout")
        self.music_type_description_label = QLabel(self.music_box)
        self.music_type_description_label.setObjectName(u"music_type_description_label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.music_type_description_label.sizePolicy().hasHeightForWidth())
        self.music_type_description_label.setSizePolicy(sizePolicy2)
        self.music_type_description_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.music_type_description_label.setWordWrap(True)

        self.music_layout.addWidget(self.music_type_description_label, 3, 0, 1, 2)

        self.song_box = QGroupBox(self.music_box)
        self.song_box.setObjectName(u"song_box")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.song_box.sizePolicy().hasHeightForWidth())
        self.song_box.setSizePolicy(sizePolicy3)
        self.song_box.setCheckable(False)
        self.horizontalLayout = QHBoxLayout(self.song_box)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.song_cs_check = QCheckBox(self.song_box)
        self.song_cs_check.setObjectName(u"song_cs_check")

        self.horizontalLayout.addWidget(self.song_cs_check)

        self.song_beta_check = QCheckBox(self.song_box)
        self.song_beta_check.setObjectName(u"song_beta_check")

        self.horizontalLayout.addWidget(self.song_beta_check)

        self.song_kero_check = QCheckBox(self.song_box)
        self.song_kero_check.setObjectName(u"song_kero_check")

        self.horizontalLayout.addWidget(self.song_kero_check)


        self.music_layout.addWidget(self.song_box, 4, 0, 1, 2)

        self.music_type_combo = QComboBox(self.music_box)
        self.music_type_combo.addItem("")
        self.music_type_combo.addItem("")
        self.music_type_combo.addItem("")
        self.music_type_combo.addItem("")
        self.music_type_combo.setObjectName(u"music_type_combo")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.music_type_combo.sizePolicy().hasHeightForWidth())
        self.music_type_combo.setSizePolicy(sizePolicy4)
        self.music_type_combo.setEditable(False)

        self.music_layout.addWidget(self.music_type_combo, 0, 1, 1, 1)

        self.music_type_label = QLabel(self.music_box)
        self.music_type_label.setObjectName(u"music_type_label")
        self.music_type_label.setMaximumSize(QSize(16777215, 20))

        self.music_layout.addWidget(self.music_type_label, 0, 0, 1, 1)

        self.label = QLabel(self.music_box)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.music_layout.addWidget(self.label, 5, 0, 1, 2)


        self.verticalLayout.addWidget(self.music_box)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.verticalLayout.addItem(self.horizontalSpacer)

        self.scrollArea.setWidget(self.scroll_area_contents)

        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 3)


        self.retranslateUi(CSCosmeticPatchesDialog)

        self.accept_button.setDefault(True)


        QMetaObject.connectSlotsByName(CSCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, CSCosmeticPatchesDialog):
        CSCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("CSCosmeticPatchesDialog", u"Cave Story - Cosmetic Options", None))
        self.reset_button.setText(QCoreApplication.translate("CSCosmeticPatchesDialog", u"Reset to Defaults", None))
        self.accept_button.setText(QCoreApplication.translate("CSCosmeticPatchesDialog", u"Accept", None))
        self.cancel_button.setText(QCoreApplication.translate("CSCosmeticPatchesDialog", u"Cancel", None))
        self.mychar_box.setTitle(QCoreApplication.translate("CSCosmeticPatchesDialog", u"MyChar", None))
        self.mychar_img_label.setText("")
        self.mychar_name_label.setText(QCoreApplication.translate("CSCosmeticPatchesDialog", u"Quote", None))
        self.mychar_right_button.setText(QCoreApplication.translate("CSCosmeticPatchesDialog", u">", None))
        self.mychar_left_button.setText(QCoreApplication.translate("CSCosmeticPatchesDialog", u"<", None))
        self.mychar_description_label.setText("")
        self.music_box.setTitle(QCoreApplication.translate("CSCosmeticPatchesDialog", u"Music", None))
        self.music_type_description_label.setText(QCoreApplication.translate("CSCosmeticPatchesDialog", u"Music will not be randomized.", None))
        self.song_box.setTitle(QCoreApplication.translate("CSCosmeticPatchesDialog", u"Enabled Songs", None))
        self.song_cs_check.setText(QCoreApplication.translate("CSCosmeticPatchesDialog", u"Cave Story", None))
        self.song_beta_check.setText(QCoreApplication.translate("CSCosmeticPatchesDialog", u"Beta", None))
        self.song_kero_check.setText(QCoreApplication.translate("CSCosmeticPatchesDialog", u"Kero Blaster", None))
        self.music_type_combo.setItemText(0, QCoreApplication.translate("CSCosmeticPatchesDialog", u"Vanilla", None))
        self.music_type_combo.setItemText(1, QCoreApplication.translate("CSCosmeticPatchesDialog", u"Shuffle", None))
        self.music_type_combo.setItemText(2, QCoreApplication.translate("CSCosmeticPatchesDialog", u"Random", None))
        self.music_type_combo.setItemText(3, QCoreApplication.translate("CSCosmeticPatchesDialog", u"Chaos", None))

        self.music_type_label.setText(QCoreApplication.translate("CSCosmeticPatchesDialog", u"Randomization Type", None))
        self.label.setText(QCoreApplication.translate("CSCosmeticPatchesDialog", u"Note: Beta and Kero Blaster music are supported only in Freeware Cave Story and CSE2 Tweaked.", None))
    # retranslateUi

