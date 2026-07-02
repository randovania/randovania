# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_prime_hunters_gameplay.ui'
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QCheckBox, QGridLayout,
    QGroupBox, QLabel, QMainWindow, QScrollArea,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_PresetHuntersGameplay(object):
    def setupUi(self, PresetHuntersGameplay):
        if not PresetHuntersGameplay.objectName():
            PresetHuntersGameplay.setObjectName(u"PresetHuntersGameplay")
        PresetHuntersGameplay.resize(514, 434)
        self.centralWidget = QWidget(PresetHuntersGameplay)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.main_layout = QVBoxLayout(self.centralWidget)
        self.main_layout.setSpacing(6)
        self.main_layout.setContentsMargins(11, 11, 11, 11)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(6, 6, 6, 6)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 500, 420))
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
        self.energy_box = QGroupBox(self.scroll_area_contents)
        self.energy_box.setObjectName(u"energy_box")
        self.gridLayout = QGridLayout(self.energy_box)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.energy_capacity_label = QLabel(self.energy_box)
        self.energy_capacity_label.setObjectName(u"energy_capacity_label")

        self.gridLayout.addWidget(self.energy_capacity_label, 3, 0, 1, 1)

        self.energy_capacity_spin_box = QSpinBox(self.energy_box)
        self.energy_capacity_spin_box.setObjectName(u"energy_capacity_spin_box")
        self.energy_capacity_spin_box.setEnabled(True)
        self.energy_capacity_spin_box.setWrapping(False)
        self.energy_capacity_spin_box.setFrame(True)
        self.energy_capacity_spin_box.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        self.energy_capacity_spin_box.setMinimum(1)
        self.energy_capacity_spin_box.setMaximum(1099)
        self.energy_capacity_spin_box.setSingleStep(1)
        self.energy_capacity_spin_box.setValue(99)
        self.energy_capacity_spin_box.setDisplayIntegerBase(10)

        self.gridLayout.addWidget(self.energy_capacity_spin_box, 3, 1, 1, 1)

        self.energy_capacity_description = QLabel(self.energy_box)
        self.energy_capacity_description.setObjectName(u"energy_capacity_description")
        self.energy_capacity_description.setWordWrap(True)

        self.gridLayout.addWidget(self.energy_capacity_description, 0, 0, 1, 1)


        self.scroll_area_layout.addWidget(self.energy_box)

        self.optional_box = QGroupBox(self.scroll_area_contents)
        self.optional_box.setObjectName(u"optional_box")
        self.verticalLayout = QVBoxLayout(self.optional_box)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.skip_planet_intros_check = QCheckBox(self.optional_box)
        self.skip_planet_intros_check.setObjectName(u"skip_planet_intros_check")

        self.verticalLayout.addWidget(self.skip_planet_intros_check)

        self.skip_planet_intros_label = QLabel(self.optional_box)
        self.skip_planet_intros_label.setObjectName(u"skip_planet_intros_label")

        self.verticalLayout.addWidget(self.skip_planet_intros_label)


        self.scroll_area_layout.addWidget(self.optional_box)

        self.spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.spacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.main_layout.addWidget(self.scroll_area)

        PresetHuntersGameplay.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetHuntersGameplay)

        QMetaObject.connectSlotsByName(PresetHuntersGameplay)
    # setupUi

    def retranslateUi(self, PresetHuntersGameplay):
        PresetHuntersGameplay.setWindowTitle(QCoreApplication.translate("PresetHuntersGameplay", u"Energy", None))
        self.energy_box.setTitle(QCoreApplication.translate("PresetHuntersGameplay", u"Energy", None))
        self.energy_capacity_label.setText(QCoreApplication.translate("PresetHuntersGameplay", u"Starting Energy", None))
        self.energy_capacity_spin_box.setSuffix(QCoreApplication.translate("PresetHuntersGameplay", u" energy", None))
        self.energy_capacity_description.setText(QCoreApplication.translate("PresetHuntersGameplay", u"<html><head/><body><p>Configure your starting energy.</p></body></html>", None))
        self.optional_box.setTitle(QCoreApplication.translate("PresetHuntersGameplay", u"Optional Patches", None))
        self.skip_planet_intros_check.setText(QCoreApplication.translate("PresetHuntersGameplay", u"Skip Planet Intros", None))
        self.skip_planet_intros_label.setText(QCoreApplication.translate("PresetHuntersGameplay", u"If enabled, this disables the ship landing sequence for each planet.", None))
    # retranslateUi

