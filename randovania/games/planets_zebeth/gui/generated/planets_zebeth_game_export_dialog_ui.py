# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'planets_zebeth_game_export_dialog.ui'
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

class Ui_PlanetsZebethGameExportDialog(object):
    def setupUi(self, PlanetsZebethGameExportDialog):
        if not PlanetsZebethGameExportDialog.objectName():
            PlanetsZebethGameExportDialog.setObjectName(u"PlanetsZebethGameExportDialog")
        PlanetsZebethGameExportDialog.resize(527, 286)
        self.gridLayout = QGridLayout(PlanetsZebethGameExportDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.accept_button = QPushButton(PlanetsZebethGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 13, 0, 1, 1)

        self.output_folder_button = QPushButton(PlanetsZebethGameExportDialog)
        self.output_folder_button.setObjectName(u"output_folder_button")

        self.gridLayout.addWidget(self.output_folder_button, 6, 1, 1, 1)

        self.input_folder_edit = QLineEdit(PlanetsZebethGameExportDialog)
        self.input_folder_edit.setObjectName(u"input_folder_edit")

        self.gridLayout.addWidget(self.input_folder_edit, 3, 0, 1, 1)

        self.input_folder_label = QLabel(PlanetsZebethGameExportDialog)
        self.input_folder_label.setObjectName(u"input_folder_label")

        self.gridLayout.addWidget(self.input_folder_label, 2, 0, 1, 1)

        self.description_label = QLabel(PlanetsZebethGameExportDialog)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.gridLayout.addWidget(self.description_label, 0, 0, 1, 2)

        self.cancel_button = QPushButton(PlanetsZebethGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 13, 1, 1, 1)

        self.auto_save_spoiler_check = QCheckBox(PlanetsZebethGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.gridLayout.addWidget(self.auto_save_spoiler_check, 9, 0, 1, 1)

        self.line = QFrame(PlanetsZebethGameExportDialog)
        self.line.setObjectName(u"line")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.line.sizePolicy().hasHeightForWidth())
        self.line.setSizePolicy(sizePolicy)
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 7, 0, 1, 2)

        self.input_folder_button = QPushButton(PlanetsZebethGameExportDialog)
        self.input_folder_button.setObjectName(u"input_folder_button")

        self.gridLayout.addWidget(self.input_folder_button, 3, 1, 1, 1)

        self.output_folder_edit = QLineEdit(PlanetsZebethGameExportDialog)
        self.output_folder_edit.setObjectName(u"output_folder_edit")

        self.gridLayout.addWidget(self.output_folder_edit, 6, 0, 1, 1)

        self.output_format_label = QLabel(PlanetsZebethGameExportDialog)
        self.output_format_label.setObjectName(u"output_format_label")

        self.gridLayout.addWidget(self.output_format_label, 8, 0, 1, 1)

        self.output_folder_label = QLabel(PlanetsZebethGameExportDialog)
        self.output_folder_label.setObjectName(u"output_folder_label")

        self.gridLayout.addWidget(self.output_folder_label, 4, 0, 1, 1)

        self.line_2 = QFrame(PlanetsZebethGameExportDialog)
        self.line_2.setObjectName(u"line_2")
        sizePolicy.setHeightForWidth(self.line_2.sizePolicy().hasHeightForWidth())
        self.line_2.setSizePolicy(sizePolicy)
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_2, 1, 0, 1, 2)


        self.retranslateUi(PlanetsZebethGameExportDialog)

        QMetaObject.connectSlotsByName(PlanetsZebethGameExportDialog)
    # setupUi

    def retranslateUi(self, PlanetsZebethGameExportDialog):
        PlanetsZebethGameExportDialog.setWindowTitle(QCoreApplication.translate("PlanetsZebethGameExportDialog", u"Game Patching", None))
        self.accept_button.setText(QCoreApplication.translate("PlanetsZebethGameExportDialog", u"Accept", None))
        self.output_folder_button.setText(QCoreApplication.translate("PlanetsZebethGameExportDialog", u"Select Folder", None))
        self.input_folder_edit.setPlaceholderText(QCoreApplication.translate("PlanetsZebethGameExportDialog", u"Path to Metroid Planets 1.27g folder", None))
        self.input_folder_label.setText(QCoreApplication.translate("PlanetsZebethGameExportDialog", u"Input Directory (1.27g)", None))
        self.description_label.setText(QCoreApplication.translate("PlanetsZebethGameExportDialog", u"<html><head/><body><p>In order to create the randomized game, a 1.27g folder for Metroid Planets is necessary.</p></body></html>", None))
        self.cancel_button.setText(QCoreApplication.translate("PlanetsZebethGameExportDialog", u"Cancel", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("PlanetsZebethGameExportDialog", u"Include a spoiler log on same directory", None))
        self.input_folder_button.setText(QCoreApplication.translate("PlanetsZebethGameExportDialog", u"Select Folder", None))
        self.output_folder_edit.setPlaceholderText(QCoreApplication.translate("PlanetsZebethGameExportDialog", u"Path where to place the randomized game", None))
        self.output_format_label.setText(QCoreApplication.translate("PlanetsZebethGameExportDialog", u"Output Format", None))
        self.output_folder_label.setText(QCoreApplication.translate("PlanetsZebethGameExportDialog", u"Output Directory", None))
    # retranslateUi

