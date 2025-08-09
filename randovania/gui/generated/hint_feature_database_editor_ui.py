# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'hint_feature_database_editor.ui'
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
from PySide6.QtWidgets import (QApplication, QDockWidget, QHeaderView, QSizePolicy,
    QTableView, QWidget)

class Ui_HintFeatureDatabaseEditor(object):
    def setupUi(self, HintFeatureDatabaseEditor):
        if not HintFeatureDatabaseEditor.objectName():
            HintFeatureDatabaseEditor.setObjectName(u"HintFeatureDatabaseEditor")
        HintFeatureDatabaseEditor.resize(400, 300)
        self.feature_table = QTableView()
        self.feature_table.setObjectName(u"feature_table")
        HintFeatureDatabaseEditor.setWidget(self.feature_table)

        self.retranslateUi(HintFeatureDatabaseEditor)

        QMetaObject.connectSlotsByName(HintFeatureDatabaseEditor)
    # setupUi

    def retranslateUi(self, HintFeatureDatabaseEditor):
        HintFeatureDatabaseEditor.setWindowTitle(QCoreApplication.translate("HintFeatureDatabaseEditor", u"Hint Features", None))
    # retranslateUi

