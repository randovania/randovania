# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'trick_usage_popup.ui'
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
    QLabel, QScrollArea, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_TrickUsagePopup(object):
    def setupUi(self, TrickUsagePopup):
        if not TrickUsagePopup.objectName():
            TrickUsagePopup.setObjectName(u"TrickUsagePopup")
        TrickUsagePopup.resize(431, 444)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(TrickUsagePopup.sizePolicy().hasHeightForWidth())
        TrickUsagePopup.setSizePolicy(sizePolicy)
        TrickUsagePopup.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(TrickUsagePopup)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.title_label = QLabel(TrickUsagePopup)
        self.title_label.setObjectName(u"title_label")
        self.title_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)
        self.title_label.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        self.title_label.setWordWrap(True)
        self.title_label.setOpenExternalLinks(True)

        self.verticalLayout.addWidget(self.title_label)

        self.scroll_area = QScrollArea(TrickUsagePopup)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 411, 295))
        self.verticalLayout_2 = QVBoxLayout(self.scroll_area_contents)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.area_list_label = QLabel(self.scroll_area_contents)
        self.area_list_label.setObjectName(u"area_list_label")
        self.area_list_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.area_list_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.area_list_label)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.verticalLayout.addWidget(self.scroll_area)

        self.button_box = QDialogButtonBox(TrickUsagePopup)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout.addWidget(self.button_box)


        self.retranslateUi(TrickUsagePopup)

        QMetaObject.connectSlotsByName(TrickUsagePopup)
    # setupUi

    def retranslateUi(self, TrickUsagePopup):
        TrickUsagePopup.setWindowTitle(QCoreApplication.translate("TrickUsagePopup", u"Trick Usage", None))
        self.title_label.setText(QCoreApplication.translate("TrickUsagePopup", u"<html><head/><body><p>This popup lists all occurrences of tricks that are in logical use for this preset.</p><p>Enabled tricks:<br/>{trick_levels}</p><p>Click a room name to open it in the Data Visualizer for more details.</p></body></html>", None))
        self.area_list_label.setText(QCoreApplication.translate("TrickUsagePopup", u"<html><head/><body><p><a href=\"data-editor://World/Area\">INSERT AREAS!</a></p></body></html>", None))
    # retranslateUi

