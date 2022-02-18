# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'form.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Plethysmography(object):
    def setupUi(self, Plethysmography):
        Plethysmography.setObjectName("Plethysmography")
        Plethysmography.resize(3840, 2160)
        Plethysmography.setMinimumSize(QtCore.QSize(1750, 1300))
        Plethysmography.setCursor(QtGui.QCursor(QtCore.Qt.SizeAllCursor))
        Plethysmography.setAcceptDrops(True)
        self.centralwidget = QtWidgets.QWidget(Plethysmography)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.label = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(24)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout_12.addWidget(self.label)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem)
        self.mother_button = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mother_button.sizePolicy().hasHeightForWidth())
        self.mother_button.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.mother_button.setFont(font)
        self.mother_button.setObjectName("mother_button")
        self.horizontalLayout_12.addWidget(self.mother_button)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem1)
        self.horizontalLayout_12.setStretch(0, 3)
        self.horizontalLayout_12.setStretch(1, 1)
        self.horizontalLayout_12.setStretch(2, 5)
        self.horizontalLayout_12.setStretch(3, 3)
        self.gridLayout.addLayout(self.horizontalLayout_12, 0, 0, 1, 1)
        self.verticalLayout_13 = QtWidgets.QVBoxLayout()
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.signal_files = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.signal_files.setFont(font)
        self.signal_files.setObjectName("signal_files")
        self.horizontalLayout.addWidget(self.signal_files)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.check_timestamps = QtWidgets.QPushButton(self.centralwidget)
        self.check_timestamps.setObjectName("check_timestamps")
        self.verticalLayout.addWidget(self.check_timestamps)
        self.necessary_timestamp_box = QtWidgets.QComboBox(self.centralwidget)
        self.necessary_timestamp_box.setObjectName("necessary_timestamp_box")
        self.necessary_timestamp_box.addItem("")
        self.verticalLayout.addWidget(self.necessary_timestamp_box)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.signal_files_list = QtWidgets.QListWidget(self.centralwidget)
        self.signal_files_list.setAcceptDrops(True)
        self.signal_files_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.signal_files_list.setObjectName("signal_files_list")
        self.verticalLayout_4.addWidget(self.signal_files_list)
        self.horizontalLayout_6.addLayout(self.verticalLayout_4)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout()
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_6.addItem(spacerItem2)
        self.metadata = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.metadata.setFont(font)
        self.metadata.setObjectName("metadata")
        self.verticalLayout_6.addWidget(self.metadata)
        self.filemaker_button = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.filemaker_button.setFont(font)
        self.filemaker_button.setObjectName("filemaker_button")
        self.verticalLayout_6.addWidget(self.filemaker_button)
        self.variable_annotation_button = QtWidgets.QPushButton(self.centralwidget)
        self.variable_annotation_button.setObjectName("variable_annotation_button")
        self.verticalLayout_6.addWidget(self.variable_annotation_button)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_6.addItem(spacerItem3)
        self.verticalLayout_6.setStretch(4, 1)
        self.verticalLayout_8.addLayout(self.verticalLayout_6)
        spacerItem4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_8.addItem(spacerItem4)
        self.verticalLayout_7 = QtWidgets.QVBoxLayout()
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.signal_segments = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.signal_segments.setFont(font)
        self.signal_segments.setObjectName("signal_segments")
        self.verticalLayout_7.addWidget(self.signal_segments)
        spacerItem5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_7.addItem(spacerItem5)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_7.addWidget(self.label_2)
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout_7.addWidget(self.line)
        self.breath_parameters = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(8)
        self.breath_parameters.setFont(font)
        self.breath_parameters.setObjectName("breath_parameters")
        self.verticalLayout_7.addWidget(self.breath_parameters)
        self.auto_button = QtWidgets.QPushButton(self.centralwidget)
        self.auto_button.setObjectName("auto_button")
        self.verticalLayout_7.addWidget(self.auto_button)
        self.manual_button = QtWidgets.QPushButton(self.centralwidget)
        self.manual_button.setObjectName("manual_button")
        self.verticalLayout_7.addWidget(self.manual_button)
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_7.addWidget(self.frame)
        spacerItem6 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_7.addItem(spacerItem6)
        self.verticalLayout_8.addLayout(self.verticalLayout_7)
        self.verticalLayout_8.setStretch(0, 2)
        self.verticalLayout_8.setStretch(2, 3)
        self.horizontalLayout_4.addLayout(self.verticalLayout_8)
        self.verticalLayout_11 = QtWidgets.QVBoxLayout()
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.metadata_list = QtWidgets.QListWidget(self.centralwidget)
        self.metadata_list.setAcceptDrops(True)
        self.metadata_list.setObjectName("metadata_list")
        self.verticalLayout_11.addWidget(self.metadata_list)
        self.sections_list = QtWidgets.QListWidget(self.centralwidget)
        self.sections_list.setAcceptDrops(True)
        self.sections_list.setObjectName("sections_list")
        self.verticalLayout_11.addWidget(self.sections_list)
        self.verticalLayout_11.setStretch(0, 1)
        self.verticalLayout_11.setStretch(1, 3)
        self.horizontalLayout_4.addLayout(self.verticalLayout_11)
        self.horizontalLayout_6.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.variable_list = QtWidgets.QListWidget(self.centralwidget)
        self.variable_list.setViewMode(QtWidgets.QListView.ListMode)
        self.variable_list.setObjectName("variable_list")
        self.verticalLayout_5.addWidget(self.variable_list)
        self.breath_list = QtWidgets.QListWidget(self.centralwidget)
        self.breath_list.setAcceptDrops(True)
        self.breath_list.setObjectName("breath_list")
        self.verticalLayout_5.addWidget(self.breath_list)
        self.verticalLayout_5.setStretch(0, 2)
        self.verticalLayout_5.setStretch(1, 3)
        self.horizontalLayout_5.addLayout(self.verticalLayout_5)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        spacerItem7 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem7)
        self.variable_button = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.variable_button.setFont(font)
        self.variable_button.setObjectName("variable_button")
        self.verticalLayout_2.addWidget(self.variable_button)
        spacerItem8 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem8)
        self.breath_files = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.breath_files.setFont(font)
        self.breath_files.setObjectName("breath_files")
        self.verticalLayout_2.addWidget(self.breath_files)
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_2.addWidget(self.label_3)
        self.env_file = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.env_file.setFont(font)
        self.env_file.setObjectName("env_file")
        self.verticalLayout_2.addWidget(self.env_file)
        spacerItem9 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem9)
        self.verticalLayout_2.setStretch(0, 2)
        self.verticalLayout_2.setStretch(2, 4)
        self.verticalLayout_2.setStretch(6, 4)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.horizontalLayout_5.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_5.setStretch(0, 6)
        self.horizontalLayout_5.setStretch(1, 1)
        self.horizontalLayout_6.addLayout(self.horizontalLayout_5)
        self.verticalLayout_13.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout()
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        spacerItem10 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_10.addItem(spacerItem10)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem11 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem11)
        self.verticalLayout_9 = QtWidgets.QVBoxLayout()
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.parallel_box = QtWidgets.QCheckBox(self.centralwidget)
        self.parallel_box.setChecked(True)
        self.parallel_box.setObjectName("parallel_box")
        self.verticalLayout_9.addWidget(self.parallel_box)
        self.py_go = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.py_go.setFont(font)
        self.py_go.setObjectName("py_go")
        self.verticalLayout_9.addWidget(self.py_go)
        self.parallel_combo = QtWidgets.QComboBox(self.centralwidget)
        self.parallel_combo.setObjectName("parallel_combo")
        self.parallel_combo.addItem("")
        self.verticalLayout_9.addWidget(self.parallel_combo)
        self.horizontalLayout_2.addLayout(self.verticalLayout_9)
        spacerItem12 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem12)
        self.verticalLayout_10.addLayout(self.horizontalLayout_2)
        spacerItem13 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_10.addItem(spacerItem13)
        self.horizontalLayout_7.addLayout(self.verticalLayout_10)
        self.hangar = QtWidgets.QTextEdit(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.hangar.setFont(font)
        self.hangar.setObjectName("hangar")
        self.horizontalLayout_7.addWidget(self.hangar)
        self.verticalLayout_12 = QtWidgets.QVBoxLayout()
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        spacerItem14 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_12.addItem(spacerItem14)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        spacerItem15 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem15)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        spacerItem16 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem16)
        self.r_go = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.r_go.setFont(font)
        self.r_go.setObjectName("r_go")
        self.horizontalLayout_8.addWidget(self.r_go)
        spacerItem17 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem17)
        self.verticalLayout_3.addLayout(self.horizontalLayout_8)
        self.parallel_r = QtWidgets.QCheckBox(self.centralwidget)
        self.parallel_r.setChecked(True)
        self.parallel_r.setObjectName("parallel_r")
        self.verticalLayout_3.addWidget(self.parallel_r)
        self.imageformat_group = QtWidgets.QGroupBox(self.centralwidget)
        self.imageformat_group.setObjectName("imageformat_group")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.imageformat_group)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.svg_radioButton = QtWidgets.QRadioButton(self.imageformat_group)
        self.svg_radioButton.setChecked(True)
        self.svg_radioButton.setObjectName("svg_radioButton")
        self.horizontalLayout_10.addWidget(self.svg_radioButton)
        self.jpeg_radioButton = QtWidgets.QRadioButton(self.imageformat_group)
        self.jpeg_radioButton.setObjectName("jpeg_radioButton")
        self.horizontalLayout_10.addWidget(self.jpeg_radioButton)
        self.gridLayout_2.addLayout(self.horizontalLayout_10, 0, 0, 1, 1)
        self.verticalLayout_3.addWidget(self.imageformat_group)
        self.horizontalLayout_9.addLayout(self.verticalLayout_3)
        spacerItem18 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem18)
        self.verticalLayout_12.addLayout(self.horizontalLayout_9)
        spacerItem19 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_12.addItem(spacerItem19)
        self.horizontalLayout_7.addLayout(self.verticalLayout_12)
        self.horizontalLayout_7.setStretch(0, 1)
        self.horizontalLayout_7.setStretch(1, 5)
        self.horizontalLayout_7.setStretch(2, 1)
        self.verticalLayout_13.addLayout(self.horizontalLayout_7)
        self.gridLayout.addLayout(self.verticalLayout_13, 1, 0, 1, 1)
        spacerItem20 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem20, 2, 0, 1, 1)
        Plethysmography.setCentralWidget(self.centralwidget)

        self.retranslateUi(Plethysmography)
        self.breath_files.clicked.connect(Plethysmography.input_directory_r)
        self.r_go.clicked.connect(Plethysmography.r_message)
        self.mother_button.clicked.connect(Plethysmography.mothership_dir)
        self.breath_parameters.clicked.connect(Plethysmography.show_basic)
        self.py_go.clicked.connect(Plethysmography.py_message)
        self.metadata.clicked.connect(Plethysmography.get_metadata)
        self.signal_files.clicked.connect(Plethysmography.get_signal_files)
        self.signal_segments.clicked.connect(Plethysmography.get_autosections)
        self.filemaker_button.clicked.connect(Plethysmography.connect_database)
        self.sections_list.itemDoubleClicked['QListWidgetItem*'].connect(Plethysmography.open_click)
        self.breath_list.itemDoubleClicked['QListWidgetItem*'].connect(Plethysmography.open_click)
        self.variable_button.clicked.connect(Plethysmography.show_variable_config)
        self.check_timestamps.clicked.connect(Plethysmography.timestamp_dict)
        self.manual_button.clicked.connect(Plethysmography.show_manual)
        self.auto_button.clicked.connect(Plethysmography.show_auto)
        self.variable_annotation_button.clicked.connect(Plethysmography.show_annot)
        self.env_file.clicked.connect(Plethysmography.input_directory_r_env)
        self.metadata_list.itemDoubleClicked['QListWidgetItem*'].connect(Plethysmography.open_click)
        self.signal_files_list.itemDoubleClicked['QListWidgetItem*'].connect(Plethysmography.open_click)
        self.variable_list.itemDoubleClicked['QListWidgetItem*'].connect(Plethysmography.open_click)
        QtCore.QMetaObject.connectSlotsByName(Plethysmography)

    def retranslateUi(self, Plethysmography):
        _translate = QtCore.QCoreApplication.translate
        Plethysmography.setWindowTitle(_translate("Plethysmography", "Plethysmography"))
        Plethysmography.setAccessibleDescription(_translate("Plethysmography", "bob"))
        self.label.setText(_translate("Plethysmography", "Plethysmography Analysis Platform"))
        self.mother_button.setText(_translate("Plethysmography", "Default Directory"))
        self.signal_files.setText(_translate("Plethysmography", "Select signal files"))
        self.check_timestamps.setText(_translate("Plethysmography", "Check timestamps"))
        self.necessary_timestamp_box.setItemText(0, _translate("Plethysmography", "Select dataset..."))
        self.metadata.setText(_translate("Plethysmography", "Select metadata file"))
        self.filemaker_button.setText(_translate("Plethysmography", "Filemaker"))
        self.variable_annotation_button.setText(_translate("Plethysmography", "Variable Annotation"))
        self.signal_segments.setText(_translate("Plethysmography", "Select BASSPRO\n"
" settings files"))
        self.label_2.setText(_translate("Plethysmography", "Advanced Settings"))
        self.breath_parameters.setText(_translate("Plethysmography", "Basic Parameters"))
        self.auto_button.setText(_translate("Plethysmography", "Automatic Selection"))
        self.manual_button.setText(_translate("Plethysmography", "Manual Selection"))
        self.variable_button.setText(_translate("Plethysmography", "STAGG configuration\n"
"settings"))
        self.breath_files.setText(_translate("Plethysmography", "Select BASSPRO\n"
"output directory"))
        self.label_3.setText(_translate("Plethysmography", "or"))
        self.env_file.setText(_translate("Plethysmography", "Select R environment"))
        self.parallel_box.setText(_translate("Plethysmography", "Parallel processing"))
        self.py_go.setText(_translate("Plethysmography", "Launch BASSPRO"))
        self.parallel_combo.setItemText(0, _translate("Plethysmography", "Parallel processing settings..."))
        self.r_go.setText(_translate("Plethysmography", "Launch STAGG"))
        self.parallel_r.setText(_translate("Plethysmography", "Send feedback to GUI"))
        self.imageformat_group.setTitle(_translate("Plethysmography", "Image file format"))
        self.svg_radioButton.setText(_translate("Plethysmography", ".svg"))
        self.jpeg_radioButton.setText(_translate("Plethysmography", ".jpeg"))
