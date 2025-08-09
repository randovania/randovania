# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'resource_database_editor.ui'
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
    QTabWidget, QTableView, QTreeWidget, QTreeWidgetItem,
    QWidget)

class Ui_ResourceDatabaseEditor(object):
    def setupUi(self, ResourceDatabaseEditor):
        if not ResourceDatabaseEditor.objectName():
            ResourceDatabaseEditor.setObjectName(u"ResourceDatabaseEditor")
        ResourceDatabaseEditor.resize(400, 300)
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName(u"tab_widget")
        self.tab_item = QTableView()
        self.tab_item.setObjectName(u"tab_item")
        self.tab_widget.addTab(self.tab_item, "")
        self.tab_event = QTableView()
        self.tab_event.setObjectName(u"tab_event")
        self.tab_widget.addTab(self.tab_event, "")
        self.tab_trick = QTableView()
        self.tab_trick.setObjectName(u"tab_trick")
        self.tab_widget.addTab(self.tab_trick, "")
        self.tab_damage = QTableView()
        self.tab_damage.setObjectName(u"tab_damage")
        self.tab_widget.addTab(self.tab_damage, "")
        self.tab_version = QTableView()
        self.tab_version.setObjectName(u"tab_version")
        self.tab_widget.addTab(self.tab_version, "")
        self.tab_misc = QTableView()
        self.tab_misc.setObjectName(u"tab_misc")
        self.tab_widget.addTab(self.tab_misc, "")
        self.tab_template = QTreeWidget()
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.tab_template.setHeaderItem(__qtreewidgetitem)
        self.tab_template.setObjectName(u"tab_template")
        self.tab_widget.addTab(self.tab_template, "")
        ResourceDatabaseEditor.setWidget(self.tab_widget)

        self.retranslateUi(ResourceDatabaseEditor)

        self.tab_widget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(ResourceDatabaseEditor)
    # setupUi

    def retranslateUi(self, ResourceDatabaseEditor):
        ResourceDatabaseEditor.setWindowTitle(QCoreApplication.translate("ResourceDatabaseEditor", u"Resource Database", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_item), QCoreApplication.translate("ResourceDatabaseEditor", u"Item", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_event), QCoreApplication.translate("ResourceDatabaseEditor", u"Event", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_trick), QCoreApplication.translate("ResourceDatabaseEditor", u"Trick", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_damage), QCoreApplication.translate("ResourceDatabaseEditor", u"Damage", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_version), QCoreApplication.translate("ResourceDatabaseEditor", u"Version", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_misc), QCoreApplication.translate("ResourceDatabaseEditor", u"Misc", None))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.tab_template), QCoreApplication.translate("ResourceDatabaseEditor", u"Templates", None))
    # retranslateUi

