# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'debug_connector_window.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QGridLayout, QHeaderView, QLabel, QListView,
    QMainWindow, QMenuBar, QPushButton, QSizePolicy,
    QTableView, QWidget)

class Ui_DebugConnectorWindow(object):
    def setupUi(self, DebugConnectorWindow):
        if not DebugConnectorWindow.objectName():
            DebugConnectorWindow.setObjectName(u"DebugConnectorWindow")
        DebugConnectorWindow.resize(697, 430)
        self.central_widget = QWidget(DebugConnectorWindow)
        self.central_widget.setObjectName(u"central_widget")
        self.central_widget.setMaximumSize(QSize(16777215, 16777215))
        self.central_widget.setLayoutDirection(Qt.LeftToRight)
        self.grid_layout = QGridLayout(self.central_widget)
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(11, 11, 11, 11)
        self.grid_layout.setObjectName(u"grid_layout")
        self.collect_location_button = QPushButton(self.central_widget)
        self.collect_location_button.setObjectName(u"collect_location_button")

        self.grid_layout.addWidget(self.collect_location_button, 1, 1, 1, 1)

        self.reset_button = QPushButton(self.central_widget)
        self.reset_button.setObjectName(u"reset_button")

        self.grid_layout.addWidget(self.reset_button, 4, 3, 1, 1)

        self.collect_randomly_check = QCheckBox(self.central_widget)
        self.collect_randomly_check.setObjectName(u"collect_randomly_check")

        self.grid_layout.addWidget(self.collect_randomly_check, 4, 2, 1, 1)

        self.messages_list = QListView(self.central_widget)
        self.messages_list.setObjectName(u"messages_list")
        self.messages_list.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.grid_layout.addWidget(self.messages_list, 0, 2, 4, 2)

        self.current_region_combo = QComboBox(self.central_widget)
        self.current_region_combo.setObjectName(u"current_region_combo")

        self.grid_layout.addWidget(self.current_region_combo, 4, 1, 1, 1)

        self.collect_location_combo = QComboBox(self.central_widget)
        self.collect_location_combo.setObjectName(u"collect_location_combo")

        self.grid_layout.addWidget(self.collect_location_combo, 0, 0, 1, 2)

        self.current_location_label = QLabel(self.central_widget)
        self.current_location_label.setObjectName(u"current_location_label")

        self.grid_layout.addWidget(self.current_location_label, 4, 0, 1, 1)

        self.inventory_table_view = QTableView(self.central_widget)
        self.inventory_table_view.setObjectName(u"inventory_table_view")
        self.inventory_table_view.setSortingEnabled(True)
        self.inventory_table_view.setCornerButtonEnabled(False)
        self.inventory_table_view.verticalHeader().setVisible(False)

        self.grid_layout.addWidget(self.inventory_table_view, 2, 0, 1, 2)

        DebugConnectorWindow.setCentralWidget(self.central_widget)
        self.menuBar = QMenuBar(DebugConnectorWindow)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 697, 17))
        DebugConnectorWindow.setMenuBar(self.menuBar)

        self.retranslateUi(DebugConnectorWindow)

        QMetaObject.connectSlotsByName(DebugConnectorWindow)
    # setupUi

    def retranslateUi(self, DebugConnectorWindow):
        DebugConnectorWindow.setWindowTitle(QCoreApplication.translate("DebugConnectorWindow", u"Debug Backend", None))
        self.collect_location_button.setText(QCoreApplication.translate("DebugConnectorWindow", u"Collect Location", None))
        self.reset_button.setText(QCoreApplication.translate("DebugConnectorWindow", u"Finish", None))
        self.collect_randomly_check.setText(QCoreApplication.translate("DebugConnectorWindow", u"Collect locations randomly periodically", None))
        self.current_location_label.setText(QCoreApplication.translate("DebugConnectorWindow", u"Current Location", None))
    # retranslateUi

