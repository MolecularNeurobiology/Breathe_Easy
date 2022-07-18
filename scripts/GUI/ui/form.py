# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'form.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets

class DeleteButton(QtWidgets.QPushButton):
    def __init__(self, *args):
        super().__init__(*args)
        self.setStyleSheet("""background-color: #f99;""")
                           #   border-radius: 4px;
                           #   border-top-left-radius: 0;
                           #   border-bottom-left-radius: 0;
                           #   padding: 4px;
        self.setText("X")
        self.setMaximumWidth(22)
        self.setMinimumHeight(20)
        self.hide()

class DeleteLayout(QtWidgets.QHBoxLayout):
    def __init__(self, button, *args):
        super().__init__(*args)
        self.setSpacing(1)
        self.addWidget(button)
        self.delete_button = DeleteButton()
        self.addWidget(self.delete_button)


class Ui_Plethysmography(object):
    def setupUi(self, Plethysmography):
        Plethysmography.setObjectName("Plethysmography")
        Plethysmography.resize(3840, 2160)
        Plethysmography.setMinimumSize(QtCore.QSize(1500, 900))
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
        font.setPointSize(20)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout_12.addWidget(self.label)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem)

        self.output_dir_button = QtWidgets.QPushButton(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.output_dir_button.sizePolicy().hasHeightForWidth())
        self.output_dir_button.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.output_dir_button.setFont(font)
        self.output_dir_button.setObjectName("output_dir_button")
        self.horizontalLayout_12.addWidget(self.output_dir_button)

        self.output_path_display = QtWidgets.QLineEdit(self.centralwidget)
        self.output_path_display.setObjectName("output_path_display")
        self.output_path_display.setReadOnly(True)
        self.horizontalLayout_12.addWidget(self.output_path_display)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem2)

        self.horizontalLayout_12.setStretch(0, 3)
        self.horizontalLayout_12.setStretch(1, 2)
        self.horizontalLayout_12.setStretch(2, 5)
        self.horizontalLayout_12.setStretch(3, 3)
        self.horizontalLayout_12.setStretch(4, 2)
        self.gridLayout.addLayout(self.horizontalLayout_12, 0, 0, 1, 1)
        self.verticalLayout_13 = QtWidgets.QVBoxLayout()
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.timestepLayout = QtWidgets.QHBoxLayout()
        self.timestepLayout.setObjectName("timestepLayout")
        self.check_timestamps = QtWidgets.QPushButton(self.centralwidget)
        self.check_timestamps.setObjectName("check_timestamps")
        self.timestepLayout.addWidget(self.check_timestamps)

        self.necessary_timestamp_box = QtWidgets.QComboBox(self.centralwidget)
        self.necessary_timestamp_box.setObjectName("necessary_timestamp_box")
        self.necessary_timestamp_box.addItem("")
        self.timestepLayout.addWidget(self.necessary_timestamp_box)
        self.horizontalLayout.addLayout(self.timestepLayout)

        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.signal_files_list = QtWidgets.QListWidget(self.centralwidget)
        self.signal_files_list.setAcceptDrops(True)
        self.signal_files_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.signal_files_list.setObjectName("signal_files_list")
        self.verticalLayout_4.addWidget(self.signal_files_list)

        self.signal_files_button_layout = QtWidgets.QHBoxLayout()
        spacerleft = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.signal_files_button_layout.addItem(spacerleft)

        self.signal_files_button = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.signal_files_button.setFont(font)
        self.signal_files_button.setObjectName("signal_files_button")
        self.signal_files_button.setMinimumWidth(200)
        self.signal_files_button.setMinimumHeight(30)
        self.signal_files_button_layout.addWidget(self.signal_files_button)

        spacerright = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.signal_files_button_layout.addItem(spacerright)

        self.verticalLayout_4.addLayout(self.signal_files_button_layout)

        self.horizontalLayout_6.addLayout(self.verticalLayout_4)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout()
        self.verticalLayout_8.setObjectName("verticalLayout_8")

        spacerItem4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout_8.addItem(spacerItem4)

        self.metadata_button = QtWidgets.QPushButton(self.centralwidget)
        self.metadata_button.setObjectName("metadata_button")
        self.meta_layout = DeleteLayout(self.metadata_button)
        self.verticalLayout_8.addLayout(self.meta_layout)

        spacerItem5 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_8.addItem(spacerItem5)
        self.basspro_settings_button = QtWidgets.QPushButton(self.centralwidget)
        self.basspro_settings_button.setObjectName("signal_segments")
        self.verticalLayout_8.addWidget(self.basspro_settings_button)
        spacerItem6 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_8.addItem(spacerItem6)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_8.addWidget(self.label_2)
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout_8.addWidget(self.line)

        self.auto_button = QtWidgets.QPushButton(self.centralwidget)
        self.auto_button.setObjectName("auto_button")
        # Add delete option to button
        self.auto_layout = DeleteLayout(self.auto_button)
        self.verticalLayout_8.addLayout(self.auto_layout)

        self.manual_button = QtWidgets.QPushButton(self.centralwidget)
        self.manual_button.setObjectName("manual_button")
        self.manual_layout = DeleteLayout(self.manual_button)
        self.verticalLayout_8.addLayout(self.manual_layout)

        self.breath_parameters = QtWidgets.QPushButton(self.centralwidget)
        self.breath_parameters.setObjectName("breath_parameters")
        self.basic_layout = DeleteLayout(self.breath_parameters)
        self.verticalLayout_8.addLayout(self.basic_layout)

        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_8.addWidget(self.frame)
        spacerItem7 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_8.addItem(spacerItem7)
        # self.verticalLayout_8.setStretch(0, 2)
        self.verticalLayout_8.setStretch(2, 1)
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
        spacerItem8 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem8)

        self.stagg_settings_button = QtWidgets.QPushButton(self.centralwidget)
        self.stagg_settings_button.setObjectName("stagg_settings_button")
        self.stagg_settings_layout = DeleteLayout(self.stagg_settings_button)
        self.verticalLayout_2.addLayout(self.stagg_settings_layout)

        spacerItem9 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem9)
        self.breath_files_button = QtWidgets.QPushButton(self.centralwidget)
        self.breath_files_button.setObjectName("breath_files_button")
        self.verticalLayout_2.addWidget(self.breath_files_button)
        spacerItem10 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem10)
        self.verticalLayout_2.setStretch(0, 2)
        self.verticalLayout_2.setStretch(2, 4)
        self.verticalLayout_2.setStretch(4, 4)
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
        spacerItem11 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_10.addItem(spacerItem11)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem12 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem12)
        self.verticalLayout_9 = QtWidgets.QVBoxLayout()
        self.verticalLayout_9.setObjectName("verticalLayout_9")

        basspro_button_layout = QtWidgets.QHBoxLayout()
        spacerleft = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        basspro_button_layout.addItem(spacerleft)

        self.basspro_launch_button = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.basspro_launch_button.setFont(font)
        self.basspro_launch_button.setObjectName("basspro_launch_button")
        basspro_button_layout.addWidget(self.basspro_launch_button)

        spacerright = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        basspro_button_layout.addItem(spacerright)

        self.verticalLayout_9.addLayout(basspro_button_layout)

        hlayout = QtWidgets.QHBoxLayout()
        spacerleft = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        hlayout.addItem(spacerleft)

        label = QtWidgets.QLabel("# Cores:")
        hlayout.addWidget(label)

        self.parallel_combo = QtWidgets.QComboBox(self.centralwidget)
        self.parallel_combo.setObjectName("parallel_combo")
        self.parallel_combo.setMaximumWidth(50)
        hlayout.addWidget(self.parallel_combo)

        spacerright = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        hlayout.addItem(spacerright)

        self.verticalLayout_9.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        spacerleft = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        hlayout.addItem(spacerleft)

        self.full_run_checkbox = QtWidgets.QCheckBox(self.centralwidget)
        self.full_run_checkbox.setObjectName("full_run_checkbox")
        self.full_run_checkbox.setText("Full Run")
        hlayout.addWidget(self.full_run_checkbox)

        spacerright = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        hlayout.addItem(spacerright)

        self.verticalLayout_9.addLayout(hlayout)

        self.horizontalLayout_2.addLayout(self.verticalLayout_9)
        spacerItem13 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem13)
        self.verticalLayout_10.addLayout(self.horizontalLayout_2)
        spacerItem14 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_10.addItem(spacerItem14)
        self.horizontalLayout_7.addLayout(self.verticalLayout_10)
        self.hangar = QtWidgets.QTextEdit(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.hangar.setFont(font)
        self.hangar.setObjectName("hangar")
        self.horizontalLayout_7.addWidget(self.hangar)
        self.verticalLayout_12 = QtWidgets.QVBoxLayout()
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        spacerItem15 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_12.addItem(spacerItem15)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        spacerItem16 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem16)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")

        spacerItem17 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem17)

        self.stagg_launch_button = QtWidgets.QPushButton(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.stagg_launch_button.setFont(font)
        self.stagg_launch_button.setObjectName("stagg_launch_button")
        self.horizontalLayout_8.addWidget(self.stagg_launch_button)
        spacerItem18 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem18)

        self.verticalLayout_3.addLayout(self.horizontalLayout_8)
        self.imageformat_group = QtWidgets.QGroupBox(self.centralwidget)
        self.imageformat_group.setObjectName("imageformat_group")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.imageformat_group)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.svg_radioButton = QtWidgets.QRadioButton(self.imageformat_group)
        self.svg_radioButton.setObjectName("svg_radioButton")
        self.horizontalLayout_10.addWidget(self.svg_radioButton)
        self.jpeg_radioButton = QtWidgets.QRadioButton(self.imageformat_group)
        self.jpeg_radioButton.setChecked(True)
        self.jpeg_radioButton.setObjectName("jpeg_radioButton")
        self.horizontalLayout_10.addWidget(self.jpeg_radioButton)
        self.gridLayout_2.addLayout(self.horizontalLayout_10, 0, 0, 1, 1)
        self.verticalLayout_3.addWidget(self.imageformat_group)
        self.horizontalLayout_9.addLayout(self.verticalLayout_3)
        spacerItem19 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_9.addItem(spacerItem19)
        self.verticalLayout_12.addLayout(self.horizontalLayout_9)
        spacerItem20 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_12.addItem(spacerItem20)
        self.horizontalLayout_7.addLayout(self.verticalLayout_12)
        self.horizontalLayout_7.setStretch(0, 1)
        self.horizontalLayout_7.setStretch(1, 5)
        self.horizontalLayout_7.setStretch(2, 1)
        self.verticalLayout_13.addLayout(self.horizontalLayout_7)
        self.gridLayout.addLayout(self.verticalLayout_13, 1, 0, 1, 1)
        spacerItem21 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem21, 2, 0, 1, 1)
        Plethysmography.setCentralWidget(self.centralwidget)

        self.retranslateUi(Plethysmography)
        
        ## CALLBACKS ##
        #   basspro
        self.signal_files_button.clicked.connect(Plethysmography.get_signal_files)
        self.metadata_button.clicked.connect(Plethysmography.show_annot)
        self.basspro_settings_button.clicked.connect(Plethysmography.get_autosections)
        self.output_dir_button.clicked.connect(Plethysmography.select_output_dir)
        self.basspro_launch_button.clicked.connect(Plethysmography.basspro_run)

        #   stagg
        self.stagg_launch_button.clicked.connect(Plethysmography.stagg_run)
        self.breath_files_button.clicked.connect(Plethysmography.select_stagg_input_files)
        self.stagg_settings_button.clicked.connect(Plethysmography.prepare_stagg_settings)
        self.auto_button.clicked.connect(Plethysmography.show_auto)

        self.breath_parameters.clicked.connect(Plethysmography.show_basic)
        self.sections_list.itemDoubleClicked['QListWidgetItem*'].connect(Plethysmography.open_click)
        self.breath_list.itemDoubleClicked['QListWidgetItem*'].connect(Plethysmography.open_click)
        self.check_timestamps.clicked.connect(Plethysmography.timestamp_dict)
        self.manual_button.clicked.connect(Plethysmography.show_manual)
        self.metadata_list.itemDoubleClicked['QListWidgetItem*'].connect(Plethysmography.open_click)
        self.signal_files_list.itemDoubleClicked['QListWidgetItem*'].connect(Plethysmography.open_click)
        self.variable_list.itemDoubleClicked['QListWidgetItem*'].connect(Plethysmography.open_click)
        QtCore.QMetaObject.connectSlotsByName(Plethysmography)

    def retranslateUi(self, Plethysmography):
        _translate = QtCore.QCoreApplication.translate
        Plethysmography.setWindowTitle(_translate("Plethysmography", "Plethysmography"))
        Plethysmography.setAccessibleDescription(_translate("Plethysmography", "bob"))
        self.label.setText(_translate("Plethysmography", "BreatheEasy"))
        self.output_dir_button.setText(_translate("Plethysmography", "Select output directory"))
        self.signal_files_button.setText(_translate("Plethysmography", "Select signal files"))
        self.check_timestamps.setText(_translate("Plethysmography", "Check timestamps"))
        self.necessary_timestamp_box.setItemText(0, _translate("Plethysmography", "Select dataset..."))
        self.metadata_button.setText(_translate("Plethysmography", "Select metadata"))
        self.basspro_settings_button.setText(_translate("Plethysmography", "Select BASSPRO\nsettings files"))
        self.label_2.setText(_translate("Plethysmography", "Advanced Settings"))
        self.auto_button.setText(_translate("Plethysmography", "Automatic Selection"))
        self.manual_button.setText(_translate("Plethysmography", "Manual Selection"))
        self.breath_parameters.setText(_translate("Plethysmography", "Basic Settings"))
        self.stagg_settings_button.setText(_translate("Plethysmography", "Select STAGG settings"))
        self.breath_files_button.setText(_translate("Plethysmography", "Select STAGG\n"
" input files"))
        self.basspro_launch_button.setText(_translate("Plethysmography", "Launch BASSPRO"))
        self.stagg_launch_button.setText(_translate("Plethysmography", "Launch STAGG"))
        self.imageformat_group.setTitle(_translate("Plethysmography", "Image file format"))
        self.svg_radioButton.setText(_translate("Plethysmography", ".svg"))
        self.jpeg_radioButton.setText(_translate("Plethysmography", ".jpeg"))
