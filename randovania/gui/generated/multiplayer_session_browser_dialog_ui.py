# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'multiplayer_session_browser_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QCheckBox,
    QDialog, QDialogButtonBox, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMenuBar, QSizePolicy, QSpacerItem, QSpinBox,
    QTableView, QVBoxLayout, QWidget)

class Ui_MultiplayerSessionBrowserDialog(object):
    def setupUi(self, MultiplayerSessionBrowserDialog):
        if not MultiplayerSessionBrowserDialog.objectName():
            MultiplayerSessionBrowserDialog.setObjectName(u"MultiplayerSessionBrowserDialog")
        MultiplayerSessionBrowserDialog.resize(780, 455)
        self.verticalLayout = QVBoxLayout(MultiplayerSessionBrowserDialog)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.menu_bar = QMenuBar(MultiplayerSessionBrowserDialog)
        self.menu_bar.setObjectName(u"menu_bar")

        self.verticalLayout.addWidget(self.menu_bar)

        self.table_widget = QTableView(MultiplayerSessionBrowserDialog)
        self.table_widget.setObjectName(u"table_widget")
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_widget.setTabKeyNavigation(False)
        self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.verticalHeader().setDefaultSectionSize(24)

        self.verticalLayout.addWidget(self.table_widget)

        self.filter_group = QGroupBox(MultiplayerSessionBrowserDialog)
        self.filter_group.setObjectName(u"filter_group")
        self.gridLayout = QGridLayout(self.filter_group)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.has_password_no_check = QCheckBox(self.filter_group)
        self.has_password_no_check.setObjectName(u"has_password_no_check")
        self.has_password_no_check.setChecked(True)

        self.gridLayout.addWidget(self.has_password_no_check, 2, 2, 1, 1)

        self.state_visibile_check = QCheckBox(self.filter_group)
        self.state_visibile_check.setObjectName(u"state_visibile_check")
        self.state_visibile_check.setChecked(True)

        self.gridLayout.addWidget(self.state_visibile_check, 3, 1, 1, 1)

        self.filter_age_spin = QSpinBox(self.filter_group)
        self.filter_age_spin.setObjectName(u"filter_age_spin")
        self.filter_age_spin.setMaximum(365)
        self.filter_age_spin.setValue(14)

        self.gridLayout.addWidget(self.filter_age_spin, 4, 2, 1, 2)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 2, 4, 1, 1)

        self.filter_name_edit = QLineEdit(self.filter_group)
        self.filter_name_edit.setObjectName(u"filter_name_edit")

        self.gridLayout.addWidget(self.filter_name_edit, 0, 1, 1, 4)

        self.state_filter_label = QLabel(self.filter_group)
        self.state_filter_label.setObjectName(u"state_filter_label")

        self.gridLayout.addWidget(self.state_filter_label, 3, 0, 1, 1)

        self.filter_age_label = QLabel(self.filter_group)
        self.filter_age_label.setObjectName(u"filter_age_label")

        self.gridLayout.addWidget(self.filter_age_label, 4, 0, 1, 1)

        self.has_password_label = QLabel(self.filter_group)
        self.has_password_label.setObjectName(u"has_password_label")

        self.gridLayout.addWidget(self.has_password_label, 2, 0, 1, 1)

        self.filter_name_label = QLabel(self.filter_group)
        self.filter_name_label.setObjectName(u"filter_name_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.filter_name_label.sizePolicy().hasHeightForWidth())
        self.filter_name_label.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.filter_name_label, 0, 0, 1, 1)

        self.filter_age_check = QCheckBox(self.filter_group)
        self.filter_age_check.setObjectName(u"filter_age_check")
        self.filter_age_check.setChecked(True)

        self.gridLayout.addWidget(self.filter_age_check, 4, 1, 1, 1)

        self.has_password_yes_check = QCheckBox(self.filter_group)
        self.has_password_yes_check.setObjectName(u"has_password_yes_check")
        self.has_password_yes_check.setChecked(True)

        self.gridLayout.addWidget(self.has_password_yes_check, 2, 1, 1, 1)

        self.is_member_label = QLabel(self.filter_group)
        self.is_member_label.setObjectName(u"is_member_label")

        self.gridLayout.addWidget(self.is_member_label, 5, 0, 1, 1)

        self.is_member_yes_check = QCheckBox(self.filter_group)
        self.is_member_yes_check.setObjectName(u"is_member_yes_check")
        self.is_member_yes_check.setChecked(True)

        self.gridLayout.addWidget(self.is_member_yes_check, 5, 1, 1, 1)

        self.is_member_no_check = QCheckBox(self.filter_group)
        self.is_member_no_check.setObjectName(u"is_member_no_check")
        self.is_member_no_check.setChecked(True)

        self.gridLayout.addWidget(self.is_member_no_check, 5, 2, 1, 1)

        self.state_hidden_check = QCheckBox(self.filter_group)
        self.state_hidden_check.setObjectName(u"state_hidden_check")

        self.gridLayout.addWidget(self.state_hidden_check, 3, 2, 1, 1)


        self.verticalLayout.addWidget(self.filter_group)

        self.label_layout = QHBoxLayout()
        self.label_layout.setSpacing(6)
        self.label_layout.setObjectName(u"label_layout")
        self.status_label = QLabel(MultiplayerSessionBrowserDialog)
        self.status_label.setObjectName(u"status_label")
        self.status_label.setWordWrap(True)

        self.label_layout.addWidget(self.status_label)

        self.server_connection_label = QLabel(MultiplayerSessionBrowserDialog)
        self.server_connection_label.setObjectName(u"server_connection_label")
        self.server_connection_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.label_layout.addWidget(self.server_connection_label)


        self.verticalLayout.addLayout(self.label_layout)

        self.button_box = QDialogButtonBox(MultiplayerSessionBrowserDialog)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setMinimumSize(QSize(500, 0))
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.button_box)


        self.retranslateUi(MultiplayerSessionBrowserDialog)

        QMetaObject.connectSlotsByName(MultiplayerSessionBrowserDialog)
    # setupUi

    def retranslateUi(self, MultiplayerSessionBrowserDialog):
        MultiplayerSessionBrowserDialog.setWindowTitle(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"Session Browser", None))
        self.filter_group.setTitle(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"Filters", None))
        self.has_password_no_check.setText(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"No", None))
        self.state_visibile_check.setText(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"Visible", None))
        self.filter_age_spin.setSuffix(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u" days", None))
        self.state_filter_label.setText(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"Visibility:", None))
        self.filter_age_label.setText(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"Age:", None))
        self.has_password_label.setText(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"Has Password?", None))
        self.filter_name_label.setText(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"Name", None))
        self.filter_age_check.setText(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"Limit to", None))
        self.has_password_yes_check.setText(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"Yes", None))
        self.is_member_label.setText(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"Is Member?", None))
        self.is_member_yes_check.setText(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"Yes", None))
        self.is_member_no_check.setText(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"No", None))
        self.state_hidden_check.setText(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"Hidden", None))
        self.status_label.setText("")
        self.server_connection_label.setText(QCoreApplication.translate("MultiplayerSessionBrowserDialog", u"Server: Disconnected", None))
    # retranslateUi

