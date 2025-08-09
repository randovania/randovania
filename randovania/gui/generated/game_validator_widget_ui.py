# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'game_validator_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QTreeWidget, QTreeWidgetItem,
    QWidget)

class Ui_GameValidatorWidget(object):
    def setupUi(self, GameValidatorWidget):
        if not GameValidatorWidget.objectName():
            GameValidatorWidget.setObjectName(u"GameValidatorWidget")
        GameValidatorWidget.resize(758, 558)
        self.root_layout = QGridLayout(GameValidatorWidget)
        self.root_layout.setSpacing(6)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.start_button = QPushButton(GameValidatorWidget)
        self.start_button.setObjectName(u"start_button")
        self.start_button.setMinimumSize(QSize(120, 0))

        self.root_layout.addWidget(self.start_button, 3, 4, 1, 1)

        self.status_label = QLabel(GameValidatorWidget)
        self.status_label.setObjectName(u"status_label")
        self.status_label.setWordWrap(True)

        self.root_layout.addWidget(self.status_label, 3, 3, 1, 1)

        self.log_widget = QTreeWidget(GameValidatorWidget)
        QTreeWidgetItem(self.log_widget)
        QTreeWidgetItem(self.log_widget)
        self.log_widget.setObjectName(u"log_widget")
        self.log_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.log_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.log_widget.setTextElideMode(Qt.ElideNone)
        self.log_widget.setColumnCount(1)
        self.log_widget.header().setDefaultSectionSize(50)
        self.log_widget.header().setStretchLastSection(True)

        self.root_layout.addWidget(self.log_widget, 2, 0, 1, 6)

        self.options_layout = QGridLayout()
        self.options_layout.setSpacing(6)
        self.options_layout.setObjectName(u"options_layout")
        self.verbosity_label = QLabel(GameValidatorWidget)
        self.verbosity_label.setObjectName(u"verbosity_label")

        self.options_layout.addWidget(self.verbosity_label, 0, 0, 1, 1)

        self.verbosity_combo = QComboBox(GameValidatorWidget)
        self.verbosity_combo.addItem("")
        self.verbosity_combo.addItem("")
        self.verbosity_combo.addItem("")
        self.verbosity_combo.addItem("")
        self.verbosity_combo.setObjectName(u"verbosity_combo")

        self.options_layout.addWidget(self.verbosity_combo, 0, 1, 1, 1)

        self.filter_actions_layout = QHBoxLayout()
        self.filter_actions_layout.setSpacing(6)
        self.filter_actions_layout.setObjectName(u"filter_actions_layout")
        self.show_pickups_check = QCheckBox(GameValidatorWidget)
        self.show_pickups_check.setObjectName(u"show_pickups_check")
        self.show_pickups_check.setChecked(True)

        self.filter_actions_layout.addWidget(self.show_pickups_check)

        self.show_minors_check = QCheckBox(GameValidatorWidget)
        self.show_minors_check.setObjectName(u"show_minors_check")

        self.filter_actions_layout.addWidget(self.show_minors_check)

        self.show_events_check = QCheckBox(GameValidatorWidget)
        self.show_events_check.setObjectName(u"show_events_check")
        self.show_events_check.setChecked(True)

        self.filter_actions_layout.addWidget(self.show_events_check)

        self.show_hints_check = QCheckBox(GameValidatorWidget)
        self.show_hints_check.setObjectName(u"show_hints_check")

        self.filter_actions_layout.addWidget(self.show_hints_check)

        self.show_locks_check = QCheckBox(GameValidatorWidget)
        self.show_locks_check.setObjectName(u"show_locks_check")

        self.filter_actions_layout.addWidget(self.show_locks_check)


        self.options_layout.addLayout(self.filter_actions_layout, 1, 0, 1, 2)


        self.root_layout.addLayout(self.options_layout, 3, 0, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.root_layout.addItem(self.horizontalSpacer, 3, 2, 1, 1)

        self.needs_refresh_label = QLabel(GameValidatorWidget)
        self.needs_refresh_label.setObjectName(u"needs_refresh_label")
        self.needs_refresh_label.setStyleSheet(u"color: red;")
        self.needs_refresh_label.setWordWrap(True)
        self.needs_refresh_label.setMargin(0)

        self.root_layout.addWidget(self.needs_refresh_label, 3, 1, 1, 1)


        self.retranslateUi(GameValidatorWidget)

        self.verbosity_combo.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(GameValidatorWidget)
    # setupUi

    def retranslateUi(self, GameValidatorWidget):
        GameValidatorWidget.setWindowTitle(QCoreApplication.translate("GameValidatorWidget", u"Game Validator", None))
        self.start_button.setText(QCoreApplication.translate("GameValidatorWidget", u"Start", None))
        self.status_label.setText(QCoreApplication.translate("GameValidatorWidget", u"Not started", None))
        ___qtreewidgetitem = self.log_widget.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("GameValidatorWidget", u"Playthrough", None));

        __sortingEnabled = self.log_widget.isSortingEnabled()
        self.log_widget.setSortingEnabled(False)
        ___qtreewidgetitem1 = self.log_widget.topLevelItem(0)
        ___qtreewidgetitem1.setText(0, QCoreApplication.translate("GameValidatorWidget", u"To view the playthrough, it's necessary to run the solver.", None));
        ___qtreewidgetitem2 = self.log_widget.topLevelItem(1)
        ___qtreewidgetitem2.setText(0, QCoreApplication.translate("GameValidatorWidget", u"Press the Start button at the bottom-right and wait for it to finish.", None));
        self.log_widget.setSortingEnabled(__sortingEnabled)

        self.verbosity_label.setText(QCoreApplication.translate("GameValidatorWidget", u"<html><head/><body><p>Verbosity</p></body></html>", None))
        self.verbosity_combo.setItemText(0, QCoreApplication.translate("GameValidatorWidget", u"Silent", None))
        self.verbosity_combo.setItemText(1, QCoreApplication.translate("GameValidatorWidget", u"Normal", None))
        self.verbosity_combo.setItemText(2, QCoreApplication.translate("GameValidatorWidget", u"High", None))
        self.verbosity_combo.setItemText(3, QCoreApplication.translate("GameValidatorWidget", u"Extreme", None))

        self.show_pickups_check.setText(QCoreApplication.translate("GameValidatorWidget", u"Majors", None))
        self.show_minors_check.setText(QCoreApplication.translate("GameValidatorWidget", u"Minors", None))
        self.show_events_check.setText(QCoreApplication.translate("GameValidatorWidget", u"Events", None))
        self.show_hints_check.setText(QCoreApplication.translate("GameValidatorWidget", u"Hints", None))
        self.show_locks_check.setText(QCoreApplication.translate("GameValidatorWidget", u"Door Locks", None))
        self.needs_refresh_label.setText("")
    # retranslateUi

