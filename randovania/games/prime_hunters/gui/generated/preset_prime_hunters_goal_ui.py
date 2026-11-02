# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_prime_hunters_goal.ui'
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
from PySide6.QtWidgets import (QApplication, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QRadioButton, QSizePolicy,
    QSlider, QVBoxLayout, QWidget)

from randovania.gui.widgets.scroll_protected import ScrollProtectedSlider

class Ui_PresetHuntersGoal(object):
    def setupUi(self, PresetHuntersGoal):
        if not PresetHuntersGoal.objectName():
            PresetHuntersGoal.setObjectName(u"PresetHuntersGoal")
        PresetHuntersGoal.resize(573, 284)
        self.centralWidget = QWidget(PresetHuntersGoal)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.goal_layout = QGridLayout(self.centralWidget)
        self.goal_layout.setSpacing(6)
        self.goal_layout.setContentsMargins(11, 11, 11, 11)
        self.goal_layout.setObjectName(u"goal_layout")
        self.placed_description = QLabel(self.centralWidget)
        self.placed_description.setObjectName(u"placed_description")
        self.placed_description.setWordWrap(True)

        self.goal_layout.addWidget(self.placed_description, 0, 0, 1, 1)

        self.slider_layout = QHBoxLayout()
        self.slider_layout.setSpacing(6)
        self.slider_layout.setObjectName(u"slider_layout")
        self.placed_slider = ScrollProtectedSlider(self.centralWidget)
        self.placed_slider.setObjectName(u"placed_slider")
        self.placed_slider.setMaximum(8)
        self.placed_slider.setPageStep(2)
        self.placed_slider.setOrientation(Qt.Horizontal)
        self.placed_slider.setTickPosition(QSlider.TicksBelow)

        self.slider_layout.addWidget(self.placed_slider)

        self.placed_slider_label = QLabel(self.centralWidget)
        self.placed_slider_label.setObjectName(u"placed_slider_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.placed_slider_label.sizePolicy().hasHeightForWidth())
        self.placed_slider_label.setSizePolicy(sizePolicy)
        self.placed_slider_label.setMinimumSize(QSize(20, 0))
        self.placed_slider_label.setAlignment(Qt.AlignCenter)

        self.slider_layout.addWidget(self.placed_slider_label)


        self.goal_layout.addLayout(self.slider_layout, 1, 0, 1, 1)

        self.placement_group = QGroupBox(self.centralWidget)
        self.placement_group.setObjectName(u"placement_group")
        self.verticalLayout = QVBoxLayout(self.placement_group)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.restrict_placement_radiobutton = QRadioButton(self.placement_group)
        self.restrict_placement_radiobutton.setObjectName(u"restrict_placement_radiobutton")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.restrict_placement_radiobutton.sizePolicy().hasHeightForWidth())
        self.restrict_placement_radiobutton.setSizePolicy(sizePolicy1)

        self.verticalLayout.addWidget(self.restrict_placement_radiobutton)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(20, -1, -1, -1)
        self.restrict_placement_label = QLabel(self.placement_group)
        self.restrict_placement_label.setObjectName(u"restrict_placement_label")
        self.restrict_placement_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.restrict_placement_label)


        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.free_placement_radiobutton = QRadioButton(self.placement_group)
        self.free_placement_radiobutton.setObjectName(u"free_placement_radiobutton")
        sizePolicy1.setHeightForWidth(self.free_placement_radiobutton.sizePolicy().hasHeightForWidth())
        self.free_placement_radiobutton.setSizePolicy(sizePolicy1)

        self.verticalLayout.addWidget(self.free_placement_radiobutton)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(6)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(20, -1, -1, -1)
        self.free_placement_label = QLabel(self.placement_group)
        self.free_placement_label.setObjectName(u"free_placement_label")
        self.free_placement_label.setWordWrap(True)

        self.verticalLayout_3.addWidget(self.free_placement_label)


        self.verticalLayout.addLayout(self.verticalLayout_3)


        self.goal_layout.addWidget(self.placement_group, 2, 0, 1, 1)

        PresetHuntersGoal.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetHuntersGoal)

        QMetaObject.connectSlotsByName(PresetHuntersGoal)
    # setupUi

    def retranslateUi(self, PresetHuntersGoal):
        PresetHuntersGoal.setWindowTitle(QCoreApplication.translate("PresetHuntersGoal", u"Goal", None))
        self.placed_description.setText(QCoreApplication.translate("PresetHuntersGoal", u"<html><head/><body><p>Controls how many Octoliths are needed in order to unlock Oubliette.</p></body></html>", None))
        self.placed_slider_label.setText(QCoreApplication.translate("PresetHuntersGoal", u"0", None))
        self.placement_group.setTitle(QCoreApplication.translate("PresetHuntersGoal", u"Placement", None))
        self.restrict_placement_radiobutton.setText(QCoreApplication.translate("PresetHuntersGoal", u"Restricted Placement", None))
        self.restrict_placement_label.setText(QCoreApplication.translate("PresetHuntersGoal", u"<html><head/><body><p>Octoliths can only be placed on bosses in Biodefense Chambers where Cretaphid and Slench are located.</p></body></html>", None))
        self.free_placement_radiobutton.setText(QCoreApplication.translate("PresetHuntersGoal", u"Free Placement", None))
        self.free_placement_label.setText(QCoreApplication.translate("PresetHuntersGoal", u"Enables Octoliths to be placed anywhere.", None))
    # retranslateUi

