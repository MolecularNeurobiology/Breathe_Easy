# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'scripts/GUI/ui/ordering_form.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_GroupOrdering(object):
    def setupUi(self, GroupOrdering):
        GroupOrdering.setObjectName("GroupOrdering")
        GroupOrdering.resize(400, 300)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(GroupOrdering)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.title = QtWidgets.QLabel(GroupOrdering)
        self.title.setObjectName("title")
        self.horizontalLayout_2.addWidget(self.title)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.item_list = QtWidgets.QListWidget(GroupOrdering)
        self.item_list.setObjectName("item_list")
        self.horizontalLayout.addWidget(self.item_list)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.up_button = QtWidgets.QPushButton(GroupOrdering)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.up_button.sizePolicy().hasHeightForWidth())
        self.up_button.setSizePolicy(sizePolicy)
        self.up_button.setObjectName("up_button")
        self.verticalLayout.addWidget(self.up_button)
        self.down_button = QtWidgets.QPushButton(GroupOrdering)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.down_button.sizePolicy().hasHeightForWidth())
        self.down_button.setSizePolicy(sizePolicy)
        self.down_button.setObjectName("down_button")
        self.verticalLayout.addWidget(self.down_button)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(GroupOrdering)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(GroupOrdering)
        self.buttonBox.accepted.connect(GroupOrdering.accept) # type: ignore
        self.buttonBox.rejected.connect(GroupOrdering.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(GroupOrdering)

    def retranslateUi(self, GroupOrdering):
        _translate = QtCore.QCoreApplication.translate
        GroupOrdering.setWindowTitle(_translate("GroupOrdering", "Variable Order"))
        self.title.setText(_translate("GroupOrdering", "All Items"))
        self.up_button.setText(_translate("GroupOrdering", "Up"))
        self.down_button.setText(_translate("GroupOrdering", "Down"))
