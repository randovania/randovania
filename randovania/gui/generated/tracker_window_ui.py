# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tracker_window.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QMenu, QMenuBar, QPushButton, QScrollArea,
    QSizePolicy, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget)

from randovania.gui.lib.data_editor_canvas import DataEditorCanvas

class Ui_TrackerWindow(object):
    def setupUi(self, TrackerWindow):
        if not TrackerWindow.objectName():
            TrackerWindow.setObjectName(u"TrackerWindow")
        TrackerWindow.resize(1040, 495)
        self.actionAction = QAction(TrackerWindow)
        self.actionAction.setObjectName(u"actionAction")
        self.menu_reset_action = QAction(TrackerWindow)
        self.menu_reset_action.setObjectName(u"menu_reset_action")
        self.centralWidget = QWidget(TrackerWindow)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.gridLayout = QGridLayout(self.centralWidget)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.configuration_label = QLabel(self.centralWidget)
        self.configuration_label.setObjectName(u"configuration_label")
        self.configuration_label.setWordWrap(True)

        self.gridLayout.addWidget(self.configuration_label, 0, 0, 1, 3)

        self.tab_widget = QTabWidget(self.centralWidget)
        self.tab_widget.setObjectName(u"tab_widget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab_widget.sizePolicy().hasHeightForWidth())
        self.tab_widget.setSizePolicy(sizePolicy)
        self.tab_inventory = QWidget()
        self.tab_inventory.setObjectName(u"tab_inventory")
        self.tab_inventory_layout = QVBoxLayout(self.tab_inventory)
        self.tab_inventory_layout.setSpacing(0)
        self.tab_inventory_layout.setContentsMargins(11, 11, 11, 11)
        self.tab_inventory_layout.setObjectName(u"tab_inventory_layout")
        self.tab_inventory_layout.setContentsMargins(0, 0, 0, 0)
        self.pickups_scroll_area = QScrollArea(self.tab_inventory)
        self.pickups_scroll_area.setObjectName(u"pickups_scroll_area")
        sizePolicy.setHeightForWidth(self.pickups_scroll_area.sizePolicy().hasHeightForWidth())
        self.pickups_scroll_area.setSizePolicy(sizePolicy)
        self.pickups_scroll_area.setMinimumSize(QSize(285, 0))
        self.pickups_scroll_area.setFrameShape(QFrame.NoFrame)
        self.pickups_scroll_area.setFrameShadow(QFrame.Plain)
        self.pickups_scroll_area.setLineWidth(0)
        self.pickups_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.pickups_scroll_area.setWidgetResizable(True)
        self.pickups_scroll_contents = QWidget()
        self.pickups_scroll_contents.setObjectName(u"pickups_scroll_contents")
        self.pickups_scroll_contents.setGeometry(QRect(0, 0, 333, 402))
        self.pickup_box_layout = QVBoxLayout(self.pickups_scroll_contents)
        self.pickup_box_layout.setSpacing(0)
        self.pickup_box_layout.setContentsMargins(11, 11, 11, 11)
        self.pickup_box_layout.setObjectName(u"pickup_box_layout")
        self.pickup_box_layout.setContentsMargins(0, 0, 0, 0)
        self.upgrades_box = QGroupBox(self.pickups_scroll_contents)
        self.upgrades_box.setObjectName(u"upgrades_box")
        self.upgrades_layout = QGridLayout(self.upgrades_box)
        self.upgrades_layout.setSpacing(6)
        self.upgrades_layout.setContentsMargins(11, 11, 11, 11)
        self.upgrades_layout.setObjectName(u"upgrades_layout")

        self.pickup_box_layout.addWidget(self.upgrades_box)

        self.translators_box = QGroupBox(self.pickups_scroll_contents)
        self.translators_box.setObjectName(u"translators_box")
        self.translators_layout = QGridLayout(self.translators_box)
        self.translators_layout.setSpacing(6)
        self.translators_layout.setContentsMargins(11, 11, 11, 11)
        self.translators_layout.setObjectName(u"translators_layout")

        self.pickup_box_layout.addWidget(self.translators_box)

        self.expansions_box = QGroupBox(self.pickups_scroll_contents)
        self.expansions_box.setObjectName(u"expansions_box")
        self.expansions_layout = QGridLayout(self.expansions_box)
        self.expansions_layout.setSpacing(6)
        self.expansions_layout.setContentsMargins(11, 11, 11, 11)
        self.expansions_layout.setObjectName(u"expansions_layout")

        self.pickup_box_layout.addWidget(self.expansions_box)

        self.keys_box = QGroupBox(self.pickups_scroll_contents)
        self.keys_box.setObjectName(u"keys_box")
        self.keys_layout = QGridLayout(self.keys_box)
        self.keys_layout.setSpacing(6)
        self.keys_layout.setContentsMargins(11, 11, 11, 11)
        self.keys_layout.setObjectName(u"keys_layout")

        self.pickup_box_layout.addWidget(self.keys_box)

        self.events_box = QGroupBox(self.pickups_scroll_contents)
        self.events_box.setObjectName(u"events_box")
        self.events_layout = QVBoxLayout(self.events_box)
        self.events_layout.setSpacing(6)
        self.events_layout.setContentsMargins(11, 11, 11, 11)
        self.events_layout.setObjectName(u"events_layout")

        self.pickup_box_layout.addWidget(self.events_box)

        self.pickups_scroll_area.setWidget(self.pickups_scroll_contents)

        self.tab_inventory_layout.addWidget(self.pickups_scroll_area)

        self.tab_widget.addTab(self.tab_inventory, "")
        self.tab_elevators = QWidget()
        self.tab_elevators.setObjectName(u"tab_elevators")
        self.tab_elevators_layout = QVBoxLayout(self.tab_elevators)
        self.tab_elevators_layout.setSpacing(6)
        self.tab_elevators_layout.setContentsMargins(11, 11, 11, 11)
        self.tab_elevators_layout.setObjectName(u"tab_elevators_layout")
        self.tab_elevators_layout.setContentsMargins(0, 0, 0, 0)
        self.elevators_scroll_area = QScrollArea(self.tab_elevators)
        self.elevators_scroll_area.setObjectName(u"elevators_scroll_area")
        sizePolicy.setHeightForWidth(self.elevators_scroll_area.sizePolicy().hasHeightForWidth())
        self.elevators_scroll_area.setSizePolicy(sizePolicy)
        self.elevators_scroll_area.setMinimumSize(QSize(285, 0))
        self.elevators_scroll_area.setFrameShape(QFrame.NoFrame)
        self.elevators_scroll_area.setFrameShadow(QFrame.Plain)
        self.elevators_scroll_area.setWidgetResizable(True)
        self.teleporters_scroll_contents = QWidget()
        self.teleporters_scroll_contents.setObjectName(u"teleporters_scroll_contents")
        self.teleporters_scroll_contents.setGeometry(QRect(0, 0, 333, 402))
        self.teleporters_scroll_layout = QVBoxLayout(self.teleporters_scroll_contents)
        self.teleporters_scroll_layout.setSpacing(6)
        self.teleporters_scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporters_scroll_layout.setObjectName(u"teleporters_scroll_layout")
        self.teleporters_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.elevators_scroll_area.setWidget(self.teleporters_scroll_contents)

        self.tab_elevators_layout.addWidget(self.elevators_scroll_area)

        self.tab_widget.addTab(self.tab_elevators, "")
        self.tab_translator_gate = QWidget()
        self.tab_translator_gate.setObjectName(u"tab_translator_gate")
        self.tab_translator_gate_layout = QVBoxLayout(self.tab_translator_gate)
        self.tab_translator_gate_layout.setSpacing(6)
        self.tab_translator_gate_layout.setContentsMargins(11, 11, 11, 11)
        self.tab_translator_gate_layout.setObjectName(u"tab_translator_gate_layout")
        self.tab_translator_gate_layout.setContentsMargins(0, 0, 0, 0)
        self.translator_gate_scroll_area = QScrollArea(self.tab_translator_gate)
        self.translator_gate_scroll_area.setObjectName(u"translator_gate_scroll_area")
        sizePolicy.setHeightForWidth(self.translator_gate_scroll_area.sizePolicy().hasHeightForWidth())
        self.translator_gate_scroll_area.setSizePolicy(sizePolicy)
        self.translator_gate_scroll_area.setWidgetResizable(True)
        self.translator_gate_scroll_contents = QWidget()
        self.translator_gate_scroll_contents.setObjectName(u"translator_gate_scroll_contents")
        self.translator_gate_scroll_contents.setGeometry(QRect(0, 0, 331, 400))
        self.translator_gate_scroll_layout = QGridLayout(self.translator_gate_scroll_contents)
        self.translator_gate_scroll_layout.setSpacing(6)
        self.translator_gate_scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.translator_gate_scroll_layout.setObjectName(u"translator_gate_scroll_layout")
        self.translator_gate_scroll_layout.setContentsMargins(3, 3, 3, 3)
        self.translator_gate_scroll_area.setWidget(self.translator_gate_scroll_contents)

        self.tab_translator_gate_layout.addWidget(self.translator_gate_scroll_area)

        self.tab_widget.addTab(self.tab_translator_gate, "")

        self.gridLayout.addWidget(self.tab_widget, 2, 0, 1, 1)

        self.map_tab_widget = QTabWidget(self.centralWidget)
        self.map_tab_widget.setObjectName(u"map_tab_widget")
        self.tab_text_map = QWidget()
        self.tab_text_map.setObjectName(u"tab_text_map")
        self.tab_text_map_layout = QVBoxLayout(self.tab_text_map)
        self.tab_text_map_layout.setSpacing(6)
        self.tab_text_map_layout.setContentsMargins(11, 11, 11, 11)
        self.tab_text_map_layout.setObjectName(u"tab_text_map_layout")
        self.tab_text_map_layout.setContentsMargins(4, 4, 4, 4)
        self.resource_filter_check = QCheckBox(self.tab_text_map)
        self.resource_filter_check.setObjectName(u"resource_filter_check")
        self.resource_filter_check.setChecked(True)

        self.tab_text_map_layout.addWidget(self.resource_filter_check)

        self.hide_collected_resources_check = QCheckBox(self.tab_text_map)
        self.hide_collected_resources_check.setObjectName(u"hide_collected_resources_check")

        self.tab_text_map_layout.addWidget(self.hide_collected_resources_check)

        self.current_location_label = QLabel(self.tab_text_map)
        self.current_location_label.setObjectName(u"current_location_label")
        self.current_location_label.setWordWrap(True)

        self.tab_text_map_layout.addWidget(self.current_location_label)

        self.possible_locations_tree = QTreeWidget(self.tab_text_map)
        self.possible_locations_tree.setObjectName(u"possible_locations_tree")
        sizePolicy.setHeightForWidth(self.possible_locations_tree.sizePolicy().hasHeightForWidth())
        self.possible_locations_tree.setSizePolicy(sizePolicy)
        self.possible_locations_tree.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.tab_text_map_layout.addWidget(self.possible_locations_tree)

        self.map_tab_widget.addTab(self.tab_text_map, "")
        self.tab_map = QWidget()
        self.tab_map.setObjectName(u"tab_map")
        self.tab_map_layout = QVBoxLayout(self.tab_map)
        self.tab_map_layout.setSpacing(6)
        self.tab_map_layout.setContentsMargins(11, 11, 11, 11)
        self.tab_map_layout.setObjectName(u"tab_map_layout")
        self.tab_map_layout.setContentsMargins(2, 2, 2, 2)
        self.map_area_layout = QHBoxLayout()
        self.map_area_layout.setSpacing(6)
        self.map_area_layout.setObjectName(u"map_area_layout")
        self.map_region_combo = QComboBox(self.tab_map)
        self.map_region_combo.setObjectName(u"map_region_combo")

        self.map_area_layout.addWidget(self.map_region_combo)

        self.map_area_combo = QComboBox(self.tab_map)
        self.map_area_combo.setObjectName(u"map_area_combo")

        self.map_area_layout.addWidget(self.map_area_combo)


        self.tab_map_layout.addLayout(self.map_area_layout)

        self.map_canvas = DataEditorCanvas(self.tab_map)
        self.map_canvas.setObjectName(u"map_canvas")

        self.tab_map_layout.addWidget(self.map_canvas)

        self.map_tab_widget.addTab(self.tab_map, "")
        self.tab_graph_map = QWidget()
        self.tab_graph_map.setObjectName(u"tab_graph_map")
        self.tab_graph_map_layout = QVBoxLayout(self.tab_graph_map)
        self.tab_graph_map_layout.setSpacing(6)
        self.tab_graph_map_layout.setContentsMargins(11, 11, 11, 11)
        self.tab_graph_map_layout.setObjectName(u"tab_graph_map_layout")
        self.tab_graph_map_layout.setContentsMargins(0, 0, 0, 0)
        self.graph_map_region_combo = QComboBox(self.tab_graph_map)
        self.graph_map_region_combo.setObjectName(u"graph_map_region_combo")

        self.tab_graph_map_layout.addWidget(self.graph_map_region_combo)

        self.map_tab_widget.addTab(self.tab_graph_map, "")
        self.tab_actions = QWidget()
        self.tab_actions.setObjectName(u"tab_actions")
        self.tab_actions_layout = QVBoxLayout(self.tab_actions)
        self.tab_actions_layout.setSpacing(6)
        self.tab_actions_layout.setContentsMargins(11, 11, 11, 11)
        self.tab_actions_layout.setObjectName(u"tab_actions_layout")
        self.tab_actions_layout.setContentsMargins(4, 4, 4, 4)
        self.undo_last_action_button = QPushButton(self.tab_actions)
        self.undo_last_action_button.setObjectName(u"undo_last_action_button")

        self.tab_actions_layout.addWidget(self.undo_last_action_button)

        self.actions_title_label = QLabel(self.tab_actions)
        self.actions_title_label.setObjectName(u"actions_title_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.actions_title_label.sizePolicy().hasHeightForWidth())
        self.actions_title_label.setSizePolicy(sizePolicy1)
        self.actions_title_label.setWordWrap(True)

        self.tab_actions_layout.addWidget(self.actions_title_label)

        self.actions_list = QListWidget(self.tab_actions)
        self.actions_list.setObjectName(u"actions_list")

        self.tab_actions_layout.addWidget(self.actions_list)

        self.map_tab_widget.addTab(self.tab_actions, "")

        self.gridLayout.addWidget(self.map_tab_widget, 2, 1, 1, 2)

        TrackerWindow.setCentralWidget(self.centralWidget)
        self.menu_bar = QMenuBar(TrackerWindow)
        self.menu_bar.setObjectName(u"menu_bar")
        self.menu_bar.setGeometry(QRect(0, 0, 1040, 22))
        self.menu_tracker = QMenu(self.menu_bar)
        self.menu_tracker.setObjectName(u"menu_tracker")
        TrackerWindow.setMenuBar(self.menu_bar)

        self.menu_bar.addAction(self.menu_tracker.menuAction())
        self.menu_tracker.addAction(self.menu_reset_action)

        self.retranslateUi(TrackerWindow)

        self.tab_widget.setCurrentIndex(0)
        self.map_tab_widget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(TrackerWindow)
    # setupUi

    def retranslateUi(self, TrackerWindow):
        TrackerWindow.setWindowTitle(QCoreApplication.translate("TrackerWindow", u"Tracker", None))
        self.actionAction.setText(QCoreApplication.translate("TrackerWindow", u"Action", None))
        self.menu_reset_action.setText(QCoreApplication.translate("TrackerWindow", u"Reset", None))
        self.configuration_label.setText(QCoreApplication.translate("TrackerWindow", u"Trick Level: ???; Elevators: Vanilla; Item Loss: ???", None))
        self.upgrades_box.setTitle(QCoreApplication.translate("TrackerWindow", u"Upgrades", None))
        self.translators_box.setTitle(QCoreApplication.translate("TrackerWindow", u"Translators", None))
        self.expansions_box.setTitle(QCoreApplication.translate("TrackerWindow", u"Expansions", None))
        self.keys_box.setTitle(QCoreApplication.translate("TrackerWindow", u"Keys", None))
        self.events_box.setTitle(QCoreApplication.translate("TrackerWindow", u"Events", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_inventory), QCoreApplication.translate("TrackerWindow", u"Inventory", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_elevators), QCoreApplication.translate("TrackerWindow", u"Elevators", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_translator_gate), QCoreApplication.translate("TrackerWindow", u"Translator Gate", None))
        self.resource_filter_check.setText(QCoreApplication.translate("TrackerWindow", u"Show only resources", None))
        self.hide_collected_resources_check.setText(QCoreApplication.translate("TrackerWindow", u"Hide collected resources", None))
        self.current_location_label.setText(QCoreApplication.translate("TrackerWindow", u"Current location:", None))
        ___qtreewidgetitem = self.possible_locations_tree.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("TrackerWindow", u"Accessible Locations", None));
        self.map_tab_widget.setTabText(self.map_tab_widget.indexOf(self.tab_text_map), QCoreApplication.translate("TrackerWindow", u"Text Map", None))
        self.map_tab_widget.setTabText(self.map_tab_widget.indexOf(self.tab_map), QCoreApplication.translate("TrackerWindow", u"Map", None))
        self.map_tab_widget.setTabText(self.map_tab_widget.indexOf(self.tab_graph_map), QCoreApplication.translate("TrackerWindow", u"Graph Map", None))
        self.undo_last_action_button.setText(QCoreApplication.translate("TrackerWindow", u"Undo last action", None))
        self.actions_title_label.setText(QCoreApplication.translate("TrackerWindow", u"<html><head/><body><p>History of all actions that have been performed.</p><p>Press &quot;Undo last action&quot; to remove the last action from the list.</p></body></html>", None))
        self.map_tab_widget.setTabText(self.map_tab_widget.indexOf(self.tab_actions), QCoreApplication.translate("TrackerWindow", u"Actions", None))
        self.menu_tracker.setTitle(QCoreApplication.translate("TrackerWindow", u"Tracker", None))
    # retranslateUi

