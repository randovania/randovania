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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QFrame,
    QGridLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QWidget)

class Ui_YokuGameExportDialog(object):
    def setupUi(self, YokuGameExportDialog):
        if not YokuGameExportDialog.objectName():
            YokuGameExportDialog.setObjectName(u"YokuGameExportDialog")
        YokuGameExportDialog.resize(520, 240)
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

        self.output_line = QFrame(YokuGameExportDialog)
        self.output_line.setObjectName(u"output_line")
        self.output_line.setFrameShape(QFrame.Shape.HLine)
        self.output_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.root_layout.addWidget(self.output_line, 3, 0, 1, 2)

        self.auto_save_spoiler_check = QCheckBox(YokuGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.root_layout.addWidget(self.auto_save_spoiler_check, 4, 0, 1, 2)

        self.accept_button = QPushButton(YokuGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.root_layout.addWidget(self.accept_button, 5, 0, 1, 1)

        self.cancel_button = QPushButton(YokuGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.root_layout.addWidget(self.cancel_button, 5, 1, 1, 1)


        self.retranslateUi(YokuGameExportDialog)

        QMetaObject.connectSlotsByName(YokuGameExportDialog)
    # setupUi

    def retranslateUi(self, YokuGameExportDialog):
        YokuGameExportDialog.setWindowTitle(QCoreApplication.translate("YokuGameExportDialog", u"Yoku's Island Express Game Exporter", None))
        self.input_folder_label.setText(QCoreApplication.translate("YokuGameExportDialog", u"Game folder", None))
        self.input_folder_edit.setPlaceholderText(QCoreApplication.translate("YokuGameExportDialog", u"The folder with Yoku.exe", None))
        self.input_folder_button.setText(QCoreApplication.translate("YokuGameExportDialog", u"Select Folder", None))
        self.input_folder_description.setText(QCoreApplication.translate("YokuGameExportDialog", u"The export writes the seed into this folder. Start the game, choose an empty save slot and pick \"Start Randovania Seed\". Everything goes into its open-yoku-rando folder; no file of the game is changed.", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("YokuGameExportDialog", u"Include a spoiler log in the game folder", None))
        self.accept_button.setText(QCoreApplication.translate("YokuGameExportDialog", u"Accept", None))
        self.cancel_button.setText(QCoreApplication.translate("YokuGameExportDialog", u"Cancel", None))
    # retranslateUi

