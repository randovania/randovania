# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'am2r_game_export_dialog.ui'
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

class Ui_AM2RGameExportDialog(object):
    def setupUi(self, AM2RGameExportDialog):
        if not AM2RGameExportDialog.objectName():
            AM2RGameExportDialog.setObjectName(u"AM2RGameExportDialog")
        AM2RGameExportDialog.resize(527, 338)
        self.gridLayout = QGridLayout(AM2RGameExportDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.accept_button = QPushButton(AM2RGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 13, 0, 1, 1)

        self.output_file_button = QPushButton(AM2RGameExportDialog)
        self.output_file_button.setObjectName(u"output_file_button")

        self.gridLayout.addWidget(self.output_file_button, 6, 1, 1, 1)

        self.input_file_edit = QLineEdit(AM2RGameExportDialog)
        self.input_file_edit.setObjectName(u"input_file_edit")

        self.gridLayout.addWidget(self.input_file_edit, 3, 0, 1, 1)

        self.input_file_label = QLabel(AM2RGameExportDialog)
        self.input_file_label.setObjectName(u"input_file_label")

        self.gridLayout.addWidget(self.input_file_label, 2, 0, 1, 1)

        self.description_label = QLabel(AM2RGameExportDialog)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.gridLayout.addWidget(self.description_label, 0, 0, 1, 2)

        self.cancel_button = QPushButton(AM2RGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 13, 1, 1, 1)

        self.auto_save_spoiler_check = QCheckBox(AM2RGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.gridLayout.addWidget(self.auto_save_spoiler_check, 9, 0, 1, 1)

        self.line = QFrame(AM2RGameExportDialog)
        self.line.setObjectName(u"line")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.line.sizePolicy().hasHeightForWidth())
        self.line.setSizePolicy(sizePolicy)
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 7, 0, 1, 2)

        self.input_file_button = QPushButton(AM2RGameExportDialog)
        self.input_file_button.setObjectName(u"input_file_button")

        self.gridLayout.addWidget(self.input_file_button, 3, 1, 1, 1)

        self.output_file_edit = QLineEdit(AM2RGameExportDialog)
        self.output_file_edit.setObjectName(u"output_file_edit")

        self.gridLayout.addWidget(self.output_file_edit, 6, 0, 1, 1)

        self.output_format_label = QLabel(AM2RGameExportDialog)
        self.output_format_label.setObjectName(u"output_format_label")

        self.gridLayout.addWidget(self.output_format_label, 8, 0, 1, 1)

        self.output_file_label = QLabel(AM2RGameExportDialog)
        self.output_file_label.setObjectName(u"output_file_label")

        self.gridLayout.addWidget(self.output_file_label, 4, 0, 1, 1)

        self.line_2 = QFrame(AM2RGameExportDialog)
        self.line_2.setObjectName(u"line_2")
        sizePolicy.setHeightForWidth(self.line_2.sizePolicy().hasHeightForWidth())
        self.line_2.setSizePolicy(sizePolicy)
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_2, 1, 0, 1, 2)


        self.retranslateUi(AM2RGameExportDialog)

        QMetaObject.connectSlotsByName(AM2RGameExportDialog)
    # setupUi

    def retranslateUi(self, AM2RGameExportDialog):
        AM2RGameExportDialog.setWindowTitle(QCoreApplication.translate("AM2RGameExportDialog", u"Game Patching", None))
        self.accept_button.setText(QCoreApplication.translate("AM2RGameExportDialog", u"Accept", None))
        self.output_file_button.setText(QCoreApplication.translate("AM2RGameExportDialog", u"Select Folder", None))
        self.input_file_edit.setPlaceholderText(QCoreApplication.translate("AM2RGameExportDialog", u"Path to AM2R 1.5.5 folder", None))
        self.input_file_label.setText(QCoreApplication.translate("AM2RGameExportDialog", u"Input Directory (1.5.5)", None))
        self.description_label.setText(QCoreApplication.translate("AM2RGameExportDialog", u"<html><head/><body><p>In order to create the randomized game, a 1.5.5 folder for AM2R is necessary.</p><p>If you're using the AM2RLauncher and are unsure where that folder is, you can click on the launchers \"Mod Settings\"-Tab, ensure that \"Community Updates (Latest)\" is selected, and then click on the \"Open Profile Folder\" button.</p></body></html>", None))
        self.cancel_button.setText(QCoreApplication.translate("AM2RGameExportDialog", u"Cancel", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("AM2RGameExportDialog", u"Include a spoiler log on same directory", None))
        self.input_file_button.setText(QCoreApplication.translate("AM2RGameExportDialog", u"Select Folder", None))
        self.output_file_edit.setPlaceholderText(QCoreApplication.translate("AM2RGameExportDialog", u"Path where to place the randomized game", None))
        self.output_format_label.setText(QCoreApplication.translate("AM2RGameExportDialog", u"Output Format", None))
        self.output_file_label.setText(QCoreApplication.translate("AM2RGameExportDialog", u"Output Directory", None))
    # retranslateUi

