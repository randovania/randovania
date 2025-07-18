# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'standard_pickup_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QFrame,
    QGridLayout, QLabel, QSizePolicy, QWidget)

from randovania.gui.lib.scroll_protected import (ScrollProtectedComboBox, ScrollProtectedSpinBox)

class Ui_StandardPickupWidget(object):
    def setupUi(self, StandardPickupWidget):
        if not StandardPickupWidget.objectName():
            StandardPickupWidget.setObjectName(u"StandardPickupWidget")
        StandardPickupWidget.resize(880, 88)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(StandardPickupWidget.sizePolicy().hasHeightForWidth())
        StandardPickupWidget.setSizePolicy(sizePolicy)
        StandardPickupWidget.setMaximumSize(QSize(16777215, 16777215))
        self.root_layout = QGridLayout(StandardPickupWidget)
        self.root_layout.setSpacing(6)
        self.root_layout.setContentsMargins(11, 11, 11, 11)
        self.root_layout.setObjectName(u"root_layout")
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.priority_label = QLabel(StandardPickupWidget)
        self.priority_label.setObjectName(u"priority_label")

        self.root_layout.addWidget(self.priority_label, 3, 2, 1, 1)

        self.pickup_name_label = QLabel(StandardPickupWidget)
        self.pickup_name_label.setObjectName(u"pickup_name_label")
        self.pickup_name_label.setMinimumSize(QSize(150, 0))
        font = QFont()
        font.setBold(True)
        self.pickup_name_label.setFont(font)

        self.root_layout.addWidget(self.pickup_name_label, 1, 0, 1, 1)

        self.starting_check = QCheckBox(StandardPickupWidget)
        self.starting_check.setObjectName(u"starting_check")

        self.root_layout.addWidget(self.starting_check, 3, 1, 1, 1)

        self.vanilla_check = QCheckBox(StandardPickupWidget)
        self.vanilla_check.setObjectName(u"vanilla_check")

        self.root_layout.addWidget(self.vanilla_check, 3, 0, 1, 1)

        self.shuffled_spinbox = ScrollProtectedSpinBox(StandardPickupWidget)
        self.shuffled_spinbox.setObjectName(u"shuffled_spinbox")
        self.shuffled_spinbox.setMinimum(1)
        self.shuffled_spinbox.setMaximum(99)

        self.root_layout.addWidget(self.shuffled_spinbox, 3, 4, 1, 1)

        self.separator_line = QFrame(StandardPickupWidget)
        self.separator_line.setObjectName(u"separator_line")
        self.separator_line.setFrameShape(QFrame.Shape.HLine)
        self.separator_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.root_layout.addWidget(self.separator_line, 0, 0, 1, 5)

        self.priority_combo = ScrollProtectedComboBox(StandardPickupWidget)
        self.priority_combo.setObjectName(u"priority_combo")

        self.root_layout.addWidget(self.priority_combo, 3, 3, 1, 1)

        self.state_case_combo = ScrollProtectedComboBox(StandardPickupWidget)
        self.state_case_combo.setObjectName(u"state_case_combo")

        self.root_layout.addWidget(self.state_case_combo, 1, 4, 1, 1)

        self.provided_ammo_spinbox = ScrollProtectedSpinBox(StandardPickupWidget)
        self.provided_ammo_spinbox.setObjectName(u"provided_ammo_spinbox")

        self.root_layout.addWidget(self.provided_ammo_spinbox, 1, 2, 1, 2)


        self.retranslateUi(StandardPickupWidget)

        QMetaObject.connectSlotsByName(StandardPickupWidget)
    # setupUi

    def retranslateUi(self, StandardPickupWidget):
        StandardPickupWidget.setWindowTitle(QCoreApplication.translate("StandardPickupWidget", u"Item Configuration", None))
        self.priority_label.setText(QCoreApplication.translate("StandardPickupWidget", u"Priority for placement", None))
        self.pickup_name_label.setText(QCoreApplication.translate("StandardPickupWidget", u"Unlimited Beam Ammo", None))
        self.starting_check.setText(QCoreApplication.translate("StandardPickupWidget", u"As starting", None))
        self.vanilla_check.setText(QCoreApplication.translate("StandardPickupWidget", u"In Vanilla", None))
        self.shuffled_spinbox.setSuffix(QCoreApplication.translate("StandardPickupWidget", u" shuffled copies", None))
#if QT_CONFIG(tooltip)
        self.provided_ammo_spinbox.setToolTip(QCoreApplication.translate("StandardPickupWidget", u"<html><head/><body><p>When this item is collected, it also gives this amount of the given ammos.</p><p>This is included in the calculation of how much each pickup of this ammo gives.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

