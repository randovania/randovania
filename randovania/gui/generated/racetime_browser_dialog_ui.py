# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'racetime_browser_dialog.ui'
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
    QMenuBar, QSizePolicy, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

class Ui_RacetimeBrowserDialog(object):
    def setupUi(self, RacetimeBrowserDialog):
        if not RacetimeBrowserDialog.objectName():
            RacetimeBrowserDialog.setObjectName(u"RacetimeBrowserDialog")
        RacetimeBrowserDialog.resize(675, 453)
        self.verticalLayout = QVBoxLayout(RacetimeBrowserDialog)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.menu_bar = QMenuBar(RacetimeBrowserDialog)
        self.menu_bar.setObjectName(u"menu_bar")

        self.verticalLayout.addWidget(self.menu_bar)

        self.table_widget = QTableWidget(RacetimeBrowserDialog)
        if (self.table_widget.columnCount() < 7):
            self.table_widget.setColumnCount(7)
        __qtablewidgetitem = QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.table_widget.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        self.table_widget.setObjectName(u"table_widget")
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_widget.setTabKeyNavigation(False)
        self.table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_widget.setSortingEnabled(True)
        self.table_widget.setColumnCount(7)
        self.table_widget.verticalHeader().setVisible(False)

        self.verticalLayout.addWidget(self.table_widget)

        self.filter_group = QGroupBox(RacetimeBrowserDialog)
        self.filter_group.setObjectName(u"filter_group")
        self.gridLayout = QGridLayout(self.filter_group)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.status_pending_check = QCheckBox(self.filter_group)
        self.status_pending_check.setObjectName(u"status_pending_check")

        self.gridLayout.addWidget(self.status_pending_check, 2, 3, 1, 1)

        self.filter_name_label = QLabel(self.filter_group)
        self.filter_name_label.setObjectName(u"filter_name_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.filter_name_label.sizePolicy().hasHeightForWidth())
        self.filter_name_label.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.filter_name_label, 0, 0, 1, 1)

        self.filter_name_edit = QLineEdit(self.filter_group)
        self.filter_name_edit.setObjectName(u"filter_name_edit")

        self.gridLayout.addWidget(self.filter_name_edit, 0, 1, 1, 7)

        self.filter_status_label = QLabel(self.filter_group)
        self.filter_status_label.setObjectName(u"filter_status_label")

        self.gridLayout.addWidget(self.filter_status_label, 2, 0, 1, 1)

        self.status_open_check = QCheckBox(self.filter_group)
        self.status_open_check.setObjectName(u"status_open_check")
        self.status_open_check.setChecked(True)

        self.gridLayout.addWidget(self.status_open_check, 2, 1, 1, 1)

        self.status_inprogress_check = QCheckBox(self.filter_group)
        self.status_inprogress_check.setObjectName(u"status_inprogress_check")

        self.gridLayout.addWidget(self.status_inprogress_check, 2, 4, 1, 1)

        self.status_finished_check = QCheckBox(self.filter_group)
        self.status_finished_check.setObjectName(u"status_finished_check")

        self.gridLayout.addWidget(self.status_finished_check, 2, 6, 1, 1)

        self.status_cancelled_check = QCheckBox(self.filter_group)
        self.status_cancelled_check.setObjectName(u"status_cancelled_check")

        self.gridLayout.addWidget(self.status_cancelled_check, 2, 7, 1, 1)

        self.status_invitational_check = QCheckBox(self.filter_group)
        self.status_invitational_check.setObjectName(u"status_invitational_check")

        self.gridLayout.addWidget(self.status_invitational_check, 2, 2, 1, 1)

        self.game_filter_label = QLabel(self.filter_group)
        self.game_filter_label.setObjectName(u"game_filter_label")

        self.gridLayout.addWidget(self.game_filter_label, 3, 0, 1, 1)

        self.game_check_layout = QHBoxLayout()
        self.game_check_layout.setSpacing(6)
        self.game_check_layout.setObjectName(u"game_check_layout")

        self.gridLayout.addLayout(self.game_check_layout, 3, 1, 1, 3)


        self.verticalLayout.addWidget(self.filter_group)

        self.label_layout = QHBoxLayout()
        self.label_layout.setSpacing(6)
        self.label_layout.setObjectName(u"label_layout")
        self.status_label = QLabel(RacetimeBrowserDialog)
        self.status_label.setObjectName(u"status_label")
        self.status_label.setWordWrap(True)

        self.label_layout.addWidget(self.status_label)


        self.verticalLayout.addLayout(self.label_layout)

        self.button_box = QDialogButtonBox(RacetimeBrowserDialog)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setMinimumSize(QSize(500, 0))
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.button_box)


        self.retranslateUi(RacetimeBrowserDialog)

        QMetaObject.connectSlotsByName(RacetimeBrowserDialog)
    # setupUi

    def retranslateUi(self, RacetimeBrowserDialog):
        RacetimeBrowserDialog.setWindowTitle(QCoreApplication.translate("RacetimeBrowserDialog", u"Racetime.gg Browser", None))
        ___qtablewidgetitem = self.table_widget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Name", None));
        ___qtablewidgetitem1 = self.table_widget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Status", None));
        ___qtablewidgetitem2 = self.table_widget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Entrants", None));
        ___qtablewidgetitem3 = self.table_widget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Goal", None));
        ___qtablewidgetitem4 = self.table_widget.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Opened At", None));
        ___qtablewidgetitem5 = self.table_widget.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Info", None));
        self.filter_group.setTitle(QCoreApplication.translate("RacetimeBrowserDialog", u"Filters", None))
        self.status_pending_check.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Pending", None))
        self.filter_name_label.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Name", None))
        self.filter_status_label.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Status", None))
        self.status_open_check.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Open", None))
        self.status_inprogress_check.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"In Progress", None))
        self.status_finished_check.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Finished", None))
        self.status_cancelled_check.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Cancelled", None))
        self.status_invitational_check.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Invitational", None))
        self.game_filter_label.setText(QCoreApplication.translate("RacetimeBrowserDialog", u"Game", None))
        self.status_label.setText("")
    # retranslateUi

