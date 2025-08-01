# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_hints.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDoubleSpinBox, QFrame,
    QGroupBox, QHBoxLayout, QLabel, QMainWindow,
    QScrollArea, QSizePolicy, QSpacerItem, QSpinBox,
    QVBoxLayout, QWidget)

class Ui_PresetHints(object):
    def setupUi(self, PresetHints):
        if not PresetHints.objectName():
            PresetHints.setObjectName(u"PresetHints")
        PresetHints.resize(595, 580)
        self.centralWidget = QWidget(PresetHints)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.hint_layout = QVBoxLayout(self.centralWidget)
        self.hint_layout.setSpacing(6)
        self.hint_layout.setContentsMargins(11, 11, 11, 11)
        self.hint_layout.setObjectName(u"hint_layout")
        self.hint_layout.setContentsMargins(6, 6, 6, 6)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 567, 604))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_area_contents.sizePolicy().hasHeightForWidth())
        self.scroll_area_contents.setSizePolicy(sizePolicy)
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_contents)
        self.scroll_area_layout.setSpacing(6)
        self.scroll_area_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_area_layout.setObjectName(u"scroll_area_layout")
        self.scroll_area_layout.setContentsMargins(6, 6, 6, 6)
        self.hint_system_description = QLabel(self.scroll_area_contents)
        self.hint_system_description.setObjectName(u"hint_system_description")
        self.hint_system_description.setWordWrap(True)

        self.scroll_area_layout.addWidget(self.hint_system_description)

        self.random_hints_box = QGroupBox(self.scroll_area_contents)
        self.random_hints_box.setObjectName(u"random_hints_box")
        self.verticalLayout_3 = QVBoxLayout(self.random_hints_box)
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.enable_random_hints_check = QCheckBox(self.random_hints_box)
        self.enable_random_hints_check.setObjectName(u"enable_random_hints_check")

        self.verticalLayout_3.addWidget(self.enable_random_hints_check)

        self.enable_random_hints_description = QLabel(self.random_hints_box)
        self.enable_random_hints_description.setObjectName(u"enable_random_hints_description")
        self.enable_random_hints_description.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.enable_random_hints_description)

        self.resolver_hints_line = QFrame(self.random_hints_box)
        self.resolver_hints_line.setObjectName(u"resolver_hints_line")
        self.resolver_hints_line.setFrameShape(QFrame.Shape.HLine)
        self.resolver_hints_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_3.addWidget(self.resolver_hints_line)

        self.resolver_hints_check = QCheckBox(self.random_hints_box)
        self.resolver_hints_check.setObjectName(u"resolver_hints_check")

        self.verticalLayout_3.addWidget(self.resolver_hints_check)

        self.resolver_hints_label = QLabel(self.random_hints_box)
        self.resolver_hints_label.setObjectName(u"resolver_hints_label")
        self.resolver_hints_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.resolver_hints_label)

        self.minimum_available_locations_line = QFrame(self.random_hints_box)
        self.minimum_available_locations_line.setObjectName(u"minimum_available_locations_line")
        self.minimum_available_locations_line.setFrameShape(QFrame.Shape.HLine)
        self.minimum_available_locations_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_3.addWidget(self.minimum_available_locations_line)

        self.minimum_available_locations_widget = QWidget(self.random_hints_box)
        self.minimum_available_locations_widget.setObjectName(u"minimum_available_locations_widget")
        self.horizontalLayout = QHBoxLayout(self.minimum_available_locations_widget)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.minimum_available_locations_label = QLabel(self.minimum_available_locations_widget)
        self.minimum_available_locations_label.setObjectName(u"minimum_available_locations_label")
        self.minimum_available_locations_label.setWordWrap(False)

        self.horizontalLayout.addWidget(self.minimum_available_locations_label)

        self.minimum_available_locations_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.minimum_available_locations_spacer)

        self.minimum_available_locations_spin_box = QSpinBox(self.minimum_available_locations_widget)
        self.minimum_available_locations_spin_box.setObjectName(u"minimum_available_locations_spin_box")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.minimum_available_locations_spin_box.sizePolicy().hasHeightForWidth())
        self.minimum_available_locations_spin_box.setSizePolicy(sizePolicy1)
        self.minimum_available_locations_spin_box.setMinimumSize(QSize(54, 0))

        self.horizontalLayout.addWidget(self.minimum_available_locations_spin_box)


        self.verticalLayout_3.addWidget(self.minimum_available_locations_widget)

        self.minimum_available_locations_description = QLabel(self.random_hints_box)
        self.minimum_available_locations_description.setObjectName(u"minimum_available_locations_description")
        self.minimum_available_locations_description.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.minimum_available_locations_description)

        self.minimum_weight_line = QFrame(self.random_hints_box)
        self.minimum_weight_line.setObjectName(u"minimum_weight_line")
        self.minimum_weight_line.setFrameShape(QFrame.Shape.HLine)
        self.minimum_weight_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_3.addWidget(self.minimum_weight_line)

        self.minimum_weight_widget = QWidget(self.random_hints_box)
        self.minimum_weight_widget.setObjectName(u"minimum_weight_widget")
        self.horizontalLayout_2 = QHBoxLayout(self.minimum_weight_widget)
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.minimum_weight_label = QLabel(self.minimum_weight_widget)
        self.minimum_weight_label.setObjectName(u"minimum_weight_label")

        self.horizontalLayout_2.addWidget(self.minimum_weight_label)

        self.minimum_weight_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.minimum_weight_spacer)

        self.minimum_weight_spin_box = QDoubleSpinBox(self.minimum_weight_widget)
        self.minimum_weight_spin_box.setObjectName(u"minimum_weight_spin_box")
        sizePolicy1.setHeightForWidth(self.minimum_weight_spin_box.sizePolicy().hasHeightForWidth())
        self.minimum_weight_spin_box.setSizePolicy(sizePolicy1)
        self.minimum_weight_spin_box.setMinimumSize(QSize(54, 0))
        self.minimum_weight_spin_box.setDecimals(1)

        self.horizontalLayout_2.addWidget(self.minimum_weight_spin_box)


        self.verticalLayout_3.addWidget(self.minimum_weight_widget)

        self.minimum_weight_description = QLabel(self.random_hints_box)
        self.minimum_weight_description.setObjectName(u"minimum_weight_description")
        self.minimum_weight_description.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.minimum_weight_description)


        self.scroll_area_layout.addWidget(self.random_hints_box)

        self.specific_location_hints_box = QGroupBox(self.scroll_area_contents)
        self.specific_location_hints_box.setObjectName(u"specific_location_hints_box")
        self.verticalLayout_2 = QVBoxLayout(self.specific_location_hints_box)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.enable_specific_location_hints_check = QCheckBox(self.specific_location_hints_box)
        self.enable_specific_location_hints_check.setObjectName(u"enable_specific_location_hints_check")

        self.verticalLayout_2.addWidget(self.enable_specific_location_hints_check)

        self.enable_specific_location_hints_description = QLabel(self.specific_location_hints_box)
        self.enable_specific_location_hints_description.setObjectName(u"enable_specific_location_hints_description")
        self.enable_specific_location_hints_description.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.enable_specific_location_hints_description)


        self.scroll_area_layout.addWidget(self.specific_location_hints_box)

        self.specific_pickup_hints_box = QGroupBox(self.scroll_area_contents)
        self.specific_pickup_hints_box.setObjectName(u"specific_pickup_hints_box")
        self.verticalLayout = QVBoxLayout(self.specific_pickup_hints_box)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")

        self.scroll_area_layout.addWidget(self.specific_pickup_hints_box)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.hint_layout.addWidget(self.scroll_area)

        PresetHints.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetHints)

        QMetaObject.connectSlotsByName(PresetHints)
    # setupUi

    def retranslateUi(self, PresetHints):
        PresetHints.setWindowTitle(QCoreApplication.translate("PresetHints", u"Hints", None))
        self.hint_system_description.setText(QCoreApplication.translate("PresetHints", u"For more information about Randovania's hint system, please refer to the various hint-related tabs on this game's page.", None))
        self.random_hints_box.setTitle(QCoreApplication.translate("PresetHints", u"Random Hints", None))
        self.enable_random_hints_check.setText(QCoreApplication.translate("PresetHints", u"Enable random hints", None))
        self.enable_random_hints_description.setText(QCoreApplication.translate("PresetHints", u"Random hints are hints scattered randomly across hint locations, and can provide you with various pieces of information. If disabled, all random hints will be replaced with jokes.", None))
        self.resolver_hints_check.setText(QCoreApplication.translate("PresetHints", u"[Development] Use resolver-based hints", None))
        self.resolver_hints_label.setText(QCoreApplication.translate("PresetHints", u"Uses data from the resolver to determine hint-placement, rather than data from the generator. Always enabled in individual Door Lock Randomizer. Not compatible with multiworld.", None))
        self.minimum_available_locations_label.setText(QCoreApplication.translate("PresetHints", u"[Development] Minimum available locations for hint placement:", None))
        self.minimum_available_locations_description.setText(QCoreApplication.translate("PresetHints", u"Pickups can only be hinted if there were at least this many available locations at the time they were placed.", None))
        self.minimum_weight_label.setText(QCoreApplication.translate("PresetHints", u"[Development] Minimum location weight for hint placement:", None))
        self.minimum_weight_description.setText(QCoreApplication.translate("PresetHints", u"Pickups can only be hinted if they had this much weight when placed by the generator. Note that resolver-based hints will only ever have a weight of 0.0, so it's not recommended to raise this.", None))
        self.specific_location_hints_box.setTitle(QCoreApplication.translate("PresetHints", u"Specific Location Hints", None))
        self.enable_specific_location_hints_check.setText(QCoreApplication.translate("PresetHints", u"Enable specific location hints", None))
        self.enable_specific_location_hints_description.setText(QCoreApplication.translate("PresetHints", u"Specific location hints are hints that are always in the same hint location, and always provide you with information about the pickup in the specific pickup location associated with that hint. If disabled, all specific location hints will be replaced with jokes.", None))
        self.specific_pickup_hints_box.setTitle(QCoreApplication.translate("PresetHints", u"Specific Pickup Hints", None))
    # retranslateUi

