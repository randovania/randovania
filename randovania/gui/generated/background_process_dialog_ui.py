# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'background_process_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGridLayout, QLabel,
    QProgressBar, QPushButton, QSizePolicy, QWidget)

class Ui_BackgroundProcessDialog(object):
    def setupUi(self, BackgroundProcessDialog):
        if not BackgroundProcessDialog.objectName():
            BackgroundProcessDialog.setObjectName(u"BackgroundProcessDialog")
        BackgroundProcessDialog.resize(450, 81)
        self.gridLayout = QGridLayout(BackgroundProcessDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.update_button = QPushButton(BackgroundProcessDialog)
        self.update_button.setObjectName(u"update_button")

        self.gridLayout.addWidget(self.update_button, 1, 1, 1, 1)

        self.progress_bar = QProgressBar(BackgroundProcessDialog)
        self.progress_bar.setObjectName(u"progress_bar")
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setInvertedAppearance(False)

        self.gridLayout.addWidget(self.progress_bar, 1, 0, 1, 1)

        self.progress_label = QLabel(BackgroundProcessDialog)
        self.progress_label.setObjectName(u"progress_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.progress_label.sizePolicy().hasHeightForWidth())
        self.progress_label.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(7)
        self.progress_label.setFont(font)
        self.progress_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.progress_label.setWordWrap(True)

        self.gridLayout.addWidget(self.progress_label, 0, 0, 1, 3)


        self.retranslateUi(BackgroundProcessDialog)

        QMetaObject.connectSlotsByName(BackgroundProcessDialog)
    # setupUi

    def retranslateUi(self, BackgroundProcessDialog):
        BackgroundProcessDialog.setWindowTitle(QCoreApplication.translate("BackgroundProcessDialog", u"Background Process", None))
        self.update_button.setText(QCoreApplication.translate("BackgroundProcessDialog", u"Stop", None))
        self.progress_label.setText(QCoreApplication.translate("BackgroundProcessDialog", u"<empty>", None))
    # retranslateUi

