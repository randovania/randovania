# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'preset_prime_enemy_stat_randomizer.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDoubleSpinBox, QGridLayout,
    QLabel, QMainWindow, QScrollArea, QSizePolicy,
    QSpacerItem, QWidget)

class Ui_EnemyAttributeRandomizer(object):
    def setupUi(self, EnemyAttributeRandomizer):
        if not EnemyAttributeRandomizer.objectName():
            EnemyAttributeRandomizer.setObjectName(u"EnemyAttributeRandomizer")
        EnemyAttributeRandomizer.resize(672, 425)
        self.centralWidget = QWidget(EnemyAttributeRandomizer)
        self.centralWidget.setObjectName(u"centralWidget")
        self.centralWidget.setMaximumSize(QSize(16777215, 16777215))
        self.gridLayout = QGridLayout(self.centralWidget)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self.centralWidget)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_contents = QWidget()
        self.scroll_area_contents.setObjectName(u"scroll_area_contents")
        self.scroll_area_contents.setGeometry(QRect(0, 0, 653, 554))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scroll_area_contents.sizePolicy().hasHeightForWidth())
        self.scroll_area_contents.setSizePolicy(sizePolicy)
        self.scroll_area_layout = QGridLayout(self.scroll_area_contents)
        self.scroll_area_layout.setSpacing(6)
        self.scroll_area_layout.setContentsMargins(11, 11, 11, 11)
        self.scroll_area_layout.setObjectName(u"scroll_area_layout")
        self.scroll_area_layout.setContentsMargins(4, 6, 4, 0)
        self.verticalSpacer = QSpacerItem(20, 52, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area_layout.addItem(self.verticalSpacer, 11, 0, 1, 4)

        self.range_damage_high = QDoubleSpinBox(self.scroll_area_contents)
        self.range_damage_high.setObjectName(u"range_damage_high")
        self.range_damage_high.setEnabled(False)
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.range_damage_high.sizePolicy().hasHeightForWidth())
        self.range_damage_high.setSizePolicy(sizePolicy1)
        self.range_damage_high.setMinimumSize(QSize(0, 0))
        self.range_damage_high.setMaximumSize(QSize(16777215, 16777215))
        self.range_damage_high.setMaximum(1000.000000000000000)
        self.range_damage_high.setSingleStep(0.250000000000000)
        self.range_damage_high.setValue(1.000000000000000)

        self.scroll_area_layout.addWidget(self.range_damage_high, 7, 2, 1, 1)

        self.range_knockback_low = QDoubleSpinBox(self.scroll_area_contents)
        self.range_knockback_low.setObjectName(u"range_knockback_low")
        self.range_knockback_low.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.range_knockback_low.sizePolicy().hasHeightForWidth())
        self.range_knockback_low.setSizePolicy(sizePolicy1)
        self.range_knockback_low.setMinimumSize(QSize(0, 0))
        self.range_knockback_low.setMaximumSize(QSize(16777215, 16777215))
        self.range_knockback_low.setMaximum(1000.000000000000000)
        self.range_knockback_low.setSingleStep(0.250000000000000)
        self.range_knockback_low.setValue(1.000000000000000)

        self.scroll_area_layout.addWidget(self.range_knockback_low, 8, 1, 1, 1)

        self.range_scale_high = QDoubleSpinBox(self.scroll_area_contents)
        self.range_scale_high.setObjectName(u"range_scale_high")
        self.range_scale_high.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.range_scale_high.sizePolicy().hasHeightForWidth())
        self.range_scale_high.setSizePolicy(sizePolicy1)
        self.range_scale_high.setMinimumSize(QSize(0, 0))
        self.range_scale_high.setMaximumSize(QSize(16777215, 16777215))
        self.range_scale_high.setMinimum(0.010000000000000)
        self.range_scale_high.setMaximum(25.000000000000000)
        self.range_scale_high.setSingleStep(0.250000000000000)
        self.range_scale_high.setValue(1.000000000000000)

        self.scroll_area_layout.addWidget(self.range_scale_high, 3, 2, 1, 1)

        self.label_4 = QLabel(self.scroll_area_contents)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setWordWrap(True)

        self.scroll_area_layout.addWidget(self.label_4, 10, 0, 1, 4)

        self.label = QLabel(self.scroll_area_contents)
        self.label.setObjectName(u"label")
        self.label.setEnabled(False)
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy2)
        self.label.setMinimumSize(QSize(0, 0))
        self.label.setWordWrap(True)

        self.scroll_area_layout.addWidget(self.label, 5, 3, 1, 1)

        self.scale_attribute_label = QLabel(self.scroll_area_contents)
        self.scale_attribute_label.setObjectName(u"scale_attribute_label")
        self.scale_attribute_label.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.scale_attribute_label.sizePolicy().hasHeightForWidth())
        self.scale_attribute_label.setSizePolicy(sizePolicy1)
        self.scale_attribute_label.setMaximumSize(QSize(16777215, 16777215))

        self.scroll_area_layout.addWidget(self.scale_attribute_label, 3, 0, 1, 1)

        self.damage_attribute_label = QLabel(self.scroll_area_contents)
        self.damage_attribute_label.setObjectName(u"damage_attribute_label")
        self.damage_attribute_label.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.damage_attribute_label.sizePolicy().hasHeightForWidth())
        self.damage_attribute_label.setSizePolicy(sizePolicy1)
        self.damage_attribute_label.setMaximumSize(QSize(16777215, 16777215))

        self.scroll_area_layout.addWidget(self.damage_attribute_label, 7, 0, 1, 1)

        self.knockback_attribute_label = QLabel(self.scroll_area_contents)
        self.knockback_attribute_label.setObjectName(u"knockback_attribute_label")
        self.knockback_attribute_label.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.knockback_attribute_label.sizePolicy().hasHeightForWidth())
        self.knockback_attribute_label.setSizePolicy(sizePolicy1)
        self.knockback_attribute_label.setMaximumSize(QSize(16777215, 16777215))

        self.scroll_area_layout.addWidget(self.knockback_attribute_label, 8, 0, 1, 1)

        self.label_2 = QLabel(self.scroll_area_contents)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setEnabled(False)
        sizePolicy2.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy2)
        self.label_2.setMinimumSize(QSize(0, 0))
        self.label_2.setWordWrap(True)

        self.scroll_area_layout.addWidget(self.label_2, 6, 3, 1, 1)

        self.range_knockback_high = QDoubleSpinBox(self.scroll_area_contents)
        self.range_knockback_high.setObjectName(u"range_knockback_high")
        self.range_knockback_high.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.range_knockback_high.sizePolicy().hasHeightForWidth())
        self.range_knockback_high.setSizePolicy(sizePolicy1)
        self.range_knockback_high.setMinimumSize(QSize(0, 0))
        self.range_knockback_high.setMaximumSize(QSize(16777215, 16777215))
        self.range_knockback_high.setMaximum(1000.000000000000000)
        self.range_knockback_high.setSingleStep(0.250000000000000)
        self.range_knockback_high.setValue(1.000000000000000)

        self.scroll_area_layout.addWidget(self.range_knockback_high, 8, 2, 1, 1)

        self.health_attribute_label = QLabel(self.scroll_area_contents)
        self.health_attribute_label.setObjectName(u"health_attribute_label")
        self.health_attribute_label.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.health_attribute_label.sizePolicy().hasHeightForWidth())
        self.health_attribute_label.setSizePolicy(sizePolicy1)
        self.health_attribute_label.setMaximumSize(QSize(16777215, 16777215))

        self.scroll_area_layout.addWidget(self.health_attribute_label, 5, 0, 1, 1)

        self.range_damage_low = QDoubleSpinBox(self.scroll_area_contents)
        self.range_damage_low.setObjectName(u"range_damage_low")
        self.range_damage_low.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.range_damage_low.sizePolicy().hasHeightForWidth())
        self.range_damage_low.setSizePolicy(sizePolicy1)
        self.range_damage_low.setMinimumSize(QSize(0, 0))
        self.range_damage_low.setMaximumSize(QSize(16777215, 16777215))
        self.range_damage_low.setMaximum(1000.000000000000000)
        self.range_damage_low.setSingleStep(0.250000000000000)
        self.range_damage_low.setValue(1.000000000000000)

        self.scroll_area_layout.addWidget(self.range_damage_low, 7, 1, 1, 1)

        self.maximum_label = QLabel(self.scroll_area_contents)
        self.maximum_label.setObjectName(u"maximum_label")
        self.maximum_label.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.maximum_label.sizePolicy().hasHeightForWidth())
        self.maximum_label.setSizePolicy(sizePolicy1)
        self.maximum_label.setMinimumSize(QSize(0, 0))

        self.scroll_area_layout.addWidget(self.maximum_label, 2, 2, 1, 1)

        self.diff_xyz = QCheckBox(self.scroll_area_contents)
        self.diff_xyz.setObjectName(u"diff_xyz")
        self.diff_xyz.setEnabled(False)

        self.scroll_area_layout.addWidget(self.diff_xyz, 4, 0, 1, 3)

        self.range_health_high = QDoubleSpinBox(self.scroll_area_contents)
        self.range_health_high.setObjectName(u"range_health_high")
        self.range_health_high.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.range_health_high.sizePolicy().hasHeightForWidth())
        self.range_health_high.setSizePolicy(sizePolicy1)
        self.range_health_high.setMinimumSize(QSize(0, 0))
        self.range_health_high.setMaximumSize(QSize(16777215, 16777215))
        self.range_health_high.setMinimum(0.010000000000000)
        self.range_health_high.setMaximum(1000.000000000000000)
        self.range_health_high.setSingleStep(0.250000000000000)
        self.range_health_high.setValue(1.000000000000000)

        self.scroll_area_layout.addWidget(self.range_health_high, 5, 2, 1, 1)

        self.activate_randomizer = QCheckBox(self.scroll_area_contents)
        self.activate_randomizer.setObjectName(u"activate_randomizer")

        self.scroll_area_layout.addWidget(self.activate_randomizer, 1, 0, 1, 1)

        self.range_speed_high = QDoubleSpinBox(self.scroll_area_contents)
        self.range_speed_high.setObjectName(u"range_speed_high")
        self.range_speed_high.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.range_speed_high.sizePolicy().hasHeightForWidth())
        self.range_speed_high.setSizePolicy(sizePolicy1)
        self.range_speed_high.setMinimumSize(QSize(0, 0))
        self.range_speed_high.setMaximumSize(QSize(16777215, 16777215))
        self.range_speed_high.setMaximum(100.000000000000000)
        self.range_speed_high.setSingleStep(0.250000000000000)
        self.range_speed_high.setValue(1.000000000000000)

        self.scroll_area_layout.addWidget(self.range_speed_high, 6, 2, 1, 1)

        self.range_health_low = QDoubleSpinBox(self.scroll_area_contents)
        self.range_health_low.setObjectName(u"range_health_low")
        self.range_health_low.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.range_health_low.sizePolicy().hasHeightForWidth())
        self.range_health_low.setSizePolicy(sizePolicy1)
        self.range_health_low.setMinimumSize(QSize(0, 0))
        self.range_health_low.setMaximumSize(QSize(16777215, 16777215))
        self.range_health_low.setMinimum(0.010000000000000)
        self.range_health_low.setMaximum(1000.000000000000000)
        self.range_health_low.setSingleStep(0.250000000000000)
        self.range_health_low.setValue(1.000000000000000)

        self.scroll_area_layout.addWidget(self.range_health_low, 5, 1, 1, 1)

        self.range_speed_low = QDoubleSpinBox(self.scroll_area_contents)
        self.range_speed_low.setObjectName(u"range_speed_low")
        self.range_speed_low.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.range_speed_low.sizePolicy().hasHeightForWidth())
        self.range_speed_low.setSizePolicy(sizePolicy1)
        self.range_speed_low.setMinimumSize(QSize(0, 0))
        self.range_speed_low.setMaximumSize(QSize(16777215, 16777215))
        self.range_speed_low.setMaximum(100.000000000000000)
        self.range_speed_low.setSingleStep(0.250000000000000)
        self.range_speed_low.setValue(1.000000000000000)

        self.scroll_area_layout.addWidget(self.range_speed_low, 6, 1, 1, 1)

        self.speed_attribute_label = QLabel(self.scroll_area_contents)
        self.speed_attribute_label.setObjectName(u"speed_attribute_label")
        self.speed_attribute_label.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.speed_attribute_label.sizePolicy().hasHeightForWidth())
        self.speed_attribute_label.setSizePolicy(sizePolicy1)
        self.speed_attribute_label.setMaximumSize(QSize(16777215, 16777215))

        self.scroll_area_layout.addWidget(self.speed_attribute_label, 6, 0, 1, 1)

        self.range_scale_low = QDoubleSpinBox(self.scroll_area_contents)
        self.range_scale_low.setObjectName(u"range_scale_low")
        self.range_scale_low.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.range_scale_low.sizePolicy().hasHeightForWidth())
        self.range_scale_low.setSizePolicy(sizePolicy1)
        self.range_scale_low.setMinimumSize(QSize(0, 0))
        self.range_scale_low.setMaximumSize(QSize(16777215, 16777215))
        self.range_scale_low.setMinimum(0.010000000000000)
        self.range_scale_low.setMaximum(25.000000000000000)
        self.range_scale_low.setSingleStep(0.250000000000000)
        self.range_scale_low.setValue(1.000000000000000)

        self.scroll_area_layout.addWidget(self.range_scale_low, 3, 1, 1, 1)

        self.enemy_stat_randomizer_description = QLabel(self.scroll_area_contents)
        self.enemy_stat_randomizer_description.setObjectName(u"enemy_stat_randomizer_description")
        sizePolicy2.setHeightForWidth(self.enemy_stat_randomizer_description.sizePolicy().hasHeightForWidth())
        self.enemy_stat_randomizer_description.setSizePolicy(sizePolicy2)
        self.enemy_stat_randomizer_description.setMaximumSize(QSize(16777215, 16777215))
        self.enemy_stat_randomizer_description.setWordWrap(True)

        self.scroll_area_layout.addWidget(self.enemy_stat_randomizer_description, 0, 0, 1, 4)

        self.minimum_label = QLabel(self.scroll_area_contents)
        self.minimum_label.setObjectName(u"minimum_label")
        self.minimum_label.setEnabled(False)
        sizePolicy1.setHeightForWidth(self.minimum_label.sizePolicy().hasHeightForWidth())
        self.minimum_label.setSizePolicy(sizePolicy1)
        self.minimum_label.setMinimumSize(QSize(0, 0))

        self.scroll_area_layout.addWidget(self.minimum_label, 2, 1, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.scroll_area_layout.addItem(self.verticalSpacer_2, 9, 0, 1, 4)

        self.scroll_area.setWidget(self.scroll_area_contents)

        self.gridLayout.addWidget(self.scroll_area, 0, 0, 1, 1)

        EnemyAttributeRandomizer.setCentralWidget(self.centralWidget)
        QWidget.setTabOrder(self.scroll_area, self.activate_randomizer)
        QWidget.setTabOrder(self.activate_randomizer, self.range_scale_low)
        QWidget.setTabOrder(self.range_scale_low, self.range_scale_high)
        QWidget.setTabOrder(self.range_scale_high, self.diff_xyz)
        QWidget.setTabOrder(self.diff_xyz, self.range_health_low)
        QWidget.setTabOrder(self.range_health_low, self.range_health_high)
        QWidget.setTabOrder(self.range_health_high, self.range_speed_low)
        QWidget.setTabOrder(self.range_speed_low, self.range_speed_high)
        QWidget.setTabOrder(self.range_speed_high, self.range_damage_low)
        QWidget.setTabOrder(self.range_damage_low, self.range_damage_high)
        QWidget.setTabOrder(self.range_damage_high, self.range_knockback_low)
        QWidget.setTabOrder(self.range_knockback_low, self.range_knockback_high)

        self.retranslateUi(EnemyAttributeRandomizer)

        QMetaObject.connectSlotsByName(EnemyAttributeRandomizer)
    # setupUi

    def retranslateUi(self, EnemyAttributeRandomizer):
        EnemyAttributeRandomizer.setWindowTitle(QCoreApplication.translate("EnemyAttributeRandomizer", u"Energy", None))
        self.label_4.setText(QCoreApplication.translate("EnemyAttributeRandomizer", u"<html><head/><body><p>While this is enabled, game output type is limited to '.iso'.</p><p>If you change the minimum and maximum values for size, while also having &quot;Random Boss Sizes&quot; on, then Random Boss Sizes will be automatically disabled.</p><p>This hasn't been tested with multiworld, so take care.</p></body></html>", None))
        self.label.setText(QCoreApplication.translate("EnemyAttributeRandomizer", u"<html><head/><body><p>Includes all aspects of health such as a Sheegoth's shell and exposed back.</p></body></html>", None))
        self.scale_attribute_label.setText(QCoreApplication.translate("EnemyAttributeRandomizer", u"Size Range", None))
        self.damage_attribute_label.setText(QCoreApplication.translate("EnemyAttributeRandomizer", u"Damage Range", None))
        self.knockback_attribute_label.setText(QCoreApplication.translate("EnemyAttributeRandomizer", u"Knockback Range", None))
        self.label_2.setText(QCoreApplication.translate("EnemyAttributeRandomizer", u"<html><head/><body><p>Includes attack frequency/speed, as well as animation speed.</p></body></html>", None))
        self.health_attribute_label.setText(QCoreApplication.translate("EnemyAttributeRandomizer", u"Health Range", None))
        self.maximum_label.setText(QCoreApplication.translate("EnemyAttributeRandomizer", u"<html><head/><body><p align=\"center\">Maximum</p></body></html>", None))
        self.diff_xyz.setText(QCoreApplication.translate("EnemyAttributeRandomizer", u"Enemies/Bosses will be stretched randomly within the above range", None))
        self.activate_randomizer.setText(QCoreApplication.translate("EnemyAttributeRandomizer", u"Activate Attribute Randomizer", None))
        self.speed_attribute_label.setText(QCoreApplication.translate("EnemyAttributeRandomizer", u"Speed Range", None))
        self.enemy_stat_randomizer_description.setText(QCoreApplication.translate("EnemyAttributeRandomizer", u"<html><head/><body><p>Randomize all enemy attributes using the boxes below.</p><p>These values are applied to each enemy individually, so one beetle could be made larger while another beetle is made smaller. Keep in mind that while each box has a limit, you can still set them to extreme values that may make the game unbeatable. </p><p>These settings are <span style=\" font-weight:700;\">not logical</span>, so you'll be expected to fight every enemy as if they were normal.</p></body></html>", None))
        self.minimum_label.setText(QCoreApplication.translate("EnemyAttributeRandomizer", u"<html><head/><body><p align=\"center\">Minimum</p></body></html>", None))
    # retranslateUi

