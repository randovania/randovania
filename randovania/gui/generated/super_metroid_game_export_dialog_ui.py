# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'super_metroid_game_export_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_SuperMetroidGameExportDialog(object):
    def setupUi(self, SuperMetroidGameExportDialog):
        if not SuperMetroidGameExportDialog.objectName():
            SuperMetroidGameExportDialog.setObjectName(u"SuperMetroidGameExportDialog")
        SuperMetroidGameExportDialog.resize(508, 270)
        self.gridLayout = QGridLayout(SuperMetroidGameExportDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.accept_button = QPushButton(SuperMetroidGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 9, 0, 1, 1)

        self.input_file_button = QPushButton(SuperMetroidGameExportDialog)
        self.input_file_button.setObjectName(u"input_file_button")
        self.input_file_button.setMaximumSize(QSize(100, 16777215))

        self.gridLayout.addWidget(self.input_file_button, 2, 2, 1, 1)

        self.output_file_button = QPushButton(SuperMetroidGameExportDialog)
        self.output_file_button.setObjectName(u"output_file_button")
        self.output_file_button.setMaximumSize(QSize(100, 16777215))

        self.gridLayout.addWidget(self.output_file_button, 5, 2, 1, 1)

        self.input_file_label = QLabel(SuperMetroidGameExportDialog)
        self.input_file_label.setObjectName(u"input_file_label")
        self.input_file_label.setMaximumSize(QSize(16777215, 20))

        self.gridLayout.addWidget(self.input_file_label, 1, 0, 1, 2)

        self.input_file_edit = QLineEdit(SuperMetroidGameExportDialog)
        self.input_file_edit.setObjectName(u"input_file_edit")

        self.gridLayout.addWidget(self.input_file_edit, 2, 0, 1, 2)

        self.output_format_layout = QHBoxLayout()
        self.output_format_layout.setSpacing(6)
        self.output_format_layout.setObjectName(u"output_format_layout")
        self.output_format_label = QLabel(SuperMetroidGameExportDialog)
        self.output_format_label.setObjectName(u"output_format_label")

        self.output_format_layout.addWidget(self.output_format_label)


        self.gridLayout.addLayout(self.output_format_layout, 7, 0, 1, 1)

        self.cancel_button = QPushButton(SuperMetroidGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 9, 2, 1, 1)

        self.description_label = QLabel(SuperMetroidGameExportDialog)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.gridLayout.addWidget(self.description_label, 0, 0, 1, 3)

        self.output_file_edit = QLineEdit(SuperMetroidGameExportDialog)
        self.output_file_edit.setObjectName(u"output_file_edit")

        self.gridLayout.addWidget(self.output_file_edit, 5, 0, 1, 2)

        self.output_file_label = QLabel(SuperMetroidGameExportDialog)
        self.output_file_label.setObjectName(u"output_file_label")
        self.output_file_label.setMaximumSize(QSize(16777215, 20))

        self.gridLayout.addWidget(self.output_file_label, 4, 0, 1, 2)

        self.auto_save_spoiler_check = QCheckBox(SuperMetroidGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.gridLayout.addWidget(self.auto_save_spoiler_check, 8, 0, 1, 1)


        self.retranslateUi(SuperMetroidGameExportDialog)

        QMetaObject.connectSlotsByName(SuperMetroidGameExportDialog)
    # setupUi

    def retranslateUi(self, SuperMetroidGameExportDialog):
        SuperMetroidGameExportDialog.setWindowTitle(QCoreApplication.translate("SuperMetroidGameExportDialog", u"Game Patching", None))
        self.accept_button.setText(QCoreApplication.translate("SuperMetroidGameExportDialog", u"Accept", None))
        self.input_file_button.setText(QCoreApplication.translate("SuperMetroidGameExportDialog", u"Select File", None))
        self.output_file_button.setText(QCoreApplication.translate("SuperMetroidGameExportDialog", u"Select File", None))
        self.input_file_label.setText(QCoreApplication.translate("SuperMetroidGameExportDialog", u"Input File (Vanilla SFC/SMC)", None))
        self.input_file_edit.setPlaceholderText(QCoreApplication.translate("SuperMetroidGameExportDialog", u"Path to vanilla SFC/SMC", None))
        self.output_format_label.setText(QCoreApplication.translate("SuperMetroidGameExportDialog", u"Output Format", None))
        self.cancel_button.setText(QCoreApplication.translate("SuperMetroidGameExportDialog", u"Cancel", None))
        self.description_label.setText(QCoreApplication.translate("SuperMetroidGameExportDialog", u"<html><head/><body><p>In order to create the randomized game, an SFC/SMC file of Super Metroid for the Super Famicom/SNES is necessary.</p></body></html>", None))
        self.output_file_edit.setPlaceholderText(QCoreApplication.translate("SuperMetroidGameExportDialog", u"Path where to place randomized game", None))
        self.output_file_label.setText(QCoreApplication.translate("SuperMetroidGameExportDialog", u"Output File", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("SuperMetroidGameExportDialog", u"Include a spoiler log on same directory", None))
    # retranslateUi

