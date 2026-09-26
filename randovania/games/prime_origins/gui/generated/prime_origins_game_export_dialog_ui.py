# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'prime_origins_game_export_dialog.ui'
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

class Ui_MPOGameExportDialog(object):
    def setupUi(self, MPOGameExportDialog):
        if not MPOGameExportDialog.objectName():
            MPOGameExportDialog.setObjectName(u"MPOGameExportDialog")
        MPOGameExportDialog.resize(527, 338)
        self.gridLayout = QGridLayout(MPOGameExportDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.accept_button = QPushButton(MPOGameExportDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 13, 0, 1, 1)

        self.output_file_button = QPushButton(MPOGameExportDialog)
        self.output_file_button.setObjectName(u"output_file_button")

        self.gridLayout.addWidget(self.output_file_button, 6, 1, 1, 1)

        self.input_file_edit = QLineEdit(MPOGameExportDialog)
        self.input_file_edit.setObjectName(u"input_file_edit")

        self.gridLayout.addWidget(self.input_file_edit, 3, 0, 1, 1)

        self.input_file_label = QLabel(MPOGameExportDialog)
        self.input_file_label.setObjectName(u"input_file_label")

        self.gridLayout.addWidget(self.input_file_label, 2, 0, 1, 1)

        self.description_label = QLabel(MPOGameExportDialog)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.gridLayout.addWidget(self.description_label, 0, 0, 1, 2)

        self.cancel_button = QPushButton(MPOGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 13, 1, 1, 1)

        self.auto_save_spoiler_check = QCheckBox(MPOGameExportDialog)
        self.auto_save_spoiler_check.setObjectName(u"auto_save_spoiler_check")

        self.gridLayout.addWidget(self.auto_save_spoiler_check, 9, 0, 1, 1)

        self.line = QFrame(MPOGameExportDialog)
        self.line.setObjectName(u"line")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.line.sizePolicy().hasHeightForWidth())
        self.line.setSizePolicy(sizePolicy)
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line, 7, 0, 1, 2)

        self.input_file_button = QPushButton(MPOGameExportDialog)
        self.input_file_button.setObjectName(u"input_file_button")

        self.gridLayout.addWidget(self.input_file_button, 3, 1, 1, 1)

        self.output_file_edit = QLineEdit(MPOGameExportDialog)
        self.output_file_edit.setObjectName(u"output_file_edit")

        self.gridLayout.addWidget(self.output_file_edit, 6, 0, 1, 1)

        self.output_format_label = QLabel(MPOGameExportDialog)
        self.output_format_label.setObjectName(u"output_format_label")

        self.gridLayout.addWidget(self.output_format_label, 8, 0, 1, 1)

        self.output_file_label = QLabel(MPOGameExportDialog)
        self.output_file_label.setObjectName(u"output_file_label")

        self.gridLayout.addWidget(self.output_file_label, 4, 0, 1, 1)

        self.line_2 = QFrame(MPOGameExportDialog)
        self.line_2.setObjectName(u"line_2")
        sizePolicy.setHeightForWidth(self.line_2.sizePolicy().hasHeightForWidth())
        self.line_2.setSizePolicy(sizePolicy)
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout.addWidget(self.line_2, 1, 0, 1, 2)


        self.retranslateUi(MPOGameExportDialog)

        QMetaObject.connectSlotsByName(MPOGameExportDialog)
    # setupUi

    def retranslateUi(self, MPOGameExportDialog):
        MPOGameExportDialog.setWindowTitle(QCoreApplication.translate("MPOGameExportDialog", u"Game Patching", None))
        self.accept_button.setText(QCoreApplication.translate("MPOGameExportDialog", u"Accept", None))
        self.output_file_button.setText(QCoreApplication.translate("MPOGameExportDialog", u"Select Folder", None))
        self.input_file_edit.setPlaceholderText(QCoreApplication.translate("MPOGameExportDialog", u"Path to MPO 1.0.4 folder", None))
        self.input_file_label.setText(QCoreApplication.translate("MPOGameExportDialog", u"Input Directory (1.0.4)", None))
        self.description_label.setText(QCoreApplication.translate("MPOGameExportDialog", u"<html><head/><body><p>In order to create the randomized game, a 1.0.4 folder for Metroid Prime Origins is necessary.</p></body></html>", None))
        self.cancel_button.setText(QCoreApplication.translate("MPOGameExportDialog", u"Cancel", None))
        self.auto_save_spoiler_check.setText(QCoreApplication.translate("MPOGameExportDialog", u"Include a spoiler log on same directory", None))
        self.input_file_button.setText(QCoreApplication.translate("MPOGameExportDialog", u"Select Folder", None))
        self.output_file_edit.setPlaceholderText(QCoreApplication.translate("MPOGameExportDialog", u"Path where to place the randomized game", None))
        self.output_format_label.setText(QCoreApplication.translate("MPOGameExportDialog", u"Output Format", None))
        self.output_file_label.setText(QCoreApplication.translate("MPOGameExportDialog", u"Output Directory", None))
    # retranslateUi

