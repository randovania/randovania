# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'data_editor.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDockWidget,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QMainWindow, QPushButton, QScrollArea,
    QSizePolicy, QSlider, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget)

from randovania.gui.lib.data_editor_canvas import DataEditorCanvas

class Ui_DataEditorWindow(object):
    def setupUi(self, DataEditorWindow):
        if not DataEditorWindow.objectName():
            DataEditorWindow.setObjectName(u"DataEditorWindow")
        DataEditorWindow.resize(950, 471)
        self.unused_central_widget = QWidget(DataEditorWindow)
        self.unused_central_widget.setObjectName(u"unused_central_widget")
        self.unused_central_widget.setMaximumSize(QSize(16777215, 16777215))
        self.unused_central_layout = QGridLayout(self.unused_central_widget)
        self.unused_central_layout.setSpacing(6)
        self.unused_central_layout.setContentsMargins(11, 11, 11, 11)
        self.unused_central_layout.setObjectName(u"unused_central_layout")
        DataEditorWindow.setCentralWidget(self.unused_central_widget)
        self.points_of_interest_dock = QDockWidget(DataEditorWindow)
        self.points_of_interest_dock.setObjectName(u"points_of_interest_dock")
        self.points_of_interest_dock.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.points_of_interest_content = QWidget()
        self.points_of_interest_content.setObjectName(u"points_of_interest_content")
        self.points_of_interest_layout = QVBoxLayout(self.points_of_interest_content)
        self.points_of_interest_layout.setSpacing(6)
        self.points_of_interest_layout.setContentsMargins(11, 11, 11, 11)
        self.points_of_interest_layout.setObjectName(u"points_of_interest_layout")
        self.save_database_button = QPushButton(self.points_of_interest_content)
        self.save_database_button.setObjectName(u"save_database_button")

        self.points_of_interest_layout.addWidget(self.save_database_button)

        self.region_selector_box = QComboBox(self.points_of_interest_content)
        self.region_selector_box.setObjectName(u"region_selector_box")

        self.points_of_interest_layout.addWidget(self.region_selector_box)

        self.area_selector_box = QComboBox(self.points_of_interest_content)
        self.area_selector_box.setObjectName(u"area_selector_box")
        self.area_selector_box.setEnabled(False)

        self.points_of_interest_layout.addWidget(self.area_selector_box)

        self.edit_area_button = QPushButton(self.points_of_interest_content)
        self.edit_area_button.setObjectName(u"edit_area_button")

        self.points_of_interest_layout.addWidget(self.edit_area_button)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.delete_node_button = QPushButton(self.points_of_interest_content)
        self.delete_node_button.setObjectName(u"delete_node_button")

        self.horizontalLayout.addWidget(self.delete_node_button)

        self.new_node_button = QPushButton(self.points_of_interest_content)
        self.new_node_button.setObjectName(u"new_node_button")

        self.horizontalLayout.addWidget(self.new_node_button)


        self.points_of_interest_layout.addLayout(self.horizontalLayout)

        self.nodes_scroll_area = QScrollArea(self.points_of_interest_content)
        self.nodes_scroll_area.setObjectName(u"nodes_scroll_area")
        self.nodes_scroll_area.setWidgetResizable(True)
        self.nodes_scroll_contents = QWidget()
        self.nodes_scroll_contents.setObjectName(u"nodes_scroll_contents")
        self.nodes_scroll_contents.setGeometry(QRect(0, 0, 166, 208))
        self.nodes_scroll_layout = QVBoxLayout(self.nodes_scroll_contents)
        self.nodes_scroll_layout.setSpacing(6)
        self.nodes_scroll_layout.setContentsMargins(11, 11, 11, 11)
        self.nodes_scroll_layout.setObjectName(u"nodes_scroll_layout")
        self.nodes_scroll_layout.setContentsMargins(0, -1, 0, -1)
        self.nodes_scroll_area.setWidget(self.nodes_scroll_contents)

        self.points_of_interest_layout.addWidget(self.nodes_scroll_area)

        self.points_of_interest_dock.setWidget(self.points_of_interest_content)
        DataEditorWindow.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.points_of_interest_dock)
        self.node_info_dock = QDockWidget(DataEditorWindow)
        self.node_info_dock.setObjectName(u"node_info_dock")
        self.node_info_dock.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.node_info_content = QWidget()
        self.node_info_content.setObjectName(u"node_info_content")
        self.verticalLayout = QVBoxLayout(self.node_info_content)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.node_info_group = QGroupBox(self.node_info_content)
        self.node_info_group.setObjectName(u"node_info_group")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.node_info_group.sizePolicy().hasHeightForWidth())
        self.node_info_group.setSizePolicy(sizePolicy)
        self.gridLayout_4 = QGridLayout(self.node_info_group)
        self.gridLayout_4.setSpacing(6)
        self.gridLayout_4.setContentsMargins(11, 11, 11, 11)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.node_edit_button = QPushButton(self.node_info_group)
        self.node_edit_button.setObjectName(u"node_edit_button")
        self.node_edit_button.setMaximumSize(QSize(100, 16777215))

        self.gridLayout_4.addWidget(self.node_edit_button, 0, 2, 1, 1)

        self.node_details_label = QLabel(self.node_info_group)
        self.node_details_label.setObjectName(u"node_details_label")
        self.node_details_label.setWordWrap(True)

        self.gridLayout_4.addWidget(self.node_details_label, 1, 0, 1, 2)

        self.node_name_label = QLabel(self.node_info_group)
        self.node_name_label.setObjectName(u"node_name_label")
        self.node_name_label.setWordWrap(True)

        self.gridLayout_4.addWidget(self.node_name_label, 0, 0, 1, 1)

        self.area_spawn_check = QCheckBox(self.node_info_group)
        self.area_spawn_check.setObjectName(u"area_spawn_check")

        self.gridLayout_4.addWidget(self.area_spawn_check, 1, 2, 1, 1)

        self.node_description_label = QLabel(self.node_info_group)
        self.node_description_label.setObjectName(u"node_description_label")
        self.node_description_label.setTextFormat(Qt.MarkdownText)
        self.node_description_label.setWordWrap(True)
        self.node_description_label.setOpenExternalLinks(True)

        self.gridLayout_4.addWidget(self.node_description_label, 2, 0, 1, 1)

        self.node_heals_check = QCheckBox(self.node_info_group)
        self.node_heals_check.setObjectName(u"node_heals_check")
        self.node_heals_check.setMaximumSize(QSize(100, 16777215))

        self.gridLayout_4.addWidget(self.node_heals_check, 2, 2, 1, 1)


        self.verticalLayout.addWidget(self.node_info_group)

        self.connections_group = QGroupBox(self.node_info_content)
        self.connections_group.setObjectName(u"connections_group")
        self.connections_group.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.connections_group_layout = QGridLayout(self.connections_group)
        self.connections_group_layout.setSpacing(6)
        self.connections_group_layout.setContentsMargins(11, 11, 11, 11)
        self.connections_group_layout.setObjectName(u"connections_group_layout")
        self.other_node_connection_combo = QComboBox(self.connections_group)
        self.other_node_connection_combo.setObjectName(u"other_node_connection_combo")
        self.other_node_connection_combo.setEnabled(False)

        self.connections_group_layout.addWidget(self.other_node_connection_combo, 0, 0, 1, 1)

        self.other_node_connection_edit_button = QPushButton(self.connections_group)
        self.other_node_connection_edit_button.setObjectName(u"other_node_connection_edit_button")

        self.connections_group_layout.addWidget(self.other_node_connection_edit_button, 0, 2, 1, 1)

        self.other_node_alternatives_contents = QTreeWidget(self.connections_group)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.other_node_alternatives_contents.setHeaderItem(__qtreewidgetitem)
        self.other_node_alternatives_contents.setObjectName(u"other_node_alternatives_contents")
        self.other_node_alternatives_contents.header().setVisible(False)

        self.connections_group_layout.addWidget(self.other_node_alternatives_contents, 1, 0, 1, 3)

        self.other_node_connection_swap_button = QPushButton(self.connections_group)
        self.other_node_connection_swap_button.setObjectName(u"other_node_connection_swap_button")

        self.connections_group_layout.addWidget(self.other_node_connection_swap_button, 0, 1, 1, 1)


        self.verticalLayout.addWidget(self.connections_group)

        self.node_info_dock.setWidget(self.node_info_content)
        DataEditorWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.node_info_dock)
        self.area_view_dock = QDockWidget(DataEditorWindow)
        self.area_view_dock.setObjectName(u"area_view_dock")
        self.area_view_dock.setMinimumSize(QSize(350, 71))
        self.area_view_content = QWidget()
        self.area_view_content.setObjectName(u"area_view_content")
        self.verticalLayout_2 = QVBoxLayout(self.area_view_content)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.zoom_group = QHBoxLayout()
        self.zoom_group.setSpacing(6)
        self.zoom_group.setObjectName(u"zoom_group")
        self.zoom_label = QLabel(self.area_view_content)
        self.zoom_label.setObjectName(u"zoom_label")

        self.zoom_group.addWidget(self.zoom_label)

        self.zoom_slider = QSlider(self.area_view_content)
        self.zoom_slider.setObjectName(u"zoom_slider")
        self.zoom_slider.setMinimum(1)
        self.zoom_slider.setMaximum(40)
        self.zoom_slider.setValue(20)
        self.zoom_slider.setOrientation(Qt.Horizontal)

        self.zoom_group.addWidget(self.zoom_slider)


        self.verticalLayout_2.addLayout(self.zoom_group)

        self.area_view_canvas = DataEditorCanvas(self.area_view_content)
        self.area_view_canvas.setObjectName(u"area_view_canvas")

        self.verticalLayout_2.addWidget(self.area_view_canvas)

        self.area_view_dock.setWidget(self.area_view_content)
        DataEditorWindow.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.area_view_dock)

        self.retranslateUi(DataEditorWindow)

        QMetaObject.connectSlotsByName(DataEditorWindow)
    # setupUi

    def retranslateUi(self, DataEditorWindow):
        DataEditorWindow.setWindowTitle(QCoreApplication.translate("DataEditorWindow", u"Data Visualizer", None))
        self.points_of_interest_dock.setWindowTitle(QCoreApplication.translate("DataEditorWindow", u"Nodes", None))
        self.save_database_button.setText(QCoreApplication.translate("DataEditorWindow", u"Save as database", None))
        self.edit_area_button.setText(QCoreApplication.translate("DataEditorWindow", u"Edit Area Details", None))
        self.delete_node_button.setText(QCoreApplication.translate("DataEditorWindow", u"Delete Node", None))
        self.new_node_button.setText(QCoreApplication.translate("DataEditorWindow", u"New Node", None))
        self.node_info_dock.setWindowTitle(QCoreApplication.translate("DataEditorWindow", u"Node Info", None))
        self.node_info_group.setTitle(QCoreApplication.translate("DataEditorWindow", u"Node Info", None))
        self.node_edit_button.setText(QCoreApplication.translate("DataEditorWindow", u"Edit", None))
        self.node_details_label.setText(QCoreApplication.translate("DataEditorWindow", u"TextLabel", None))
        self.node_name_label.setText(QCoreApplication.translate("DataEditorWindow", u"TextLabel", None))
        self.area_spawn_check.setText(QCoreApplication.translate("DataEditorWindow", u"Area spawn", None))
        self.node_description_label.setText(QCoreApplication.translate("DataEditorWindow", u"TextLabel", None))
        self.node_heals_check.setText(QCoreApplication.translate("DataEditorWindow", u"Heals?", None))
        self.connections_group.setTitle(QCoreApplication.translate("DataEditorWindow", u"Connections", None))
        self.other_node_connection_edit_button.setText(QCoreApplication.translate("DataEditorWindow", u"Edit", None))
        self.other_node_connection_swap_button.setText(QCoreApplication.translate("DataEditorWindow", u"Select this", None))
        self.area_view_dock.setWindowTitle(QCoreApplication.translate("DataEditorWindow", u"Area View", None))
        self.zoom_label.setText(QCoreApplication.translate("DataEditorWindow", u"Zoom", None))
    # retranslateUi

