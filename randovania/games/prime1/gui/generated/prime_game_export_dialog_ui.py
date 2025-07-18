# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'prime_game_export_dialog.ui'
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
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QWidget)

class Ui_PrimeGameExportDialog(object):
    def setupUi(self, PrimeGameExportDialog):
        if not PrimeGameExportDialog.objectName():
            PrimeGameExportDialog.setObjectName(u"PrimeGameExportDialog")
        PrimeGameExportDialog.resize(508, 337)
        self.gridLayout = QGridLayout(PrimeGameExportDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.output_file_label = QLabel(PrimeGameExportDialog)
        self.output_file_label.setObjectName(u"output_file_label")
        self.output_file_label.setMaximumSize(QSize(16777215, 20))

        self.gridLayout.addWidget(self.output_file_label, 3, 0, 1, 2)

        self.accept_button = QPushButton(PrimeGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 12, 0, 1, 1)

        self.auto_save_spoiler_check = QCheckBox(PrimeGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.gridLayout.addWidget(self.auto_save_spoiler_check, 11, 0, 1, 1)

        self.echoes_models_check = QCheckBox(PrimeGameExportDialog)
        self.echoes_models_check.setObjectName(u"echoes_models_check")

        self.gridLayout.addWidget(self.echoes_models_check, 7, 0, 1, 1)

        self.echoes_file_label = QLabel(PrimeGameExportDialog)
        self.echoes_file_label.setObjectName(u"echoes_file_label")

        self.gridLayout.addWidget(self.echoes_file_label, 8, 0, 1, 1)

        self.input_file_button = QPushButton(PrimeGameExportDialog)
        self.input_file_button.setObjectName(u"input_file_button")
        self.input_file_button.setMaximumSize(QSize(100, 16777215))

        self.gridLayout.addWidget(self.input_file_button, 2, 2, 1, 1)

        self.echoes_file_button = QPushButton(PrimeGameExportDialog)
        self.echoes_file_button.setObjectName(u"echoes_file_button")
        self.echoes_file_button.setMinimumSize(QSize(0, 23))

        self.gridLayout.addWidget(self.echoes_file_button, 9, 2, 1, 1)

        self.cancel_button = QPushButton(PrimeGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 12, 2, 1, 1)

        self.input_file_edit = QLineEdit(PrimeGameExportDialog)
        self.input_file_edit.setObjectName(u"input_file_edit")

        self.gridLayout.addWidget(self.input_file_edit, 2, 0, 1, 2)

        self.output_file_button = QPushButton(PrimeGameExportDialog)
        self.output_file_button.setObjectName(u"output_file_button")
        self.output_file_button.setMaximumSize(QSize(100, 16777215))

        self.gridLayout.addWidget(self.output_file_button, 4, 2, 1, 1)

        self.input_file_label = QLabel(PrimeGameExportDialog)
        self.input_file_label.setObjectName(u"input_file_label")
        self.input_file_label.setMaximumSize(QSize(16777215, 20))

        self.gridLayout.addWidget(self.input_file_label, 1, 0, 1, 2)

        self.echoes_file_edit = QLineEdit(PrimeGameExportDialog)
        self.echoes_file_edit.setObjectName(u"echoes_file_edit")

        self.gridLayout.addWidget(self.echoes_file_edit, 9, 0, 1, 1)

        self.output_format_layout = QHBoxLayout()
        self.output_format_layout.setSpacing(6)
        self.output_format_layout.setObjectName(u"output_format_layout")
        self.output_format_label = QLabel(PrimeGameExportDialog)
        self.output_format_label.setObjectName(u"output_format_label")

        self.output_format_layout.addWidget(self.output_format_label)


        self.gridLayout.addLayout(self.output_format_layout, 6, 0, 1, 1)

        self.output_file_edit = QLineEdit(PrimeGameExportDialog)
        self.output_file_edit.setObjectName(u"output_file_edit")

        self.gridLayout.addWidget(self.output_file_edit, 4, 0, 1, 2)

        self.description_label = QLabel(PrimeGameExportDialog)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.gridLayout.addWidget(self.description_label, 0, 0, 1, 3)


        self.retranslateUi(PrimeGameExportDialog)

        QMetaObject.connectSlotsByName(PrimeGameExportDialog)
    # setupUi

    def retranslateUi(self, PrimeGameExportDialog):
        PrimeGameExportDialog.setWindowTitle(QCoreApplication.translate("PrimeGameExportDialog", u"Game Patching", None))
        self.output_file_label.setText(QCoreApplication.translate("PrimeGameExportDialog", u"Output File", None))
        self.accept_button.setText(QCoreApplication.translate("PrimeGameExportDialog", u"Accept", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("PrimeGameExportDialog", u"Include a spoiler log on same directory", None))
        self.echoes_models_check.setText(QCoreApplication.translate("PrimeGameExportDialog", u"Use correct models for Echoes items", None))
        self.echoes_file_label.setText(QCoreApplication.translate("PrimeGameExportDialog", u"Echoes ISO File (for item models)", None))
        self.input_file_button.setText(QCoreApplication.translate("PrimeGameExportDialog", u"Select File", None))
        self.echoes_file_button.setText(QCoreApplication.translate("PrimeGameExportDialog", u"Select File", None))
        self.cancel_button.setText(QCoreApplication.translate("PrimeGameExportDialog", u"Cancel", None))
        self.input_file_edit.setPlaceholderText(QCoreApplication.translate("PrimeGameExportDialog", u"Path to vanilla Gamecube ISO", None))
        self.output_file_button.setText(QCoreApplication.translate("PrimeGameExportDialog", u"Select File", None))
        self.input_file_label.setText(QCoreApplication.translate("PrimeGameExportDialog", u"Input File (Vanilla Gamecube ISO)", None))
        self.echoes_file_edit.setText("")
        self.echoes_file_edit.setPlaceholderText(QCoreApplication.translate("PrimeGameExportDialog", u"Path to vanilla Echoes Gamecube ISO", None))
        self.output_format_label.setText(QCoreApplication.translate("PrimeGameExportDialog", u"Output Format", None))
        self.output_file_edit.setPlaceholderText(QCoreApplication.translate("PrimeGameExportDialog", u"Path where to place randomized game", None))
        self.description_label.setText(QCoreApplication.translate("PrimeGameExportDialog", u"<html><head/><body><p>In order to create the randomized game, an ISO file of Metroid Prime for the Nintendo Gamecube is necessary.</p></body></html>", None))
    # retranslateUi

