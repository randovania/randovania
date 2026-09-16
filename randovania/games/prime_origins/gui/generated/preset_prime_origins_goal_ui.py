# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_prime_origins_goal.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel,
    QMainWindow, QSizePolicy, QSlider, QVBoxLayout,
    QWidget)

from randovania.gui.widgets.scroll_protected import ScrollProtectedSlider

class Ui_PresetPrimeOriginsGoal(object):
    def setupUi(self, PresetPrimeOriginsGoal):
        if not PresetPrimeOriginsGoal.objectName():
            PresetPrimeOriginsGoal.setObjectName(u"PresetPrimeOriginsGoal")
        PresetPrimeOriginsGoal.resize(383, 343)
        self.centralWidget = QWidget(PresetPrimeOriginsGoal)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.goal_layout = QVBoxLayout(self.centralWidget)
        self.goal_layout.setSpacing(6)
        self.goal_layout.setContentsMargins(11, 11, 11, 11)
        self.goal_layout.setObjectName(u"goal_layout")
        self.goal_layout.setContentsMargins(4, 8, 4, 0)
        self.placed_description = QLabel(self.centralWidget)
        self.placed_description.setObjectName(u"placed_description")
        self.placed_description.setWordWrap(True)

        self.goal_layout.addWidget(self.placed_description)

        self.slider_layout = QHBoxLayout()
        self.slider_layout.setSpacing(6)
        self.slider_layout.setObjectName(u"slider_layout")
        self.placed_slider = ScrollProtectedSlider(self.centralWidget)
        self.placed_slider.setObjectName(u"placed_slider")
        self.placed_slider.setMaximum(12)
        self.placed_slider.setPageStep(2)
        self.placed_slider.setOrientation(Qt.Orientation.Horizontal)
        self.placed_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        self.slider_layout.addWidget(self.placed_slider)

        self.placed_slider_label = QLabel(self.centralWidget)
        self.placed_slider_label.setObjectName(u"placed_slider_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.placed_slider_label.sizePolicy().hasHeightForWidth())
        self.placed_slider_label.setSizePolicy(sizePolicy)
        self.placed_slider_label.setMinimumSize(QSize(20, 0))
        self.placed_slider_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.slider_layout.addWidget(self.placed_slider_label)


        self.goal_layout.addLayout(self.slider_layout)

        self.required_description = QLabel(self.centralWidget)
        self.required_description.setObjectName(u"required_description")
        self.required_description.setWordWrap(True)

        self.goal_layout.addWidget(self.required_description)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.required_slider = ScrollProtectedSlider(self.centralWidget)
        self.required_slider.setObjectName(u"required_slider")
        self.required_slider.setMaximum(12)
        self.required_slider.setPageStep(2)
        self.required_slider.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout.addWidget(self.required_slider)

        self.required_slider_label = QLabel(self.centralWidget)
        self.required_slider_label.setObjectName(u"required_slider_label")

        self.horizontalLayout.addWidget(self.required_slider_label)


        self.goal_layout.addLayout(self.horizontalLayout)

        self.label = QLabel(self.centralWidget)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.goal_layout.addWidget(self.label)

        self.main_bosses_checkbox = QCheckBox(self.centralWidget)
        self.main_bosses_checkbox.setObjectName(u"main_bosses_checkbox")

        self.goal_layout.addWidget(self.main_bosses_checkbox)

        self.mini_bosses_checkbox = QCheckBox(self.centralWidget)
        self.mini_bosses_checkbox.setObjectName(u"mini_bosses_checkbox")

        self.goal_layout.addWidget(self.mini_bosses_checkbox)

        PresetPrimeOriginsGoal.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetPrimeOriginsGoal)

        QMetaObject.connectSlotsByName(PresetPrimeOriginsGoal)
    # setupUi

    def retranslateUi(self, PresetPrimeOriginsGoal):
        PresetPrimeOriginsGoal.setWindowTitle(QCoreApplication.translate("PresetPrimeOriginsGoal", u"Goal", None))
        self.placed_description.setText(QCoreApplication.translate("PresetPrimeOriginsGoal", u"<html><head/><body><p>Controls how many Artifacts will be placed.</p><p>You can always check Artifact Temple for hints where the artifacts were placed.</p></body></html>", None))
        self.placed_slider_label.setText(QCoreApplication.translate("PresetPrimeOriginsGoal", u"0", None))
        self.required_description.setText(QCoreApplication.translate("PresetPrimeOriginsGoal", u"\n"
"Controls how many Artifacts are required.\n"
"\n"
"This controls how many Artifacts are needed in order to unlock Impact Crater. This can be different from the amount of placed Artifacts.", None))
        self.required_slider_label.setText(QCoreApplication.translate("PresetPrimeOriginsGoal", u"0", None))
        self.label.setText(QCoreApplication.translate("PresetPrimeOriginsGoal", u"Boss requirements.", None))
        self.main_bosses_checkbox.setText(QCoreApplication.translate("PresetPrimeOriginsGoal", u"Require all main bosses (Flaagrah, Thardus and Omega Pirate)", None))
        self.mini_bosses_checkbox.setText(QCoreApplication.translate("PresetPrimeOriginsGoal", u"Require all minibosses (Anything with a boss icon)", None))
    # retranslateUi

