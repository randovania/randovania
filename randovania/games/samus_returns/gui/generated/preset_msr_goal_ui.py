# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_msr_goal.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGroupBox,
    QHBoxLayout, QLabel, QMainWindow, QRadioButton,
    QScrollArea, QSizePolicy, QSlider, QSpacerItem,
    QVBoxLayout, QWidget)

from randovania.gui.lib.scroll_protected import ScrollProtectedSlider

class Ui_PresetMSRGoal(object):
    def setupUi(self, PresetMSRGoal):
        if not PresetMSRGoal.objectName():
            PresetMSRGoal.setObjectName(u"PresetMSRGoal")
        PresetMSRGoal.resize(858, 805)
        self.centralWidget = QWidget(PresetMSRGoal)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.goal_layout = QVBoxLayout(self.centralWidget)
        self.goal_layout.setSpacing(6)
        self.goal_layout.setContentsMargins(11, 11, 11, 11)
        self.goal_layout.setObjectName(u"goal_layout")
        self.goal_layout.setContentsMargins(6, 6, 6, 6)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 844, 791))
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
        self.description_label = QLabel(self.scroll_area_contents)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.scroll_area_layout.addWidget(self.description_label)

        self.label_2 = QLabel(self.scroll_area_contents)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setWordWrap(True)

        self.scroll_area_layout.addWidget(self.label_2)

        self.placed_slider_layout = QHBoxLayout()
        self.placed_slider_layout.setSpacing(6)
        self.placed_slider_layout.setObjectName(u"placed_slider_layout")
        self.placed_slider_layout.setContentsMargins(6, 6, 6, 6)
        self.placed_slider = ScrollProtectedSlider(self.scroll_area_contents)
        self.placed_slider.setObjectName(u"placed_slider")
        self.placed_slider.setMaximum(39)
        self.placed_slider.setPageStep(2)
        self.placed_slider.setOrientation(Qt.Horizontal)
        self.placed_slider.setTickPosition(QSlider.TicksBelow)

        self.placed_slider_layout.addWidget(self.placed_slider)

        self.placed_slider_label = QLabel(self.scroll_area_contents)
        self.placed_slider_label.setObjectName(u"placed_slider_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.placed_slider_label.sizePolicy().hasHeightForWidth())
        self.placed_slider_label.setSizePolicy(sizePolicy1)
        self.placed_slider_label.setMinimumSize(QSize(0, 0))
        self.placed_slider_label.setAlignment(Qt.AlignCenter)

        self.placed_slider_layout.addWidget(self.placed_slider_label)


        self.scroll_area_layout.addLayout(self.placed_slider_layout)

        self.label = QLabel(self.scroll_area_contents)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.scroll_area_layout.addWidget(self.label)

        self.required_slider_layout = QHBoxLayout()
        self.required_slider_layout.setSpacing(6)
        self.required_slider_layout.setObjectName(u"required_slider_layout")
        self.required_slider_layout.setContentsMargins(6, 6, 6, 6)
        self.required_slider = ScrollProtectedSlider(self.scroll_area_contents)
        self.required_slider.setObjectName(u"required_slider")
        self.required_slider.setMaximum(39)
        self.required_slider.setPageStep(2)
        self.required_slider.setOrientation(Qt.Horizontal)
        self.required_slider.setTickPosition(QSlider.TicksBelow)

        self.required_slider_layout.addWidget(self.required_slider)

        self.required_slider_label = QLabel(self.scroll_area_contents)
        self.required_slider_label.setObjectName(u"required_slider_label")

        self.required_slider_layout.addWidget(self.required_slider_label)


        self.scroll_area_layout.addLayout(self.required_slider_layout)

        self.placement_group = QGroupBox(self.scroll_area_contents)
        self.placement_group.setObjectName(u"placement_group")
        self.verticalLayout = QVBoxLayout(self.placement_group)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.restrict_placement_radiobutton = QRadioButton(self.placement_group)
        self.restrict_placement_radiobutton.setObjectName(u"restrict_placement_radiobutton")
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

        self.prefer_metroids_check = QCheckBox(self.placement_group)
        self.prefer_metroids_check.setObjectName(u"prefer_metroids_check")
        sizePolicy1.setHeightForWidth(self.prefer_metroids_check.sizePolicy().hasHeightForWidth())
        self.prefer_metroids_check.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.prefer_metroids_check)

        self.prefer_stronger_metroids_check = QCheckBox(self.placement_group)
        self.prefer_stronger_metroids_check.setObjectName(u"prefer_stronger_metroids_check")
        sizePolicy1.setHeightForWidth(self.prefer_stronger_metroids_check.sizePolicy().hasHeightForWidth())
        self.prefer_stronger_metroids_check.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.prefer_stronger_metroids_check)

        self.prefer_bosses_check = QCheckBox(self.placement_group)
        self.prefer_bosses_check.setObjectName(u"prefer_bosses_check")
        sizePolicy1.setHeightForWidth(self.prefer_bosses_check.sizePolicy().hasHeightForWidth())
        self.prefer_bosses_check.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.prefer_bosses_check)


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


        self.scroll_area_layout.addWidget(self.placement_group)

        self.final_boss_group = QGroupBox(self.scroll_area_contents)
        self.final_boss_group.setObjectName(u"final_boss_group")
        self.verticalLayout_4 = QVBoxLayout(self.final_boss_group)
        self.verticalLayout_4.setSpacing(6)
        self.verticalLayout_4.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.final_boss_label = QLabel(self.final_boss_group)
        self.final_boss_label.setObjectName(u"final_boss_label")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.final_boss_label.sizePolicy().hasHeightForWidth())
        self.final_boss_label.setSizePolicy(sizePolicy2)
        self.final_boss_label.setMinimumSize(QSize(0, 0))
        self.final_boss_label.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.final_boss_label)

        self.final_boss_combo = QComboBox(self.final_boss_group)
        self.final_boss_combo.addItem("")
        self.final_boss_combo.addItem("")
        self.final_boss_combo.addItem("")
        self.final_boss_combo.addItem("")
        self.final_boss_combo.setObjectName(u"final_boss_combo")

        self.verticalLayout_4.addWidget(self.final_boss_combo)

        self.boss_info_label = QLabel(self.final_boss_group)
        self.boss_info_label.setObjectName(u"boss_info_label")
        self.boss_info_label.setWordWrap(True)

        self.verticalLayout_4.addWidget(self.boss_info_label)

        self.final_boss_combo.raise_()
        self.final_boss_label.raise_()
        self.boss_info_label.raise_()

        self.scroll_area_layout.addWidget(self.final_boss_group)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.goal_layout.addWidget(self.scroll_area)

        PresetMSRGoal.setCentralWidget(self.centralWidget)

        self.retranslateUi(PresetMSRGoal)

        QMetaObject.connectSlotsByName(PresetMSRGoal)
    # setupUi

    def retranslateUi(self, PresetMSRGoal):
        PresetMSRGoal.setWindowTitle(QCoreApplication.translate("PresetMSRGoal", u"Goal", None))
        self.description_label.setText(QCoreApplication.translate("PresetMSRGoal", u"<html><head/><body><p>It is now necessary to collect Metroid DNA in order to reach the final boss. The minimum and maximum are limited to 0 and 39 DNA respectively. You can choose to have more DNA in the Pool than what is required to collect.</p></body></html>", None))
        self.label_2.setText(QCoreApplication.translate("PresetMSRGoal", u"Controls how much Metroid DNA is obtainable.", None))
        self.placed_slider_label.setText(QCoreApplication.translate("PresetMSRGoal", u"0", None))
        self.label.setText(QCoreApplication.translate("PresetMSRGoal", u"Controls how much Metroid DNA is required to be collected.", None))
        self.required_slider_label.setText(QCoreApplication.translate("PresetMSRGoal", u"0", None))
        self.placement_group.setTitle(QCoreApplication.translate("PresetMSRGoal", u"Placement", None))
        self.restrict_placement_radiobutton.setText(QCoreApplication.translate("PresetMSRGoal", u"Restricted Placement", None))
        self.restrict_placement_label.setText(QCoreApplication.translate("PresetMSRGoal", u"<html><head/><body><p>The following options limit where Metroid DNA will be placed. There can only be as many DNA shuffled as there are preferred locations available. The first option adds 25 preferred locations, the second adds 14, and the third adds 4. In Multiworlds, DNA is guaranteed to be in your World. If <span style=\" font-weight:600;\">Prefer Bosses</span> is selected, DNA will not be placed on the final boss location.</p></body></html>", None))
        self.prefer_metroids_check.setText(QCoreApplication.translate("PresetMSRGoal", u"Prefer Standard Metroids (10 Alphas, 8 Gammas, 3 Zetas, 3 Omegas)", None))
        self.prefer_stronger_metroids_check.setText(QCoreApplication.translate("PresetMSRGoal", u"Prefer Stronger Metroids (7 Alpha+, 6 Gamma+, 1 Zeta+, 1 Omega+)", None))
        self.prefer_bosses_check.setText(QCoreApplication.translate("PresetMSRGoal", u"Prefer Bosses (Arachnus, Diggernaut Chase Reward, Diggernaut, Queen Metroid, Proteus Ridley)", None))
        self.free_placement_radiobutton.setText(QCoreApplication.translate("PresetMSRGoal", u"Free Placement", None))
        self.free_placement_label.setText(QCoreApplication.translate("PresetMSRGoal", u"Enables DNA to be placed anywhere. For Multiworlds, this means even other Worlds.", None))
        self.final_boss_group.setTitle(QCoreApplication.translate("PresetMSRGoal", u"Final Boss", None))
        self.final_boss_label.setText(QCoreApplication.translate("PresetMSRGoal", u"<html><head/><body><p>In vanilla and by default, the final boss is Proteus Ridley. This setting allows any of the three other bosses (Arachnus, Diggernaut, Metroid Queen) to be the final boss instead.</p><p>If Ridley is not the final boss, the fight is active right away. You can decide to fight early or continue on to <span style=\" font-weight:600;\">Landing Site</span>. Upon defeat, an item will appear next to the ship.</p><p>Besides just collecting Metroid DNA, some bosses have additional requirements that must be completed in order to fight them or have requirements after the fight.</p></body></html>", None))
        self.final_boss_combo.setItemText(0, QCoreApplication.translate("PresetMSRGoal", u"Arachnus", None))
        self.final_boss_combo.setItemText(1, QCoreApplication.translate("PresetMSRGoal", u"Diggernaut", None))
        self.final_boss_combo.setItemText(2, QCoreApplication.translate("PresetMSRGoal", u"Metroid Queen", None))
        self.final_boss_combo.setItemText(3, QCoreApplication.translate("PresetMSRGoal", u"Proteus Ridley", None))

        self.boss_info_label.setText(QCoreApplication.translate("PresetMSRGoal", u"<html><head/><body><p>&lt;description generated dynamically&gt;</p></body></html>", None))
    # retranslateUi

