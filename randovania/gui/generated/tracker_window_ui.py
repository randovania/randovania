# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tracker_window.ui'
##
## Created by: tools/uic_wrapper.py
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
from PySide6.QtWidgets import (QApplication, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_TrackerWindow(object):
    def setupUi(self, TrackerWindow):
        if not TrackerWindow.objectName():
            TrackerWindow.setObjectName(u"TrackerWindow")
        TrackerWindow.resize(1200, 600)
        TrackerWindow.setDockNestingEnabled(True)
        self.menu_reset_action = QAction(TrackerWindow)
        self.menu_reset_action.setObjectName(u"menu_reset_action")
        self.centralWidget = QWidget(TrackerWindow)
        self.centralWidget.setObjectName(u"centralWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.centralWidget.sizePolicy().hasHeightForWidth())
        self.centralWidget.setSizePolicy(sizePolicy)
        self.centralWidget.setMinimumSize(QSize(240, 0))
        self.centralWidget.setMaximumSize(QSize(400, 16777215))
        self.central_layout = QVBoxLayout(self.centralWidget)
        self.central_layout.setSpacing(6)
        self.central_layout.setContentsMargins(11, 11, 11, 11)
        self.central_layout.setObjectName(u"central_layout")
        self.central_layout.setContentsMargins(4, 4, 4, 4)
        self.configuration_label = QLabel(self.centralWidget)
        self.configuration_label.setObjectName(u"configuration_label")
        self.configuration_label.setWordWrap(True)

        self.central_layout.addWidget(self.configuration_label)

        self.undo_last_action_button = QPushButton(self.centralWidget)
        self.undo_last_action_button.setObjectName(u"undo_last_action_button")

        self.central_layout.addWidget(self.undo_last_action_button)

        self.actions_title_label = QLabel(self.centralWidget)
        self.actions_title_label.setObjectName(u"actions_title_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.actions_title_label.sizePolicy().hasHeightForWidth())
        self.actions_title_label.setSizePolicy(sizePolicy1)
        self.actions_title_label.setWordWrap(True)

        self.central_layout.addWidget(self.actions_title_label)

        self.actions_list = QListWidget(self.centralWidget)
        self.actions_list.setObjectName(u"actions_list")

        self.central_layout.addWidget(self.actions_list)

        TrackerWindow.setCentralWidget(self.centralWidget)
        self.menu_bar = QMenuBar(TrackerWindow)
        self.menu_bar.setObjectName(u"menu_bar")
        self.menu_bar.setGeometry(QRect(0, 0, 1200, 21))
        self.menu_tracker = QMenu(self.menu_bar)
        self.menu_tracker.setObjectName(u"menu_tracker")
        TrackerWindow.setMenuBar(self.menu_bar)

        self.menu_bar.addAction(self.menu_tracker.menuAction())
        self.menu_tracker.addAction(self.menu_reset_action)

        self.retranslateUi(TrackerWindow)

        QMetaObject.connectSlotsByName(TrackerWindow)
    # setupUi

    def retranslateUi(self, TrackerWindow):
        TrackerWindow.setWindowTitle(QCoreApplication.translate("TrackerWindow", u"Tracker", None))
        self.menu_reset_action.setText(QCoreApplication.translate("TrackerWindow", u"Reset", None))
        self.configuration_label.setText(QCoreApplication.translate("TrackerWindow", u"Trick Level: ???; Elevators: Vanilla; Item Loss: ???", None))
        self.undo_last_action_button.setText(QCoreApplication.translate("TrackerWindow", u"Undo last action", None))
        self.actions_title_label.setText(QCoreApplication.translate("TrackerWindow", u"<html><head/><body><p>History of all actions that have been performed.</p><p>Press &quot;Undo last action&quot; to remove the last action from the list.</p></body></html>", None))
        self.menu_tracker.setTitle(QCoreApplication.translate("TrackerWindow", u"Tracker", None))
    # retranslateUi

