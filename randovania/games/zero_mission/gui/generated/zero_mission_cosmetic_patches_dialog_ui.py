# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'zero_mission_cosmetic_patches_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_MZMCosmeticPatchesDialog(object):
    def setupUi(self, BlankCosmeticPatchesDialog):
        if not BlankCosmeticPatchesDialog.objectName():
            BlankCosmeticPatchesDialog.setObjectName(u"BlankCosmeticPatchesDialog")
        BlankCosmeticPatchesDialog.resize(396, 246)
        self.verticalLayout_2 = QVBoxLayout(BlankCosmeticPatchesDialog)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(BlankCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 394, 198))
        self.verticalLayout = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea.setWidget(self.scroll_area_contents)

        self.verticalLayout_2.addWidget(self.scrollArea)

        self.line = QFrame(BlankCosmeticPatchesDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.line)

        self.footer_layout = QHBoxLayout()
        self.footer_layout.setSpacing(6)
        self.footer_layout.setObjectName(u"footer_layout")
        self.footer_layout.setContentsMargins(6, 6, 6, 6)
        self.reset_button = QPushButton(BlankCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")
        self.reset_button.setText(u"\u2b8c Reset to Defaults")

        self.footer_layout.addWidget(self.reset_button)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.footer_layout.addItem(self.horizontalSpacer)

        self.accept_button = QPushButton(BlankCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.accept_button.sizePolicy().hasHeightForWidth())
        self.accept_button.setSizePolicy(sizePolicy)
        self.accept_button.setMinimumSize(QSize(96, 0))
        self.accept_button.setText(u"\U0001f5f8 Accept")

        self.footer_layout.addWidget(self.accept_button)

        self.cancel_button = QPushButton(BlankCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")
        sizePolicy.setHeightForWidth(self.cancel_button.sizePolicy().hasHeightForWidth())
        self.cancel_button.setSizePolicy(sizePolicy)
        self.cancel_button.setMinimumSize(QSize(96, 0))
        self.cancel_button.setText(u"\U0001f6c7 Cancel")

        self.footer_layout.addWidget(self.cancel_button)


        self.verticalLayout_2.addLayout(self.footer_layout)


        self.retranslateUi(BlankCosmeticPatchesDialog)

        self.accept_button.setDefault(True)


        QMetaObject.connectSlotsByName(BlankCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, BlankCosmeticPatchesDialog):
        BlankCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("MZMCosmeticPatchesDialog", u"MZM Game - Cosmetic Options", None))
    # retranslateUi

