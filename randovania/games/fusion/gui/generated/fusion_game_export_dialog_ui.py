# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fusion_game_export_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QFrame,
    QGridLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QWidget)

class Ui_FusionGameExportDialog(object):
    def setupUi(self, FusionGameExportDialog):
        if not FusionGameExportDialog.objectName():
            FusionGameExportDialog.setObjectName(u"FusionGameExportDialog")
        FusionGameExportDialog.resize(508, 309)
        self.gridLayout = QGridLayout(FusionGameExportDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.input_file_edit = QLineEdit(FusionGameExportDialog)
        self.input_file_edit.setObjectName(u"input_file_edit")

        self.gridLayout.addWidget(self.input_file_edit, 4, 0, 1, 1)

        self.accept_button = QPushButton(FusionGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 11, 0, 1, 1)

        self.input_file_button = QPushButton(FusionGameExportDialog)
        self.input_file_button.setObjectName(u"input_file_button")

        self.gridLayout.addWidget(self.input_file_button, 4, 1, 1, 1)

        self.input_file_label = QLabel(FusionGameExportDialog)
        self.input_file_label.setObjectName(u"input_file_label")

        self.gridLayout.addWidget(self.input_file_label, 3, 0, 1, 1)

        self.description_label = QLabel(FusionGameExportDialog)
        self.description_label.setObjectName(u"description_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.description_label.sizePolicy().hasHeightForWidth())
        self.description_label.setSizePolicy(sizePolicy)
        self.description_label.setMinimumSize(QSize(0, 75))
        self.description_label.setMaximumSize(QSize(480, 16777215))
        self.description_label.setTextFormat(Qt.TextFormat.RichText)
        self.description_label.setWordWrap(True)
        self.description_label.setOpenExternalLinks(True)

        self.gridLayout.addWidget(self.description_label, 0, 0, 1, 2)

        self.output_file_label = QLabel(FusionGameExportDialog)
        self.output_file_label.setObjectName(u"output_file_label")

        self.gridLayout.addWidget(self.output_file_label, 5, 0, 1, 1)

        self.output_file_edit = QLineEdit(FusionGameExportDialog)
        self.output_file_edit.setObjectName(u"output_file_edit")

        self.gridLayout.addWidget(self.output_file_edit, 6, 0, 1, 1)

        self.line = QFrame(FusionGameExportDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 1, 0, 1, 2)

        self.cancel_button = QPushButton(FusionGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 11, 1, 1, 1)

        self.line_2 = QFrame(FusionGameExportDialog)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_2, 7, 0, 1, 2)

        self.output_file_button = QPushButton(FusionGameExportDialog)
        self.output_file_button.setObjectName(u"output_file_button")

        self.gridLayout.addWidget(self.output_file_button, 6, 1, 1, 1)

        self.output_format_label = QLabel(FusionGameExportDialog)
        self.output_format_label.setObjectName(u"output_format_label")

        self.gridLayout.addWidget(self.output_format_label, 8, 0, 1, 1)

        self.auto_save_spoiler_check = QCheckBox(FusionGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.gridLayout.addWidget(self.auto_save_spoiler_check, 9, 0, 1, 1)


        self.retranslateUi(FusionGameExportDialog)

        QMetaObject.connectSlotsByName(FusionGameExportDialog)
    # setupUi

    def retranslateUi(self, FusionGameExportDialog):
        FusionGameExportDialog.setWindowTitle(QCoreApplication.translate("FusionGameExportDialog", u"Game Patching", None))
        self.input_file_edit.setText("")
        self.input_file_edit.setPlaceholderText(QCoreApplication.translate("FusionGameExportDialog", u"Path to Fusion.gba", None))
        self.accept_button.setText(QCoreApplication.translate("FusionGameExportDialog", u"Accept", None))
        self.input_file_button.setText(QCoreApplication.translate("FusionGameExportDialog", u"Select File", None))
        self.input_file_label.setText(QCoreApplication.translate("FusionGameExportDialog", u"Input File (Vanilla Fusion US GBA)", None))
        self.description_label.setText(QCoreApplication.translate("FusionGameExportDialog", u"<html><head/><body><p>In order to create the randomized game, a copy of the US version of Fusion.gba is necessary.</p></body></html>", None))
        self.output_file_label.setText(QCoreApplication.translate("FusionGameExportDialog", u"Output File", None))
        self.output_file_edit.setPlaceholderText(QCoreApplication.translate("FusionGameExportDialog", u"Path to where the randomized game will be outputted", None))
        self.cancel_button.setText(QCoreApplication.translate("FusionGameExportDialog", u"Cancel", None))
        self.output_file_button.setText(QCoreApplication.translate("FusionGameExportDialog", u"Select File", None))
        self.output_format_label.setText(QCoreApplication.translate("FusionGameExportDialog", u"Output Format", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("FusionGameExportDialog", u"Include a spoiler log in the same directory", None))
    # retranslateUi

