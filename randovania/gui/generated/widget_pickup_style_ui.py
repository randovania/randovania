# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'widget_pickup_style.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGroupBox, QLabel,
    QSizePolicy, QVBoxLayout, QWidget)

from randovania.gui.lib.scroll_protected import ScrollProtectedComboBox

class Ui_PickupStyleWidget(object):
    def setupUi(self, PickupStyleWidget):
        if not PickupStyleWidget.objectName():
            PickupStyleWidget.setObjectName(u"PickupStyleWidget")
        PickupStyleWidget.resize(534, 116)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PickupStyleWidget.sizePolicy().hasHeightForWidth())
        PickupStyleWidget.setSizePolicy(sizePolicy)
        PickupStyleWidget.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout = QVBoxLayout(PickupStyleWidget)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.pickup_style_box = QGroupBox(PickupStyleWidget)
        self.pickup_style_box.setObjectName(u"pickup_style_box")
        sizePolicy.setHeightForWidth(self.pickup_style_box.sizePolicy().hasHeightForWidth())
        self.pickup_style_box.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QVBoxLayout(self.pickup_style_box)
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.pickup_model_combo = ScrollProtectedComboBox(self.pickup_style_box)
        self.pickup_model_combo.addItem("")
        self.pickup_model_combo.addItem("")
        self.pickup_model_combo.addItem("")
        self.pickup_model_combo.addItem("")
        self.pickup_model_combo.setObjectName(u"pickup_model_combo")

        self.verticalLayout_2.addWidget(self.pickup_model_combo)

        self.pickup_data_source_label = QLabel(self.pickup_style_box)
        self.pickup_data_source_label.setObjectName(u"pickup_data_source_label")

        self.verticalLayout_2.addWidget(self.pickup_data_source_label)

        self.pickup_data_source_combo = ScrollProtectedComboBox(self.pickup_style_box)
        self.pickup_data_source_combo.addItem("")
        self.pickup_data_source_combo.addItem("")
        self.pickup_data_source_combo.addItem("")
        self.pickup_data_source_combo.setObjectName(u"pickup_data_source_combo")

        self.verticalLayout_2.addWidget(self.pickup_data_source_combo)


        self.verticalLayout.addWidget(self.pickup_style_box)


        self.retranslateUi(PickupStyleWidget)

        QMetaObject.connectSlotsByName(PickupStyleWidget)
    # setupUi

    def retranslateUi(self, PickupStyleWidget):
        PickupStyleWidget.setWindowTitle(QCoreApplication.translate("PickupStyleWidget", u"Item Configuration", None))
        self.pickup_style_box.setTitle(QCoreApplication.translate("PickupStyleWidget", u"Pickup style", None))
        self.pickup_model_combo.setItemText(0, QCoreApplication.translate("PickupStyleWidget", u"Use correct item model, scan and name", None))
        self.pickup_model_combo.setItemText(1, QCoreApplication.translate("PickupStyleWidget", u"Use correct scan and name, hide the model", None))
        self.pickup_model_combo.setItemText(2, QCoreApplication.translate("PickupStyleWidget", u"Use correct name, hide the model and scan", None))
        self.pickup_model_combo.setItemText(3, QCoreApplication.translate("PickupStyleWidget", u"Hide the model, scan and name", None))

        self.pickup_data_source_label.setText(QCoreApplication.translate("PickupStyleWidget", u"When hiding some part of the pickup, it's replaced with:", None))
        self.pickup_data_source_combo.setItemText(0, QCoreApplication.translate("PickupStyleWidget", u"Energy Transfer Module/Nothing's data", None))
        self.pickup_data_source_combo.setItemText(1, QCoreApplication.translate("PickupStyleWidget", u"A random item data", None))
        self.pickup_data_source_combo.setItemText(2, QCoreApplication.translate("PickupStyleWidget", u"The data of the pickup in that place", None))

    # retranslateUi

