# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'fusion_game_export_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

class Ui_FusionGameExportDialog(object):
    def setupUi(self, FusionGameExportDialog):
        if not FusionGameExportDialog.objectName():
            FusionGameExportDialog.setObjectName(u"FusionGameExportDialog")
        FusionGameExportDialog.resize(508, 273)
        self.gridLayout = QGridLayout(FusionGameExportDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.description_label = QLabel(FusionGameExportDialog)
        self.description_label.setObjectName(u"description_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.description_label.sizePolicy().hasHeightForWidth())
        self.description_label.setSizePolicy(sizePolicy)
        self.description_label.setMinimumSize(QSize(0, 75))
        self.description_label.setMaximumSize(QSize(480, 16777215))
        self.description_label.setTextFormat(Qt.RichText)
        self.description_label.setWordWrap(True)
        self.description_label.setOpenExternalLinks(True)

        self.gridLayout.addWidget(self.description_label, 0, 0, 1, 2)

        self.cancel_button = QPushButton(FusionGameExportDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 2, 0, 1, 2)


        self.retranslateUi(FusionGameExportDialog)

        QMetaObject.connectSlotsByName(FusionGameExportDialog)
    # setupUi

    def retranslateUi(self, FusionGameExportDialog):
        FusionGameExportDialog.setWindowTitle(QCoreApplication.translate("FusionGameExportDialog", u"Game Patching", None))
        self.description_label.setText(QCoreApplication.translate("FusionGameExportDialog", u"<html><head/><body><p>Exporting is currently not supported for Fusion!</p><p>Please be patient, as we are still very early in development :)</p></body></html>", None))
        self.cancel_button.setText(QCoreApplication.translate("FusionGameExportDialog", u"Cancel", None))
    # retranslateUi

