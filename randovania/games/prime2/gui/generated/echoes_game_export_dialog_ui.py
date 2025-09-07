# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'echoes_game_export_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGridLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QWidget)

class Ui_EchoesGameExportDialog(object):
    def setupUi(self, EchoesGameExportDialog):
        if not EchoesGameExportDialog.objectName():
            EchoesGameExportDialog.setObjectName(u"EchoesGameExportDialog")
        EchoesGameExportDialog.resize(508, 340)
        self.gridLayout = QGridLayout(EchoesGameExportDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.description_label = QLabel(EchoesGameExportDialog)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.gridLayout.addWidget(self.description_label, 0, 0, 1, 3)

        self.accept_button = QPushButton(EchoesGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 10, 0, 1, 1)

        self.input_file_edit = QLineEdit(EchoesGameExportDialog)
        self.input_file_edit.setObjectName(u"input_file_edit")

        self.gridLayout.addWidget(self.input_file_edit, 2, 0, 1, 2)

        self.output_file_button = QPushButton(EchoesGameExportDialog)
        self.output_file_button.setObjectName(u"output_file_button")
        self.output_file_button.setMaximumSize(QSize(100, 16777215))

        self.gridLayout.addWidget(self.output_file_button, 5, 2, 1, 1)

        self.auto_save_spoiler_check = QCheckBox(EchoesGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.gridLayout.addWidget(self.auto_save_spoiler_check, 9, 0, 1, 1)

        self.cancel_button = QPushButton(EchoesGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 10, 2, 1, 1)

        self.input_file_button = QPushButton(EchoesGameExportDialog)
        self.input_file_button.setObjectName(u"input_file_button")
        self.input_file_button.setMaximumSize(QSize(100, 16777215))

        self.gridLayout.addWidget(self.input_file_button, 2, 2, 1, 1)

        self.output_file_edit = QLineEdit(EchoesGameExportDialog)
        self.output_file_edit.setObjectName(u"output_file_edit")

        self.gridLayout.addWidget(self.output_file_edit, 5, 0, 1, 2)

        self.output_file_label = QLabel(EchoesGameExportDialog)
        self.output_file_label.setObjectName(u"output_file_label")
        self.output_file_label.setMaximumSize(QSize(16777215, 20))

        self.gridLayout.addWidget(self.output_file_label, 4, 0, 1, 2)

        self.prime_file_button = QPushButton(EchoesGameExportDialog)
        self.prime_file_button.setObjectName(u"prime_file_button")

        self.gridLayout.addWidget(self.prime_file_button, 8, 2, 1, 1)

        self.input_file_label = QLabel(EchoesGameExportDialog)
        self.input_file_label.setObjectName(u"input_file_label")
        self.input_file_label.setMaximumSize(QSize(16777215, 20))

        self.gridLayout.addWidget(self.input_file_label, 1, 0, 1, 2)

        self.prime_file_edit = QLineEdit(EchoesGameExportDialog)
        self.prime_file_edit.setObjectName(u"prime_file_edit")

        self.gridLayout.addWidget(self.prime_file_edit, 8, 0, 1, 1)

        self.prime_file_label = QLabel(EchoesGameExportDialog)
        self.prime_file_label.setObjectName(u"prime_file_label")

        self.gridLayout.addWidget(self.prime_file_label, 7, 0, 1, 1)

        self.prime_models_check = QCheckBox(EchoesGameExportDialog)
        self.prime_models_check.setObjectName(u"prime_models_check")

        self.gridLayout.addWidget(self.prime_models_check, 6, 0, 1, 1)


        self.retranslateUi(EchoesGameExportDialog)

        QMetaObject.connectSlotsByName(EchoesGameExportDialog)
    # setupUi

    def retranslateUi(self, EchoesGameExportDialog):
        EchoesGameExportDialog.setWindowTitle(QCoreApplication.translate("EchoesGameExportDialog", u"Game Patching", None))
        self.description_label.setText(QCoreApplication.translate("EchoesGameExportDialog", u"<html><head/><body><p>In order to create the randomized game, a ISO file of Metroid Prime 2: Echoes for the Nintendo Gamecube is necessary.</p><p>After using it once, a copy is kept by Randovania for later use.</p></body></html>", None))
        self.accept_button.setText(QCoreApplication.translate("EchoesGameExportDialog", u"Accept", None))
        self.input_file_edit.setPlaceholderText(QCoreApplication.translate("EchoesGameExportDialog", u"Path to vanilla Gamecube ISO", None))
        self.output_file_button.setText(QCoreApplication.translate("EchoesGameExportDialog", u"Select File", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("EchoesGameExportDialog", u"Include a spoiler log on same directory", None))
        self.cancel_button.setText(QCoreApplication.translate("EchoesGameExportDialog", u"Cancel", None))
        self.input_file_button.setText(QCoreApplication.translate("EchoesGameExportDialog", u"Select File", None))
        self.output_file_edit.setPlaceholderText(QCoreApplication.translate("EchoesGameExportDialog", u"Path where to place randomized game", None))
        self.output_file_label.setText(QCoreApplication.translate("EchoesGameExportDialog", u"Output File", None))
        self.prime_file_button.setText(QCoreApplication.translate("EchoesGameExportDialog", u"Select File", None))
        self.input_file_label.setText(QCoreApplication.translate("EchoesGameExportDialog", u"Input File (Vanilla Gamecube ISO)", None))
        self.prime_file_edit.setPlaceholderText(QCoreApplication.translate("EchoesGameExportDialog", u"Path to vanilla Prime Gamecube ISO", None))
        self.prime_file_label.setText(QCoreApplication.translate("EchoesGameExportDialog", u"Prime 1 ISO (for item models)", None))
        self.prime_models_check.setText(QCoreApplication.translate("EchoesGameExportDialog", u"Use correct models for Prime items", None))
    # retranslateUi

