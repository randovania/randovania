# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'async_race_room_window.ui'
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
    QLabel, QMainWindow, QMenuBar, QPushButton,
    QSizePolicy, QStatusBar, QToolButton, QWidget)

from randovania.gui.widgets.background_task_widget import BackgroundTaskWidget

class Ui_AsyncRaceRoomWindow(object):
    def setupUi(self, AsyncRaceRoomWindow):
        if not AsyncRaceRoomWindow.objectName():
            AsyncRaceRoomWindow.setObjectName(u"AsyncRaceRoomWindow")
        AsyncRaceRoomWindow.resize(542, 386)
        self.centralwidget = QWidget(AsyncRaceRoomWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.game_details_group = QGroupBox(self.centralwidget)
        self.game_details_group.setObjectName(u"game_details_group")
        self.game_details_layout = QHBoxLayout(self.game_details_group)
        self.game_details_layout.setObjectName(u"game_details_layout")
        self.game_details_layout.setContentsMargins(4, 4, 4, 4)
        self.game_details_label = QLabel(self.game_details_group)
        self.game_details_label.setObjectName(u"game_details_label")

        self.game_details_layout.addWidget(self.game_details_label)

        self.view_preset_description_button = QPushButton(self.game_details_group)
        self.view_preset_description_button.setObjectName(u"view_preset_description_button")

        self.game_details_layout.addWidget(self.view_preset_description_button)

        self.customize_cosmetic_button = QPushButton(self.game_details_group)
        self.customize_cosmetic_button.setObjectName(u"customize_cosmetic_button")

        self.game_details_layout.addWidget(self.customize_cosmetic_button)


        self.gridLayout.addWidget(self.game_details_group, 3, 0, 1, 2)

        self.participation_group = QGroupBox(self.centralwidget)
        self.participation_group.setObjectName(u"participation_group")
        self.gridLayout_2 = QGridLayout(self.participation_group)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.participation_label = QLabel(self.participation_group)
        self.participation_label.setObjectName(u"participation_label")
        self.participation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.participation_label, 0, 0, 1, 6)

        self.submit_proof_button = QPushButton(self.participation_group)
        self.submit_proof_button.setObjectName(u"submit_proof_button")

        self.gridLayout_2.addWidget(self.submit_proof_button, 1, 5, 1, 1)

        self.join_and_export_button = QPushButton(self.participation_group)
        self.join_and_export_button.setObjectName(u"join_and_export_button")

        self.gridLayout_2.addWidget(self.join_and_export_button, 1, 0, 1, 1)

        self.finish_button = QPushButton(self.participation_group)
        self.finish_button.setObjectName(u"finish_button")

        self.gridLayout_2.addWidget(self.finish_button, 1, 3, 1, 1)

        self.start_button = QPushButton(self.participation_group)
        self.start_button.setObjectName(u"start_button")

        self.gridLayout_2.addWidget(self.start_button, 1, 1, 1, 1)

        self.forfeit_button = QPushButton(self.participation_group)
        self.forfeit_button.setObjectName(u"forfeit_button")

        self.gridLayout_2.addWidget(self.forfeit_button, 1, 4, 1, 1)

        self.pause_button = QPushButton(self.participation_group)
        self.pause_button.setObjectName(u"pause_button")

        self.gridLayout_2.addWidget(self.pause_button, 1, 2, 1, 1)


        self.gridLayout.addWidget(self.participation_group, 4, 0, 1, 2)

        self.name_label = QLabel(self.centralwidget)
        self.name_label.setObjectName(u"name_label")

        self.gridLayout.addWidget(self.name_label, 0, 0, 1, 1)

        self.start_end_date_label = QLabel(self.centralwidget)
        self.start_end_date_label.setObjectName(u"start_end_date_label")

        self.gridLayout.addWidget(self.start_end_date_label, 0, 1, 1, 1)

        self.results_group = QGroupBox(self.centralwidget)
        self.results_group.setObjectName(u"results_group")
        self.results_layout = QHBoxLayout(self.results_group)
        self.results_layout.setObjectName(u"results_layout")
        self.results_layout.setContentsMargins(4, 4, 4, 4)
        self.view_spoiler_button = QPushButton(self.results_group)
        self.view_spoiler_button.setObjectName(u"view_spoiler_button")

        self.results_layout.addWidget(self.view_spoiler_button)

        self.view_leaderboard_button = QPushButton(self.results_group)
        self.view_leaderboard_button.setObjectName(u"view_leaderboard_button")

        self.results_layout.addWidget(self.view_leaderboard_button)


        self.gridLayout.addWidget(self.results_group, 5, 0, 1, 2)

        self.administration_button = QToolButton(self.centralwidget)
        self.administration_button.setObjectName(u"administration_button")
        self.administration_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.administration_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.administration_button.setArrowType(Qt.ArrowType.DownArrow)

        self.gridLayout.addWidget(self.administration_button, 6, 1, 1, 1)

        self.background_task_widget = BackgroundTaskWidget(self.centralwidget)
        self.background_task_widget.setObjectName(u"background_task_widget")

        self.gridLayout.addWidget(self.background_task_widget, 6, 0, 1, 1)

        AsyncRaceRoomWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(AsyncRaceRoomWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 542, 17))
        AsyncRaceRoomWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(AsyncRaceRoomWindow)
        self.statusbar.setObjectName(u"statusbar")
        AsyncRaceRoomWindow.setStatusBar(self.statusbar)

        self.retranslateUi(AsyncRaceRoomWindow)

        QMetaObject.connectSlotsByName(AsyncRaceRoomWindow)
    # setupUi

    def retranslateUi(self, AsyncRaceRoomWindow):
        AsyncRaceRoomWindow.setWindowTitle(QCoreApplication.translate("AsyncRaceRoomWindow", u"Async Race Room", None))
        self.game_details_group.setTitle(QCoreApplication.translate("AsyncRaceRoomWindow", u"Game Details", None))
        self.game_details_label.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"GAME NAME, SEED HASH", None))
        self.view_preset_description_button.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"View preset description", None))
        self.customize_cosmetic_button.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"Customize cosmetic options", None))
        self.participation_group.setTitle(QCoreApplication.translate("AsyncRaceRoomWindow", u"Participation", None))
        self.participation_label.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"TextLabel", None))
        self.submit_proof_button.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"Submit Proof", None))
        self.join_and_export_button.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"Join and export game", None))
        self.finish_button.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"Finish", None))
        self.start_button.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"Start", None))
        self.forfeit_button.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"Forfeit", None))
        self.pause_button.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"Pause", None))
        self.name_label.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"RACE NAME", None))
        self.start_end_date_label.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"Race End: in <> days, at <>", None))
        self.results_group.setTitle(QCoreApplication.translate("AsyncRaceRoomWindow", u"Race Results", None))
        self.view_spoiler_button.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"View spoiler", None))
        self.view_leaderboard_button.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"View leaderboard", None))
        self.administration_button.setText(QCoreApplication.translate("AsyncRaceRoomWindow", u"Room administration", None))
    # retranslateUi

