# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'widget_location_pool_row.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QRadioButton,
    QSizePolicy, QWidget)

class Ui_LocationPoolRowWidget(object):
    def setupUi(self, LocationPoolRowWidget):
        if not LocationPoolRowWidget.objectName():
            LocationPoolRowWidget.setObjectName(u"LocationPoolRowWidget")
        LocationPoolRowWidget.resize(616, 41)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(LocationPoolRowWidget.sizePolicy().hasHeightForWidth())
        LocationPoolRowWidget.setSizePolicy(sizePolicy)
        LocationPoolRowWidget.setMaximumSize(QSize(16777215, 16777215))
        self.root_layout = QHBoxLayout(LocationPoolRowWidget)
        self.root_layout.setSpacing(6)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.root_layout.setContentsMargins(0, 2, 0, 0)
        self.label_location_name = QLabel(LocationPoolRowWidget)
        self.label_location_name.setObjectName(u"label_location_name")
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        self.label_location_name.setFont(font)

        self.root_layout.addWidget(self.label_location_name)

        self.radio_shuffled = QRadioButton(LocationPoolRowWidget)
        self.radio_shuffled.setObjectName(u"radio_shuffled")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.radio_shuffled.sizePolicy().hasHeightForWidth())
        self.radio_shuffled.setSizePolicy(sizePolicy1)
        self.radio_shuffled.setChecked(True)

        self.root_layout.addWidget(self.radio_shuffled)

        self.radio_shuffled_no_progression = QRadioButton(LocationPoolRowWidget)
        self.radio_shuffled_no_progression.setObjectName(u"radio_shuffled_no_progression")
        sizePolicy1.setHeightForWidth(self.radio_shuffled_no_progression.sizePolicy().hasHeightForWidth())
        self.radio_shuffled_no_progression.setSizePolicy(sizePolicy1)

        self.root_layout.addWidget(self.radio_shuffled_no_progression)


        self.retranslateUi(LocationPoolRowWidget)

        QMetaObject.connectSlotsByName(LocationPoolRowWidget)
    # setupUi

    def retranslateUi(self, LocationPoolRowWidget):
        LocationPoolRowWidget.setWindowTitle(QCoreApplication.translate("LocationPoolRowWidget", u"\n"
"				Item Configuration\n"
"			", None))
        self.label_location_name.setText(QCoreApplication.translate("LocationPoolRowWidget", u"Location name", None))
#if QT_CONFIG(tooltip)
        self.radio_shuffled.setToolTip(QCoreApplication.translate("LocationPoolRowWidget", u"This location is shuffled normally", None))
#endif // QT_CONFIG(tooltip)
        self.radio_shuffled.setText(QCoreApplication.translate("LocationPoolRowWidget", u"Shuffled", None))
#if QT_CONFIG(tooltip)
        self.radio_shuffled_no_progression.setToolTip(QCoreApplication.translate("LocationPoolRowWidget", u"This location is shuffled, but cannot contain a item required for progression", None))
#endif // QT_CONFIG(tooltip)
        self.radio_shuffled_no_progression.setText(QCoreApplication.translate("LocationPoolRowWidget", u"Shuffled (no progression)", None))
    # retranslateUi

