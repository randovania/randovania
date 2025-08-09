# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'node_details_popup.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QGridLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QTabWidget, QTextEdit, QVBoxLayout,
    QWidget)

from randovania.gui.lib.editable_list_view import EditableListView
from randovania.gui.lib.hint_feature_list_view import HintFeatureListView

class Ui_NodeDetailsPopup(object):
    def setupUi(self, NodeDetailsPopup):
        if not NodeDetailsPopup.objectName():
            NodeDetailsPopup.setObjectName(u"NodeDetailsPopup")
        NodeDetailsPopup.resize(556, 1004)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(NodeDetailsPopup.sizePolicy().hasHeightForWidth())
        NodeDetailsPopup.setSizePolicy(sizePolicy)
        NodeDetailsPopup.setMaximumSize(QSize(16777215, 16777215))
        self.main_layout = QVBoxLayout(NodeDetailsPopup)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(11, 11, 11, 11)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.name_layout = QHBoxLayout()
        self.name_layout.setSpacing(6)
        self.name_layout.setObjectName(u"name_layout")
        self.name_label = QLabel(NodeDetailsPopup)
        self.name_label.setObjectName(u"name_label")
        sizePolicy.setHeightForWidth(self.name_label.sizePolicy().hasHeightForWidth())
        self.name_label.setSizePolicy(sizePolicy)

        self.name_layout.addWidget(self.name_label)

        self.name_edit = QLineEdit(NodeDetailsPopup)
        self.name_edit.setObjectName(u"name_edit")

        self.name_layout.addWidget(self.name_edit)


        self.main_layout.addLayout(self.name_layout)

        self.heals_check = QCheckBox(NodeDetailsPopup)
        self.heals_check.setObjectName(u"heals_check")

        self.main_layout.addWidget(self.heals_check)

        self.location_group = QGroupBox(NodeDetailsPopup)
        self.location_group.setObjectName(u"location_group")
        self.location_group.setCheckable(True)
        self.location_group.setChecked(True)
        self.location_layout = QHBoxLayout(self.location_group)
        self.location_layout.setSpacing(6)
        self.location_layout.setContentsMargins(11, 11, 11, 11)
        self.location_layout.setObjectName(u"location_layout")
        self.location_layout.setContentsMargins(4, 6, 4, 2)
        self.location_x_label = QLabel(self.location_group)
        self.location_x_label.setObjectName(u"location_x_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.location_x_label.sizePolicy().hasHeightForWidth())
        self.location_x_label.setSizePolicy(sizePolicy1)
        self.location_x_label.setMinimumSize(QSize(20, 0))

        self.location_layout.addWidget(self.location_x_label)

        self.location_x_spin = QDoubleSpinBox(self.location_group)
        self.location_x_spin.setObjectName(u"location_x_spin")
        self.location_x_spin.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.location_x_spin.setMinimum(-99999.990000000005239)
        self.location_x_spin.setMaximum(99999.990000000005239)

        self.location_layout.addWidget(self.location_x_spin)

        self.location_y_label = QLabel(self.location_group)
        self.location_y_label.setObjectName(u"location_y_label")
        sizePolicy1.setHeightForWidth(self.location_y_label.sizePolicy().hasHeightForWidth())
        self.location_y_label.setSizePolicy(sizePolicy1)
        self.location_y_label.setMinimumSize(QSize(20, 0))

        self.location_layout.addWidget(self.location_y_label)

        self.location_y_spin = QDoubleSpinBox(self.location_group)
        self.location_y_spin.setObjectName(u"location_y_spin")
        self.location_y_spin.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.location_y_spin.setMinimum(-99999.990000000005239)
        self.location_y_spin.setMaximum(99999.990000000005239)

        self.location_layout.addWidget(self.location_y_spin)

        self.location_z_label = QLabel(self.location_group)
        self.location_z_label.setObjectName(u"location_z_label")
        sizePolicy1.setHeightForWidth(self.location_z_label.sizePolicy().hasHeightForWidth())
        self.location_z_label.setSizePolicy(sizePolicy1)
        self.location_z_label.setMinimumSize(QSize(20, 0))

        self.location_layout.addWidget(self.location_z_label)

        self.location_z_spin = QDoubleSpinBox(self.location_group)
        self.location_z_spin.setObjectName(u"location_z_spin")
        self.location_z_spin.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.location_z_spin.setMinimum(-99999.990000000005239)
        self.location_z_spin.setMaximum(99999.990000000005239)

        self.location_layout.addWidget(self.location_z_spin)


        self.main_layout.addWidget(self.location_group)

        self.description_label = QLabel(NodeDetailsPopup)
        self.description_label.setObjectName(u"description_label")

        self.main_layout.addWidget(self.description_label)

        self.description_edit = QTextEdit(NodeDetailsPopup)
        self.description_edit.setObjectName(u"description_edit")
        self.description_edit.setMaximumSize(QSize(16777215, 100))

        self.main_layout.addWidget(self.description_edit)

        self.layers_layout = QHBoxLayout()
        self.layers_layout.setSpacing(6)
        self.layers_layout.setObjectName(u"layers_layout")
        self.layers_label = QLabel(NodeDetailsPopup)
        self.layers_label.setObjectName(u"layers_label")

        self.layers_layout.addWidget(self.layers_label)

        self.layers_combo = QComboBox(NodeDetailsPopup)
        self.layers_combo.setObjectName(u"layers_combo")

        self.layers_layout.addWidget(self.layers_combo)


        self.main_layout.addLayout(self.layers_layout)

        self.extra_label = QLabel(NodeDetailsPopup)
        self.extra_label.setObjectName(u"extra_label")

        self.main_layout.addWidget(self.extra_label)

        self.extra_edit = QPlainTextEdit(NodeDetailsPopup)
        self.extra_edit.setObjectName(u"extra_edit")
        self.extra_edit.setMaximumSize(QSize(16777215, 100))

        self.main_layout.addWidget(self.extra_edit)

        self.node_type_combo = QComboBox(NodeDetailsPopup)
        self.node_type_combo.setObjectName(u"node_type_combo")

        self.main_layout.addWidget(self.node_type_combo)

        self.tab_widget = QTabWidget(NodeDetailsPopup)
        self.tab_widget.setObjectName(u"tab_widget")
        self.tab_generic = QWidget()
        self.tab_generic.setObjectName(u"tab_generic")
        self.generic_layout = QHBoxLayout(self.tab_generic)
        self.generic_layout.setSpacing(6)
        self.generic_layout.setContentsMargins(11, 11, 11, 11)
        self.generic_layout.setObjectName(u"generic_layout")
        self.label = QLabel(self.tab_generic)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.generic_layout.addWidget(self.label)

        self.tab_widget.addTab(self.tab_generic, "")
        self.tab_dock = QWidget()
        self.tab_dock.setObjectName(u"tab_dock")
        self.dock_layout = QGridLayout(self.tab_dock)
        self.dock_layout.setSpacing(6)
        self.dock_layout.setContentsMargins(11, 11, 11, 11)
        self.dock_layout.setObjectName(u"dock_layout")
        self.dock_layout.setContentsMargins(2, 2, 2, 2)
        self.dock_incompatible_box = EditableListView(self.tab_dock)
        self.dock_incompatible_box.setObjectName(u"dock_incompatible_box")

        self.dock_layout.addWidget(self.dock_incompatible_box, 5, 0, 4, 1)

        self.ui_name_box = QHBoxLayout()
        self.ui_name_box.setSpacing(6)
        self.ui_name_box.setObjectName(u"ui_name_box")
        self.ui_name_label = QLabel(self.tab_dock)
        self.ui_name_label.setObjectName(u"ui_name_label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.ui_name_label.sizePolicy().hasHeightForWidth())
        self.ui_name_label.setSizePolicy(sizePolicy2)

        self.ui_name_box.addWidget(self.ui_name_label)

        self.ui_name_edit = QLineEdit(self.tab_dock)
        self.ui_name_edit.setObjectName(u"ui_name_edit")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.ui_name_edit.sizePolicy().hasHeightForWidth())
        self.ui_name_edit.setSizePolicy(sizePolicy3)

        self.ui_name_box.addWidget(self.ui_name_edit)


        self.dock_layout.addLayout(self.ui_name_box, 3, 0, 1, 2)

        self.groupBox = QGroupBox(self.tab_dock)
        self.groupBox.setObjectName(u"groupBox")
        self.horizontalLayout = QHBoxLayout(self.groupBox)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, 4, 2, 2)
        self.dock_type_combo = QComboBox(self.groupBox)
        self.dock_type_combo.addItem("")
        self.dock_type_combo.addItem("")
        self.dock_type_combo.addItem("")
        self.dock_type_combo.addItem("")
        self.dock_type_combo.setObjectName(u"dock_type_combo")

        self.horizontalLayout.addWidget(self.dock_type_combo)

        self.dock_weakness_combo = QComboBox(self.groupBox)
        self.dock_weakness_combo.setObjectName(u"dock_weakness_combo")

        self.horizontalLayout.addWidget(self.dock_weakness_combo)


        self.dock_layout.addWidget(self.groupBox, 1, 0, 1, 2)

        self.dock_update_name_button = QPushButton(self.tab_dock)
        self.dock_update_name_button.setObjectName(u"dock_update_name_button")

        self.dock_layout.addWidget(self.dock_update_name_button, 5, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.dock_layout.addItem(self.verticalSpacer, 8, 1, 1, 1)

        self.dock_connection_group = QGroupBox(self.tab_dock)
        self.dock_connection_group.setObjectName(u"dock_connection_group")
        self.dock_connection_layout = QHBoxLayout(self.dock_connection_group)
        self.dock_connection_layout.setSpacing(6)
        self.dock_connection_layout.setContentsMargins(11, 11, 11, 11)
        self.dock_connection_layout.setObjectName(u"dock_connection_layout")
        self.dock_connection_layout.setContentsMargins(2, 4, 2, 2)
        self.dock_connection_region_combo = QComboBox(self.dock_connection_group)
        self.dock_connection_region_combo.setObjectName(u"dock_connection_region_combo")

        self.dock_connection_layout.addWidget(self.dock_connection_region_combo)

        self.dock_connection_area_combo = QComboBox(self.dock_connection_group)
        self.dock_connection_area_combo.setObjectName(u"dock_connection_area_combo")

        self.dock_connection_layout.addWidget(self.dock_connection_area_combo)

        self.dock_connection_node_combo = QComboBox(self.dock_connection_group)
        self.dock_connection_node_combo.setObjectName(u"dock_connection_node_combo")

        self.dock_connection_layout.addWidget(self.dock_connection_node_combo)


        self.dock_layout.addWidget(self.dock_connection_group, 0, 0, 1, 2)

        self.dock_exclude_lock_rando_check = QCheckBox(self.tab_dock)
        self.dock_exclude_lock_rando_check.setObjectName(u"dock_exclude_lock_rando_check")

        self.dock_layout.addWidget(self.dock_exclude_lock_rando_check, 6, 1, 1, 1)

        self.tab_widget.addTab(self.tab_dock, "")
        self.tab_pickup = QWidget()
        self.tab_pickup.setObjectName(u"tab_pickup")
        self.pickup_layout = QGridLayout(self.tab_pickup)
        self.pickup_layout.setSpacing(6)
        self.pickup_layout.setContentsMargins(11, 11, 11, 11)
        self.pickup_layout.setObjectName(u"pickup_layout")
        self.pickup_layout.setContentsMargins(2, 2, 2, 2)
        self.pickup_index_spin = QSpinBox(self.tab_pickup)
        self.pickup_index_spin.setObjectName(u"pickup_index_spin")
        self.pickup_index_spin.setMaximum(999)

        self.pickup_layout.addWidget(self.pickup_index_spin, 0, 1, 1, 1)

        self.location_category_label = QLabel(self.tab_pickup)
        self.location_category_label.setObjectName(u"location_category_label")

        self.pickup_layout.addWidget(self.location_category_label, 1, 0, 1, 1)

        self.pickup_index_label = QLabel(self.tab_pickup)
        self.pickup_index_label.setObjectName(u"pickup_index_label")

        self.pickup_layout.addWidget(self.pickup_index_label, 0, 0, 1, 1)

        self.pickup_index_button = QPushButton(self.tab_pickup)
        self.pickup_index_button.setObjectName(u"pickup_index_button")

        self.pickup_layout.addWidget(self.pickup_index_button, 0, 2, 1, 1)

        self.location_category_combo = QComboBox(self.tab_pickup)
        self.location_category_combo.setObjectName(u"location_category_combo")

        self.pickup_layout.addWidget(self.location_category_combo, 1, 1, 1, 2)

        self.hint_feature_box = HintFeatureListView(self.tab_pickup)
        self.hint_feature_box.setObjectName(u"hint_feature_box")

        self.pickup_layout.addWidget(self.hint_feature_box, 2, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.pickup_layout.addItem(self.verticalSpacer_2, 2, 1, 1, 1)

        self.tab_widget.addTab(self.tab_pickup, "")
        self.tab_teleporter = QWidget()
        self.tab_teleporter.setObjectName(u"tab_teleporter")
        self.teleporter_layout = QGridLayout(self.tab_teleporter)
        self.teleporter_layout.setSpacing(6)
        self.teleporter_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporter_layout.setObjectName(u"teleporter_layout")
        self.teleporter_layout.setContentsMargins(2, 2, 2, 2)
        self.teleporter_vanilla_name_edit = QCheckBox(self.tab_teleporter)
        self.teleporter_vanilla_name_edit.setObjectName(u"teleporter_vanilla_name_edit")

        self.teleporter_layout.addWidget(self.teleporter_vanilla_name_edit, 1, 1, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.teleporter_layout.addItem(self.verticalSpacer_3, 2, 0, 1, 1)

        self.teleporter_editable_check = QCheckBox(self.tab_teleporter)
        self.teleporter_editable_check.setObjectName(u"teleporter_editable_check")

        self.teleporter_layout.addWidget(self.teleporter_editable_check, 1, 0, 1, 1)

        self.teleporter_destination_group = QGroupBox(self.tab_teleporter)
        self.teleporter_destination_group.setObjectName(u"teleporter_destination_group")
        sizePolicy.setHeightForWidth(self.teleporter_destination_group.sizePolicy().hasHeightForWidth())
        self.teleporter_destination_group.setSizePolicy(sizePolicy)
        self.teleporter_destination_layout = QHBoxLayout(self.teleporter_destination_group)
        self.teleporter_destination_layout.setSpacing(6)
        self.teleporter_destination_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporter_destination_layout.setObjectName(u"teleporter_destination_layout")
        self.teleporter_destination_layout.setContentsMargins(2, 2, 2, 2)
        self.teleporter_destination_region_combo = QComboBox(self.teleporter_destination_group)
        self.teleporter_destination_region_combo.setObjectName(u"teleporter_destination_region_combo")

        self.teleporter_destination_layout.addWidget(self.teleporter_destination_region_combo)

        self.teleporter_destination_area_combo = QComboBox(self.teleporter_destination_group)
        self.teleporter_destination_area_combo.setObjectName(u"teleporter_destination_area_combo")

        self.teleporter_destination_layout.addWidget(self.teleporter_destination_area_combo)


        self.teleporter_layout.addWidget(self.teleporter_destination_group, 0, 0, 1, 2)

        self.tab_widget.addTab(self.tab_teleporter, "")
        self.tab_event = QWidget()
        self.tab_event.setObjectName(u"tab_event")
        self.event_layout = QGridLayout(self.tab_event)
        self.event_layout.setSpacing(6)
        self.event_layout.setContentsMargins(11, 11, 11, 11)
        self.event_layout.setObjectName(u"event_layout")
        self.event_layout.setContentsMargins(2, 2, 2, 2)
        self.event_resource_label = QLabel(self.tab_event)
        self.event_resource_label.setObjectName(u"event_resource_label")

        self.event_layout.addWidget(self.event_resource_label, 0, 0, 1, 1)

        self.event_resource_combo = QComboBox(self.tab_event)
        self.event_resource_combo.setObjectName(u"event_resource_combo")

        self.event_layout.addWidget(self.event_resource_combo, 0, 1, 1, 1)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.event_layout.addItem(self.verticalSpacer_4, 1, 0, 1, 1)

        self.tab_widget.addTab(self.tab_event, "")
        self.tab_configurable = QWidget()
        self.tab_configurable.setObjectName(u"tab_configurable")
        self.translator_gate_layout = QGridLayout(self.tab_configurable)
        self.translator_gate_layout.setSpacing(6)
        self.translator_gate_layout.setContentsMargins(11, 11, 11, 11)
        self.translator_gate_layout.setObjectName(u"translator_gate_layout")
        self.translator_gate_layout.setContentsMargins(2, 2, 2, 2)
        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.translator_gate_layout.addItem(self.verticalSpacer_5, 0, 0, 1, 1)

        self.tab_widget.addTab(self.tab_configurable, "")
        self.tab_hint = QWidget()
        self.tab_hint.setObjectName(u"tab_hint")
        self.hint_layout = QGridLayout(self.tab_hint)
        self.hint_layout.setSpacing(6)
        self.hint_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_layout.setObjectName(u"hint_layout")
        self.hint_requirement_to_collect_button = QPushButton(self.tab_hint)
        self.hint_requirement_to_collect_button.setObjectName(u"hint_requirement_to_collect_button")

        self.hint_layout.addWidget(self.hint_requirement_to_collect_button, 1, 0, 1, 2)

        self.hint_requirement_to_collect_group = QGroupBox(self.tab_hint)
        self.hint_requirement_to_collect_group.setObjectName(u"hint_requirement_to_collect_group")
        self.hint_requirement_to_collect_layout = QGridLayout(self.hint_requirement_to_collect_group)
        self.hint_requirement_to_collect_layout.setSpacing(2)
        self.hint_requirement_to_collect_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_requirement_to_collect_layout.setObjectName(u"hint_requirement_to_collect_layout")
        self.hint_requirement_to_collect_layout.setContentsMargins(2, 2, 2, 2)

        self.hint_layout.addWidget(self.hint_requirement_to_collect_group, 2, 0, 1, 2)

        self.hint_kind_label = QLabel(self.tab_hint)
        self.hint_kind_label.setObjectName(u"hint_kind_label")

        self.hint_layout.addWidget(self.hint_kind_label, 0, 0, 1, 1)

        self.hint_kind_combo = QComboBox(self.tab_hint)
        self.hint_kind_combo.setObjectName(u"hint_kind_combo")

        self.hint_layout.addWidget(self.hint_kind_combo, 0, 1, 1, 1)

        self.tab_widget.addTab(self.tab_hint, "")
        self.tab_teleporter_network = QWidget()
        self.tab_teleporter_network.setObjectName(u"tab_teleporter_network")
        self.teleporter_network_layout = QGridLayout(self.tab_teleporter_network)
        self.teleporter_network_layout.setSpacing(6)
        self.teleporter_network_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporter_network_layout.setObjectName(u"teleporter_network_layout")
        self.teleporter_network_layout.setContentsMargins(2, 2, 2, 2)
        self.teleporter_network_unlocked_button = QPushButton(self.tab_teleporter_network)
        self.teleporter_network_unlocked_button.setObjectName(u"teleporter_network_unlocked_button")

        self.teleporter_network_layout.addWidget(self.teleporter_network_unlocked_button, 3, 0, 1, 2)

        self.teleporter_network_edit = QLineEdit(self.tab_teleporter_network)
        self.teleporter_network_edit.setObjectName(u"teleporter_network_edit")

        self.teleporter_network_layout.addWidget(self.teleporter_network_edit, 0, 1, 1, 1)

        self.teleporter_network_unlocked_group = QGroupBox(self.tab_teleporter_network)
        self.teleporter_network_unlocked_group.setObjectName(u"teleporter_network_unlocked_group")
        self.teleporter_network_unlocked_layout = QGridLayout(self.teleporter_network_unlocked_group)
        self.teleporter_network_unlocked_layout.setSpacing(2)
        self.teleporter_network_unlocked_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporter_network_unlocked_layout.setObjectName(u"teleporter_network_unlocked_layout")
        self.teleporter_network_unlocked_layout.setContentsMargins(2, 2, 2, 2)

        self.teleporter_network_layout.addWidget(self.teleporter_network_unlocked_group, 4, 0, 1, 2)

        self.teleporter_network_label = QLabel(self.tab_teleporter_network)
        self.teleporter_network_label.setObjectName(u"teleporter_network_label")

        self.teleporter_network_layout.addWidget(self.teleporter_network_label, 0, 0, 1, 1)

        self.teleporter_network_activate_group = QGroupBox(self.tab_teleporter_network)
        self.teleporter_network_activate_group.setObjectName(u"teleporter_network_activate_group")
        self.teleporter_network_activate_layout = QGridLayout(self.teleporter_network_activate_group)
        self.teleporter_network_activate_layout.setSpacing(2)
        self.teleporter_network_activate_layout.setContentsMargins(11, 11, 11, 11)
        self.teleporter_network_activate_layout.setObjectName(u"teleporter_network_activate_layout")
        self.teleporter_network_activate_layout.setContentsMargins(2, 2, 2, 2)

        self.teleporter_network_layout.addWidget(self.teleporter_network_activate_group, 6, 0, 1, 2)

        self.teleporter_network_activate_button = QPushButton(self.tab_teleporter_network)
        self.teleporter_network_activate_button.setObjectName(u"teleporter_network_activate_button")

        self.teleporter_network_layout.addWidget(self.teleporter_network_activate_button, 5, 0, 1, 2)

        self.tab_widget.addTab(self.tab_teleporter_network, "")

        self.main_layout.addWidget(self.tab_widget)

        self.verticalSpacer_7 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.main_layout.addItem(self.verticalSpacer_7)

        self.button_box = QDialogButtonBox(NodeDetailsPopup)
        self.button_box.setObjectName(u"button_box")
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)

        self.main_layout.addWidget(self.button_box)


        self.retranslateUi(NodeDetailsPopup)

        self.tab_widget.setCurrentIndex(2)


        QMetaObject.connectSlotsByName(NodeDetailsPopup)
    # setupUi

    def retranslateUi(self, NodeDetailsPopup):
        NodeDetailsPopup.setWindowTitle(QCoreApplication.translate("NodeDetailsPopup", u"Node Configuration", None))
        self.name_label.setText(QCoreApplication.translate("NodeDetailsPopup", u"Name:", None))
        self.heals_check.setText(QCoreApplication.translate("NodeDetailsPopup", u"Heals", None))
        self.location_group.setTitle(QCoreApplication.translate("NodeDetailsPopup", u"Location", None))
        self.location_x_label.setText(QCoreApplication.translate("NodeDetailsPopup", u"X", None))
        self.location_y_label.setText(QCoreApplication.translate("NodeDetailsPopup", u"Y", None))
        self.location_z_label.setText(QCoreApplication.translate("NodeDetailsPopup", u"Z", None))
        self.description_label.setText(QCoreApplication.translate("NodeDetailsPopup", u"Description:", None))
        self.description_edit.setPlaceholderText(QCoreApplication.translate("NodeDetailsPopup", u"Node description", None))
        self.layers_label.setText(QCoreApplication.translate("NodeDetailsPopup", u"Layers:", None))
        self.extra_label.setText(QCoreApplication.translate("NodeDetailsPopup", u"Extra:", None))
        self.label.setText(QCoreApplication.translate("NodeDetailsPopup", u"Nothing!", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_generic), QCoreApplication.translate("NodeDetailsPopup", u"Generic", None))
        self.dock_incompatible_box.setTitle(QCoreApplication.translate("NodeDetailsPopup", u"Incompatible Weaknesses for Dock Lock rando", None))
        self.ui_name_label.setText(QCoreApplication.translate("NodeDetailsPopup", u"Custom name", None))
        self.groupBox.setTitle(QCoreApplication.translate("NodeDetailsPopup", u"Dock Type and Weakness", None))
        self.dock_type_combo.setItemText(0, QCoreApplication.translate("NodeDetailsPopup", u"Door", None))
        self.dock_type_combo.setItemText(1, QCoreApplication.translate("NodeDetailsPopup", u"Morph Ball Door", None))
        self.dock_type_combo.setItemText(2, QCoreApplication.translate("NodeDetailsPopup", u"Other", None))
        self.dock_type_combo.setItemText(3, QCoreApplication.translate("NodeDetailsPopup", u"Portal", None))

        self.dock_update_name_button.setText(QCoreApplication.translate("NodeDetailsPopup", u"Update node name", None))
        self.dock_connection_group.setTitle(QCoreApplication.translate("NodeDetailsPopup", u"Dock Connection", None))
        self.dock_exclude_lock_rando_check.setText(QCoreApplication.translate("NodeDetailsPopup", u"Exclude from Dock Lock rando", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_dock), QCoreApplication.translate("NodeDetailsPopup", u"Dock", None))
        self.location_category_label.setText(QCoreApplication.translate("NodeDetailsPopup", u"Location Category:", None))
        self.pickup_index_label.setText(QCoreApplication.translate("NodeDetailsPopup", u"Pickup Index:", None))
        self.pickup_index_button.setText(QCoreApplication.translate("NodeDetailsPopup", u"Find free index", None))
        self.hint_feature_box.setTitle(QCoreApplication.translate("NodeDetailsPopup", u"Hint Features", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_pickup), QCoreApplication.translate("NodeDetailsPopup", u"Pickup", None))
        self.teleporter_vanilla_name_edit.setText(QCoreApplication.translate("NodeDetailsPopup", u"Keep name when vanilla?", None))
        self.teleporter_editable_check.setText(QCoreApplication.translate("NodeDetailsPopup", u"Randomizable?", None))
        self.teleporter_destination_group.setTitle(QCoreApplication.translate("NodeDetailsPopup", u"Region/Area Selection", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_teleporter), QCoreApplication.translate("NodeDetailsPopup", u"Teleporter", None))
        self.event_resource_label.setText(QCoreApplication.translate("NodeDetailsPopup", u"Event:", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_event), QCoreApplication.translate("NodeDetailsPopup", u"Event", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_configurable), QCoreApplication.translate("NodeDetailsPopup", u"Configurable", None))
        self.hint_requirement_to_collect_button.setText(QCoreApplication.translate("NodeDetailsPopup", u"Edit requirement to collect", None))
        self.hint_requirement_to_collect_group.setTitle("")
        self.hint_kind_label.setText(QCoreApplication.translate("NodeDetailsPopup", u"Kind", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_hint), QCoreApplication.translate("NodeDetailsPopup", u"Hint", None))
        self.teleporter_network_unlocked_button.setText(QCoreApplication.translate("NodeDetailsPopup", u"Edit unlocked by", None))
        self.teleporter_network_unlocked_group.setTitle("")
        self.teleporter_network_label.setText(QCoreApplication.translate("NodeDetailsPopup", u"Network name", None))
        self.teleporter_network_activate_group.setTitle("")
        self.teleporter_network_activate_button.setText(QCoreApplication.translate("NodeDetailsPopup", u"Edit requirement to activate", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_teleporter_network), QCoreApplication.translate("NodeDetailsPopup", u"Teleporter Network", None))
    # retranslateUi

