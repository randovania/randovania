# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'auto_tracker_window.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QHBoxLayout,
    QLabel, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QSpacerItem, QWidget)

class Ui_AutoTrackerWindow(object):
    def setupUi(self, AutoTrackerWindow):
        if not AutoTrackerWindow.objectName():
            AutoTrackerWindow.setObjectName(u"AutoTrackerWindow")
        AutoTrackerWindow.resize(243, 210)
        self.actions = QAction(AutoTrackerWindow)
        self.actions.setObjectName(u"actions")
        self.centralwidget = QWidget(AutoTrackerWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.item_tracker_widget = QWidget(self.centralwidget)
        self.item_tracker_widget.setObjectName(u"item_tracker_widget")
        self.inventory_layout = QGridLayout(self.item_tracker_widget)
        self.inventory_layout.setObjectName(u"inventory_layout")

        self.gridLayout.addWidget(self.item_tracker_widget, 0, 0, 1, 1)

        self.connected_game_state_label = QLabel(self.centralwidget)
        self.connected_game_state_label.setObjectName(u"connected_game_state_label")

        self.gridLayout.addWidget(self.connected_game_state_label, 3, 0, 1, 1)

        self.select_game_layout = QHBoxLayout()
        self.select_game_layout.setObjectName(u"select_game_layout")
        self.select_game_combo = QComboBox(self.centralwidget)
        self.select_game_combo.setObjectName(u"select_game_combo")

        self.select_game_layout.addWidget(self.select_game_combo)

        self.select_game_button = QPushButton(self.centralwidget)
        self.select_game_button.setObjectName(u"select_game_button")
        self.select_game_button.setMaximumSize(QSize(120, 16777215))

        self.select_game_layout.addWidget(self.select_game_button)


        self.gridLayout.addLayout(self.select_game_layout, 2, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 1, 0, 1, 1)

        AutoTrackerWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(AutoTrackerWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 243, 17))
        self.menu_options = QMenu(self.menubar)
        self.menu_options.setObjectName(u"menu_options")
        self.menu_tracker = QMenu(self.menu_options)
        self.menu_tracker.setObjectName(u"menu_tracker")
        self.menu_default_game = QMenu(self.menu_options)
        self.menu_default_game.setObjectName(u"menu_default_game")
        AutoTrackerWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menu_options.menuAction())
        self.menu_options.addAction(self.menu_tracker.menuAction())
        self.menu_options.addAction(self.menu_default_game.menuAction())

        self.retranslateUi(AutoTrackerWindow)

        QMetaObject.connectSlotsByName(AutoTrackerWindow)
    # setupUi

    def retranslateUi(self, AutoTrackerWindow):
        AutoTrackerWindow.setWindowTitle(QCoreApplication.translate("AutoTrackerWindow", u"Auto Tracker", None))
        self.actions.setText(QCoreApplication.translate("AutoTrackerWindow", u"s", None))
        self.connected_game_state_label.setText("")
        self.select_game_button.setText(QCoreApplication.translate("AutoTrackerWindow", u"Connections", None))
        self.menu_options.setTitle(QCoreApplication.translate("AutoTrackerWindow", u"Options", None))
        self.menu_tracker.setTitle(QCoreApplication.translate("AutoTrackerWindow", u"Theme", None))
        self.menu_default_game.setTitle(QCoreApplication.translate("AutoTrackerWindow", u"Default Game", None))
    # retranslateUi

