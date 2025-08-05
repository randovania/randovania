# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'reporting_optout_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QLabel,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_ReportingOptOutWidget(object):
    def setupUi(self, ReportingOptOutWidget):
        if not ReportingOptOutWidget.objectName():
            ReportingOptOutWidget.setObjectName(u"ReportingOptOutWidget")
        ReportingOptOutWidget.resize(375, 277)
        self.root_layout = QVBoxLayout(ReportingOptOutWidget)
        self.root_layout.setObjectName(u"root_layout")
        self.intro_label = QLabel(ReportingOptOutWidget)
        self.intro_label.setObjectName(u"intro_label")
        self.intro_label.setTextFormat(Qt.MarkdownText)
        self.intro_label.setWordWrap(True)

        self.root_layout.addWidget(self.intro_label)

        self.allow_reports_check = QCheckBox(ReportingOptOutWidget)
        self.allow_reports_check.setObjectName(u"allow_reports_check")

        self.root_layout.addWidget(self.allow_reports_check)

        self.allow_reports_label = QLabel(ReportingOptOutWidget)
        self.allow_reports_label.setObjectName(u"allow_reports_label")
        self.allow_reports_label.setTextFormat(Qt.MarkdownText)
        self.allow_reports_label.setWordWrap(True)

        self.root_layout.addWidget(self.allow_reports_label)

        self.include_user_check = QCheckBox(ReportingOptOutWidget)
        self.include_user_check.setObjectName(u"include_user_check")

        self.root_layout.addWidget(self.include_user_check)

        self.line = QFrame(ReportingOptOutWidget)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.root_layout.addWidget(self.line)

        self.privacy_policy_label = QLabel(ReportingOptOutWidget)
        self.privacy_policy_label.setObjectName(u"privacy_policy_label")
        self.privacy_policy_label.setWordWrap(True)
        self.privacy_policy_label.setOpenExternalLinks(True)

        self.root_layout.addWidget(self.privacy_policy_label)


        self.retranslateUi(ReportingOptOutWidget)

        QMetaObject.connectSlotsByName(ReportingOptOutWidget)
    # setupUi

    def retranslateUi(self, ReportingOptOutWidget):
        ReportingOptOutWidget.setWindowTitle(QCoreApplication.translate("ReportingOptOutWidget", u"Automatic Data Collection and Reporting", None))
        self.intro_label.setText(QCoreApplication.translate("ReportingOptOutWidget", u"<html><head/><body><p>The following settings controls how the Randovania client application reports data. </p></body></html>", None))
        self.allow_reports_check.setText(QCoreApplication.translate("ReportingOptOutWidget", u"Automatically report errors and performance of key components", None))
        self.allow_reports_label.setText(QCoreApplication.translate("ReportingOptOutWidget", u"<html><head/><body><p>These repots include:</p><p>- All errors that happen, with contextual data of the situation they happened.<br/>- Performance metrics of key locations of the application </p><p>These reports are filtered of any known identifiable data, such as Windows usernames, but some may still be accidentally included.</p><p>Restarting Randovania is required for changes to this to take effect.</p></body></html>", None))
        self.include_user_check.setText(QCoreApplication.translate("ReportingOptOutWidget", u"Allow reports to be associated with your user, if logged in", None))
        self.privacy_policy_label.setText(QCoreApplication.translate("ReportingOptOutWidget", u"<html><head/><body><p>Any data collected is only visible by trusted members of the Randovania team, and is utilized in accordance to our <a href=\"https://github.com/randovania/randovania/blob/main/PRIVACY_POLICY.md\"><span style=\" text-decoration: underline; color:#007af4;\">Privacy Policy</span></a>.</p><p>All reporting, aggregating and hosting of the data is done by <a href=\"https://sentry.io/\"><span style=\" text-decoration: underline; color:#007af4;\">sentry.io</span></a>, which has graciously sponsored a free account for Randovania.</p></body></html>", None))
    # retranslateUi

