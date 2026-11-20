# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'base_cosmetic_patches_dialog_base.ui'
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

class Ui_BaseCosmeticPatchesDialog(object):
    def setupUi(self, BaseCosmeticPatchesDialog):
        if not BaseCosmeticPatchesDialog.objectName():
            BaseCosmeticPatchesDialog.setObjectName(u"BaseCosmeticPatchesDialog")
        BaseCosmeticPatchesDialog.resize(548, 533)
        self.verticalLayout_2 = QVBoxLayout(BaseCosmeticPatchesDialog)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.scrollArea = QScrollArea(BaseCosmeticPatchesDialog)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 546, 485))
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_contents)
        self.scroll_area_layout.setSpacing(6)
        self.scroll_area_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_area_layout.setObjectName(u"scroll_area_layout")
        self.contentWidget = QWidget(self.scroll_area_contents)
        self.contentWidget.setObjectName(u"contentWidget")

        self.scroll_area_layout.addWidget(self.contentWidget)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scroll_area_contents)

        self.verticalLayout_2.addWidget(self.scrollArea)

        self.line_3 = QFrame(BaseCosmeticPatchesDialog)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.line_3)

        self.footer_layout = QHBoxLayout()
        self.footer_layout.setSpacing(6)
        self.footer_layout.setObjectName(u"footer_layout")
        self.footer_layout.setContentsMargins(6, 6, 6, 6)
        self.reset_button = QPushButton(BaseCosmeticPatchesDialog)
        self.reset_button.setObjectName(u"reset_button")
        self.reset_button.setText(u"\u2b8c Reset to Defaults")
        self.reset_button.setAutoDefault(True)

        self.footer_layout.addWidget(self.reset_button)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.footer_layout.addItem(self.horizontalSpacer_2)

        self.accept_button = QPushButton(BaseCosmeticPatchesDialog)
        self.accept_button.setObjectName(u"accept_button")
        self.accept_button.setMinimumSize(QSize(96, 0))
        self.accept_button.setText(u"\U0001f5f8 Accept")
        self.accept_button.setAutoDefault(True)

        self.footer_layout.addWidget(self.accept_button)

        self.cancel_button = QPushButton(BaseCosmeticPatchesDialog)
        self.cancel_button.setObjectName(u"cancel_button")
        self.cancel_button.setMinimumSize(QSize(96, 0))
        self.cancel_button.setText(u"\U0001f6c7 Cancel")
        self.cancel_button.setAutoDefault(True)

        self.footer_layout.addWidget(self.cancel_button)


        self.verticalLayout_2.addLayout(self.footer_layout)


        self.retranslateUi(BaseCosmeticPatchesDialog)

        self.accept_button.setDefault(True)


        QMetaObject.connectSlotsByName(BaseCosmeticPatchesDialog)
    # setupUi

    def retranslateUi(self, BaseCosmeticPatchesDialog):
        BaseCosmeticPatchesDialog.setWindowTitle(QCoreApplication.translate("BaseCosmeticPatchesDialog", u"PLACEHOLDER TITLE", None))
    # retranslateUi

