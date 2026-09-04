# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'async_race_settings.ui'
##
## Created by: tools/uic_wrapper.py
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
    QGridLayout, QLabel, QLineEdit, QSizePolicy,
    QWidget)

class Ui_AsyncRaceRoomSettingsWidget(object):
    def setupUi(self, AsyncRaceRoomSettingsWidget):
        if not AsyncRaceRoomSettingsWidget.objectName():
            AsyncRaceRoomSettingsWidget.setObjectName(u"AsyncRaceRoomSettingsWidget")
        AsyncRaceRoomSettingsWidget.resize(362, 276)
        self.root_layout = QGridLayout(AsyncRaceRoomSettingsWidget)
        self.root_layout.setSpacing(6)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.team_timer_label = QLabel(AsyncRaceRoomSettingsWidget)
        self.team_timer_label.setObjectName(u"team_timer_label")

        self.root_layout.addWidget(self.team_timer_label, 7, 0, 1, 1)

        self.team_timer_combo_box = QComboBox(AsyncRaceRoomSettingsWidget)
        self.team_timer_combo_box.addItem("")
        self.team_timer_combo_box.addItem("")
        self.team_timer_combo_box.setObjectName(u"team_timer_combo_box")

        self.root_layout.addWidget(self.team_timer_combo_box, 7, 1, 1, 1)

        self.allow_coop_check = QCheckBox(AsyncRaceRoomSettingsWidget)
        self.allow_coop_check.setObjectName(u"allow_coop_check")

        self.root_layout.addWidget(self.allow_coop_check, 9, 0, 1, 1)

        self.start_time_edit = QDateTimeEdit(AsyncRaceRoomSettingsWidget)
        self.start_time_edit.setObjectName(u"start_time_edit")
        self.start_time_edit.setCalendarPopup(True)

        self.root_layout.addWidget(self.start_time_edit, 2, 1, 1, 1)

        self.password_edit = QLineEdit(AsyncRaceRoomSettingsWidget)
        self.password_edit.setObjectName(u"password_edit")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.root_layout.addWidget(self.password_edit, 1, 1, 1, 1)

        self.visibility_label = QLabel(AsyncRaceRoomSettingsWidget)
        self.visibility_label.setObjectName(u"visibility_label")

        self.root_layout.addWidget(self.visibility_label, 6, 0, 1, 1)

        self.password_check = QCheckBox(AsyncRaceRoomSettingsWidget)
        self.password_check.setObjectName(u"password_check")

        self.root_layout.addWidget(self.password_check, 1, 0, 1, 1)

        self.end_time_edit = QDateTimeEdit(AsyncRaceRoomSettingsWidget)
        self.end_time_edit.setObjectName(u"end_time_edit")
        self.end_time_edit.setCalendarPopup(True)

        self.root_layout.addWidget(self.end_time_edit, 3, 1, 1, 1)

        self.name_edit = QLineEdit(AsyncRaceRoomSettingsWidget)
        self.name_edit.setObjectName(u"name_edit")

        self.root_layout.addWidget(self.name_edit, 0, 1, 1, 1)

        self.end_time_label = QLabel(AsyncRaceRoomSettingsWidget)
        self.end_time_label.setObjectName(u"end_time_label")

        self.root_layout.addWidget(self.end_time_label, 3, 0, 1, 1)

        self.visibility_combo_box = QComboBox(AsyncRaceRoomSettingsWidget)
        self.visibility_combo_box.addItem("")
        self.visibility_combo_box.addItem("")
        self.visibility_combo_box.setObjectName(u"visibility_combo_box")

        self.root_layout.addWidget(self.visibility_combo_box, 6, 1, 1, 1)

        self.name_label = QLabel(AsyncRaceRoomSettingsWidget)
        self.name_label.setObjectName(u"name_label")

        self.root_layout.addWidget(self.name_label, 0, 0, 1, 1)

        self.allow_abandon_worlds_check = QCheckBox(AsyncRaceRoomSettingsWidget)
        self.allow_abandon_worlds_check.setObjectName(u"allow_abandon_worlds_check")

        self.root_layout.addWidget(self.allow_abandon_worlds_check, 11, 0, 1, 2)

        self.start_time_label = QLabel(AsyncRaceRoomSettingsWidget)
        self.start_time_label.setObjectName(u"start_time_label")

        self.root_layout.addWidget(self.start_time_label, 2, 0, 1, 1)

        self.allow_pause_check = QCheckBox(AsyncRaceRoomSettingsWidget)
        self.allow_pause_check.setObjectName(u"allow_pause_check")

        self.root_layout.addWidget(self.allow_pause_check, 8, 0, 1, 1)


        self.retranslateUi(AsyncRaceRoomSettingsWidget)

        QMetaObject.connectSlotsByName(AsyncRaceRoomSettingsWidget)
    # setupUi

    def retranslateUi(self, AsyncRaceRoomSettingsWidget):
        AsyncRaceRoomSettingsWidget.setWindowTitle(QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Async Race Room Settings", None))
        self.team_timer_label.setText(QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Team Timer", None))
        self.team_timer_combo_box.setItemText(0, QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Shared by the whole team", None))
        self.team_timer_combo_box.setItemText(1, QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Accumulated across all members", None))

#if QT_CONFIG(tooltip)
        self.team_timer_combo_box.setToolTip(QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"How a team is timed. Either the whole team shares one timer, or every member is timed separately and their times are added up. The captain starts the race for the team either way.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.allow_coop_check.setToolTip(QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Lets several members of a team play the same world together. Teams can then have more members than the race has worlds.", None))
#endif // QT_CONFIG(tooltip)
        self.allow_coop_check.setText(QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Allow co-op", None))
        self.visibility_label.setText(QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Visibility", None))
        self.password_check.setText(QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Password", None))
        self.end_time_label.setText(QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"End Time", None))
        self.visibility_combo_box.setItemText(0, QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Visible", None))
        self.visibility_combo_box.setItemText(1, QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Hidden", None))

        self.name_label.setText(QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Name", None))
#if QT_CONFIG(tooltip)
        self.allow_abandon_worlds_check.setToolTip(QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Lets a team hand a world over to the abandoned world bot, so the rest can keep playing if someone drops out.", None))
#endif // QT_CONFIG(tooltip)
        self.allow_abandon_worlds_check.setText(QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Allow abandoning worlds (bot)", None))
        self.start_time_label.setText(QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Start Time", None))
        self.allow_pause_check.setText(QCoreApplication.translate("AsyncRaceRoomSettingsWidget", u"Allow pausing", None))
    # retranslateUi

