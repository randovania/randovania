# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'yokus_island_express_game_export_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QFrame, QGridLayout, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QWidget)

class Ui_YokuGameExportDialog(object):
    def setupUi(self, YokuGameExportDialog):
        if not YokuGameExportDialog.objectName():
            YokuGameExportDialog.setObjectName(u"YokuGameExportDialog")
        YokuGameExportDialog.resize(520, 360)
        self.root_layout = QGridLayout(YokuGameExportDialog)
        self.root_layout.setSpacing(6)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.input_folder_label = QLabel(YokuGameExportDialog)
        self.input_folder_label.setObjectName(u"input_folder_label")

        self.root_layout.addWidget(self.input_folder_label, 0, 0, 1, 2)

        self.input_folder_edit = QLineEdit(YokuGameExportDialog)
        self.input_folder_edit.setObjectName(u"input_folder_edit")

        self.root_layout.addWidget(self.input_folder_edit, 1, 0, 1, 1)

        self.input_folder_button = QPushButton(YokuGameExportDialog)
        self.input_folder_button.setObjectName(u"input_folder_button")

        self.root_layout.addWidget(self.input_folder_button, 1, 1, 1, 1)

        self.input_folder_description = QLabel(YokuGameExportDialog)
        self.input_folder_description.setObjectName(u"input_folder_description")
        self.input_folder_description.setWordWrap(True)

        self.root_layout.addWidget(self.input_folder_description, 2, 0, 1, 2)

        self.input_line = QFrame(YokuGameExportDialog)
        self.input_line.setObjectName(u"input_line")
        self.input_line.setFrameShape(QFrame.Shape.HLine)
        self.input_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.root_layout.addWidget(self.input_line, 3, 0, 1, 2)

        self.output_folder_label = QLabel(YokuGameExportDialog)
        self.output_folder_label.setObjectName(u"output_folder_label")

        self.root_layout.addWidget(self.output_folder_label, 4, 0, 1, 2)

        self.output_folder_edit = QLineEdit(YokuGameExportDialog)
        self.output_folder_edit.setObjectName(u"output_folder_edit")

        self.root_layout.addWidget(self.output_folder_edit, 5, 0, 1, 1)

        self.output_folder_button = QPushButton(YokuGameExportDialog)
        self.output_folder_button.setObjectName(u"output_folder_button")

        self.root_layout.addWidget(self.output_folder_button, 5, 1, 1, 1)

        self.use_default_button = QPushButton(YokuGameExportDialog)
        self.use_default_button.setObjectName(u"use_default_button")

        self.root_layout.addWidget(self.use_default_button, 6, 1, 1, 1)

        self.save_slot_label = QLabel(YokuGameExportDialog)
        self.save_slot_label.setObjectName(u"save_slot_label")

        self.root_layout.addWidget(self.save_slot_label, 7, 0, 1, 1)

        self.save_slot_combo = QComboBox(YokuGameExportDialog)
        self.save_slot_combo.setObjectName(u"save_slot_combo")

        self.root_layout.addWidget(self.save_slot_combo, 7, 1, 1, 1)

        self.save_slot_description = QLabel(YokuGameExportDialog)
        self.save_slot_description.setObjectName(u"save_slot_description")
        self.save_slot_description.setWordWrap(True)

        self.root_layout.addWidget(self.save_slot_description, 8, 0, 1, 2)

        self.output_line = QFrame(YokuGameExportDialog)
        self.output_line.setObjectName(u"output_line")
        self.output_line.setFrameShape(QFrame.Shape.HLine)
        self.output_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.root_layout.addWidget(self.output_line, 9, 0, 1, 2)

        self.auto_save_spoiler_check = QCheckBox(YokuGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.root_layout.addWidget(self.auto_save_spoiler_check, 10, 0, 1, 2)

        self.accept_button = QPushButton(YokuGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.root_layout.addWidget(self.accept_button, 11, 0, 1, 1)

        self.cancel_button = QPushButton(YokuGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.root_layout.addWidget(self.cancel_button, 11, 1, 1, 1)


        self.retranslateUi(YokuGameExportDialog)

        QMetaObject.connectSlotsByName(YokuGameExportDialog)
    # setupUi

    def retranslateUi(self, YokuGameExportDialog):
        YokuGameExportDialog.setWindowTitle(QCoreApplication.translate("YokuGameExportDialog", u"Yoku's Island Express Save Exporter", None))
        self.input_folder_label.setText(QCoreApplication.translate("YokuGameExportDialog", u"Game folder", None))
        self.input_folder_edit.setPlaceholderText(QCoreApplication.translate("YokuGameExportDialog", u"The folder with Yoku.exe", None))
        self.input_folder_button.setText(QCoreApplication.translate("YokuGameExportDialog", u"Select Folder", None))
        self.input_folder_description.setText(QCoreApplication.translate("YokuGameExportDialog", u"Nothing items add model files to the game folder and rewrite its item names. A Steam or Epic file check restores it.", None))
        self.output_folder_label.setText(QCoreApplication.translate("YokuGameExportDialog", u"Save folder", None))
        self.output_folder_edit.setPlaceholderText(QCoreApplication.translate("YokuGameExportDialog", u"The folder with the game's saves", None))
        self.output_folder_button.setText(QCoreApplication.translate("YokuGameExportDialog", u"Select Folder", None))
        self.use_default_button.setText(QCoreApplication.translate("YokuGameExportDialog", u"Use default", None))
        self.save_slot_label.setText(QCoreApplication.translate("YokuGameExportDialog", u"Save slot", None))
        self.save_slot_description.setText(QCoreApplication.translate("YokuGameExportDialog", u"The export replaces the game in this save slot. A save that is already there, with its map and trail, is moved to the open-yoku-rando-backups folder in the save folder.", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("YokuGameExportDialog", u"Include a spoiler log in the save folder", None))
        self.accept_button.setText(QCoreApplication.translate("YokuGameExportDialog", u"Accept", None))
        self.cancel_button.setText(QCoreApplication.translate("YokuGameExportDialog", u"Cancel", None))
    # retranslateUi

