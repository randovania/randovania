# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'game_connection_window.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QScrollArea, QSizePolicy,
    QSpacerItem, QToolButton, QVBoxLayout, QWidget)

class Ui_GameConnectionWindow(object):
    def setupUi(self, GameConnectionWindow):
        if not GameConnectionWindow.objectName():
            GameConnectionWindow.setObjectName(u"GameConnectionWindow")
        GameConnectionWindow.resize(472, 288)
        self.centralwidget = QWidget(GameConnectionWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.root_layout = QGridLayout(self.centralwidget)
        self.root_layout.setObjectName(u"root_layout")
        self.root_layout.setContentsMargins(-1, 4, 4, 4)
        self.help_label = QLabel(self.centralwidget)
        self.help_label.setObjectName(u"help_label")
        self.help_label.setTextFormat(Qt.MarkdownText)
        self.help_label.setWordWrap(True)

        self.root_layout.addWidget(self.help_label, 1, 0, 1, 1)

        self.builders_scroll = QScrollArea(self.centralwidget)
        self.builders_scroll.setObjectName(u"builders_scroll")
        self.builders_scroll.setWidgetResizable(True)
        self.builders_content = QWidget()
        self.builders_content.setObjectName(u"builders_content")
        self.builders_content.setGeometry(QRect(0, 0, 460, 189))
        self.builders_layout = QVBoxLayout(self.builders_content)
        self.builders_layout.setObjectName(u"builders_layout")
        self.builders_layout.setContentsMargins(4, 4, 4, 4)
        self.builders_scroll.setWidget(self.builders_content)

        self.root_layout.addWidget(self.builders_scroll, 2, 0, 1, 1)

        self.meta_group = QGroupBox(self.centralwidget)
        self.meta_group.setObjectName(u"meta_group")
        self.meta_group.setFlat(True)
        self.meta_layout = QHBoxLayout(self.meta_group)
        self.meta_layout.setObjectName(u"meta_layout")
        self.meta_layout.setContentsMargins(1, 1, 1, 1)
        self.add_builder_button = QToolButton(self.meta_group)
        self.add_builder_button.setObjectName(u"add_builder_button")
        self.add_builder_button.setPopupMode(QToolButton.InstantPopup)
        self.add_builder_button.setToolButtonStyle(Qt.ToolButtonTextOnly)

        self.meta_layout.addWidget(self.add_builder_button)


        self.root_layout.addWidget(self.meta_group, 3, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.root_layout.addItem(self.verticalSpacer, 0, 0, 1, 1)

        GameConnectionWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(GameConnectionWindow)

        QMetaObject.connectSlotsByName(GameConnectionWindow)
    # setupUi

    def retranslateUi(self, GameConnectionWindow):
        GameConnectionWindow.setWindowTitle(QCoreApplication.translate("GameConnectionWindow", u"Game Connections", None))
        self.help_label.setText(QCoreApplication.translate("GameConnectionWindow", u"In order for the Auto Tracker and Multiworld to function, Randovania needs to be configured so it can communicate with the games\n"
"\n"
"\n"
"Press &quot;Add new connection&quot; below and select the appropriate option. For more details, check [Randovania Help](help://tab_multiworld).", None))
        self.meta_group.setTitle("")
        self.add_builder_button.setText(QCoreApplication.translate("GameConnectionWindow", u"Add new connection", None))
    # retranslateUi

