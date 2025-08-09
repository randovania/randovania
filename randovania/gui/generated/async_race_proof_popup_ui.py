# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'async_race_proof_popup.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QLabel, QLineEdit, QPlainTextEdit, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_AsyncRaceProof(object):
    def setupUi(self, AsyncRaceProof):
        if not AsyncRaceProof.objectName():
            AsyncRaceProof.setObjectName(u"AsyncRaceProof")
        AsyncRaceProof.resize(350, 253)
        self.root_layout = QVBoxLayout(AsyncRaceProof)
        self.root_layout.setObjectName(u"root_layout")
        self.proof_label = QLabel(AsyncRaceProof)
        self.proof_label.setObjectName(u"proof_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.proof_label.sizePolicy().hasHeightForWidth())
        self.proof_label.setSizePolicy(sizePolicy)

        self.root_layout.addWidget(self.proof_label)

        self.proof_edit = QLineEdit(AsyncRaceProof)
        self.proof_edit.setObjectName(u"proof_edit")

        self.root_layout.addWidget(self.proof_edit)

        self.notes_label = QLabel(AsyncRaceProof)
        self.notes_label.setObjectName(u"notes_label")

        self.root_layout.addWidget(self.notes_label)

        self.notes_edit = QPlainTextEdit(AsyncRaceProof)
        self.notes_edit.setObjectName(u"notes_edit")
        self.notes_edit.setMaximumSize(QSize(16777215, 100))

        self.root_layout.addWidget(self.notes_edit)

        self.vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.root_layout.addItem(self.vertical_spacer)

        self.button_box = QDialogButtonBox(AsyncRaceProof)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setOrientation(Qt.Orientation.Horizontal)
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.root_layout.addWidget(self.button_box)


        self.retranslateUi(AsyncRaceProof)

        QMetaObject.connectSlotsByName(AsyncRaceProof)
    # setupUi

    def retranslateUi(self, AsyncRaceProof):
        AsyncRaceProof.setWindowTitle(QCoreApplication.translate("AsyncRaceProof", u"Async Race Proof", None))
        self.proof_label.setText(QCoreApplication.translate("AsyncRaceProof", u"Proof URL:", None))
        self.notes_label.setText(QCoreApplication.translate("AsyncRaceProof", u"Submission Notes", None))
    # retranslateUi

