# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_history_dialog.ui'
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
    QListWidget, QListWidgetItem, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_PresetHistoryDialog(object):
    def setupUi(self, PresetHistoryDialog):
        if not PresetHistoryDialog.objectName():
            PresetHistoryDialog.setObjectName(u"PresetHistoryDialog")
        PresetHistoryDialog.resize(650, 475)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PresetHistoryDialog.sizePolicy().hasHeightForWidth())
        PresetHistoryDialog.setSizePolicy(sizePolicy)
        self.gridLayout = QGridLayout(PresetHistoryDialog)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.cancel_button = QPushButton(PresetHistoryDialog)
        self.cancel_button.setObjectName(u"cancel_button")

        self.gridLayout.addWidget(self.cancel_button, 3, 3, 1, 1)

        self.accept_button = QPushButton(PresetHistoryDialog)
        self.accept_button.setObjectName(u"accept_button")

        self.gridLayout.addWidget(self.accept_button, 3, 1, 1, 1)

        self.version_widget = QListWidget(PresetHistoryDialog)
        self.version_widget.setObjectName(u"version_widget")
        self.version_widget.setMinimumSize(QSize(150, 0))
        self.version_widget.setMaximumSize(QSize(150, 16777215))

        self.gridLayout.addWidget(self.version_widget, 0, 0, 1, 1)

        self.scroll_area = QScrollArea(PresetHistoryDialog)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_contents = QWidget()
        self.scroll_contents.setObjectName(u"scroll_contents")
        self.scroll_contents.setGeometry(QRect(0, 0, 482, 439))
        self.scroll_layout = QVBoxLayout(self.scroll_contents)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_layout.setObjectName(u"scroll_layout")
        self.scroll_layout.setContentsMargins(2, 2, 2, 2)
        self.label = QLabel(self.scroll_contents)
        self.label.setObjectName(u"label")
        self.label.setTextFormat(Qt.MarkdownText)
        self.label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.label.setWordWrap(True)

        self.scroll_layout.addWidget(self.label)

        self.scroll_area.setWidget(self.scroll_contents)

        self.gridLayout.addWidget(self.scroll_area, 0, 1, 1, 3)

        self.export_button = QPushButton(PresetHistoryDialog)
        self.export_button.setObjectName(u"export_button")

        self.gridLayout.addWidget(self.export_button, 3, 2, 1, 1)


        self.retranslateUi(PresetHistoryDialog)

        QMetaObject.connectSlotsByName(PresetHistoryDialog)
    # setupUi

    def retranslateUi(self, PresetHistoryDialog):
        PresetHistoryDialog.setWindowTitle(QCoreApplication.translate("PresetHistoryDialog", u"Preset History", None))
        self.cancel_button.setText(QCoreApplication.translate("PresetHistoryDialog", u"Cancel", None))
        self.accept_button.setText(QCoreApplication.translate("PresetHistoryDialog", u"Revert to selected", None))
        self.export_button.setText(QCoreApplication.translate("PresetHistoryDialog", u"Export selected", None))
    # retranslateUi

