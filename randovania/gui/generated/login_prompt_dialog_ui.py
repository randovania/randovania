# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'login_prompt_dialog.ui'
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
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_LoginPromptDialog(object):
    def setupUi(self, LoginPromptDialog):
        if not LoginPromptDialog.objectName():
            LoginPromptDialog.setObjectName(u"LoginPromptDialog")
        LoginPromptDialog.resize(331, 233)
        self.layout = QVBoxLayout(LoginPromptDialog)
        self.layout.setSpacing(6)
        self.layout.setContentsMargins(11, 11, 11, 11)
        self.layout.setObjectName(u"layout")
        self.title_label = QLabel(LoginPromptDialog)
        self.title_label.setObjectName(u"title_label")
        self.title_label.setWordWrap(True)

        self.layout.addWidget(self.title_label)

        self.discord_button = QPushButton(LoginPromptDialog)
        self.discord_button.setObjectName(u"discord_button")

        self.layout.addWidget(self.discord_button)

        self.discord_label = QLabel(LoginPromptDialog)
        self.discord_label.setObjectName(u"discord_label")
        self.discord_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.discord_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.discord_label.setWordWrap(True)
        self.discord_label.setOpenExternalLinks(True)
        self.discord_label.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.layout.addWidget(self.discord_label)

        self.discord_qr_label = QLabel(LoginPromptDialog)
        self.discord_qr_label.setObjectName(u"discord_qr_label")
        self.discord_qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.discord_qr_label)

        self.guest_button = QPushButton(LoginPromptDialog)
        self.guest_button.setObjectName(u"guest_button")

        self.layout.addWidget(self.guest_button)

        self.connection_status_label = QLabel(LoginPromptDialog)
        self.connection_status_label.setObjectName(u"connection_status_label")
        self.connection_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(self.connection_status_label)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.layout.addItem(self.spacer)

        self.privacy_policy_label = QLabel(LoginPromptDialog)
        self.privacy_policy_label.setObjectName(u"privacy_policy_label")
        self.privacy_policy_label.setAlignment(Qt.AlignmentFlag.AlignBottom|Qt.AlignmentFlag.AlignHCenter)
        self.privacy_policy_label.setWordWrap(True)
        self.privacy_policy_label.setOpenExternalLinks(True)

        self.layout.addWidget(self.privacy_policy_label)

        self.button_box = QDialogButtonBox(LoginPromptDialog)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Reset)

        self.layout.addWidget(self.button_box)


        self.retranslateUi(LoginPromptDialog)

        QMetaObject.connectSlotsByName(LoginPromptDialog)
    # setupUi

    def retranslateUi(self, LoginPromptDialog):
        LoginPromptDialog.setWindowTitle(QCoreApplication.translate("LoginPromptDialog", u"Login Window", None))
        self.title_label.setText(QCoreApplication.translate("LoginPromptDialog", u"<html><head/><body><p>Usage of Randovania's online services depends on an user account.</p><p>Currently, only login via Discord is supported.</p></body></html>", None))
        self.discord_button.setText(QCoreApplication.translate("LoginPromptDialog", u"Login with Discord", None))
        self.guest_button.setText(QCoreApplication.translate("LoginPromptDialog", u"Login as Guest", None))
        self.connection_status_label.setText("")
        self.privacy_policy_label.setText(QCoreApplication.translate("LoginPromptDialog", u"<html><head/><body><p>By creating an account, you are agreeing to Randovania's <a href=\"https://github.com/randovania/randovania/blob/master/PRIVACY_POLICY.md\"><span style=\" text-decoration: underline; color:#0000ff;\">Privacy Policy</span></a>.</p></body></html>", None))
    # retranslateUi

