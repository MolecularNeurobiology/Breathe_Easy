#%%
#region Libraries
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5 import uic
from form import Ui_Plethysmography
from thorbass import Ui_Thorbass
from thumbass import Ui_Thumbass
from thinbass import Ui_Thinbass
from config_form import Ui_Config
from custom_config import Ui_Custom
from manual_form import Ui_Manual
from auto_form import Ui_Auto
from basic_form import Ui_Basic
from stagg_form import Ui_Stagg
from auto_simp_form import Ui_Auto_simp
import csv
import glob
import sip
from pathlib import Path, PurePath
import subprocess
from subprocess import PIPE, Popen
import datetime
import time
import os
import copy
import json
import pyodbc
import tkinter
import tkinter.filedialog
import tkinter as tk 
from tkinter import N, ttk
import shutil
import pandas as pd
import threading
import re
# import asyncio
import multiprocessing
import MainGUIworker
import AnnotGUI
from bs4 import BeautifulSoup as bs

#endregion

#%%
#region classes
class AlignDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter

class StudySelector(): # changed the organization of this a bit, need to test
    def __init__(self,Exp_List):
        self.study="unknown"
        self.Exp_List=Exp_List
        # Creating tkinter window 
        self.window = tk.Tk() 
        self.window.geometry('1100x500') 
        
        # Label 
        ttk.Label(self.window, text = "Select Study:",  
                font = ("MS Shell Dlg", 12)).grid(column = 0,  
                row = 15, padx = 10, pady = 25) 
          
        n = tk.StringVar() 
        self.exp_choice = ttk.Combobox(self.window, width = 60,  
                                    textvariable = n) 
          
        # Adding combobox drop down list 
        self.exp_choice['values'] = [i[0] for i in Exp_List]
          
        self.exp_choice.grid(column = 1, row = 15) 
          
        # Shows unknown as a self.AnalysisParameters value 
        self.exp_choice.current(len(Exp_List)-1)
        
        def printvariable(self=self): #
            #This function prints the option selected
            self.study=self.exp_choice.get()
            print (self.exp_choice.get())
            self.window.destroy()  
            
        #create a button widget called btn
        self.btn = tk.Button(self.window, text="     Select     ", command=printvariable)
        self.btn.grid(column=0,row = 30, padx=10, pady=25)
          
        self.window.mainloop()

class Worker_Single(QtCore.QObject):
    # This is the Qobject we will pass to the thread so avoid 
    # QObject::setParent: Cannot set parent, new parent is in a different thread
    # error. 

    start = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self,function):
        super(Worker_Single,self).__init__()
        self.function = function
        self.start.connect(self.run)
    
    # this decorator lets Qt check the location of the worker instance when the signal is emitted so
    # that emitting the signal after moveToThread executes the slot in the worker thread
    # regardless of when the connection was made to moveToThread. Without it, Qt freezes the
    # location of the worker instance to when the connection was made. If done before moveToThread
    # the worker instance is bound to the main thread. This helps it to know that run should be happening
    # in the new thread because the signal is testy.started and run is the slot for that signal.
    @pyqtSlot()
    def run(self):
        print('worker thread id',threading.get_ident())
        print("worker process id", os.getpid())
        self.function()
        self.connect()
        self.finished.emit()
#endregion

class Thinbass(QDialog,Ui_Thinbass):
    """
    Standard dialog to help protect people from themselves.
    """
    def __init__(self,Plethysmography):
        super(Thinbass, self).__init__()
        self.pleth = Plethysmography
        # self.label = QLabel("Another Window % d" % randint(0,100))
        self.setupUi(self)
        self.setWindowTitle("Variables list sources")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        # self.pleth = Plethysmography
        # self.message_received()
    
    def settings(self):
        print("thinbass.settings()")
        self.pleth.test_configuration()
        try:
            self.pleth.variable_configuration()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
        self.pleth.v.show()
    
    def output(self):
        print("thinbass.output()")
        try:
            first = next(file for file in glob.glob(f'{self.pleth.input_dir_r}/*.json'))
            with open(first) as first_json:
                bp_output = json.load(first_json)
            for k in bp_output.keys():
                self.pleth.breath_df.append(k)
            try:
                self.variable_configuration()
                self.v.show()
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            pass

#region Thumbass
class Thumbass(QWidget, Ui_Thumbass):
    """
    Standard dialog to help protect people from themselves.
    """
    def __init__(self,Plethysmography):
        super(Thumbass, self).__init__()
        # self.label = QLabel("Another Window % d" % randint(0,100))
        self.setupUi(self)
        self.setWindowTitle("Nailed it.")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.label.setOpenExternalLinks(True)
        self.pleth = Plethysmography
        # self.message_received()
    
    def message_received(self,title,words):
        print("thumbass.message_received()")
        self.setWindowTitle(title)
        self.label.setText(words)
        # self.browser.setPlainText(words)
#endregion

#region Thorbass
class Thorbass(QDialog,Ui_Thorbass):
    """
    Standard dialog to help protect people from themselves.
    """
    def __init__(self,Plethysmography):
        super(Thorbass, self).__init__()
        self.pleth = Plethysmography
        # self.label = QLabel("Another Window % d" % randint(0,100))
        self.setupUi(self)
        self.setWindowTitle("Nailed it.")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        # self.pleth = Plethysmography
        # self.message_received()
    
    def message_received(self,title,words,new,opens):
        print("thorbass.message_received()")
        self.setWindowTitle(title)
        self.label.setText(words)
        self.new_button.clicked.connect(new)
        self.open_button.clicked.connect(opens)

    def new_variable_config(self):
        print("thorbass.new_variable_config()")
        self.pleth.new_variable_config()
    
    def get_variable_config(self):
        print("thorbass.get_variable_config()")
        self.pleth.get_variable_config()
    
    def new_manual_file(self):
        print("thorbass.new_manual_file()")
        self.pleth.m.new_manual_file()

    def load_manual_file(self):
        print("thorbass.load_manual_file()")
        self.pleth.m.load_manual_file()
        
        # self.browser.setPlainText(words)
#endregion

#region class Basic Parameters
class Basic(QWidget, Ui_Basic):
    def __init__(self,Plethysmography):
        super(Basic, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Basic BASSPRO settings")
        self.pleth = Plethysmography
        # self.isActiveWindow()
        self.isMaximized()
        self.setup_variables()
        self.setup_tabs()
        self.path = ""
        
    def setup_variables(self):
        print("basic.setup_variables()")
        self.basic_dict = self.pleth.bc_config['Dictionaries']['AP']['default']
        self.widgy = {self.basic_reference:[self.help_minTI,self.help_minPIF,self.help_minPEF,self.help_TTwin,self.help_SIGHwin,self.help_minAplTT,self.help_minApsTT],
        self.rig_reference:[self.help_ConvertTemp,self.help_ConvertCO2,self.help_ConvertO2,self.help_Flowrate,self.help_Roto_x,self.help_Roto_y,self.help_chamber_temp_cutoffs,self.help_chamber_temperature_units,self.help_chamber_temperature_default,self.help_chamber_temperature_trim_size,self.help_chamber_temperature_narrow_fix],
        self.crude_reference: [self.help_per500win,self.help_perX,self.help_maxPer500,self.help_maximum_DVTV,self.help_apply_smoothing_filter,self.help_maxTV,self.help_maxVEVO2]}

        self.lineEdits = {self.lineEdit_minimum_TI: "minimum_TI", 
                    self.lineEdit_minimum_PIF: "minimum_PIF",
                    self.lineEdit_minimum_PEF: "minimum_PEF", 
                    self.lineEdit_apnea_window: "apnea_window", 
                    self.lineEdit_percent_X_window: "percent_X_window", 
                    self.lineEdit_percent_X_value: "percent_X_value",
                    self.lineEdit_maximum_percent_X: "maximum_percent_X", 
                    self.lineEdit_maximum_DVTV: "maximum_DVTV",
                    self.lineEdit_sigh_window: "sigh_window",
                    self.lineEdit_apply_smoothing_filter: "apply_smoothing_filter",
                    self.lineEdit_temperature_calibration_factor: "temperature_calibration_factor",
                    self.lineEdit_CO2_calibration_factor: "CO2_calibration_factor",
                    self.lineEdit_O2_calibration_factor: "O2_calibration_factor",
                    self.lineEdit_flowrate: "flowrate",
                    self.lineEdit_rotometer_standard_curve_readings: "rotometer_standard_curve_readings",
                    self.lineEdit_rotometer_standard_curve_flowrates: "rotometer_standard_curve_flowrates",
                    self.lineEdit_minimum_apnea_duration_x_local_TT: "minimum_apnea_duration_x_local_TT",
                    self.lineEdit_minimum_sigh_amplitude_x_local_VT: "minimum_sigh_amplitude_x_local_VT",
                    self.lineEdit_chamber_temperature_units: "chamber_temperature_units",
                    self.lineEdit_chamber_temperature_default: "chamber_temperature_default",
                    self.lineEdit_chamber_temperature_trim_size: "chamber_temperature_trim_size",
                    self.lineEdit_chamber_temperature_narrow_fix: "chamber_temperature_narrow_fix",
                    self.lineEdit_chamber_temp_cutoffs: "chamber_temp_cutoffs",
                    self.lineEdit_maxTV: "maxTV",
                    self.lineEdit_maxVEVO2: "maxVEVO2"
        }
        
        self.resets = [self.reset_minimum_TI,
                        self.reset_minimum_PIF,
                        self.reset_minimum_PEF,
                        self.reset_apnea_window,
                        self.reset_percent_X_window,
                        self.reset_percent_X_value,
                        self.reset_maximum_percent_X,
                        self.reset_maximum_DVTV,
                        self.reset_minimum_apnea_duration_x_local_TT,
                        self.reset_minimum_sigh_amplitude_x_local_VT,
                        self.reset_sigh_window,
                        self.reset_apply_smoothing_filter,
                        self.reset_temperature_calibration_factor,
                        self.reset_CO2_calibration_factor,
                        self.reset_O2_calibration_factor,
                        self.reset_flowrate,
                        self.reset_rotometer_standard_curve_readings,
                        self.reset_rotometer_standard_curve_flowrates,
                        self.reset_chamber_temp_cutoffs,
                        self.reset_chamber_temperature_units,
                        self.reset_chamber_temperature_default,
                        self.reset_chamber_temperature_trim_size,
                        self.reset_chamber_temperature_narrow_fix,
                        self.reset_maxTV,
                        self.reset_maxVEVO2
                        ]

        for v in self.widgy.values():
            for vv in v:
                vv.clicked.connect(self.reference_event)
                
        for r in self.resets:
            r.clicked.connect(self.reset_event)
        
        for l in self.lineEdits:
            l.textChanged.connect(self.update_table_event)
        
        # for r in range(self.view_tab.rowCount()):
        #     self.view_tab.cellChanged.connect(self.update_tabs)

    def setup_tabs(self):
        print("basic.setup_tabs()")
        print(self.pleth.basicap)
        # Populate lineEdit widgets with default basic parameter values from breathcaller configuration file:
        self.basic_dict = self.pleth.bc_config['Dictionaries']['AP']['default']
        for widget in self.lineEdits:
            # print(widget)
            # print(self.lineEdits[widget])
            # print(self.pleth.bc_config['Dictionaries']['AP']['default'])
            # print(self.pleth.bc_config['Dictionaries']['AP']['default'][self.lineEdits[widget]])
            widget.setText(str(self.pleth.bc_config['Dictionaries']['AP']['default'][self.lineEdits[widget]]))

        if self.pleth.basicap != "":
            if Path(self.pleth.basicap).exists():
                self.basic_df = pd.read_csv(self.pleth.basicap)
        else:
            self.basic_df = pd.DataFrame.from_dict(self.basic_dict,orient='index').reset_index()
            self.basic_df.columns = ['Parameters','Settings']
            # Populate table of summary tab:
        self.populate_table(self.basic_df,self.view_tab)
    
    def reference_event(self):
        sbutton = self.sender()
        self.populate_reference(sbutton.objectName())
    
    def reset_event(self):
        sbutton = self.sender()
        self.reset_parameter(sbutton.objectName())
    
    def update_table_event(self):
        sbutton = self.sender()
        self.update_table(sbutton.objectName())

    def populate_reference(self,butt):
        for k,v in self.widgy.items():
            for vv in v:
                if vv.objectName() == str(butt):
                    k.setPlainText(self.pleth.rc_config['References']['Definitions'][butt.replace("help_","")])
                    k.setOpenExternalLinks(True)
   
    def populate_table(self,frame,table):
        print("basic.populate_table()")
        # Populate tablewidgets with views of uploaded csv. Currently editable.
        table.setColumnCount(len(frame.columns))
        table.setRowCount(len(frame))
        for col in range(table.columnCount()):
            for row in range(table.rowCount()):
                table.setItem(row,col,QTableWidgetItem(str(frame.iloc[row,col])))
                table.item(row,0).setFlags(Qt.ItemIsEditable)
        table.setHorizontalHeaderLabels(frame.columns)
        self.view_tab.cellChanged.connect(self.update_tabs)
        self.view_tab.resizeColumnsToContents()
        self.view_tab.resizeRowsToContents()

    def update_table(self,donor):
        print("basic.update_table()")
        for l in self.lineEdits:
            if donor == l.objectName():
                d = l
        for row in range(self.view_tab.rowCount()):
            if self.view_tab.item(row,0).text() == donor.replace("lineEdit_",""):
                self.view_tab.item(row,1).setText(d.text())
        
    def update_tabs(self):
        print("basic.update_tabs()")
        for row in range(self.view_tab.rowCount()):
            for l in self.lineEdits:
                if self.view_tab.item(row,0).text() == l.objectName().replace("lineEdit_",""):
                    l.setText(self.view_tab.item(row,1).text())

    def reset_parameter(self,butts):
        print("basic.reset_parameter()")
        for widget in self.lineEdits:
            if widget.objectName().replace("lineEdit_","") == str(butts).replace("reset_",""):
                widget.setText(str(self.basic_dict[self.lineEdits[widget]]))

    def get_parameter(self):
        print("basic.get_parameter()")
        for k,v in self.lineEdits.items():
            self.pleth.bc_config['Dictionaries']['AP']['current'].update({v:k.text()})
        self.basic_df = pd.DataFrame.from_dict(self.pleth.bc_config['Dictionaries']['AP']['current'],orient='index').reset_index()
        self.basic_df.columns = ['Parameter','Setting']
    
    def save_checker(self,folder,title):
        print("basic.save_checker()")
        if folder == "":
            path = QFileDialog.getSaveFileName(self, 'Save BASSPRO basic parameters file', f"basics_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}", ".csv(*.csv))")[0]
            if not path:
                print("dialog cancelled")
            else:
                self.path = path
        else:
            self.path = os.path.join(folder, f"{title}.csv")
    
    def saveas_basic_path(self):
        print("basic.saveas_basic_path()")
        self.get_parameter()
        if self.pleth.mothership == "":
            dire = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/")
        else:
            dire = self.pleth.mothership
        path = QFileDialog.getSaveFileName(self, 'Save BASSPRO basic parameters file', dire+f"basics_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}", ".csv(*.csv))")[0]
        try:
            print(path)
            self.path = path
            self.actual_saving()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print("saveas_basic_path didn't work")

    def save_basic_path(self):
        print("basic.save_basic_path()")
        self.get_parameter()
        # self.save_checker(self.pleth.mothership,"basics")
        try:
            if self.pleth.mothership == "":
                self.path = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/basics.csv")
                # self.saveas_basic_path()
            else:
                self.path = os.path.join(self.pleth.mothership, f"basics.csv")
            self.actual_saving()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            self.saveas_basic_path()
    
    def actual_saving(self):
        print("basic.actual_saving_basic()")
        print(self.pleth.basicap)
        self.pleth.basicap = self.path
        # Saving the dataframes holding the configuration preferences to csvs and assigning them their paths:
        try:
            self.basic_df.set_index('Parameter').to_csv(self.pleth.basicap)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print("actual saving basic to designated path (be it save or saveas) didn't work")
        
        # Copying current settings for appropriate entry in breathcaller_config:
        # new_current = pd.DataFrame.to_json(self.basic_df.set_index("index"))
        # self.pleth.bc_config['Dictionaries']['AP']['current'].update(new_current)

        with open(f'{Path(__file__).parent}/breathcaller_config.json','w') as bconfig_file:
            json.dump(self.pleth.bc_config,bconfig_file)
        
        print(self.pleth.breath_df)
        if self.pleth.breath_df != []:
            self.pleth.update_breath_df()
        print(self.pleth.breath_df)
        if self.pleth.basicap != "":
        # Clearing the sections panel of the mainGUI and adding to it to reflect changes:
            for item in self.pleth.sections_list.findItems("basic",Qt.MatchContains):
                self.pleth.sections_list.takeItem(self.pleth.sections_list.row(item))
            if self.pleth.autosections != "" or self.pleth.mansections != "":
                for item in self.pleth.sections_list.findItems("selected",Qt.MatchContains):
                    self.pleth.sections_list.takeItem(self.pleth.sections_list.row(item))
            self.pleth.sections_list.addItem(self.pleth.basicap)
            self.pleth.hangar.append("BASSPRO basic settings files saved.")

    def load_basic_file(self):
        print("basic.load_basic_file()")
        # if Path(self.pleth.mothership).exists():
        #     load_path = self.pleth.mothership
        # else:
        #     load_path = str(Path.home())

        # Opens open file dialog
        file = QFileDialog.getOpenFileName(self, 'Select breathcaller configuration file to edit basic parameters:', str(self.pleth.mothership))

        # If you the file you chose sucks, the GUI won't crap out.
        try:
        # if not file[0]:
        #     print("that didn't work")
            if Path(file[0]).suffix == ".json":
                # Access configuration settings for the breathcaller in breathcaller_config.json:
                # with open(file[0]) as bconfig_file:
                print("basic load json")
                self.basic_df = pd.DataFrame.from_dict(self.pleth.bc_config['Dictionaries']['AP']['current'],orient='index').reset_index()
                self.basic_df.columns = ['Parameter','Setting']
                # self.populate_table(self.basic_df,self.view_tab)
            elif Path(file[0]).suffix == ".csv":
                print("basic load csv")
                self.basic_df = pd.read_csv(file[0])
                # self.populate_table(self.basic_df,self.view_tab)
            elif Path(file[0]).suffix == ".xlsx":
                print("basic load xlsx")
                self.basic_df = pd.read_excel(file[0])
            self.populate_table(self.basic_df,self.view_tab)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            reply = QMessageBox.information(self, 'Incorrect file format', 'The selected file is not in the correct format. Only .csv, .xlsx, or .JSON files are accepted.\nWould you like to select a different file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.load_basic_file()
        # self.populate_table(self.basic_df,self.view_tab)
            # with open(file[0],mode='r') as bd:
            #     reader = csv.reader(bd)
            #     next(reader)
                
    def load_basic_current(self):
        print("basic.load_basic_current()")
        self.basic_dict = self.pleth.bc_config['Dictionaries']['AP']['current']
        self.setup_tabs()
        
#endregion

#region class Auto Sections
class Auto(QWidget, Ui_Auto):
    def __init__(self,Plethysmography):
        super(Auto, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Automated sections file creation")
        self.pleth = Plethysmography
        # self.isActiveWindow()
        self.isMaximized()
        
        # self.setup_variables()
        # self.setup_tabs()
        # Grab the relevant labels dicionary from the reference config json file to provide the relationships between tabs, sections, and widgets so that one functions can create the lineEdit tables throughout the subGUI. However, this renders the list order of the labels within the dictionary (the value of the key in the lowest level of the nested dictionary is a list) as the sole determinant of correct order when populating. The labels - OH I COULD MAKE THE LABELS DYNAMIC TOOOOOOO, eh later - no, no I should do that, balls, well I already have the dictionary of actual labels so YES all right this is happening. Ok, so scratch that warning, I'm adding the labels to the widgets so that everything and their grandmother will populate dynamically with the exception of the summary tab table and the reference table. Score. Ugh, but how do I make it so that the labels don't spawn OH I know. Nope, nope you also have the reference buttons, ok do this later, everything will break and explode and you need to check shit off your list before you can play and destroy.
        # So in the end, because the widgets are dynamically populated without referring to the order of the labels that are already statically in place, the matching of labels and values relies solely on the whimsy of list order in the dictionary. Ideally, I will return to this situation and incorporate both labels and the ref buttons into the dynamism so that everything relies on a single simple function and an outrageously convoluted dictionary. :D
        # What the hell just happened? This is why I don't write comments, jesus.
        self.widgy = self.pleth.rc_config['References']['Widget Labels']['Auto']

    # def setup_variables(self):
    #  {item: {col: None for col in self.config.custom_dict[item]} for item in self.config.custom_dict}
        # self.tables = {}
        self.refs = {self.sections_reference:[self.help_alias,self.help_key,self.help_cal_seg,self.help_auto_ind_include,self.help_auto_ind_injection,self.help_startpoint,self.help_midpoint,self.help_endpoint],
        self.cal_reference:[self.help_auto_ind_cal,self.help_auto_ind_gas_cal,self.help_cal_co2,self.help_cal_o2],
        self.thresh_reference: [self.help_min_co2,self.help_max_co2,self.help_min_o2,self.help_max_calibrated_TV,self.help_max_VEVO2,self.help_max_o2,self.help_within_start,self.help_within_end,self.help_after_start,self.help_before_end],
        self.inc_reference: [self.help_min_TT,self.help_max_TT,self.help_max_dvtv,self.help_X,self.help_max_pX,self.help_vol_mov_avg_drift,self.help_min_tv,self.help_min_bout,self.help_include_apnea,self.help_include_sigh,self.help_include_high_chamber_temp]}

        # self.lineEdits = {self.lineEdit_alias: "Alias",
        #                     self.lineEdit_key: "Key",
        #                     self.lineEdit_cal_seg: "Cal Seg",
        #                     self.lineEdit_auto_ind_include: "AUTO_IND_INCLUDE"}

        for v in self.refs.values():
            for vv in v:
                vv.clicked.connect(self.reference_event)

        # for r in self.resets:
        #     r.clicked.connect(self.reset_event)
        
        # for l in self.lineEdits:
        #     l.textChanged.connect(self.update_table_event)
        self.auto_setting_combo.addItems([x for x in self.pleth.bc_config['Dictionaries']['Auto Settings']['default'].keys()])
        self.choose_dict()

    def choose_dict(self):
        print("auto.choose_dict()")
        # Get the appropriate template based on user's choice of experimental condition:
        if self.auto_setting_combo.currentText() in self.pleth.bc_config['Dictionaries']['Auto Settings']['default'].keys():
            print('default auto dictionary accessed')
            self.auto_dict = self.pleth.bc_config['Dictionaries']['Auto Settings']['default'][self.auto_setting_combo.currentText()]
            # print(self.auto_dict)
        else:
            self.auto_dict = self.pleth.bc_config['Dictionaries']['Auto Settings']['generic']['Room Air']
            print("generic dictionary accessed")
        self.frame = pd.DataFrame(self.auto_dict).reset_index()
        # if (verticalLayout in globals()) == True:
        #     self.verticalLayout.setParent(None)

        # index = myLayout.count()
        # while(index >= 0):
        #     myWidget = myLayout.itemAt(index).widget()
        #     myWidget.setParent(None)
        #     index -=1
        self.setup_tabs()
#region Alternative setups
    def nsetup_tabs(self):
        # keynum = 0 
        self.config.custom_port = {item: {col: None for col in self.config.custom_dict[item]} for item in self.config.custom_dict}
        # for tab in self.widgy:
        #     for panel in self.widgy[tab]
        self.widgible = {
            self.sections_widget:{key: {col: self.auto_dict[key]["Alias"] for col in self.auto_dict[key]} for key in self.auto_dict}}
  
# THERE ARE SEVERAL BOOLEANS THAT WOULD BENEFIT FROM A COMBOBOX OR CHECKBOX INSTEAD OF LINEEDIT

        for key in self.auto_dict.keys():
            # The encompassing widget and main horizonalLayout are statically in place.
            # Establish verticalLayout that the lineEdits and their spacers go into.
            self.verticalLayout = QtWidgets.QVBoxLayout()
            # Label it uniquely so the program doesn't implode. Note that it's labeled with the name of the experiment condition - we are essentially using the verticalLayout as columns in a table.
            self.verticalLayout.setObjectName(f"verticalLayout_{key}")
            label = QtWidgets.QLabel(Auto)
            # We want spacers above and below every lineEdit. It's written to include a spacer below every lineEdit when creating the lineEdits, so this just adds that first top one that wouldn't be added when creating lineEdits.
            self.spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self.verticalLayout.addItem(self.spacerItem)

            self.lineEdit_auto_ind_include = QtWidgets.QLineEdit(self.widget)
            self.lineEdit_auto_ind_include.setObjectName(f"lineEdit_auto_ind_include_{key}")
            self.lineEdit_auto_ind_include.setText(str(self.auto_dict[key]["AUTO_IND_INCLUDE"]))
            self.verticalLayout.addWidget(self.lineEdit_auto_ind_include)
            self.spacerItem4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self.verticalLayout.addItem(self.spacerItem4)
            self.horizontalLayout_5.addLayout(self.verticalLayout)
            self.spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
            self.horizontalLayout_5.addItem(self.spacerItem5)
            self.gridLayout_2.addLayout(self.horizontalLayout_5, 0, 0, 1, 1)
    

    def lsetup_tabs(self):
        for key in self.auto_dict.keys():
            self.verticalLayout = QtWidgets.QVBoxLayout()
            self.verticalLayout.setObjectName(f"verticalLayout_{key}")
            self.spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            # self.spacerItem.setObjectName(f"spacerItem_{key}")
            self.verticalLayout.addItem(self.spacerItem)
            self.lineEdit_alias = QtWidgets.QLineEdit(self.widget)
            self.lineEdit_alias.setObjectName(f"lineEdit_alias_{key}")
            self.lineEdit_alias.setText(str(self.auto_dict[key]["Alias"]))
            self.verticalLayout.addWidget(self.lineEdit_alias)
            self.spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self.verticalLayout.addItem(self.spacerItem1)
            self.lineEdit_key = QtWidgets.QLineEdit(self.widget)
            self.lineEdit_key.setObjectName(f"lineEdit_key_{key}")
            self.lineEdit_key.setText(key)
            self.verticalLayout.addWidget(self.lineEdit_key)
            self.spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self.verticalLayout.addItem(self.spacerItem2)
            self.lineEdit_cal_seg = QtWidgets.QLineEdit(self.widget)
            self.lineEdit_cal_seg.setObjectName(f"lineEdit_cal_seg_{key}")
            self.lineEdit_cal_seg.setText(str(self.auto_dict[key]["Cal Seg"]))
            self.verticalLayout.addWidget(self.lineEdit_cal_seg)
            self.spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self.verticalLayout.addItem(self.spacerItem3)
            self.lineEdit_auto_ind_include = QtWidgets.QLineEdit(self.widget)
            self.lineEdit_auto_ind_include.setObjectName(f"lineEdit_auto_ind_include_{key}")
            self.lineEdit_auto_ind_include.setText(str(self.auto_dict[key]["AUTO_IND_INCLUDE"]))
            self.verticalLayout.addWidget(self.lineEdit_auto_ind_include)
            self.spacerItem4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self.verticalLayout.addItem(self.spacerItem4)
            self.horizontalLayout_5.addLayout(self.verticalLayout)
            self.spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
            self.horizontalLayout_5.addItem(self.spacerItem5)
            self.gridLayout_2.addLayout(self.horizontalLayout_5, 0, 0, 1, 1)
#endregion

    def setup_tabs(self):
        print("auto.setup_tabs()")
        # Populate table of threshold tab:
        auto_labels = self.pleth.gui_config['Dictionaries']['Settings Names']['Auto Settings']
        sec_char_df = self.frame.loc[(self.frame['index'].isin(auto_labels['Section Characterization']['Section Identification and Settings'].values())),:]
        # print(sec_char_df)
        sec_spec_df = self.frame.loc[(self.frame['index'].isin(auto_labels['Section Characterization']['Interruptions'].values())),:]
        cal_df = self.frame.loc[(self.frame['index'].isin(auto_labels['Section Calibration']['Volume and Gas Calibrations'].values())),:]
        gas_thresh_df = self.frame.loc[(self.frame['index'].isin(auto_labels['Threshold Settings']['Gas Thresholds'].values())),:]
        time_thresh_df = self.frame.loc[(self.frame['index'].isin(auto_labels['Threshold Settings']['Time Thresholds'].values())),:]
        inc_df = self.frame.loc[(self.frame['index'].isin(auto_labels['Inclusion Criteria']['Breath Quality Standards'].values())),:]
        
        # Populate table of tabs with appropriately sliced dataframes derived from selected settings template:
        self.populate_table(sec_char_df,self.sections_char_table)
        self.populate_table(sec_spec_df,self.sections_spec_table)
        self.populate_table(cal_df,self.cal_table)
        self.populate_table(gas_thresh_df,self.gas_thresh_table)
        self.populate_table(time_thresh_df,self.time_thresh_table)
        self.populate_table(inc_df,self.inc_table)
        self.populate_table(self.frame,self.view_tab)

        # print(self.frame)
        # print(sec_char_df)

    def setup_tabs_load(self):
        print("auto.setup_tabs_load()")
        # Populate table of threshold tab:
        auto_labels = self.pleth.gui_config['Dictionaries']['Settings Names']['Auto Settings']
        sec_char_df = self.frame.loc[(self.frame['index'].isin(auto_labels['Section Characterization']['Section Identification and Settings'].values())),:]
        # print(sec_char_df)
        sec_spec_df = self.frame.loc[(self.frame['index'].isin(auto_labels['Section Characterization']['Interruptions'].values())),:]
        cal_df = self.frame.loc[(self.frame['index'].isin(auto_labels['Section Calibration']['Volume and Gas Calibrations'].values())),:]
        gas_thresh_df = self.frame.loc[(self.frame['index'].isin(auto_labels['Threshold Settings']['Gas Thresholds'].values())),:]
        time_thresh_df = self.frame.loc[(self.frame['index'].isin(auto_labels['Threshold Settings']['Time Thresholds'].values())),:]
        inc_df = self.frame.loc[(self.frame['index'].isin(auto_labels['Inclusion Criteria']['Breath Quality Standards'].values())),:]
        
        # Populate table of tabs with appropriately sliced dataframes derived from selected settings template:
        self.populate_table_load(sec_char_df,self.sections_char_table)
        self.populate_table_load(sec_spec_df,self.sections_spec_table)
        self.populate_table_load(cal_df,self.cal_table)
        self.populate_table_load(gas_thresh_df,self.gas_thresh_table)
        self.populate_table_load(time_thresh_df,self.time_thresh_table)
        self.populate_table_load(inc_df,self.inc_table)
        self.populate_table_load(self.frame,self.view_tab)

        self.auto_setting_combo.setCurrentText("Choose default criteria settings:")

        # print(self.frame)
        # print(sec_char_df)
    
    def reference_event(self):
        sbutton = self.sender()
        self.populate_reference(sbutton.objectName())

    # def reset_event(self):
    #     sbutton = self.sender()
    #     self.reset_parameter(sbutton.objectName())
    
    def update_table_event(self):
        sbutton = self.sender()
        self.update_table(sbutton.objectName())

    # def update_table(self,donor):
    #     for l in self.lineEdits:
    #         if donor == l.objectName():
    #             d = l
    #     for row in range(self.view_tab.rowCount()):
    #         if self.view_tab.item(row,0).text() == donor.replace("lineEdit_",""):
    #             self.view_tab.item(row,1).setText(d.text())
        
    # def update_tabs(self):
    #     for row in range(self.view_tab.rowCount()):
    #         for l in self.lineEdits:
    #             if self.view_tab.item(row,0).text() == l.objectName().replace("lineEdit_",""):
    #                 l.setText(self.view_tab.item(row,1).text())

    def populate_reference(self,butt):
        # for k in self.pleth.rc_config['References']['Definitions'].keys():
            # if f'help_{k}' == str(butt):
        for k,v in self.refs.items():
            for vv in v:
                if vv.objectName() == str(butt):
                    k.setPlainText(self.pleth.rc_config['References']['Definitions'][butt.replace("help_","")])
   
    def populate_table(self,frame,table):
        print("auto.populate_table()")
            # Populate tablewidgets with views of uploaded csv. Currently editable.
            # frame = frame.set_index('index')
        table.setColumnCount(len(frame.columns))
        table.setRowCount(len(frame))
        for col in range(table.columnCount()):
            for row in range(table.rowCount()):
                table.setItem(row,col,QTableWidgetItem(str(frame.iloc[row,col])))
        table.setHorizontalHeaderLabels(frame.columns)
        # table.setVerticalHeaderLabels()

    def populate_table_load(self,frame,table):
        print("auto.populate_table_load()")
            # Populate tablewidgets with views of uploaded csv. Currently editable.
            # frame = frame.set_index('index')
        table.setColumnCount(len(frame.columns))
        table.setRowCount(len(frame))
        for col in range(table.columnCount()):
            for row in range(table.rowCount()):
                table.setItem(row,col,QTableWidgetItem(str(frame.iloc[row,col])))
        table.setHorizontalHeaderLabels(frame.columns)
    
    def collate_dfs(self,table):
        print("auto.collate_dfs()")
        for row in range(table.rowCount()):
            rows = []
            for col in range(table.columnCount()):
                if table.item(row,col) is not None:
                    rows.append(table.item(row,col).text())
                else:
                    rows.append("")

    def save_as(self):
        print("auto.save_as()")
        # self.pleth.hangar.append("Saving autosections file...")
        self.path = QFileDialog.getSaveFileName(self, 'Save File', "auto_sections", ".csv(*.csv))")[0]
        self.save_auto_file()

    def save_checkerargs(self,folder,title):
        print("auto.save_checkerargs()")
        # self.pleth.hangar.append("Saving autosections file...")
        if folder == "":
            path = QFileDialog.getSaveFileName(self, 'Save File', f"{title}", ".csv(*.csv))")[0]
            if not path:
                print("dialog cancelled")
            else:
                self.path = path
        else:
            self.path = os.path.join(folder, f"{title}.csv")
    
    def save_checker(self):
        print("auto.save_checker()")
        # self.pleth.hangar.append("Saving autosections file...")
        if self.pleth.mothership == "":
            path = QFileDialog.getSaveFileName(self, 'Save File', "auto_sections", ".csv(*.csv))")[0]
            if not path:
                print("dialog cancelled")
            else:
                self.path = path
        else:
            self.path = os.path.join(self.pleth.mothership, "auto_sections.csv")
        self.save_auto_file()

    def save_auto_file(self):
        print("auto.save_auto_file()")
        self.pleth.autosections = self.path
        # self.pleth.autosections = os.path.join(self.pleth.mothership, "auto_sections.csv")
        # self.auto_df = self.frame
        try:
        # Saving the dataframes holding the configuration preferences to csvs and assigning them their paths:
            with open(self.pleth.autosections,'w',newline = '') as stream:
                    writer = csv.writer(stream)
                    header = []
                    for row in range(self.view_tab.rowCount()):
                        item = self.view_tab.item(row,0)
                        print(item.text())
                        if item.text() == "nan":
                            header.append("")
                        elif item.text() == "index":
                            header.append("Key")
                        else:
                            header.append(item.text())
                    writer.writerow(header)
                    for column in range(self.view_tab.columnCount()):
                        coldata = []
                        for row in range(self.view_tab.rowCount()):
                            item = self.view_tab.item(row, column)
                            print(item.text())
                            if item.text() == "nan":
                                print("it's nan")
                                coldata.append(
                                    "")
                            else:
                                coldata.append(item.text())
                        writer.writerow(coldata)
            if self.pleth.breath_df != []:
                self.pleth.update_breath_df()
        # DO NOT KEEP THIS NONSENSE JUST INVERSE THE ROWS AND COLUMNS IN THE NESTING ABOVE
        # QUICK FIX
        # self.auto_df.transpose().to_csv(self.pleth.autosections)

            # Clearing the sections panel of the mainGUI and adding to it to reflect changes:
            for item in self.pleth.sections_list.findItems("auto_sections.csv",Qt.MatchEndsWith):
                self.pleth.sections_list.takeItem(self.pleth.sections_list.row(item))
            for item in self.pleth.sections_list.findItems("not detected",Qt.MatchContains):
                self.pleth.sections_list.takeItem(self.pleth.sections_list.row(item))
            self.pleth.sections_list.addItem(self.pleth.autosections)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            reply = QMessageBox.information(self, 'File in use', 'One or more of the files you are trying to save is open in another program.', QMessageBox.Ok)
            # self.thumb = Thumbass()
            # self.thumb.show()
            # self.thumb.message_received("The file(s) you're working with appear to be open in another program.")

        # self.auto_df = pd.read_csv(self.pleth.autosections)
        
        # current = pd.DataFrame.to_dict(self.auto_df.set_index("index"))
        # new_current = {}
        # new_current[self.auto_setting_combo.currentText()]=current
        # self.pleth.bc_config['Dictionaries']['Auto Settings']['current'] = new_current

        # with open(f'{Path(__file__).parent}/breathcaller_config.json','w') as bconfig_file:
        #     json.dump(self.pleth.bc_config,bconfig_file)

    def load_auto_file(self):
        print("auto.load_auto_file()")
        if Path(self.pleth.mothership).exists():
            load_path = self.pleth.mothership
        else:
            load_path = str(Path.home())

        # Opens open file dialog
        file = QFileDialog.getOpenFileName(self, 'Select automatic selection file to edit:', str(load_path))

        # If you the file you chose sucks, the GUI won't crap out.
        if not file[0]:
            print("that didn't work")
        else:
            # Access configuration settings for the breathcaller in breathcaller_config.json:
            # with open(file[0],mode='r') as ad:
            #     reader = csv.reader(ad)
            #     next(reader)
            #     # self.auto_dict = {rows[0]:rows[1] for rows in reader}
            # print(self.auto_dict)
            self.frame = pd.read_csv(file[0],index_col='Key').transpose().reset_index()
            print(f'normal:{self.frame}')
            # print(f'transposed:{self.frame.transpose()}')

            self.setup_tabs_load()

    def load_auto_current(self):
        print("auto.load_auto_current()")
        self.auto_dict = self.pleth.bc_config['Dictionaries']['Auto Settings']['current']
        self.setup_tabs()

#endregion

#region class Simp Sections
# YOu need to make the columns reflect the headers of the dataframess
class Simp(QWidget, Ui_Auto_simp):
    def __init__(self,Plethysmography):
        super(Simp, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Autosections input")
        self.pleth = Plethysmography
        # self.isActiveWindow()
        self.isMaximized()
        self.auto_simp_df = ""

    def start_up(self):
        if self.pleth.autosections == "":
            print("Choose an autosections file.")
        else:
            self.auto_simp_df = pd.read_csv(self.pleth.autosections)
            self.populate_table(self.auto_simp_df,self.simp_table)
    # def load_config_files(self):
    #     if not self.pleth.mothership:
    #         file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(Path.home()))
    #     else:
    #         file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(self.pleth.mothership))
    #     # self.signal_files=[]
    #     if not file_name[0]:
    #         print("no config files selected")
    #     else:
    #         for x in range(len(file_name[0])):
    #             if os.path.basename(file_name[0][x]).startswith("r_config"):
    #                 self.r_config_df = pd.read_csv(file_name[0][x])
    #                 self.populate_table(self.r_config_df,self.r_config_table)
    #             elif os.path.basename(file_name[0][x]).startswith("g_config"):
    #                 self.g_config_df = pd.read_csv(file_name[0][x])
    #                 self.populate_table(self.g_config_df,self.g_config_table)
    #             elif os.path.basename(file_name[0][x]).startswith("o_config"):
    #                 self.o_config_df = pd.read_csv(file_name[0][x])
    #                 self.populate_table(self.o_config_df,self.o_config_table)
    #             else:
    #                 self.thumb = Thumbass()
    #                 self.thumb.show()
    #                 self.thumb.message_received("Please name the configuration files so that their file basename begins with r_config, g_config, and o_config. Otherwise, please load the settings individually.")

    def populate_table(self,frame,view):
        # Populate tablewidgets with views of uploaded csv. Currently editable.
        view.setColumnCount(len(frame.columns))
        view.setRowCount(len(frame))
        for col in range(view.columnCount()):
            for row in range(view.rowCount()):
                view.setItem(row,col,QTableWidgetItem(str(frame.iloc[row,col])))
        view.setHorizontalHeaderLabels(frame.columns)

    def load_auto_simp_file(self):
        # Groping around to find a convenient directory:
        # if Path(self.Plethysmography.py_output_folder).exists():
            # load_path = self.Plethysmography.py_output_folder
        if Path(self.pleth.mothership).exists():
            load_path = self.pleth.mothership
        else:
            load_path = str(Path.home())

        # Opens open file dialog
        file = QFileDialog.getOpenFileName(self, 'Select autosections file to edit:', str(load_path))

        # If you the file you chose sucks, the GUI won't crap out.
        if not file[0]:
            print("nope")
        else:
            self.auto_simp_df = pd.read_csv(file[0])
            self.populate_table(self.auto_simp_df,self.simp_table)
    
    def save_checker(self,folder):
        self.pleth.hangar.append("Saving...")
        if folder == "":
            # path = QFileDialog.getSaveFileName(self, 'Save File', f"{title}", ".csv(*.csv))")[0]
            dire = QFileDialog.getExistingDirectory(self, 'Choose directory', str(Path.home()))
            if not dire:
                print("dialog cancelled")
            else:
                self.dire = dire
        else:
            dire = QFileDialog.getExistingDirectory(self, 'Choose directory', str(folder))
            if not dire:
                print("dialog cancelled")
            else:
                self.dire = dire

    def save_auto_simp_files(self):
        self.save_checker(self.pleth.mothership)
        if not self.auto_simp_df.empty:
            self.table_pack(self.auto_simp_df,self.simp_table,self.pleth.autosections,"auto_sections")
        print(self.pleth.autosections)
        
    def table_pack(self,frame,table,varia,title):
        # table_dict = {}
        varia = os.path.join(self.dire, f"{title}.csv")
        print(varia)
        with open(Path(varia),'w',newline = '') as stream:
                writer = csv.writer(stream)
                header = []
                for column in range(table.columnCount()):
                    item = table.horizontalHeaderItem(column)
                    print(item.text())
                    if item.text() == "nan":
                        print("it's nan")
                        header.append(
                            "")
                    else:
                        header.append(item.text())
                writer.writerow(header)
                for row in range(table.rowCount()):
                    rowdata = []
                    for column in range(table.columnCount()):
                        item = table.item(row, column)
                        print(item.text())
                        print(rowdata)
                        if item.text() == "nan":
                            print("it's nan")
                            rowdata.append(
                                "")
                        else:
                            rowdata.append(item.text())
                    writer.writerow(rowdata)
        
        # Clearing the sections panel of the mainGUI and adding to it to reflect changes:
        for item in self.pleth.sections_list.findItems("auto_sections.csv",Qt.MatchEndsWith):
            self.pleth.sections_list.takeItem(self.pleth.sections_list.row(item))
        for item in self.pleth.sections_list.findItems("not detected",Qt.MatchContains):
            self.pleth.sections_list.takeItem(self.pleth.sections_list.row(item))
        self.pleth.sections_list.addItem(self.pleth.autosections)
#endregion

#region class STagg Sections
# YOu need to make the columns reflect the headers of the dataframess
class Stagg(QWidget, Ui_Stagg):
    def __init__(self,Plethysmography):
        super(Stagg, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("STAGG input")
        self.pleth = Plethysmography
        # self.isActiveWindow()
        self.isMaximized()
        self.r_config_df = ""
        self.g_config_df = ""
        self.o_config_df = ""

    def load_config_files(self):
        if not self.pleth.mothership:
            file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(Path.home()))
        else:
            file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(self.pleth.mothership))
        # self.signal_files=[]
        if not file_name[0]:
            print("no config files selected")
        else:
            for x in range(len(file_name[0])):
                if os.path.basename(file_name[0][x]).startswith("r_config"):
                    self.r_config_df = pd.read_csv(file_name[0][x])
                    self.populate_table(self.r_config_df,self.r_config_table)
                elif os.path.basename(file_name[0][x]).startswith("g_config"):
                    self.g_config_df = pd.read_csv(file_name[0][x])
                    self.populate_table(self.g_config_df,self.g_config_table)
                elif os.path.basename(file_name[0][x]).startswith("other_config"):
                    self.o_config_df = pd.read_csv(file_name[0][x])
                    self.populate_table(self.o_config_df,self.o_config_table)
                else:
                    self.thumb = Thumbass(self)
                    self.thumb.show()
                    self.thumb.message_received("Please name the configuration files so that their file basename begins with variable_config, graph_config, and other_config. Otherwise, please load the settings files individually.")

    def populate_table(self,frame,view):
        # Populate tablewidgets with views of uploaded csv. Currently editable.
        view.setColumnCount(len(frame.columns))
        view.setRowCount(len(frame))
        for col in range(view.columnCount()):
            for row in range(view.rowCount()):
                view.setItem(row,col,QTableWidgetItem(str(frame.iloc[row,col])))
        view.setHorizontalHeaderLabels(frame.columns)

    def load_rconfig_file(self):
        # Groping around to find a convenient directory:
        # if Path(self.Plethysmography.py_output_folder).exists():
            # load_path = self.Plethysmography.py_output_folder
        # if Path(self.pleth.mothership).exists():
        #     load_path = self.pleth.mothership
        # else:
        #     load_path = str(Path.home())

        # Opens open file dialog
        file = QFileDialog.getOpenFileName(self, 'Select r_config file to edit:', str(self.pleth.mothership))

        # If you the file you chose sucks, the GUI won't crap out.
        if not file[0]:
            print("nope")
        else:
            self.r_config_df = pd.read_csv(file[0])
            self.populate_table(self.r_config_df,self.r_config_table)

    def load_gconfig_file(self):
        # Groping around to find a convenient directory:
        # if Path(self.Plethysmography.py_output_folder).exists():
            # load_path = self.Plethysmography.py_output_folder
        # if Path(self.pleth.mothership).exists():
        #     load_path = self.pleth.mothership
        # else:
        #     load_path = str(Path.home())

        # Opens open file dialog
        file = QFileDialog.getOpenFileName(self, 'Select g_config file to edit:', str(self.pleth.mothership))

        # If you the file you chose sucks, the GUI won't crap out.
        if not file[0]:
            print("nope")
        else:
            self.g_config_df = pd.read_csv(file[0])
            self.populate_table(self.g_config_df,self.g_config_table)

    def load_oconfig_file(self):
        # Groping around to find a convenient directory:
        # if Path(self.Plethysmography.py_output_folder).exists():
            # load_path = self.Plethysmography.py_output_folder
        # if Path(self.pleth.mothership).exists():
        #     load_path = self.pleth.mothership
        # else:
        #     load_path = str(Path.home())

        # Opens open file dialog
        file = QFileDialog.getOpenFileName(self, 'Select o_config file to edit:', str(self.pleth.mothership))

        # If you the file you chose sucks, the GUI won't crap out.
        if not file[0]:
            print("nope")
        else:
            self.o_config_df = pd.read_csv(file[0])
            self.populate_table(self.o_config_df,self.o_config_table)
    
    def save_checker(self,folder):
        self.pleth.hangar.append("Saving...")
        if folder == "":
            # path = QFileDialog.getSaveFileName(self, 'Save File', f"{title}", ".csv(*.csv))")[0]
            dire = QFileDialog.getExistingDirectory(self, 'Choose directory', str(self.pleth.mothership))
            if not dire:
                print("dialog cancelled")
            else:
                self.dire = dire
        else:
            dire = QFileDialog.getExistingDirectory(self, 'Choose directory', str(folder))
            if not dire:
                print("dialog cancelled")
            else:
                self.dire = dire

    def save_config_files(self):
        self.save_checker(self.pleth.mothership)
        if not self.r_config_df.empty:
            self.table_pack(self.r_config_df,self.r_config_table,self.pleth.variable_config,"variable_config")
        if not self.g_config_df.empty:
            self.table_pack(self.g_config_df,self.g_config_table,self.pleth.graph_config,"graph_config")
        if not self.o_config_df.empty:
            self.table_pack(self.o_config_df,self.o_config_table,self.pleth.other_config,"other_config")
        
    def table_pack(self,frame,table,varia,title):
        # table_dict = {}
        varia = os.path.join(self.dire, f"{title}.csv")
        print(varia)
        try:
            with open(Path(varia),'w',newline = '') as stream:
                    writer = csv.writer(stream)
                    header = []
                    for column in range(table.columnCount()):
                        item = table.horizontalHeaderItem(column)
                        print(item.text())
                        if item.text() == "nan":
                            print("it's nan")
                            header.append(
                                "")
                        else:
                            header.append(item.text())
                    writer.writerow(header)
                    for row in range(table.rowCount()):
                        rowdata = []
                        for column in range(table.columnCount()):
                            item = table.item(row, column)
                            print(item.text())
                            print(rowdata)
                            if item.text() == "nan":
                                print("it's nan")
                                rowdata.append(
                                    "")
                            else:
                                rowdata.append(item.text())
                        writer.writerow(rowdata)
        except PermissionError as e:
            print(f'{type(e).__name__}: {e}')
            reply = QMessageBox.information(self, 'File in use', 'One or more of the files you are trying to save is open in another program.', QMessageBox.Ok)
        
        # Clearing the config panel of the mainGUI and adding to it to reflect changes:
        for f in ["variable_config","graph_config","other_config"]:
            for item in self.pleth.variable_list.findItems(f,Qt.MatchContains):
                self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
        for p in [self.pleth.variable_config,self.pleth.graph_config,self.pleth.other_config]:
            self.pleth.variable_list.addItem(self.pleth.variable_config)
        for item in self.pleth.variable_list.findItems("Configuration files not detected.",Qt.MatchExactly):
            self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
#endregion

#region class Manual Sections
# YOu need to make the columns reflect the headers of the dataframess
# self.hypercapnia_default = {"Cal 20 Room Air": {"Alias": "Cal 20 Room Air", "Cal Seg": "Cal 20 Room Air", "MAN_IND_INCLUDE": 0, "MAN_IND_CAL": 1, "MAN_IND_GAS": "RA", "MAN_IND_INJECTION": "Cal"}, "Cal 20 5% CO2": {"Alias": "Cal 20 5% CO2", "Cal Seg": "Cal 20 5% CO2", "MAN_IND_INCLUDE": 0, "MAN_IND_CAL": 1, "MAN_IND_GAS": "CO2", "MAN_IND_INJECTION": "Cal"}, "Room Air": {"Alias": "Room Air", "Cal Seg": "Cal 20 Room Air", "MAN_IND_INCLUDE": 1, "MAN_IND_CAL": 1, "MAN_IND_GAS": "RA", "MAN_IND_INJECTION": "NA"}, "5% CO2": {"Alias": "5% CO2", "Cal Seg": "Cal 20 5% CO2", "MAN_IND_INCLUDE": 1, "MAN_IND_CAL": 1, "MAN_IND_GAS": "CO2", "MAN_IND_INJECTION": "NA"}, "Room Air 2": {"Alias": "Room Air 2", "Cal Seg": "Cal 20 Room Air", "MAN_IND_INCLUDE": 0, "MAN_IND_CAL": 1, "MAN_IND_GAS": "RA", "MAN_IND_INJECTION": "NA"}}

class Manual(QWidget, Ui_Manual):
    def __init__(self,Plethysmography):
        super(Manual, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Manual sections file creation")
        self.pleth = Plethysmography
        # self.isActiveWindow()
        self.isMaximized()
        self.datapad = None
        self.preset = None
        self.manual_df = ""
        self.vals = ['animal id','PLYUID','start','stop','duration','mFrequency_Hz','mPeriod_s','mHeight_V','mO2_V','mCO2_V','mTchamber_V','segment']

    def get_datapad(self):
        print("manual.get_datapad()")
        file = QFileDialog.getOpenFileNames(self, 'Select Labchart datapad export file', str(self.pleth.mothership))
        print(len(file))
        print(len(file[0]))
        # If you the file you chose sucks, the GUI won't crap out.
        if not file[0]:
            print("nope")
        else:
            dfs=[]
            for f in file[0]:
                if f.endswith('.csv'):
                    df = pd.read_csv(f,header=[2])
                    mp = os.path.basename(f).rsplit(".csv")[0]
                elif f.endswith('.txt'):
                    df = pd.read_csv(f,sep="\t",header=[2])
                    mp = os.path.basename(f).rsplit(".txt")[0]
                elif f.endswith('.xlsx'):
                    df = pd.read_excel(f,header=[0])
                    mp = os.path.basename(f).rsplit(".xlsx")[0]
                if "_" in mp:
                    df['animal id'] = mp.rsplit("_")[0]
                    df['PLYUID'] = mp.rsplit("_")[1]
                else:
                    df['animal id'] = mp
                    df['PLYUID'] = ""
                dfs.append(df)
            dc = pd.concat(dfs, ignore_index=True)
            dc.insert(0,'PLYUID',dc.pop('PLYUID'))
            dc.insert(0,'animal id',dc.pop('animal id'))
            keys = dc.columns
            mand = {}
            for key,val in zip(keys,self.vals):
                mand.update({key: val})
            dc = dc.rename(columns = mand)
            dc['start_time'] = pd.to_timedelta(dc['start'])
            dc['start'] = dc['start_time'].dt.total_seconds()
            dc['stop_time'] = pd.to_timedelta(dc['stop'])
            dc['stop'] = dc['stop_time'].dt.total_seconds()
            self.datapad = dc
            print(self.datapad)
            self.populate_table(self.datapad, self.datapad_view)
            self.datapad.to_csv("C:/Users/atwit/Desktop/datapad.csv")
        # ou'll need to implement measures to ensure correct columns names, correct data type, etc.

    def get_preset(self):
        print("manual.get_preset()")
        self.preset = pd.DataFrame.from_dict(self.pleth.bc_config['Dictionaries']['Manual Settings']['default'][self.preset_menu.currentText()].values())
        # self.preset = pd.DataFrame.from_dict(self.hypercapnia_default.values())
        self.populate_table(self.preset, self.settings_view)    
    
    def manual_merge(self):
        print("manual.manual_merge()")
        # if self.datapad == "":
        #     self.get_datapad()
        try:
            self.manual_df = self.datapad.merge(self.preset,'outer',left_on=self.datapad['segment'],right_on=self.preset['Alias'])
            self.manual_df = self.manual_df.iloc[:,1:]
            self.populate_table(self.manual_df,self.manual_view)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            if self.datapad is None and self.preset is not None:
                reply = QMessageBox.information(self, 'Missing datapad file', 'You need to select a LabChart datapad exported as a text file. Would you like to select a file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                if reply == QMessageBox.Ok:
                    self.get_datapad()
            elif self.preset is None and self.datapad is not None:
                reply = QMessageBox.information(self, 'Missing sections settings', 'Please select one of the options from the dropdown menu above.', QMessageBox.Ok)
            elif self.datapad is None and self.preset is None:
                self.thorb = Thorbass(self)
                self.thorb.show()
                self.thorb.message_received('Nope.', 'There is nothing to merge. Would you like to open an existing manual sections settings file or create a new one?',self.new_manual_file,self.load_manual_file)
                # reply = QMessageBox.information(self, 'What are you doing?', 'There is nothing to merge. Would you like to open an existing manual sections settings file or create a new one?', QMessageBox.New | QMessageBox.Open | QMessageBox.Cancel, QMessageBox.Ok)
    
    def new_manual_file(self):
        print("manual.new_manual_file()")
        if self.datapad == "":
            reply = QMessageBox.information(self, 'Missing datapad file', 'You need to select a LabChart datapad exported as a text file. Would you like to select a file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Yes:
                self.get_datapad()
        if self.preset == "":
            reply = QMessageBox.information(self, 'Missing sections settings', 'Please select one of the options from the dropdown menu above.', QMessageBox.Ok)

    def populate_table(self,frame,view):
        print("manual.populate_table()")
        # Populate tablewidgets with views of uploaded csv. Currently editable.
        view.setColumnCount(len(frame.columns))
        view.setRowCount(len(frame))
        for col in range(view.columnCount()):
            for row in range(view.rowCount()):
                view.setItem(row,col,QTableWidgetItem(str(frame.iloc[row,col])))
        view.setHorizontalHeaderLabels(frame.columns)

    def save_checker(self,folder,title):
        print("manual.save_checker()")
        if folder == "":
            path = QFileDialog.getSaveFileName(self, 'Save File', f"{title}", ".csv(*.csv))")[0]
            if not path:
                print("dialog cancelled")
            else:
                self.path = path
        else:
            self.path = os.path.join(folder, f"{title}.csv")

    def save_manual_file(self):
        print("manual.save_manual_file()")
        try:
            self.save_checker(self.pleth.mothership,"manual_sections")
            self.pleth.mansections = self.path
        
        # Saving the dataframes holding the configuration preferences to csvs and assigning them their paths:
            self.manual_df.to_csv(self.pleth.mansections,index=False)

            if self.pleth.breath_df != []:
                self.pleth.update_breath_df()
        
        # current = pd.DataFrame.to_dict(self.manual_df.set_index("index"))
        # print(current)
        # new_current = {}
        # new_current[self.preset_menu.currentText()]=current
        # print(new_current)
        # self.pleth.bc_config['Dictionaries']['Auto Settings']['current'] = new_current

        # with open(f'{Path(__file__).parent}/breathcaller_config.json','w') as bconfig_file:
        #     json.dump(self.pleth.bc_config,bconfig_file)
        
        # Clearing the sections panel of the mainGUI and adding to it to reflect changes:
            for item in self.pleth.sections_list.findItems("manual_sections.csv",Qt.MatchEndsWith):
                self.pleth.sections_list.takeItem(self.pleth.sections_list.row(item))
            for item in self.pleth.sections_list.findItems("not detected",Qt.MatchContains):
                self.pleth.sections_list.takeItem(self.pleth.sections_list.row(item))
            self.pleth.sections_list.addItem(self.pleth.mansections)
            self.pleth.hangar.append("Manual sections file saved.")
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            reply = QMessageBox.information(self, 'File in use', 'One or more of the files you are trying to save is open in another program.', QMessageBox.Ok)
    
    def load_manual_file(self):
        print("manual.load_manual_file()")
        # Groping around to find a convenient directory:
        # if Path(self.Plethysmography.py_output_folder).exists():
            # load_path = self.Plethysmography.py_output_folder
        # if Path(self.pleth.mothership).exists():
        #     load_path = self.pleth.mothership
        # else:
        #     load_path = str(self.pleth.mothership)

        # Opens open file dialog
        file = QFileDialog.getOpenFileName(self, 'Select manual sections file to edit:', str(self.pleth.mothership))

        # If you the file you chose sucks, the GUI won't crap out.
        if not file[0]:
            print("nope")
        else:
            self.load_manual = pd.read_csv(file[0])
            self.datapad = self.load_manual.loc[:,[x for x in self.vals]]
            self.preset = self.load_manual.loc[:,[x for x in self.load_manual.columns if x not in self.datapad.columns]].drop_duplicates()
            # self.manual_df = self.datapad.merge(self.preset,'outer',left_on=self.datapad['segment'],right_on=self.preset['Alias'])
            # self.manual_df = self.manual_df.iloc[:,1:]
            self.manual_df = self.load_manual
            self.populate_table(self.manual_df,self.manual_view)
            # self.populate_table(self.load_manual,self.manual_view)
            self.populate_table(self.datapad, self.datapad_view)
            self.populate_table(self.preset, self.settings_view)
            # print(self.manual_df)
            # print(self.load_manual)

    def load_manual_current(self):
        print("manual.load_manual_current()")
        self.manual_dict = self.pleth.bc_config['Dictionaries']['Manual Settings']['current']
        self.setup_tabs()
#endregion

class CheckableComboBox(QComboBox):

    # Subclass Delegate to increase item height
    class Delegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            # size.setHeight(20)
            return size

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make the combo editable to set a custom text, but readonly
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        # Make the lineedit the same color as QPushButton
        palette = qApp.palette()
        palette.setBrush(QPalette.Base, palette.button())
        self.lineEdit().setPalette(palette)

        # Use custom delegate
        self.setItemDelegate(CheckableComboBox.Delegate())

        # Update the text when an item is toggled
        self.model().dataChanged.connect(self.updateText)

        # Hide and show popup when clicking the line edit
        self.lineEdit().installEventFilter(self)
        self.closeOnLineEditClick = False

        # Prevent popup from closing when clicking on an item
        self.view().viewport().installEventFilter(self)

    def resizeEvent(self, event):
        # Recompute text to elide as needed
        self.updateText()
        super().resizeEvent(event)

    def eventFilter(self, object, event):

        if object == self.lineEdit():
            if event.type() == QEvent.MouseButtonRelease:
                if self.closeOnLineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return False

        if object == self.view().viewport():
            if event.type() == QEvent.MouseButtonRelease:
                index = self.view().indexAt(event.pos())
                item = self.model().item(index.row())

                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                return True
        return False

    def showPopup(self):
        super().showPopup()
        # When the popup is displayed, a click on the lineedit should close it
        self.closeOnLineEditClick = True

    def hidePopup(self):
        super().hidePopup()
        # Used to prevent immediate reopening when clicking on the lineEdit
        self.startTimer(100)
        # Refresh the display text when closing
        self.updateText()

    def timerEvent(self, event):
        # After timeout, kill timer, and reenable click on line edit
        self.killTimer(event.timerId())
        self.closeOnLineEditClick = False

    def updateText(self):
        texts = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                texts.append(self.model().item(i).text())
        text = ", ".join(texts)

        # Compute elided text (with "...")
        metrics = QFontMetrics(self.lineEdit().font())
        elidedText = metrics.elidedText(text, Qt.ElideRight, self.lineEdit().width())
        self.lineEdit().setText(elidedText)

    def loadCustom(self,tran):
        for t in tran:
            for i in range(self.model().rowCount()):
                if self.model().item(i).text() == t:
                    print("checking t")
                    self.model().item(i).setCheckState(Qt.Checked)

    def addItem(self, text, data=None):
        item = QStandardItem()
        item.setText(text)
        if data is None:
            item.setData(text)
        else:
            item.setData(data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, texts, datalist=None):
        for i, text in enumerate(texts):
            try:
                # print(i)
                # print(text)
                data = datalist[i]
                # print(data)
            # except (TypeError, IndexError):
            except Exception as e:
                # print(f'{type(e).__name__}: {e}')
                data = None
            self.addItem(text, data)

    def currentData(self):
        # Return the list of selected items data
        res = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                res.append(self.model().item(i).data())
        return res

#region class Custom Config Sections
class Custom(QWidget, Ui_Custom):
    def __init__(self,Config):
        super(Custom, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Custom graph settings configuration")
        # self.pleth = Plethysmography
        self.config = Config
        # self.thumb = Thumbass
        # self.isActiveWindow()
        self.isMaximized()
        # self.extract_variable()
        # self.custom_port = {}
        self.custom_alias = []
        self.ymin = []
        self.ymax = []
        self.custom_transform = []
        self.custom_poincare = []
        self.custom_spectral = []
        self.custom_irreg = []
    
    # def update_custom_dict(self,combo):
    #     for widget in self.config.additional_dict:
    #         if 
    #         if widget.objectName() == str(combo):
    #             if widget.currentText() == "None":
    #                 for item in self.custom_dict:
    #                     self.custom_dict[item][self.config.additional_dict[widget]].

    def populate_reference(self,butt):
        for k,v in self.widgy.items():
            for vv in v:
                if vv.objectName() == str(butt):
                    k.setPlainText(self.pleth.rc_config['References']['Definitions'][butt.replace("help_","")])

    def extract_variable(self):
        print("custom.extract_variable()")
        print(self.config.deps)
        if self.config.deps.empty:
            reply = QMessageBox.information(self, 'Choose variables', 'Please select response variables to be modeled.', QMessageBox.Ok)
            # self.thumb = Thumbass()
            # self.thumb.show()
            # self.thumb.message_received("Please select the response variables to be modeled.")
        else:
            self.populate_table(self.config.deps,self.custom_table)
            self.show()
    

    def addItem(self, text, data=None):
        print("custom.addItem()")
        item = QStandardItem()
        item.setText(text)
        if data is None:
            item.setData(text)
        else:
            item.setData(data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)

    def populate_table(self,frame,table):
        print("custom started populating table")
        # Populate tablewidgets with dictionary holding widgets. 
        # self.custom_dict = {}
        # print(f'before: {self.config.custom_dict}')
        table.setRowCount(len(frame))
        row = 0
        for item in frame:
            print("making first level")
            self.config.custom_dict[item] = {}
            # The first two columns are the name of the dependent variables selected and empty strings for ymin and ymax:
            print("making alias")
            self.config.custom_dict[item]["Alias"]=QTableWidgetItem(item)
            print("making ymin/max")
            self.config.custom_dict[item]["ymin"]=QTableWidgetItem("")
            self.config.custom_dict[item]["ymax"]=QTableWidgetItem("")
            # Creating the radio buttons that will populate the cells in each row:
            # self.custom_dict[item]["Filter"]=QCheckBox()
            print("making poincare/spectral")
            self.config.custom_dict[item]["Poincare"]=QCheckBox()
            self.config.custom_dict[item]["Spectral"]=QCheckBox()
            # self.config.custom_dict[item]["Irregularity"]=QCheckBox()
            # self.config.custom_dict[item]["Inclusive"]=QCheckBox()
            # self.custom_dict[item]["Inclusive"].setAlignment(Qt.AlignHCenter)
            # Creating the combo boxes that will populate the cells in each row:
            # self.custom_dict[item]["Filter"]=QCheckBox()
            print("making transform")
            self.config.custom_dict[item]["Transformation"]=CheckableComboBox()
            print("checkalbe transform made")
            
            self.config.custom_dict[item]["Transformation"].addItems(["raw","log10","ln","sqrt"])
            # self.custom_dict[item]["Transformation"].addItem("log10")
        # table.setColumnCount(len(frame.columns))
        # print(self.custom_dict)
        # for row in range(table.rowCount()):
        #     for k in self.custom_dict:
        #         print(k)
            print("setting widgets in table")
            table.setItem(row,0,self.config.custom_dict[item]["Alias"])
            # table.item(row,0).setFlags(Qt.ItemIsEditable)
            # for col in range(table.columnCount()):
                # Populating the table widget with the row:
            table.setItem(row,1,self.config.custom_dict[item]["ymin"])
            table.setItem(row,2,self.config.custom_dict[item]["ymax"])

            # table.setCellWidget(row,3,self.custom_dict[item]["Filter"])
            table.setCellWidget(row,3,self.config.custom_dict[item]["Transformation"])
            # table.setCellWidget(row,4,self.config.custom_dict[item]["Inclusive"])
            table.setCellWidget(row,4,self.config.custom_dict[item]["Poincare"])
            table.setCellWidget(row,5,self.config.custom_dict[item]["Spectral"])
            # table.setCellWidget(row,6,self.config.custom_dict[item]["Irregularity"])
                # table.item(row,0).setFlags(Qt.ItemIsEditable)
        # table.setHorizontalHeaderLabels(frame.columns)
            row += 1
        # self.view_tab.cellChanged.connect(self.update_tabs)
        print("custom finished populating table")
        # print(f'after: {self.config.custom_dict}')
# for role in self.role_list[1:6]:
#     self.pleth.loop_menu[self.loop_table][loop_row][role] = QComboBox()
#     self.pleth.loop_menu[self.loop_table][loop_row][role].addItems([""])
#     self.pleth.loop_menu[self.loop_table][loop_row][role].addItems([x for x in self.pleth.breath_df])

# self.loop_table.setCellWidget(loop_row,1,self.pleth.loop_menu[self.loop_table][loop_row]["Variable"])
# self.loop_table.setCellWidget(loop_row,2,self.pleth.loop_menu[self.loop_table][loop_row]["Xvar"])
# self.loop_table.setCellWidget(loop_row,3,self.pleth.loop_menu[self.loop_table][loop_row]["Pointdodge"])
# self.loop_table.setCellWidget(loop_row,4,self.pleth.loop_menu[self.loop_table][loop_row]["Facet1"])
# self.loop_table.setCellWidget(loop_row,5,self.pleth.loop_menu[self.loop_table][loop_row]["Facet2"])
    def get_key(self,dic,val):
        print("custom.get_key()")
        for key,value in dic.items():
            if val == value:
                return key

    def save_custom(self):
        print("custom.save_custom()")
        # self.config.custom_port = copy.deepcopy(self.config.custom_dict)
        self.config.custom_port = {item: {col: None for col in self.config.custom_dict[item]} for item in self.config.custom_dict}
        # print(f'port before: ID {id(self.config.custom_port)}')
        # print(f'{self.config.custom_port}')
        # print(f'dict before: ID {id(self.config.custom_dict)}')
        # print(f'{self.config.custom_dict}')
        for item in self.config.custom_dict:
            for col in self.config.custom_dict[item]:
                # print(col.value)
                # print(str(type(self.config.custom_port[item][col])))
                if "QTableWidgetItem" in str(type(self.config.custom_dict[item][col])):
                    self.config.custom_port[item].update({col:self.config.custom_dict[item][col].text()})
                elif "QCheckBox" in str(type(self.config.custom_dict[item][col])):
                    self.config.custom_port[item].update({col:int(self.config.custom_dict[item][col].isChecked())})
                elif "QComboBox" in str(type(self.config.custom_dict[item][col])):
                    self.config.custom_port[item].update({col:self.config.custom_dict[item][col].currentText()})
                elif "CheckableComboBox" in str(type(self.config.custom_dict[item][col])):
                    # print(self.config.custom_dict[item][col].currentData())
                    # print(self.config.custom_dict[item][col].currentData()[0])
                    # tran = self.config.custom_dict[item][col].currentData()
                    self.config.custom_port[item].update({col:self.config.custom_dict[item][col].currentData()})
                else:
                    print("wibblecol")
            # self.ymin.append(self.custom_dict[item]["ymin"].text())
            # self.ymax.append(self.custom_dict[item]["ymax"].text())
            # self.custom_transform.append(self.custom_dict[item]["Transformation"].currentText())
            # self.custom_poincare.append(self.config.custom_port[item]["Poincare"])
            # self.custom_spectral.append(self.config.custom_port[item]["Spectral"])
            # self.custom_irreg.append(self.config.custom_port[item]["Irregularity"])
        # if any(self.custom_irreg) == 1:
            # self.config.irreg_combo.setCurrentText("Custom")
        # if any(self.custom_spectral) == 1:
        # if any(self.config.custom_port[])
        #     self.config.Spectral_combo.setCurrentText("Custom")
        # if any(self.custom_poincare) == 1:
        #     self.config.Poincare_combo.setCurrentText("Custom")
        for key,value in {self.config.Poincare_combo:"Poincare",self.config.Spectral_combo:"Spectral"}.items():
            if all([self.config.custom_port[var][value] == 1 for var in self.config.custom_port]):
                key.setCurrentText("All")
            if any([self.config.custom_port[var][value] == 1 for var in self.config.custom_port]):
                key.setCurrentText("Custom")
            else:
                key.setCurrentText("None")
               
        # if all(self.config.custom_port[item][col]) == 1:
        #     self.get_key(self.additional_dict,col).setCurrentText("All")
        # elif any(self.config.custom_port[item][col]) == 1:
        #     self.get_key(self.additional_dict,col).setCurrentText("Custom")
        # else:
        #     self.get_key(self.additional_dict,col).setCurrentText("None")
        if any([self.config.custom_port[t]["Transformation"] for t in self.config.custom_port]) in ["raw","log10","ln","sqrt"]:
            print("hay transformation custom")
            self.config.transform_combo.setCurrentText("Custom")
        # print(f'port after: ID {id(self.config.custom_port)}')
        # print(f'{self.config.custom_port}')
        # print(f'dict after: ID {id(self.config.custom_dict)}')
        # print(f'{self.config.custom_dict}')
            
#endregion

class myStyle(QCommonStyle):

    def __init__(self, angl=0, point=QPoint(0, 0)):
        super(myStyle, self).__init__()
        self.angl = angl
        self.point = point

    def drawItemText(self, painter, rect, flags, pal, enabled, text, textRole):
        if not text:
            return
        savedPen = painter.pen()
        if textRole != QPalette.NoRole:
            painter.setPen(QPen(pal.brush(textRole), savedPen.widthF()))
        if not enabled:
            pen = painter.pen()
            painter.setPen(pen)
        painter.translate(self.point)
        painter.rotate(self.angl)
        painter.drawText(rect, flags, text)
        painter.setPen(savedPen)

#region class Variable
class Config(QWidget, Ui_Config):
    def __init__(self,Plethysmography):
        super(Config, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("STAGG Variable Configuration")
        self.pleth = Plethysmography
        # self.isActiveWindow()
        self.isMaximized()
        self.deps = []
        
        # self.role_list = ["Graph","Variable","Xvar","Pointdodge","Facet1","Facet2","Poincare","Y axis minimum","Y axis maximum","Inclusion"]
        # self.graph_role = []
        # # self.combos = [self.Xvar_combo, self.Pointdodge_combo, self.Facet1_combo, self.Facet2_combo]
        # # self.static = {"Start Body Temp": [], "Mid Body Temp": [], "End Body Temp": [], "Post Body Temp": [], "Body Weight": []}
        # self.settings_dict = {"role": {self.Xvar_combo:1,self.Pointdodge_combo:2,self.Facet1_combo:3,self.Facet2_combo:4}, 
        #                       "rel": {"Xvar":self.Xvar_combo,"Pointdodge":self.Pointdodge_combo,"Facet1":self.Facet1_combo,"Facet2":self.Facet2_combo}}
        # self.widgy = {self.config_reference:[self.help_xvar,self.help_pointdodge,self.help_facet1,self.help_facet2,self.help_feature,self.help_poincare,self.help_spectral,self.help_irregularity,self.help_transformation]}
        # self.alias = []
        # self.independent = []
        # self.dependent = []
        # self.covariate = []
        # self.graphic.setStyleSheet("border-image:url(graphic.png)")
        # # self.pointdodge_label.setStyle(myStyle(90))
        
        # for v in self.widgy.values():
        #     for vv in v:
        #         vv.clicked.connect(self.reference_event)
        # print("Config")
        self.setup_variables_config()
        # self.setup_config()

        for v in self.additional_dict:
            v.currentTextChanged.connect(self.combo_event)
    
    def minus_loop(self):
        print("config.minus_loop()")
        for r in self.loop_table.selectedItems():
            self.loop_table.removeRow(self.loop_table.row(r))

    def combo_event(self):
        print("combo_event()")
        # sbutton = self.sender()
        # if str(sbutton.objectName()) != "feature_combo":
        #     print("not feature")
        #     self.classy()
        #     deps = self.clades.loc[(self.clades["Dependent"] == 1)]["Alias"]
        # # print(deps)
        # if self.custom_dict == {}:
        #     self.pleth.c = Custom(self)
        #     self.pleth.c.extract_variable(deps)
        #     self.update_custom_dict(sbutton.objectName())
        
    def reference_event(self):
        sbutton = self.sender()
        self.populate_reference(sbutton.objectName())

    def populate_reference(self,butt):
        for k,v in self.widgy.items():
            for vv in v:
                if vv.objectName() == str(butt):
                    k.setPlainText(self.pleth.rc_config['References']['Definitions'][butt.replace("help_","")])

    def setup_transform_combo(self):
        spacerItem64 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_25.addItem(spacerItem64)
        self.transform_combo = CheckableComboBox()
        self.transform_combo.addItems(["raw","log10","ln","sqrt","Custom"])
        self.verticalLayout_25.addWidget(self.transform_combo)
        spacerItem65 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_25.addItem(spacerItem65)

    def setup_variables_config(self): 
        print("config.setup_variables_config()")
        try:
            if not self.transform_combo:
                print("no transform_combo")
        except Exception as e:
            self.setup_transform_combo()
        # print(self.pleth.breath_df)
        # self.pleth.cons = {"variable_config":self.pleth.variable_config,"graph_config":self.pleth.graph_config,"other_config":self.pleth.other_config}
        self.role_list = ["Graph","Variable","Xvar","Pointdodge","Facet1","Facet2","Inclusion","Y axis minimum","Y axis maximum"]
        self.graph_role = []
        # self.combos = [self.Xvar_combo, self.Pointdodge_combo, self.Facet1_combo, self.Facet2_combo]
        # self.static = {"Start Body Temp": [], "Mid Body Temp": [], "End Body Temp": [], "Post Body Temp": [], "Body Weight": []}
        self.additional_dict = {self.feature_combo:"Feature",self.Poincare_combo:"Poincare",self.Spectral_combo:"Spectral",self.transform_combo:"Transformation"}
        self.settings_dict = {"role": {self.Xvar_combo:1,self.Pointdodge_combo:2,self.Facet1_combo:3,self.Facet2_combo:4}, 
                              "rel": {"Xvar":self.Xvar_combo,"Pointdodge":self.Pointdodge_combo,"Facet1":self.Facet1_combo,"Facet2":self.Facet2_combo}}
        self.widgy = {self.config_reference:[self.help_xvar,self.help_pointdodge,self.help_facet1,self.help_facet2,self.help_feature,self.help_poincare,self.help_spectral,self.help_transformation]}
        self.alias = []
        self.independent = []
        self.dependent = []
        self.covariate = []
        self.graphic.setStyleSheet("border-image:url(graphic.png)")

        self.custom_dict = {}
        self.custom_port = {}
        self.clades = []
        self.clades_graph = []
        self.clades_other = []
        self.baddies = []
        self.goodies = []
        self.configs = {"variable_config":{"variable":self.pleth.variable_config,"path":"","frame":self.clades,"df":[]},"graph_config":{"variable":self.pleth.graph_config,"path":"","frame":self.clades_graph,"df":[]},"other_config":{"variable":self.pleth.other_config,"path":"","frame":self.clades_other,"df":[]}}

        for v in self.widgy.values():
            for vv in v:
                vv.clicked.connect(self.reference_event)

        for a in self.additional_dict:
            a.currentTextChanged.connect(self.combo_event)
    
    def setup_table_config(self):
        print("config.setup_table_config()")
        self.stack = []
        # The following "header" stanzas make the columns within the tables of equal width.
        header = self.variable_table.horizontalHeader()
        for header_col in range(0,6):
            header.setSectionResizeMode(header_col,QHeaderView.Stretch)

        header_loop = self.loop_table.horizontalHeader()
        for header_loop_col in range(0,6):
            header_loop.setSectionResizeMode(header_loop_col,QHeaderView.Stretch)

        # header_upper_loop = self.v.upper_loop_table.horizontalHeader()
        # for header_upper_loop_col in range(0,6):
        #     header_upper_loop.setSectionResizeMode(header_upper_loop_col,QHeaderView.Stretch)

        # loop_list = [self.v.loop_table, self.v.upper_loop_table]
        # for table in loop_list:
        #     header_loop = table.horizontalHeader()
        #     for header_col_loop in range(0,7):
        #         header_loop.setSectionResizeMode(header_col_loop,QHeaderView.Stretch)

        # I've forgotten what this was specifically about, but I remember it had something to do with spacing or centering text or something.
        delegate = AlignDelegate(self.variable_table)
        delegate_loop = AlignDelegate(self.loop_table)
        # delegate_loop_up = AlignDelegate(self.v.upper_loop_table)
        self.variable_table.setItemDelegate(delegate)
        self.loop_table.setItemDelegate(delegate_loop)
        # self.v.upper_loop_table.setItemDelegate(delegate_loop_up)

        # Setting the number of rows in each table upon opening the window:
        self.variable_table.setRowCount(len(self.pleth.breath_df))
        self.loop_table.setRowCount(1)
        # self.v.upper_loop_table.setRowCount(1)
        
        row = 0
        # Establishing the dictionary in which the table contents will be stored for delivery to r_config.csv:
        self.pleth.buttonDict_variable = {}

        # Grabbing every item in breath_df and making a row for each: 
        for item in self.pleth.breath_df:
            # Establishing each row as its own group to ensure mutual exclusivity for each row within the table:
            self.pleth.buttonDict_variable[item]={"group": QButtonGroup()}
            # self.buttonDict_variable[item]["group"].buttonClicked.connect(self.check_buttons)

            # The first two columns are the text of the variable name. Alias should be text editable.
            self.pleth.buttonDict_variable[item]["orig"] = QTableWidgetItem(item)
            self.pleth.buttonDict_variable[item]["Alias"] = QTableWidgetItem(item)

            # Creating the radio buttons that will populate the cells in each row:
            self.pleth.buttonDict_variable[item]["Independent"] = QRadioButton("Independent")
            self.pleth.buttonDict_variable[item]["Dependent"] = QRadioButton("Dependent")
            self.pleth.buttonDict_variable[item]["Covariate"] = QRadioButton("Covariate")
            self.pleth.buttonDict_variable[item]["Ignore"] = QRadioButton("Ignore")
            self.pleth.buttonDict_variable[item]["Ignore"].setChecked(True)

            # Adding those radio buttons to the group to ensure mutual exclusivity across the row:
            self.pleth.buttonDict_variable[item]["group"].addButton(self.pleth.buttonDict_variable[item]["Independent"])
            self.pleth.buttonDict_variable[item]["group"].addButton(self.pleth.buttonDict_variable[item]["Dependent"])
            self.pleth.buttonDict_variable[item]["group"].addButton(self.pleth.buttonDict_variable[item]["Covariate"])
            self.pleth.buttonDict_variable[item]["group"].addButton(self.pleth.buttonDict_variable[item]["Ignore"])
            
            # Populating the table widget with the row:
            self.variable_table.setItem(row,0,self.pleth.buttonDict_variable[item]["orig"])
            self.variable_table.setItem(row,1,self.pleth.buttonDict_variable[item]["Alias"])

            self.variable_table.setCellWidget(row,2,self.pleth.buttonDict_variable[item]["Independent"])
            self.variable_table.setCellWidget(row,3,self.pleth.buttonDict_variable[item]["Dependent"])
            self.variable_table.setCellWidget(row,4,self.pleth.buttonDict_variable[item]["Covariate"])
            self.variable_table.setCellWidget(row,5,self.pleth.buttonDict_variable[item]["Ignore"])

            # self.buttonDict_variable[item]["role"] = QComboBox()
            # self.buttonDict_variable[item]["static"] = QComboBox()

            # self.buttonDict_variable[item]["role"].addItems(["","xvar","pointdodge","facet1","facet2"])
            # self.buttonDict_variable[item]["static"].addItems(["","Start Body Temp","Mid Body Temp","End Body Temp","Post Body Temp","Body Weight"])

            # self.v.variable_table.setCellWidget(row,6,self.buttonDict_variable[item]["role"])
            # self.v.variable_table.setCellWidget(row,7,self.buttonDict_variable[item]["static"])

            row += 1
            # you have to iteratively create the widgets for each row, not just iteratively
            # add the widgets for each row because it'll only do the last row
            # so every row's radio button will 
            # self.buttonDict_variable[item]["static"].activated.connect(self.v.replace)
            # self.buttonDict_variable[item]["role"].activated.connect(self.v.replace)
            self.pleth.buttonDict_variable[item]["Independent"].toggled.connect(self.add_combos)
            self.pleth.buttonDict_variable[item]["Covariate"].toggled.connect(self.add_combos)
            # self.pleth.buttonDict_variable[item]["Alias"].textChanged.connect(self.update_alias)
            # self.buttonDict_variable[item]["Covariate"].toggled.connect(self.v.populate_combos(self.buttonDict_variable[item].))
        # Creating the dictionary that will store the cells' statuses based on user selection. The table's need separate dictionaries because they'll be yielding separate csvs:
        # self.loop_menu = {}

        # self.show_loops(self.loop_table,0)
    
    def show_loops(self,table,rows):
        print("config.show_loops()")
        self.pleth.loop_menu = {}
        self.pleth.loop_menu.update({table:{}})
        for row in range(rows):
            print(rows)
            print(row)
            self.pleth.loop_menu[table].update({row:{}})
            print(self.pleth.loop_menu)
            # Creating the widgets within the above dictionary that will populate the cells of each row:
            self.pleth.loop_menu[table][row]["Graph"] = QLineEdit()
            self.pleth.loop_menu[table][row]["Y axis minimum"] = QLineEdit()
            self.pleth.loop_menu[table][row]["Y axis maximum"] = QLineEdit()
            self.pleth.loop_menu[table][row]["Inclusion"] = QComboBox()
            self.pleth.loop_menu[table][row]["Inclusion"].addItems(["No","Yes"])
            for role in self.role_list[1:6]:
                self.pleth.loop_menu[table][row][role] = QComboBox()
                self.pleth.loop_menu[table][row][role].addItems([""])
                self.pleth.loop_menu[table][row][role].addItems([x for x in self.pleth.breath_df])
            
            # self.loop_menu[table][row]["Poincare"] = QComboBox()
            # self.loop_menu[table][row]["Poincare"].addItems(["Yes","No"])
            # self.loop_menu[table][row]["Y axis minimum"] = QComboBox()
            # self.loop_menu[table][row]["Y axis minimum"].addItems(["Automatic",""])
            # self.loop_menu[table][row]["Y axis maximum"] = QComboBox()
            # self.loop_menu[table][row]["Y axis maximum"].addItems(["Automatic",""])
            
            
            # Adding the contents based on the variable list of the drop down menus for the combo box widgets:
            # for role in self.v.role_list:
                # self.loop_menu[table][self.row_loop][role].addItems([""])
                # self.loop_menu[table][self.row_loop][role].addItems([x for x in self.breath_df])
        
            
            # Populating the table cells with their widget content stored in the dictionary:
            # for n in range(0,7):
            #     for role in role_list:
            #         table.setCellWidget(self.row_loop,n,self.loop_menu[table][self.row_loop][role])
            table.setCellWidget(row,0,self.pleth.loop_menu[table][row]["Graph"])
            table.setCellWidget(row,1,self.pleth.loop_menu[table][row]["Variable"])
            table.setCellWidget(row,2,self.pleth.loop_menu[table][row]["Xvar"])
            table.setCellWidget(row,3,self.pleth.loop_menu[table][row]["Pointdodge"])
            table.setCellWidget(row,4,self.pleth.loop_menu[table][row]["Facet1"])
            table.setCellWidget(row,5,self.pleth.loop_menu[table][row]["Facet2"])
            # table.setCellWidget(row,6,self.pleth.loop_menu[table][row]["Poincare"])
            table.setCellWidget(row,6,self.pleth.loop_menu[table][row]["Inclusion"])
            table.setCellWidget(row,7,self.pleth.loop_menu[table][row]["Y axis minimum"])
            table.setCellWidget(row,8,self.pleth.loop_menu[table][row]["Y axis maximum"])

            print(self.pleth.loop_menu)
            # if table == self.loop_table:
            #     self.loop_menu[table][row]["poincare"] = QComboBox()
            #     self.loop_menu[table][row]["poincare"].addItems(["","Yes","No"])
            #     table.setCellWidget(row,6,self.loop_menu[table][row]["poincare"])

    def show_custom(self):
        print("config.show_custom()")
        self.old_deps = self.deps
        self.classy()
        self.deps = self.clades.loc[(self.clades["Dependent"] == 1)]["Alias"]
        print(self.deps)
        print(self.custom_dict)
        if self.custom_dict == {}:
            print("custom dict apparently empty")
            self.pleth.c = Custom(self)
            self.pleth.c.extract_variable()
            # self.pleth.c.show()
        elif set(self.deps) != set(self.old_deps):
            print("custom dict is not empty but new variables chosen")
            self.pleth.c = Custom(self)
            self.pleth.c.extract_variable()
            # self.pleth.c.show()
        else:
            print("custom dict not empty")
            self.pleth.c.show()

    def classy(self):
        print("config.classy()")
        self.clades = pd.DataFrame(columns= ["Column","Alias","Independent","Dependent","Covariate","ymin","ymax","Poincare","Spectral","Transformation"])
        self.clades_graph = pd.DataFrame(columns = ["Alias","Role"])
        self.clades_other = pd.DataFrame(columns = ["Graph","Variable","Xvar","Pointdodge","Facet1","Facet2","ymin","ymax","Filter"])
        # self.mega = self.signals[0].removesuffix(".txt")
        # the above function only works in 3.9 which I have but it throws tantrums so for the sake of having a functioning subwindow:
        origin = []
        self.alias = []
        self.independent = []
        self.dependent = []
        self.covariate = []
        # self.ignore = []

        for item in self.pleth.buttonDict_variable:
            origin.append(item)
            self.alias.append(self.pleth.buttonDict_variable[item]["Alias"].text())
            self.independent.append(self.pleth.buttonDict_variable[item]["Independent"].isChecked())
            self.dependent.append(self.pleth.buttonDict_variable[item]["Dependent"].isChecked())
            self.covariate.append(self.pleth.buttonDict_variable[item]["Covariate"].isChecked())
            
        self.clades["Column"] = origin
        self.clades["Alias"] = self.alias
        self.clades["Independent"] = self.independent
        self.clades["Dependent"] = self.dependent
        self.clades["Covariate"] = self.covariate
        self.clades[["Independent","Dependent","Covariate"]] = self.clades[["Independent","Dependent","Covariate"]].astype(int)
        self.clades[["Poincare","Spectral"]] = self.clades[["Poincare","Spectral"]].fillna(0)

        print('classy clades')
        #     currents=[graph_current,yaxis_current,xvar_current,pd_current,f1_current,f2_current,pc_current]

        #     if graph_current == "":
        #         self.clades_other["Graph"] = f"{yaxis_current} vs {xvar_current}"
        #         print("empty")
        #     else:
        #         self.clades_other.at[self.Plethysmography.row_loop,"Graph"] = graph_current
        #         print("not empty")
        #     if pc_current == "Yes":
        #         currents[6] = 1
        #     else:
        #         currents[6] = 0
        #     for c in range(1,7):
        #         self.clades_other.iat[self.Plethysmography.row_loop,c] = currents[c]
    def update_alias_event(self):
        sbutton = self.sender()
        self.update_alias(sbutton.objectName())
    
    def update_alias(self,donor):
        print(donor)

    def populate_combos(self):
        print("config.populate_combos()")
        self.classy()
        for c in self.settings_dict['role'].keys():
            c.clear()
            c.addItem("Select variable:")
            c.addItems([x for x in self.clades.loc[(self.clades["Independent"] == 1) | (self.clades['Covariate'] == 1)]['Alias']])
    
    def add_combos(self):
        print("add_combos()")
        self.classy()
        current = {}
        for c in self.settings_dict['role'].keys():
            # current.update({c:c.currentText()})
            c.clear()
            c.addItem("Select variable:")
            c.addItems([x for x in self.clades.loc[(self.clades["Independent"] == 1) | (self.clades['Covariate'] == 1)]['Alias']])
            # c.setCurrentText(current[c])
        # print([x for x in self.clades.loc[(self.clades["Independent"] == 1) | (self.clades['Covariate'] == 1)]['Alias']])
    
    def exclude_combos(self):
        print("exclude_combos()")
        for c in self.settings_dict['role'].keys():
            print(c)

    def graphy(self):
        print("config.graphy()")
        clades_role_dict = {}
        for col in self.role_list[2:6]:
            if self.settings_dict["rel"][col].currentText() == "Select variable:":
                clades_role_dict.update({self.settings_dict["role"][self.settings_dict["rel"][col]]:""})
            else:
                clades_role_dict.update({self.settings_dict["role"][self.settings_dict["rel"][col]]: self.settings_dict["rel"][col].currentText()})
        # print(clades_role_dict)
        self.clades_graph = pd.DataFrame.from_dict(clades_role_dict,orient='index').reset_index()
        self.clades_graph.columns = ['Role','Alias']
        print(f'graph clades:{self.clades_graph.columns}')
    
    def othery(self):
        print("config.othery()")
        clades_other_dict = {}
        for row in range(self.loop_table.rowCount()):
            clades_other_dict.update({row:{}})
            for r in [0,7,8]:
                clades_other_dict[row].update({self.role_list[r]: self.pleth.loop_menu[self.loop_table][row][self.role_list[r]].text()})
            for col in self.role_list[1:7]:
                clades_other_dict[row].update({col: self.pleth.loop_menu[self.loop_table][row][col].currentText()})
            if clades_other_dict[row]['Inclusion'] == 'Yes':
                clades_other_dict[row]['Inclusion'] = 1
            else:
                clades_other_dict[row]['Inclusion'] = 0   
        # print(clades_other_dict)
        self.clades_other = pd.DataFrame.from_dict(clades_other_dict)
        # print(self.clades_other)
        self.clades_other = self.clades_other.transpose()
        if self.feature_combo.currentText() != "None":
            if self.feature_combo.currentText() == "All":
                self.clades_other.at[self.loop_table.rowCount()-1,"Graph"] = "Apneas"
                self.clades_other.at[self.loop_table.rowCount(),"Graph"] = "Sighs"
            else:
                self.clades_other.at[self.loop_table.rowCount()-1,"Graph"] = self.feature_combo.currentText()
        print(f'other clades:{self.clades_other.columns}')
        # self.clades_graph.columns = ['Alias','Role']
        # if self.feature_combo.currentText() == "All":
            # self.clades_other
    
    # def update_custom(self):

    
#     def combo_save(self):
        
#         if self.Poincare_combo.currentText() == "All":
#             self.clades.loc[(self.clades["Dependent"] == 1),"Poincare"] = 1
#         if self.Spectral_combo.currentText() == "All":
#             self.clades.loc[(self.clades["Dependent"] == 1),"Spectral"] = 1
#         if self.transform_combo.currentText() != "":

#         elif "CheckableComboBox" in str(type(self.config.custom_dict[item][col])):
#                     # print(self.config.custom_dict[item][col].currentData())
#                     # print(self.config.custom_dict[item][col].currentData()[0])
#                     # tran = self.config.custom_dict[item][col].currentData()
#                     self.config.custom_port[item].update({col:self.config.custom_dict[item][col].currentData()})     

# if self.vdf[k]['Transformation'] != "":
#                 transform = [s.replace("non","raw") and s.replace("log","ln") for s in self.vdf[k]['Transformation'].split('@')]
#                 transform = [z.replace("ln10","log10") for z in transform]
#                 # print(transform)
#                 # print(','.join([t for t in transform]))
#                 self.custom_dict[k]['Transformation'].loadCustom(transform)
#                 self.custom_dict[k]['Transformation'].updateText()
#                 self.transform_combo.setCurrentText("Custom")

        
    def classy_save(self):
        print("config.classy_save()")
        # print(f'cons: {self.pleth.cons}')
        # print(f'configs: {self.configs}')
        # print(f'v:{self.pleth.variable_config}')
        # print(f'g:{self.pleth.graph_config}')
        # print(f'o:{self.pleth.other_config}')
        # Grabbing the user's selections from the widgets and storing them in dataframes:
        self.classy()
        # # print(self.clades)
        # self.show_custom()
        if self.custom_port == {}:
            print("empty custom") 
            self.pleth.c = Custom(self)
            self.show_custom()
            self.pleth.c.save_custom()
        else:
            # Custom.save_custom(self)
            for cladcol in self.clades:
                for item in self.custom_port:
                    for col in self.custom_port[item]:
                        if col is "Irregularity":
                            if self.custom_port[item][col] == 1:
                                print("irregularity is 1")
                                # print(self.clades.loc[(self.clades["Alias"] == self.pleth.c.custom_port[item]["Alias"]),"Column"].values)
                                print(f'Irreg_Score_{self.clades.loc[(self.clades["Alias"] == self.custom_port[item]["Alias"]),"Column"].values[0]}')
                                irr = f'Irreg_Score_{self.clades.loc[(self.clades["Alias"] == self.custom_port[item]["Alias"]),"Column"].values[0]}'
                                print(irr)
                                if irr in self.clades["Column"]:
                                    print("irreg found")
                                    self.clades.loc[(self.clades["Column"] == f'Irreg_Score_{self.clades.loc[(self.clades["Alias"] == self.custom_port[item]["Alias"]),"Column"].values[0]}'),"Dependent"] == 1 
                                else:
                                    print("no irreg")
                        elif col is "Transformation":
                            self.custom_port[item][col] = [x.replace("raw","non") for x in self.custom_port[item][col]]
                            self.custom_port[item][col] = [x.replace("ln","log") for x in self.custom_port[item][col]]
                            # print(self.custom_port[item][col])
                            # print("@".join(self.custom_port[item][col]))
                            # if len(self.custom_port[item][col])>1:
                            self.clades.loc[(self.clades["Alias"] == self.custom_port[item]["Alias"]) & (cladcol == col),cladcol] = "@".join(self.custom_port[item][col])
                            # # elif len(self.custom_port[item][col])==1:
                            # #     self.clades.loc[(self.clades["Alias"] == self.custom_port[item]["Alias"]) & (cladcol == col),cladcol] = self.custom_port[item][col][0]
                            # else:
                            #     # print(f'CladAlias: {self.clades["Alias"]}')
                            #     print(f'Port Alias: {self.custom_port[item]["Alias"]}')
                            #     print(f'Col: {self.custom_port[item][col]}')
                            #     # print(f'Cladcol: {self.clades[cladcol]}')
                            #     # print(self.clades.loc[(self.clades["Alias"] == self.custom_port[item]["Alias"]) & (cladcol == col),cladcol])
                            #     self.clades.loc[(self.clades["Alias"] == self.custom_port[item]["Alias"]), col] = self.custom_port[item][col]
                        else:
                            self.clades.loc[(self.clades["Alias"] == self.custom_port[item]["Alias"]),col] = self.custom_port[item][col]
        
        
        # if self.irreg_combo.currentText() == "All":
            # self.clades.loc[(self.clades["Dependent"] == 1),"Irregularity"] = 1 
        self.configs["variable_config"].update({"df":self.clades})
        self.graphy()
        self.configs["graph_config"].update({"df":self.clades_graph})
        self.othery()
        self.configs["other_config"].update({"df":self.clades_other})
        # Converting the values for these columns from boolean to 0s and 1s:
        # self.clades[["Independent","Dependent","Covariate"]] = self.clades[["Independent","Dependent","Covariate"]].astype(int)
        # Assigning paths within the mothership to Pleth variables that will be arguments for breathcaller:
        # self.pleth.variable_config = os.path.join(self.pleth.mothership, "R_config/variable_config.csv")
        # self.pleth.graph_config = os.path.join(self.pleth.mothership, "R_config/graph_config.csv")
        # self.pleth.other_config = os.path.join(self.pleth.mothership, "R_config/other_config.csv")
        
        # print(f'configs refresh:{self.configs}')
        # print(f'clades:{self.clades.columns}')
        # having columns named true or false will fuck up our code
        # Saving the dataframes holding the configuration preferences to csvs and assigning them their paths:
        
    def save_config(self):
        print("config.save_config()")
        thumbholes = []
        self.classy_save()
        self.pleth.dir_checker(self.pleth.output_dir_r,self.pleth.r_output_folder,"STAGG")
        if self.pleth.output_folder != "":
            self.pleth.output_dir_r = self.pleth.output_folder
        print(self.pleth.output_dir_r)
        # for path in self.configs
        for key in self.configs:
            print(f'path: {self.configs[key]["path"]}')
        #         if os.path.basename(self.configs[key]["path"]).startswith(str(path).split('.')[2]):
        #             path = self.configs[key]["path"]
            # if self.pleth.mothership == "":
            #     self.pleth.mothership = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output")
            # if Path(self.pleth.mothership).exists():
            #     try:
            #         if Path(os.path.join(self.pleth.mothership,'STAGG_config')).exists():
            #             self.configs[key]["df"].to_csv(os.path.join(self.pleth.mothership, f'STAGG_config/{key}.csv'),index=False)
            #         else:
            #             Path(os.path.join(self.pleth.mothership,'STAGG_config')).mkdir()
            #             self.configs[key]["df"].to_csv(os.path.join(self.pleth.mothership, f'STAGG_config/{key}.csv'),index=False)
            #     except PermissionError as e:
            #         print(f'{type(e).__name__}: {e}')
            #         thumbholes.append(self.configs[key]["path"])
            #         pass
            try:
                if self.configs[key]["path"] == "":
                    self.configs[key]["path"] = os.path.join(self.pleth.output_dir_r,f"{key}_{os.path.basename(self.pleth.output_dir_r).lstrip('STAGG_output')}.csv")
                try:
                    self.configs[key]["df"].to_csv(self.configs[key]["path"],index=False)
                except PermissionError as e:
                    print(f'{type(e).__name__}: {e}')
                    thumbholes.append(self.configs[key]["path"])
                    pass
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                self.saveas_config()
            if self.pleth.mothership == "":
                self.mothership = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output")
            if Path(self.pleth.mothership).exists():
                try:
                    if Path(os.path.join(self.pleth.mothership,'STAGG_config')).exists():
                        self.configs[key]["df"].to_csv(os.path.join(self.pleth.mothership, f'STAGG_config/{key}.csv'),index=False)
                    else:
                        Path(os.path.join(self.pleth.mothership,'STAGG_config')).mkdir()
                        self.configs[key]["df"].to_csv(os.path.join(self.pleth.mothership, f'STAGG_config/{key}.csv'),index=False)
                except PermissionError as e:
                    print(f'{type(e).__name__}: {e}')
                    thumbholes.append(self.configs[key]["path"])
                    pass
    
        if len(thumbholes)>0:
            self.thumb = Thumbass(self)
            self.thumb.show()
            self.thumb.message_received("File in use",f"One or more of the files selected is open in another program:\n{os.linesep.join([os.path.basename(thumb) for thumb in set(thumbholes)])}")

        for f in self.configs:
            for item in self.pleth.variable_list.findItems(f,Qt.MatchContains):
                self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
            self.pleth.variable_list.addItem(self.configs[f]['path'])
        for item in self.pleth.variable_list.findItems("Configuration files not detected.",Qt.MatchExactly):
            self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
        print(self.pleth.output_dir_r)
    # If I load previously made things, I have paths but they haven't been assigned. I assign them above. They'll overwrite the files they're editing. 
    
    def saveas_config(self):
        print("config.saveas_config()")
        thumbholes = []
        self.classy_save()
        self.pleth.dir_checker(self.pleth.output_dir_r,self.pleth.r_output_folder,"STAGG")
        # for p in [self.pleth.variable_config,self.pleth.graph_config,self.pleth.other_config]:
        #     for c in self.pleth.cons:
        #         if os.path.basename(self.pleth.cons[c]).startswith(str(p).split('.')[2]):
        #             p = self.pleth.cons[c]
            
        if Path(os.path.join(self.pleth.mothership,'STAGG_config')).exists():
            auto_save_path = os.path.join(self.pleth.mothership,'STAGG_config')
            print("r config found")
        if Path(self.pleth.output_dir_r).exists():
            save_path = self.pleth.output_dir_r
            print("output dir r found")
        elif Path(self.pleth.r_output_folder).exists():
            save_path = self.pleth.r_output_folder
            print("r output folder found")
        elif Path(self.pleth.mothership).exists():
            print("mothership found")
            save_path = self.mothership
        else:
            save_path = str(self.mothership)
            print("no one found")
        
        save_dir = QFileDialog.getExistingDirectory(self, 'Choose directory for STAGG configuration files', save_path)

        if not save_dir:
            print("saveas_config canceled")
        else:
            # self.pleth.variable_config = os.path.join(save_dir, 'variable_config_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')
            self.configs['variable_config']['path'] = os.path.join(save_dir, 'variable_config_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')
            # self.pleth.graph_config = os.path.join(save_dir, 'graph_config_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')
            self.configs['graph_config']['path'] = os.path.join(save_dir, 'graph_config_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')
            # self.pleth.other_config = os.path.join(save_dir, 'other_config_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')
            self.configs['other_config']['path'] = os.path.join(save_dir, 'other_config_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')

            for key in self.configs:
                try:
                    self.configs[key]["df"].to_csv(self.configs[key]["path"],index=False)
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    thumbholes.append(self.configs[key]["path"])
                    pass
                if self.pleth.mothership == "":
                    self.mothership = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output")
                if Path(self.pleth.mothership).exists():
                    try:
                        if Path(os.path.join(self.pleth.mothership,'STAGG_config')).exists():
                            self.configs[key]["df"].to_csv(os.path.join(self.pleth.mothership, f'STAGG_config/{key}.csv'),index=False)
                        else:
                            Path(os.path.join(self.pleth.mothership,'STAGG_config')).mkdir()
                            self.configs[key]["df"].to_csv(os.path.join(self.pleth.mothership, f'STAGG_config/{key}.csv'),index=False)
                    except PermissionError as e:
                        print(f'{type(e).__name__}: {e}')
                        thumbholes.append(self.configs[key]["path"])
                        pass
            
            if len(thumbholes)>0:
                self.thumb = Thumbass(self)
                self.thumb.show()
                self.thumb.message_received("File in use",f"One or more of the files selected is open in another program:\n{os.linesep.join([os.path.basename(thumb) for thumb in set(thumbholes)])}")
            
            # Clearing the config panel of the mainGUI and adding to it to reflect changes:
            for f in self.configs:
                for item in self.pleth.variable_list.findItems(f,Qt.MatchContains):
                    self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                self.pleth.variable_list.addItem(self.configs[f]['path'])
            for item in self.pleth.variable_list.findItems("Configuration files not detected.",Qt.MatchExactly):
                self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))

    # retired
    def add_upper_loop(self):
        print("config.add_upper_loop()")
        self.classy()
        self.upper_loop_table.removeRow(0)
        self.upper_loop_table.insertRow(0)
        # self.Plethysmography.row_loop = 0

        # Setting up graph name cell of upper loop table so that it says the title's will be supplied automatically (STaGG takes care of this) and to make the text read only:
        self.pleth.loop_menu[self.upper_loop_table][0]["Graph"] = QLineEdit()
        self.pleth.loop_menu[self.upper_loop_table][0]["Graph"].setText("Automated")
        self.pleth.loop_menu[self.upper_loop_table][0]["Graph"].setReadOnly(True)
        self.upper_loop_table.setCellWidget(0,0,self.pleth.loop_menu[self.upper_loop_table][0]["Graph"])
        # Setting up the yaxis cell of the upper loop table so that it lists in it dropdown menu all the selected dependents, but the active text says selected folks only and this is also read only:
        self.pleth.loop_menu[self.upper_loop_table][0]["Variable"] = QComboBox()
        self.pleth.loop_menu[self.upper_loop_table][0]["Variable"].addItems(["Selected dependent variables"])
        self.upper_loop_table.setCellWidget(0,1,self.pleth.loop_menu[self.upper_loop_table][0]["Variable"])
        # Setting up the poincare cell of the upper loop table:
        # self.Plethysmography.loop_menu[self.upper_loop_table][0]["poincare"] = QComboBox()
        # self.Plethysmography.loop_menu[self.upper_loop_table][0]["poincare"].addItems(["","Yes","No"])
        # self.upper_loop_table.setCellWidget(0,6,self.Plethysmography.loop_menu[self.upper_loop_table][0]["poincare"])
        # Setting up the remaining cells of the upper loop table:
        for role in self.role_list[2:6]:
            self.pleth.loop_menu[self.upper_loop_table][0][role] = QComboBox()
            self.pleth.loop_menu[self.upper_loop_table][0][role].addItems([""])
            # Restricting the drop down menu to the user's selection of indepedent and covariate variables:
            self.pleth.loop_menu[self.upper_loop_table][0][role].addItems([x for x in self.clades.loc[(self.clades['Independent'] == 1) | (self.clades['Covariate'] == 1)]['Alias']])
        # Populating the upper loop table with the widgets created above:
        self.upper_loop_table.setCellWidget(0,2,self.pleth.loop_menu[self.upper_loop_table][0]["Xvar"])
        self.upper_loop_table.setCellWidget(0,3,self.pleth.loop_menu[self.upper_loop_table][0]["Pointdodge"])
        self.upper_loop_table.setCellWidget(0,4,self.pleth.loop_menu[self.upper_loop_table][0]["Facet1"])
        self.upper_loop_table.setCellWidget(0,5,self.pleth.loop_menu[self.upper_loop_table][0]["Facet2"])
        # self.upper_loop_table.setCellWidget(0,6,self.Plethysmography.loop_menu[self.upper_loop_table][0]["poincare"])

    def add_loop(self):
        print("config.add_loop()")
        # It isn't working and I think the issue is that self.Pleth.row_loop is tied to the dictionary so when you're using the dictionary you're asking for a row that doesn't exist as a key:
        loop_row = self.loop_table.rowCount()
        self.loop_table.insertRow(loop_row)
        self.pleth.loop_menu[self.loop_table].update({loop_row: {"Graph": QLineEdit()}})
        # self.pleth.loop_menu[self.loop_table][loop_row]["Graph"].setText("New model")
        # self.Plethysmography.loop_menu[self.loop_table].update({1: {"graph": "pickle"}})
        self.loop_table.setCellWidget(loop_row,0,self.pleth.loop_menu[self.loop_table][loop_row]["Graph"])
        # self.pleth.loop_menu[self.loop_table][loop_row].update({"Poincare": QComboBox()})
        # self.pleth.loop_menu[self.loop_table][loop_row]["Poincare"].addItems(["","Yes","No"])
        # self.loop_table.setCellWidget(loop_row,6,self.pleth.loop_menu[self.loop_table][loop_row]["Poincare"])
        self.pleth.loop_menu[self.loop_table][loop_row].update({"Y axis minimum": QLineEdit()})
        # self.pleth.loop_menu[self.loop_table][loop_row]["Y axis minimum"].addItems(["Automatic",""])
        self.loop_table.setCellWidget(loop_row,7,self.pleth.loop_menu[self.loop_table][loop_row]["Y axis minimum"])
        self.pleth.loop_menu[self.loop_table][loop_row].update({"Y axis maximum": QLineEdit()})
        # self.pleth.loop_menu[self.loop_table][loop_row]["Y axis maximum"].addItems(["Automatic",""])
        self.loop_table.setCellWidget(loop_row,8,self.pleth.loop_menu[self.loop_table][loop_row]["Y axis maximum"])
        self.pleth.loop_menu[self.loop_table][loop_row].update({"Inclusion": QComboBox()})
        self.pleth.loop_menu[self.loop_table][loop_row]["Inclusion"].addItems(["No","Yes"])
        self.loop_table.setCellWidget(loop_row,6,self.pleth.loop_menu[self.loop_table][loop_row]["Inclusion"])

        for role in self.role_list[1:6]:
            self.pleth.loop_menu[self.loop_table][loop_row][role] = QComboBox()
            self.pleth.loop_menu[self.loop_table][loop_row][role].addItems([""])
            self.pleth.loop_menu[self.loop_table][loop_row][role].addItems([x for x in self.pleth.breath_df])
        
        self.loop_table.setCellWidget(loop_row,1,self.pleth.loop_menu[self.loop_table][loop_row]["Variable"])
        self.loop_table.setCellWidget(loop_row,2,self.pleth.loop_menu[self.loop_table][loop_row]["Xvar"])
        self.loop_table.setCellWidget(loop_row,3,self.pleth.loop_menu[self.loop_table][loop_row]["Pointdodge"])
        self.loop_table.setCellWidget(loop_row,4,self.pleth.loop_menu[self.loop_table][loop_row]["Facet1"])
        self.loop_table.setCellWidget(loop_row,5,self.pleth.loop_menu[self.loop_table][loop_row]["Facet2"])

    def reset_config(self):
        print("config.reset_config()")
        try:
            self.setup_variables_config()
            self.setup_table_config()
            self.show_loops(self.loop_table,0)
            for s in self.settings_dict['role']:
                s.clear()
                s.addItem("Select variable:")
            for p in self.additional_dict:
                p.setCurrentText("None")
            # self.baddies = []
            # self.goodies = []
            # self.configs = {self.pleth.variable_config:self.clades,self.pleth.graph_config:self.clades_graph,self.pleth.other_config:self.clades_other}
            # self.custom_dict = {}
            self.deps = []
            self.deps = self.clades.loc[(self.clades["Dependent"] == 1)]["Alias"]
            self.pleth.c.populate_table(self.deps,self.pleth.c.custom_table)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print("Apparently reset_config only knows how to land by crashing into objects like my bird. I don't understand why this except makes things work, and that makes me uncomfortable.")

    def to_check_load_variable_config(self):
        self.check_load_variable_config("yes")

    def check_load_variable_config(self,open_file):
        paths = []
        print("self.check_load_variable_config has started")
        if open_file == "yes":
        # Groping around to find a convenient directory:
        
            if Path(os.path.join(self.pleth.mothership,'STAGG_config')).exists():
                load_path = os.path.join(self.pleth.mothership,'STAGG_config')
            elif Path(self.pleth.mothership).exists():
                load_path = self.pleth.mothership
            else:
                load_path = str(os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/STAGG_config"))

            # Opens open file dialog
            file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/")))
            paths = file_name[0]
        elif open_file == "no":
            paths = [self.configs[p]["path"] for p in self.configs]
        if paths == []:
            print("no file selected")
        else:
            # self.pleth.variable_list.clear()
            for x in range(len(paths)):
                print(x)
                for key in self.configs:
                    if key in paths[x]:
                        print(key)
                        if Path(paths[x]).is_file():
                            print(f'{paths[x]} is a real file')
                            if paths[x].endswith('.csv') or paths[x].endswith('.xlsx'):
                                print(f'{paths[x]} ends with .xlsx or .csv')
                                if os.path.basename(paths[x]).startswith(key):
                                    print(f'{paths[x]} starts with {key}')
                                    if paths[x] in self.goodies:
                                        self.goodies.remove(paths[x])
                                    if paths[x] in self.baddies:
                                        self.baddies.remove(paths[x])
                                    if key in self.goodies:
                                        self.goodies.remove(key)
                                    if key in self.baddies:
                                        self.baddies.remove(key)
                                    self.configs[key]["path"] = paths[x]
                                    for item in self.pleth.variable_list.findItems(key,Qt.MatchContains):
                                        self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                                    self.pleth.variable_list.addItem(self.configs[key]["path"])
                                    self.goodies.append(key)
                                else:
                                    print(f'{paths[x]} does not start with {key}')
                                    if paths[x] in self.baddies:
                                        self.baddies.remove(paths[x])
                                    self.baddies.append(paths[x])
                                    if len(self.baddies)>0:
                                        print(f'baddies got {paths[x]} cause it does not start with {key}')
                                        self.thumb = Thumbass(self.pleth)
                                        self.thumb.show()
                                        self.thumb.message_received("Wrong file name",f"""One or more of the files selected is cannot be recognized:\n{os.linesep.join([b for b in self.baddies])}\nPlease rename the file(s) as described in the <a href="https://github.com/">documentation</a> or select a different file.""")
                                    
                            else:
                                print(f'{paths[x]} does not end with .xlsx or .csv')
                                if paths[x] in self.baddies:
                                    self.baddies.remove(paths[x])
                                self.baddies.append(paths[x])
                                if len(self.baddies)>0:
                                    print(f'baddies got {paths[x]} cause it does not end with .xlsx or .csv')
                                    self.thumb = Thumbass(self.pleth)
                                    self.thumb.show()
                                    self.thumb.message_received("Incorrect file format",f"One or more of the files selected is not in the correct file format:\n{os.linesep.join([b for b in self.baddies])}\nOnly .csv or .xlsx are accepted.")
                        else:
                            print(f'{paths[x]} is not a real file')
                            if paths[x] in self.baddies:
                                self.baddies.remove(paths[x])
                            self.baddies.append(paths[x])
                            if len(self.baddies)>0:
                                print(f'baddies got {paths[x]} cause it is not a real file')
                                self.thumb = Thumbass(self.pleth)
                                self.thumb.show()
                                self.thumb.message_received("Files not found", f"One or more of the files selected cannot be found:\n{os.linesep.join([b for b in self.baddies])}")
            print(f'goodies: {self.goodies}')
            print(f'baddies: {self.baddies}')
            if "variable_config" in self.goodies:
                try:
                    self.load_variable_config()
                    # try:
                    #     print("setting checks")
                    #     self.vdf.update({dict(row)['Column']:dict(row)})
                    #     self.pleth.buttonDict_variable[dict(row)['Column']]["Alias"].setText(dict(row)["Alias"])
                    #     self.pleth.buttonDict_variable[dict(row)['Column']][k].setChecked(True)
                    #     print("button dict checked")
                    # except KeyError as e:
                    #     print("this error?")
                    #     print(f'{type(e).__name__}: {e}')
                    #     pass
                    for item in self.pleth.variable_list.findItems("Configuration files not detected.",Qt.MatchExactly):
                        self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                    for item in self.pleth.variable_list.findItems("variable_config",Qt.MatchContains):
                        self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                    self.pleth.variable_list.addItem(self.configs["variable_config"]['path'])
                except KeyError as e:
                    print(f'{type(e).__name__}: {e}')
                    self.goodies.remove("variable_config")
                    self.baddies.append("variable_config")
                    print(f'baddies got "variable_config" because of a key error')
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
            if "graph_config" in self.goodies:
                try:
                    self.load_graph_config()
                    for item in self.pleth.variable_list.findItems("Configuration files not detected.",Qt.MatchExactly):
                        self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                    for item in self.pleth.variable_list.findItems("graph_config",Qt.MatchContains):
                        self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                    self.pleth.variable_list.addItem(self.configs["graph_config"]['path'])
                except KeyError as e:
                    print(f'{type(e).__name__}: {e}')
                    self.goodies.remove("graph_config")
                    self.baddies.append("graph_config")
                    print(f'baddies got "graph_config" because of a key error')
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
            if "other_config" in self.goodies:
                try:
                    self.load_other_config()
                    for item in self.pleth.variable_list.findItems("Configuration files not detected.",Qt.MatchExactly):
                        self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                    for item in self.pleth.variable_list.findItems("other_config",Qt.MatchContains):
                        self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                    self.pleth.variable_list.addItem(self.configs["other_config"]['path'])
                except KeyError as e:
                    print(f'{type(e).__name__}: {e}')
                    self.goodies.remove("other_config")
                    self.baddies.append("other_config")
                    print(f'baddies got "other_config" because of a key error')
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
        if len(self.baddies)>0:
            print(f'baddies got something because of a key error')
            print(self.baddies)
            self.thumb = Thumbass(self.pleth)
            self.thumb.show()
            documentation = '<a href="https://github.com/">documentation</a>'
            self.thumb.message_received("Error reading file",f"""One or more of the files selected is not formatted correctly:<br><br>{os.linesep.join([self.configs[b]['path'] for b in self.baddies])}<br><br>Please refer to the <a href="https://github.com/">documentation</a> for structuring your data.""")
        # self.load_variable_config()     
        print("self.check_load_variable_config() has finished")

    def load_variable_config(self):
        print("loading variable config")
        if self.configs["variable_config"]["path"].endswith(".xlsx"):
            xl = pd.read_excel(self.configs["variable_config"]["path"])
            xl.to_csv(f'{os.path.splitext(self.configs["variable_config"]["path"])[0]}.csv')
        self.pleth.breath_df = pd.read_csv(f'{os.path.splitext(self.configs["variable_config"]["path"])[0]}.csv')['Column'].tolist()
        self.setup_table_config()
        self.vdf = {}
        with open(self.configs["variable_config"]["path"],'r') as f:
            r = csv.DictReader(f)
            for row in r:
                for k in dict(row):
                    if dict(row)[k] == "1":
                        self.vdf.update({dict(row)['Column']:dict(row)})
                        # try:
                        #     print("setting checks")
                        #     self.pleth.buttonDict_variable[dict(row)['Column']]["Alias"].setText(dict(row)["Alias"])
                        #     self.pleth.buttonDict_variable[dict(row)['Column']][k].setChecked(True)
                        #     print("button dict checked")
                        # except KeyError as e:
                        #     print("this error?")
                        #     print(f'{type(e).__name__}: {e}')
                        #     pass
                        # self.pleth.buttonDict_variable[dict(row)['Column']]["Alias"].setText(dict(row)["Alias"])
        print(self.vdf)
        for a in self.vdf:
            self.pleth.buttonDict_variable[a]['Alias'].setText(self.vdf[a]['Alias'])
            for k in ["Independent","Dependent","Covariate"]:
                if self.vdf[a][k] == '1':
                    self.pleth.buttonDict_variable[a][k].setChecked(True)
        self.load_custom_config()

    def load_custom_config(self):
        print("loading custom config")
        for p in self.additional_dict:
            p.setCurrentText("None")
        # self.classy()
        # deps = self.clades.loc[(self.clades["Dependent"] == 1)]["Alias"]
        self.deps = [self.vdf[a]['Alias'] for a in self.vdf if self.vdf[a]['Dependent'] == '1']
        print(f'self.deps: {self.deps}')
        self.custom_dict = {}
        self.pleth.c = Custom(self)
        self.pleth.c.populate_table(self.deps,self.pleth.c.custom_table)
        # print(self.custom_dict)
        for k in self.vdf:
            # for v in ['Poincare','Spectral']:
            if self.vdf[k]['Poincare'] == "1":
                self.custom_dict[k]['Poincare'].setChecked(True)
                self.Poincare_combo.setCurrentText("Custom")
            if self.vdf[k]['Spectral'] == "1":
                self.custom_dict[k]['Spectral'].setChecked(True)
                self.Spectral_combo.setCurrentText("Custom")
            for y in ['ymin','ymax']:
                if self.vdf[k][y] != "":
                    self.custom_dict[k][y].setText(self.vdf[k][y])
            if self.vdf[k]['Transformation'] != "":
                transform = [s.replace("non","raw") and s.replace("log","ln") for s in self.vdf[k]['Transformation'].split('@')]
                transform = [z.replace("ln10","log10") for z in transform]
                # print(transform)
                # print(','.join([t for t in transform]))
                self.custom_dict[k]['Transformation'].loadCustom(transform)
                self.custom_dict[k]['Transformation'].updateText()
                self.transform_combo.setCurrentText("Custom")
        
    def load_graph_config(self):
        print("loading graph config")
        gdf = pd.read_csv(self.configs["graph_config"]["path"], index_col=False)
        if "variable_config" in self.goodies:
            print("vc avail")
            for c in self.settings_dict['role']:
                c.clear()
                c.addItem("Select variable:")
                c.addItems([[self.vdf[k]["Alias"] for k in self.vdf if self.vdf[k][v] == "1"] for v in ["Independent","Covariate"]][0])
                try:
                    c.setCurrentText([x for x in gdf.loc[(gdf['Role'] == self.settings_dict['role'][c])]['Alias'] if pd.notna(x) == True][0])
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print("program can't handle nan in gdf for some reason. so if there aren't four graph roles chosen, current text doesn't indicate selections. nvm i just fixed it. it needed a hallpass")
                    pass
        else:
            print("alone")
            for c in self.settings_dict['role']:
                c.clear()
                c.addItem("Select variable:")
                c.addItems([x for x in gdf['Alias'] if pd.notna(x) == True])
                # print([x for x in gdf.loc[(gdf['Role'] == self.settings_dict['role'][c])]['Alias'] if pd.notna(x) == True])
                try:
                    c.setCurrentText([x for x in gdf.loc[(gdf['Role'] == self.settings_dict['role'][c])]['Alias'] if pd.notna(x) == True][0])
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print("program can't handle nan in gdf for some reason. so if there aren't four graph roles chosen, current text doesn't indicate selections. nvm i just fixed it. it needed a hallpass")
                    pass
            try:
                for c in self.settings_dict['role']:
               # print([x for x in gdf.loc[(gdf['Role'] == self.settings_dict['role'][c])]['Alias'] if pd.notna(x) == True][0])
                    c.setCurrentText([x for x in gdf.loc[(gdf['Role'] == self.settings_dict['role'][c])]['Alias'] if pd.notna(x) == True])
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
            

    def load_other_config(self):
        print("loading other config")
        odf = pd.read_csv(self.configs["other_config"]['path'], index_col=False)
        self.feature_combo.setCurrentText("None")
        if "Apneas" in set(odf["Graph"]):
            # print("Apneas")
            self.feature_combo.setCurrentText("Apneas")
        if "Sighs" in set(odf["Graph"]):
            # print("Sighs")
            self.feature_combo.setCurrentText("Sighs") 
        if ("Apneas" and "Sighs") in set(odf["Graph"]):
            # print("All")
            self.feature_combo.setCurrentText("All")
        self.show_loops(self.loop_table,len(odf))
        if len(odf)>1:
            
            print(len(odf))
            # self.loop_table.setRowCount(len(odf))
            for row_1 in range(len(odf)):
                self.loop_table.cellWidget(row_1,0).setText(str(odf.at[row_1,'Graph']))
                self.loop_table.cellWidget(row_1,7).setText(str(odf.at[row_1,'Y axis minimum']))
                self.loop_table.cellWidget(row_1,8).setText(str(odf.at[row_1,'Y axis maximum']))
                self.loop_table.cellWidget(row_1,1).setCurrentText(str(odf.at[row_1,'Variable']))
                self.loop_table.cellWidget(row_1,2).setCurrentText(str(odf.at[row_1,'Xvar']))
                self.loop_table.cellWidget(row_1,3).setCurrentText(str(odf.at[row_1,'Pointdodge']))
                self.loop_table.cellWidget(row_1,4).setCurrentText(str(odf.at[row_1,'Facet1']))
                self.loop_table.cellWidget(row_1,5).setCurrentText(str(odf.at[row_1,'Facet2']))
                if odf.at[row_1,'Inclusion'] == 1:
                    self.loop_table.cellWidget(row_1,6).setCurrentText("Yes")
                else:
                    self.loop_table.cellWidget(row_1,6).setCurrentText("No")
                if row_1 < (len(odf)-1):
                    try:
                        self.add_loop()
                    except Exception as e:
                        print("no added loop")
                        print(f'{type(e).__name__}: {e}')
        # Iterating over everything and their grandmother takes forever. I should look into a more efficient way of populating the table from loaded specs.
        # toc=datetime.datetime.now()
        # print(toc-tic)

    def replace(self):
        print("config.replace()")
        current_combo = self.variable_table.cellWidget(self.variable_table.currentRow(), self.variable_table.currentColumn())
        if current_combo.currentText() in self.pleth.stack:
            for item in self.buttonDict_variable:
                if self.buttonDict_variable[item]["role"] != current_combo:
                    if self.buttonDict_variable[item]["role"].currentText() == current_combo.currentText():
                        self.buttonDict_variable[item]["role"].setCurrentText("") 
                if self.buttonDict_variable[item]["self.static"] != current_combo:
                    if self.buttonDict_variable[item]["self.static"].currentText() == current_combo.currentText():
                        self.buttonDict_variable[item]["self.static"].setCurrentText("")
        #     stack.append(self.buttonDict_variable)[item]["dynamic"].currentText())
        #     dynamic.append(self.buttonDict_variable[item]["dynamic"].currentText())
            # self.static.append(self.buttonDict_variable[item]["self.static"].currentText())
        else:
            self.pleth.stack.append(current_combo.currentText())

    def checkable_ind(self,state):
        try:
            print("true")
            for selected_rows in self.variable_table.selectedRanges():
                for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
                    self.variable_table.cellWidget(row,2).setChecked(True)
                    # that took me an hour to figure out WOOOOO 
        except:
            print("nope")
        # 
    def checkable_dep(self):
        try:
            for selected_rows in self.variable_table.selectedRanges():
                for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
                    self.variable_table.cellWidget(row,3).setChecked(True)
                    # that took me an hour to figure out WOOOOO 
        except:
            print("nope")
        
    def checkable_cov(self):
        try:
            for selected_rows in self.variable_table.selectedRanges():
                for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
                    self.variable_table.cellWidget(row,4).setChecked(True)
                    # that took me an hour to figure out WOOOOO 
        except:
            print("nope")

    def checkable_ign(self):
        try:
            for selected_rows in self.variable_table.selectedRanges():
                for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
                    self.variable_table.cellWidget(row,5).setChecked(True)
                    # that took me an hour to figure out WOOOOO 
        except:
            print("nope")
#endregion

class Plethysmography(QMainWindow, Ui_Plethysmography):
    def __init__(self):
        super(Plethysmography, self).__init__()

#region class methods
        # Access configuration settings for GUI in gui_config.json:
        with open(f'{Path(__file__).parent}/gui_config.json') as config_file:
            self.gui_config = json.load(config_file)
        print(f'{Path(__file__).parent}/gui_config.json')

        # Access timestamp settings for validating and storing timestamper results in timestamps.json:
        with open(f'{Path(__file__).parent}/timestamps.json') as stamp_file:
            self.stamp = json.load(stamp_file)
        print(f'{Path(__file__).parent}/timestamps.json')

        # Access configuration settings for the breathcaller in breathcaller_config.json:
        with open(f'{Path(__file__).parent}/breathcaller_config.json') as bconfig_file:
            self.bc_config = json.load(bconfig_file)
        print(f'{Path(__file__).parent}/breathcaller_config.json')

        # Access references for the breathcaller in breathcaller_config.json:
        with open(f'{Path(__file__).parent}/reference_config.json') as rconfig_file:
            self.rc_config = json.load(rconfig_file)
        print(f'{Path(__file__).parent}/reference_config.json')

        self.breath_df = []

        # self.v = Config(self)
        # self.s = Stagg(self)
        # self.p = Auto(self)
        # self.c = ""
        # # self.v = Config(self)
        # self.m = Manual(self)
        # self.a = Auto(self)
        # self.b = Basic(self)
        # self.g = AnnotGUI.Annot(self)
        self.GUIpath=os.path.realpath(__file__)
        self.setupUi(self)
        self.threadpool = []

        self.setWindowTitle("Plethysmography Analysis Pipeline")
        self.isActiveWindow()
        self.showMaximized()

        

        # with open(f'{Path(__file__).parent.parent.parent}/gui_config.json') as config_file:
        #     self.gui_config = json.load(config_file)
        # print(f'{Path(__file__).parent.parent.parent}/gui_config.json')
        # self.gui_config['Dictionaries']['Paths'].update({'breathcaller':str(Path(f'{Path(__file__).parent.parent.parent.parent}/python_module.py'))})
        # print(self.gui_config['Dictionaries']['Paths']['breathcaller'])
        # self.gui_config['Dictionaries']['Paths'].update({'papr':str(Path(f'{Path(__file__).parent.parent.parent.parent}/papr'))})
        # print(self.gui_config['Dictionaries']['Paths']['papr'])

        # Load variables with paths for BASSPro and StaGG stored in gui_config dictionary:
        self.gui_config['Dictionaries']['Paths'].update({'breathcaller':str(Path(f'{Path(__file__).parent.parent}/python_module.py'))})
        print(self.gui_config['Dictionaries']['Paths']['breathcaller'])
        self.gui_config['Dictionaries']['Paths'].update({'papr':str(Path(f'{Path(__file__).parent.parent}/papr'))})
        print(self.gui_config['Dictionaries']['Paths']['papr'])
        self.gui_config['Dictionaries']['Paths'].update({'rscript1':str(Path(f'{Path(__file__).parent.parent}/R-Portable-3-6-3/App/R-Portable/bin/Rscript.exe'))})
        print(self.gui_config['Dictionaries']['Paths']['rscript1'])
        

        # # Populate GUI widgets with experimental condition choices: 
        # self.necessary_timestamp_box.addItems([need for need in self.stamp['Dictionaries']['Necessary_Timestamps']])
        # self.parallel_combo.addItems([str(num) for num in list(range(1,os.cpu_count()+1))])

        # # Populate GUI widgets with experimental condition choices:
        # self.m.preset_menu.addItems([x for x in self.bc_config['Dictionaries']['Manual Settings']['default'].keys()])
        # self.a.auto_setting_combo.addItems([x for x in self.bc_config['Dictionaries']['Auto Settings']['default'].keys()])

#endregion

#region class attributes
    # def create_attributes(self):
    #     # self.ETTC=""
        self.mothership=""
        self.breathcaller_path = self.gui_config['Dictionaries']['Paths']['breathcaller']
        self.output_dir_py=""
        self.input_dir_py=""
        self.input_dir_r=""
        self.output_dir_r=""
        self.autosections=""
        self.mansections=""
        self.basicap=""
        self.metadata=""
        self.graph_toggle="None"
        self.papr_dir = self.gui_config['Dictionaries']['Paths']['papr']
        self.py_output_folder=""
        self.r_output_folder=""
        self.variable_config=""
        self.graph_config=""
        self.other_config=""
        self.signals = []
        self.metadata_path = ""
        self.mouse_list = []
        self.mp_parsed = {}
        self.mp_parserrors = []
        self.p_mouse_dict={}
        self.m_mouse_dict={}
        self.metadata_warnings = {}
        self.metadata_passlist = []
        self.tsbyfile = {}
        self.row_loop = ""
        self.image_format = ""
        self.buttonDict_variable = {}
        
        self.v = Config(self)
        self.s = Stagg(self)
        self.p = Auto(self)
        self.c = ""
        # self.v = Config(self)
        self.m = Manual(self)
        self.a = Auto(self)
        self.b = Basic(self)
        self.g = AnnotGUI.Annot(self)

         # Populate GUI widgets with experimental condition choices: 
        self.necessary_timestamp_box.addItems([need for need in self.stamp['Dictionaries']['Necessary_Timestamps']])
        self.parallel_combo.addItems([str(num) for num in list(range(1,os.cpu_count()+1))])

        # Populate GUI widgets with experimental condition choices:
        self.m.preset_menu.addItems([x for x in self.bc_config['Dictionaries']['Manual Settings']['default'].keys()])
        self.a.auto_setting_combo.addItems([x for x in self.bc_config['Dictionaries']['Auto Settings']['default'].keys()])

        # for widget in [self.variable_list,self.signal_files_list,self.metadata_list,self.sections_list,self.breath_list]:
        #     self.keyPressEvent.connect(self.on_key(widget))

#endregion

#region Analysis parameters

        self.AnalysisParameters={}
        self.AnalysisParameters['minTI']=0.05
        self.AnalysisParameters['minPIF']=0.0015
        self.AnalysisParameters['minPEF']=-0.003
        self.AnalysisParameters['TTwin']=7
        self.AnalysisParameters['per500win']=201
        self.AnalysisParameters['maxPer500']=1.0
        self.AnalysisParameters['maxDVTV']=100
        self.AnalysisParameters['minApSec']=0.5
        self.AnalysisParameters['minApsTT']=2
        self.AnalysisParameters['minAplTT']=2
        self.AnalysisParameters['SIGHwin']=11
        self.AnalysisParameters['SmoothFilt']='y'
        self.AnalysisParameters['convert_temp']=1000
        self.AnalysisParameters['convert_co2']=1
        self.AnalysisParameters['convert_o2']=10
        self.AnalysisParameters['flowrate']=0.19811
        self.AnalysisParameters['roto_x']="50,75,80,90,95,100,110,125,150"
        self.AnalysisParameters['roto_y']="0.0724,0.13476,0.14961,0.18137,0.19811,0.21527,0.2504,0.30329,0.38847"
        # self.AnalysisParameters = self.gui_config['Dictionaries']['AP']['current']

    # def reset_parameter(self):
    #     self.AnalysisParameters = self.gui_config['Dictionaries']['AP']['default']
    #     lineEdits = {self.lineEdit_minTI: "minTI", 
    #                 self.lineEdit_minPIF: "minPIF",
    #                 self.lineEdit_minPEF: "minPEF", 
    #                 self.lineEdit_TTwin: "TTwin", 
    #                 self.lineEdit_per500win: "per500win", 
    #                 self.lineEdit_maxper500: "maxPer500", 
    #                 self.lineEdit_maxDVTV: "maxDVTV",
    #                 self.lineEdit_minApSec: "minApSec",
    #                 self.lineEdit_minApsTT: "minApsTT",
    #                 self.lineEdit_minAplTT: "minAplTT",
    #                 self.lineEdit_sighwin: "SIGHwin",
    #                 self.lineEdit_smoothfilt: "SmoothFilt",
    #                 self.lineEdit_converttemp: "convert_temp",
    #                 self.lineEdit_convertco2: "convert_co2",
    #                 self.lineEdit_converto2: "convert_o2",
    #                 self.lineEdit_flowrate: "flowrate",
    #                 self.lineEdit_roto_x: "roto_x",
    #                 self.lineEdit_roto_y: "roto_y"}

    #     for widget in lineEdits:
    #         widget.setText(str(self.AnalysisParameters[lineEdits[widget]]))

    # def get_parameter(self):

    #     minTI=self.lineEdit_minTI.text()
    #     minPIF=self.lineEdit_minPIF.text()
    #     minPEF=self.lineEdit_minPEF.text()
    #     TTwin=self.lineEdit_TTwin.text()
    #     per500win=self.lineEdit_per500win.text()
    #     maxper500=self.lineEdit_maxper500.text()
    #     maxDVTV=self.lineEdit_maxDVTV.text()
    #     minApSec=self.lineEdit_minApSec.text()
    #     minApsTT=self.lineEdit_minApsTT.text()
    #     minAplTT=self.lineEdit_minAplTT.text()
    #     SIGHwin=self.lineEdit_sighwin.text()
    #     SmoothFilt=self.lineEdit_smoothfilt.text()
    #     ConvertTemp=self.lineEdit_converttemp.text()
    #     ConvertCO2=self.lineEdit_convertco2.text()
    #     ConvertO2=self.lineEdit_converto2.text()
    #     Flowrate=self.lineEdit_flowrate.text()
    #     Roto_x=self.lineEdit_roto_x.text()
    #     Roto_y=self.lineEdit_roto_y.text()

    #     self.AnalysisParameters.update({"minTI":minTI})
    #     self.AnalysisParameters.update({"minPIF":minPIF})
    #     self.AnalysisParameters.update({"minPEF":minPEF})
    #     self.AnalysisParameters.update({"TTwin":TTwin})
    #     self.AnalysisParameters.update({"per500win":per500win})
    #     self.AnalysisParameters.update({"maxPer500":maxper500})
    #     self.AnalysisParameters.update({"maxDVTV":maxDVTV})
    #     self.AnalysisParameters.update({"minApSec":minApSec})
    #     self.AnalysisParameters.update({"minApsTT":minApsTT})
    #     self.AnalysisParameters.update({"minAplTT":minAplTT})
    #     self.AnalysisParameters.update({"SIGHwin":SIGHwin})
    #     self.AnalysisParameters.update({"SmoothFilt":SmoothFilt})
    #     self.AnalysisParameters.update({"convert_temp":ConvertTemp})
    #     self.AnalysisParameters.update({"convert_co2":ConvertCO2})
    #     self.AnalysisParameters.update({"convert_o2":ConvertO2})
    #     self.AnalysisParameters.update({"flowrate":Flowrate})
    #     self.AnalysisParameters.update({"roto_x":Roto_x})
    #     self.AnalysisParameters.update({"roto_y":Roto_y})

    #     self.gui_config['Dictionaries']['AP']['current'].update(self.AnalysisParameters)
    
    #     with open(f'{Path(__file__).parent}/gui_config.json','w') as config_file:
    #         json.dump(self.gui_config, config_file)

    # def print_parameters(self):
    #     print(self.AnalysisParameters)
    #     print(self.signals)
    #     print(os.path.join(self.mothership, "JSON"))

        # if not self.py_output_folder:
        #     if not self.mothership:
        #         ap_file = QFileDialog.getOpenFileNames(self, 'Select files', str(Path.home()))
        #     else:
        #         ap_file = QFileDialog.getOpenFileNames(self, 'Select files', str(self.mothership))
        # else:
        #     ap_file = QFileDialog.getOpenFileNames(self, 'Select files', str(self.py_output_folder))
            
        # if ap_file == ([],''):
        #     pass
        # else:
        #     with open(str(ap_file),'r') as openfile:
        #         self.AnalysisParameters = json.load(openfile)
        #     lineEdits = {self.lineEdit_minTI: "minTI", 
        #                 self.lineEdit_minPIF: "minPIF",
        #                 self.lineEdit_minPEF: "minPEF", 
        #                 self.lineEdit_TTwin: "TTwin", 
        #                 self.lineEdit_per500win: "per500win", 
        #                 self.lineEdit_maxper500: "maxPer500", 
        #                 self.lineEdit_maxDVTV: "maxDVTV",
        #                 self.lineEdit_minApSec: "minApSec",
        #                 self.lineEdit_minApsTT: "minApsTT",
        #                 self.lineEdit_minAplTT: "minAplTT",
        #                 self.lineEdit_sighwin: "SIGHwin",
        #                 self.lineEdit_smoothfilt: "SmoothFilt",
        #                 self.lineEdit_converttemp: "convert_temp",
        #                 self.lineEdit_convertco2: "convert_co2",
        #                 self.lineEdit_converto2: "convert_o2",
        #                 self.lineEdit_flowrate: "flowrate",
        #                 self.lineEdit_roto_x: "roto_x",
        #                 self.lineEdit_roto_y: "roto_y"}

        #     for widget in lineEdits:
        #         widget.setText(str(self.AnalysisParameters[lineEdits[widget]]))

        # self.metadict = {self.metadata:id(self.metadata)}
        # for l in list(self.metadata,self.autosections,self.mansections):
            

#endregion

#region Timestamper...

    def timestamp_dict(self):
        tic=datetime.datetime.now()
        print(tic)
        self.stamp['Dictionaries']['Data'] = {}
        combo_need = self.necessary_timestamp_box.currentText()
        if self.input_dir_py == "":
        # if self.signals == []:
            print("signals lsit empty")
            reply = QMessageBox.information(self, 'Missing signal files', 'No signal files selected.\nWould you like to select a signal file directory?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.get_signal_files()
            # self.hangar.append("Please choose signal files to check for timestamps.")
            # self.setAnimated(self.signal_files)
        elif combo_need == "Select dataset...":
            print("empty timestamp combo")
            reply = QMessageBox.information(self, 'Missing dataset', 'Please select one of the options from the dropdown menu above.', QMessageBox.Ok)
            # self.hangar.append("Please choose a set of timestamps.")
        elif not all(x.endswith(".txt") for x in self.signals)==True:
            print("wrong file format")
            reply = QMessageBox.information(self, 'Incorrect file format', 'The selected signal files are not text formatted.\nWould you like to select a different signal file directory?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.get_signal_files()
        else:
            print("apparently all fine")
            epoch = [os.path.basename(Path(self.signals[0]).parent.parent)]
            condition = [os.path.basename(Path(self.signals[0]).parent)]
            
            for f in self.signals:
                # epoch = os.path.basename(Path(f).parent)
                if os.path.basename(Path(f).parent.parent) in epoch:
                    continue
                else:
                    epoch.append(os.path.basename(Path(f).parent.parent))
                    if os.path.basename(Path(f).parent) in condition:
                        continue
                    else:
                        condition.append(os.path.basename(Path(f).parent))

            for c in condition:
                for e in epoch:
                    if e in self.stamp['Dictionaries']['Data']:
                        if c in self.stamp['Dictionaries']['Data'][e]:
                            continue
                        else:
                            self.stamp['Dictionaries']['Data'][e][c] = {}
                    else:
                        self.stamp['Dictionaries']['Data'][e] = {}
                        self.stamp['Dictionaries']['Data'][e][c] = {}

            self.need = self.stamp['Dictionaries']['Necessary_Timestamps'][combo_need]

            self.grabTimeStamps()
            self.checkFileTimeStamps()

            for e in epoch:
                for c in condition:
                    self.stamp['Dictionaries']['Data'][e][c]["tsbyfile"] = self.tsbyfile
                    for notable in self.check:
                        self.stamp['Dictionaries']['Data'][e][c][notable] = self.check[notable]
            # self.hangar.append(f"{self.stamp['Dictionaries']['Data'][]}")        
            print(f"{self.stamp['Dictionaries']['Data']}")
            try:
                with open(os.path.join(Path(self.signals[0]).parent,f"timestamp_{os.path.basename(Path(self.signals[0]).parent)}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"),"w") as tspath:
                    tspath.write(json.dumps(self.stamp))
                    tspath.close()
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                self.thumb = Thumbass(self)
                self.thumb.show()
                self.thumb.message_received("Your signal files aren't vibing with the timestamp function.")
            # shutil.copy(tspath, os.path.join(os.path.join(Path(self.signals[0]).parent.parent), f"timestamp_{os.path.basename(Path(self.signals[0]).parent.parent)}"))

            toc=datetime.datetime.now()
            print(toc)
            print(toc-tic) 

            # for you want to whittle down to the unique new_ts:
            # for e in stamp:
            #     for c in stamp[e]:
            #         for n in stamp[e][c]:
            #             if n == "new_ts":
            #                 print(f"{e}: {set([t for t in stamp[e][c][n]])}")
            #                 for s in set([t for t in stamp[e][c][n]]):
            #                     if s not in unt:
            #                         unt.append(s)
            # you can also use sadcapox.ipynb

    def grabTimeStamps(self):
        """
        iterates through files in filepathlist to gather unique timestamps 
        contained in the files - this is useful for building AutoCriteria Files
        """
        errors = []
        timestamps = []
        
        for CurFile in self.signals:
            self.tsbyfile[CurFile]=[]
            print(CurFile)
            # try:
            with open(CurFile,'r') as opfi:
                i=0
                l=0
                for line in opfi:
                    if '#' in line:
                        # self.hangar.append('{} TS AT LINE: {} - {}'.format(os.path.basename(CurFile),i,line.split('#')[1][2:]))
                        print('{} TS AT LINE: {} - {}'.format(os.path.basename(CurFile),i,line.split('#')[1][2:]))
                        timestamps.append(line.split('#')[1][2:])
                        # self.tsbyfile[CurFile].append(line.split('#* ')[1].split(' \n')[0])
                        c = line.split('#')[1][2:].split(' \n')[0]
                        self.tsbyfile[CurFile].append(f"{c}_{l}")
                        l+=1
                    i+=1
            # self.tsbyfile[CurFile]=[i.split(' \n')[0] for i in self.tsbyfile[CurFile]]
            # self.cur = [i.split(' \n')[0] for i in self.tsbyfile[CurFile]]
            # self.tsbyfile[CurFile] = dict(zip(self.cur,[num for num in range(len(self.tsbyfile[CurFile]))]))
            self.tsbyfile[CurFile] = [i for i in self.tsbyfile[CurFile]]
            print(f"{os.path.basename(CurFile)}: {self.tsbyfile[CurFile]}")
            # except:
            #     print('error')
            #     errors.append(CurFile)
        #trim timestamps
        timestamps=list(set(timestamps))
        timestamps=[i.split(' \n')[0] for i in timestamps]
        timestamps.sort()

    def checkFileTimeStamps(self):
        self.check = {}
        new_ts={}
        filesmissingts={}
        filesextrats={}
        goodfiles=[]
        for f in self.tsbyfile:
            error=0
            for k in self.need: 
                nt_found=0
                for t in self.tsbyfile[f]:
                    if t in self.need[k]:
                        nt_found+=1
                if nt_found==1:
                    continue
                elif nt_found>1:
                    if k in filesextrats.keys():
                        filesextrats[k].append(os.path.basename(f))
                    else:
                        filesextrats[k] = [os.path.basename(f)]
                    error=1
                else:
                    if k in filesmissingts.keys():
                        filesmissingts[k].append(os.path.basename(f))
                    else:
                        filesmissingts[k] = [os.path.basename(f)]
                    # filesmissingts.append((f,k))
                    error=1
            for t in self.tsbyfile[f]:
                ts_found=0
                for k in self.need:
                    if t in self.need[k]:
                        ts_found=1
                if ts_found!=1:
                    if t in new_ts.keys():
                        new_ts[t].append(os.path.basename(f))
                    else:
                        new_ts[t] = [os.path.basename(f)]
                    # new_ts.append((os.path.basename(f),t))
                    error=1
            if error==0:
                goodfiles.append(os.path.basename(f))
        for m in filesmissingts:
            if len(filesmissingts[m]) == len(self.signals):
                filesmissingts[m] = ["all signal files"]
            if len(goodfiles) == len(self.signals):
                goodfiles = ["all signal files"]
        self.check = {'good_files':goodfiles,'files_missing_a_ts':filesmissingts,
            'files_with_dup_ts':filesextrats,'new_ts':new_ts}

#endregion

#region Sections
    def show_annot(self):
        self.g.show()
        self.g.show_metadata_file()

    def show_manual(self):
        self.m.show()

    def show_auto(self):
        # self.a.show()
        self.p.show()
        # self.p.start_up()

    def show_basic(self):
        self.b.show()
        
#endregion

#region Variable configuration
    def new_variable_config(self):
        if self.metadata == "":
            reply = QMessageBox.information(self, 'Missing metadata', 'Please select a metadata file.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.get_metadata()
            if reply == QMessageBox.Cancel:
                self.metadata_list.clear()
                # for item in self.metadata_list.findItems("file not detected.",Qt.MatchEndsWith):
                # and we remove them from the widget.
                    # self.metadata_list.takeItem(self.metadata_list.row(item))
                self.metadata_list.addItem("No metadata file selected.")
        if self.autosections == "" and self.mansections == "":
            reply = QMessageBox.information(self, 'Missing BASSPRO settings', 'Please select BASSPRO settings files.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
            #     for item in self.sections_list.findItems("settings files selected.",Qt.MatchEndsWith):
            # # and we remove them from the widget.
            #         self.sections_list.takeItem(self.sections_list.row(item))
                self.get_autosections()
            if reply == QMessageBox.Cancel:
                for item in self.sections_list.findItems("settings files selected.",Qt.MatchEndsWith):
            # and we remove them from the widget.
                    self.sections_list.takeItem(self.sections_list.row(item))
                # I'm lazy and it's easier to just delete and add it again then check for it's presence.
                # self.sections_list.addItem("No BASSPRO settings files selected.")
        # if self.metadata != "" and (self.mansections != "" or self.autosections != ""):
        #     self.variable_configuration()
        self.test_configuration()
        try:
            self.variable_configuration()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
        try:
            self.v.show()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
        
        
    def show_variable_config(self):
        # print("show configuration")
        if self.buttonDict_variable == {}:
            print("self.buttonDict_variable is apparently empty")
            if self.v.configs["variable_config"]["path"] != "":
                self.v.check_load_variable_config("no")
                self.v.show()
            elif self.input_dir_r != "" and os.path.isdir(self.input_dir_r)==True:
                if self.metadata != "" and (self.autosections != "" or self.mansections != ""):
                    self.thinb = Thinbass(self)
                    self.thinb.show()
                else:
                    self.test_configuration()
                    try:
                        self.variable_configuration()
                        self.v.show()
                    except Exception as e:
                        print(f'{type(e).__name__}: {e}')
                # self.v.show()
            # elif self.input_dir_r != "":
            #     if os.path.isdir(self.input_dir_r)==True:
            #         try:
            #             first = next(file for file in os.scandir(self.input_dir_r) if file.endswith(".json"))
            #             with open(first) as first_json:
            #                 bp_output = json.load(first_json)
            #             for k in bp_output.keys():
            #                 self.breath_df.append(k)
            #         except Exception as e:
            #             print(f'{type(e).__name__}: {e}')
            #             pass
            elif self.metadata != "" and (self.autosections != "" or self.mansections != ""):
                self.test_configuration()
                try:
                    self.variable_configuration()
                    self.v.show()
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
            else:
                
                # reply = QMessageBox.information(self, 'Missing source files', f"One or more of the files used to build the variable list has not been selected\nWould you like to open an existing set of variable configuration files or create a new one?", QMessageBox.New | QMessageBox.Open | QMessageBox.Cancel, QMessageBox.Cancel)
                self.thorb = Thorbass(self)
                self.thorb.show()
                self.thorb.message_received('Missing source files', f"One or more of the files used to build the variable list has not been selected.\nWould you like to open an existing set of variable configuration files or create a new one?",self.new_variable_config,self.get_variable_config)
                    # if self.metadata == "":
                    #     reply = QMessageBox.information(self, 'Missing metadata', 'Please select a metadata file.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                    #     if reply == QMessageBox.Ok:
                    #         self.get_metadata()
                    #     if reply == QMessageBox.Cancel:
                    #         self.metadata_list.clear()
                    #         # for item in self.metadata_list.findItems("file not detected.",Qt.MatchEndsWith):
                    #         # and we remove them from the widget.
                    #             # self.metadata_list.takeItem(self.metadata_list.row(item))
                    #         self.metadata_list.addItem("No metadata file selected.")
                    # if self.autosections == "" and self.mansections == "":
                    #     reply = QMessageBox.information(self, 'Missing BASSPRO settings', 'Please select BASSPRO settings files.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                    #     if reply == QMessageBox.Ok:
                    #     #     for item in self.sections_list.findItems("settings files selected.",Qt.MatchEndsWith):
                    #     # # and we remove them from the widget.
                    #     #         self.sections_list.takeItem(self.sections_list.row(item))
                    #         self.get_autosections()
                    #     if reply == QMessageBox.Cancel:
                    #         for item in self.sections_list.findItems("settings files selected.",Qt.MatchEndsWith):
                    #     # and we remove them from the widget.
                    #             self.sections_list.takeItem(self.sections_list.row(item))
                    #         # I'm lazy and it's easier to just delete and add it again then check for it's presence.
                    #         self.sections_list.addItem("No BASSPRO settings files selected.")
                    # if self.metadata != "" and (self.mansections != "" or self.autosections != ""):
                    #     self.variable_configuration()
        else:
            print("variable configuration subGUI is supposed to show")
            self.v.show()
            
    def update_breath_df(self):
        print("update_breath_df()")
        self.old_bdf = self.breath_df
        print(f"breath_df: {self.breath_df}")
        print(f"old bdf: {self.old_bdf}")
        self.breath_df = []
        print(f"blank breath_df: {self.breath_df}")
        self.missing_meta = []
        for p in [self.metadata,self.autosections,self.mansections]:
            self.try_open(p)
        try:
            with open(self.breathcaller_path) as bc:
                soup = bs(bc, 'html.parser')
            for child in soup.breathcaller_outputs.stripped_strings:
                self.breath_df.append(child)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            self.missing_meta.append(self.breathcaller_path)
        print(f"old bdf after: {self.old_bdf}")
        print(f"new breath_df: {self.breath_df}")
        if set(self.breath_df) != set(self.old_bdf):
            print("bdfs have differents unique values")
            non_match_old = set(self.old_bdf) - set(self.breath_df)
            non_match_new = set(self.breath_df) - set(self.old_bdf)
            non_match = list(non_match_old) + list(non_match_new)
            print(f"non_match_old: {non_match_old}")
            print(f"non_match_new: {non_match_new}")
            print(f"non_match: {non_match}")
            if len(non_match)>0:
                reply = QMessageBox.question(self, f'Confirm variable list', 'Would you like to update the variable list in STAGG configuration settings?\n\nUnsaved changes may be lost.\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    print("updating config settings")
                    self.v.setup_table_config()
                    # self.v.vdf = {}
                    # with open(self.v.configs["variable_config"]["path"],'r') as f:
                    #     r = csv.DictReader(f)
                    #     for row in r:
                    #         for k in dict(row):
                    #             if dict(row)[k] == "1":
                    #                 self.v.vdf.update({dict(row)['Column']:dict(row)})
                    # try:
                    for a in self.v.vdf:
                        self.buttonDict_variable[a]['Alias'].setText(self.v.vdf[a]['Alias'])
                        for k in ["Independent","Dependent","Covariate"]:
                            if self.v.vdf[a][k] == '1':
                                try:
                                    self.buttonDict_variable[a][k].setChecked(True)
                                except:
                                    print("not checkable match")
                                    pass

                    self.v.load_custom_config()
                    self.v.load_graph_config()


                else:
                    self.breath_df = self.old_bdf
                    print(f"kept current config settings")
        else:
            print("bdfs same")
        

        

    def try_open(self,path):
        print("try_open()")
        try:
            with open(path,encoding='utf-8') as file:
                columns = next(csv.reader(file))
            for column in columns:
                if "section" in str(path):
                    if "AUTO_" or "MAN_" in column:
                        self.breath_df.append(column)
                else:
                    self.breath_df.append(column)
            print(path)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            self.missing_meta.append(path)

    def test_configuration(self):
        # show_variable_config() test whether or not the source files variables are empty - essentially has the user ever started a variable configuration subGUI session within this main session? But in the situation where the source files variables are not empty but the source files nevertheless cannnot be found (because they were located on a hard drive and you closed your computer, unplugged the hard drive, did something else fabulously interesting, came back, and tried to reopen the variable configuration subGUI to find the whole thing crashes because it can't build itself without the source files you pointed it to on your damn hard drive), these trys and excepts allow the GUI to handle your gaff gracefully. Jesus. This is why I don't write comments.

        print("test_configuration() has started")
        self.missing_meta = []
        for p in [self.metadata,self.autosections,self.mansections]:
            if p != "":
                self.try_open(p)
        # try:
        #     with open(self.metadata,encoding='utf-8') as meta_file:
        #         metadata_columns = next(csv.reader(meta_file))
        #     for column in metadata_columns:
        #         self.breath_df.append(column)
        # except Exception:
        #     print(Exception)
        #     missing_meta.append(self.metadata)
        # try:
        #     if self.autosections != "":
        #         with open(self.autosections,encoding='utf-8') as auto_file:
        #             auto_columns = next(csv.reader(auto_file))
        #         for column_1 in auto_columns:
        #             if "AUTO_" in column_1:
        #                 self.breath_df.append(column_1)
        #     elif self.mansections != "":
        #         with open(self.mansections,encoding='utf-8') as man_file:
        #             man_columns = next(csv.reader(man_file))
        #         for column_1 in man_columns:
        #             if "MAN_" in column_1:
        #                 self.breath_df.append(column_1)
        # except Exception as e:
        #     print(e)
        #     missing_meta.append(self.autosections)
        # with open(self.mansections) as man_file:
        #     man_columns = next(csv.reader(man_file))
        try:
            with open(self.breathcaller_path) as bc:
                soup = bs(bc, 'html.parser')
            for child in soup.breathcaller_outputs.stripped_strings:
                self.breath_df.append(child)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            self.missing_meta.append(self.breathcaller_path)
        print(type(self.breath_df))
        if len(self.missing_meta)>0:
            print(self.missing_meta)
            reply = QMessageBox.information(self, 'Missing source files', f"One or more of the files used to build the variable list was not found:\n{os.linesep.join([m for m in self.missing_meta])}\nWould you like to select a different file?", QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                for m in self.missing_meta:
                    if m is self.mothership:
                        reply = QMessageBox.information(self, 'Missing metadata', 'Please select a metadata file.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                        if reply == QMessageBox.Ok:
                            self.get_metadata()
                        if reply == QMessageBox.Cancel:
                            self.metadata_list.clear()
                            # for item in self.metadata_list.findItems("file not detected.",Qt.MatchEndsWith):
                            # and we remove them from the widget.
                                # self.metadata_list.takeItem(self.metadata_list.row(item))
                            self.metadata_list.addItem("No metadata file selected.")
                    if m is self.autosections or m is self.mansections:
                        reply = QMessageBox.information(self, 'Missing BASSPRO settings', 'Please select BASSPRO settings files.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                        if reply == QMessageBox.Ok:
                            self.get_autosections()
                        if reply == QMessageBox.Cancel:
                            for item in self.sections_list.findItems("settings files selected.",Qt.MatchEndsWith):
                        # and we remove them from the widget.
                                self.sections_list.takeItem(self.sections_list.row(item))
                            self.sections_list.addItem("No BASSPRO settings files selected.")
                    if m is self.breathcaller_path:
                        reply = QMessageBox.information(self, "How is this program even running?", f"The program cannot find the following file: \n{self.breathcaller_path}\nYou honestly shouldn't even see this error because I don't think the program runs without this file. If you are seeing this message, congratulations! Now undo whatever you did, or download a new breathcaller_config.json file from the GitHub or just go ahead and download the whole program again. Or just plug in your external drive that has the program on it and restart it.", QMessageBox.Ok)

        print("test_configuration() has finished")

    def lvariable_configuration(self):
        self.s.show()

    def variable_configuration(self):
        print("self.variable_configuration() has started")
        # print(self.breath_df)
        # This subGUI is active as soon as the mainGUI is, but it doesn't show unless you ask.
        
        # if self.buttonDict_variable == {}:
        #     self.show_variable_config()
        #     self.v.show()
        
        # self.breath_df = pd.read_excel("C:/Users/atwit/Desktop/Mothership/BASSPRO_output/py_output20201113_135540/M17023_megax.xlsx",header=0,nrows=1).columns
        self.stack = []

        # The following "header" stanzas make the columns within the tables of equal width.
        header = self.v.variable_table.horizontalHeader()
        for header_col in range(0,6):
            header.setSectionResizeMode(header_col,QHeaderView.Stretch)

        header_loop = self.v.loop_table.horizontalHeader()
        for header_loop_col in range(0,6):
            header_loop.setSectionResizeMode(header_loop_col,QHeaderView.Stretch)

        # header_upper_loop = self.v.upper_loop_table.horizontalHeader()
        # for header_upper_loop_col in range(0,6):
        #     header_upper_loop.setSectionResizeMode(header_upper_loop_col,QHeaderView.Stretch)

        # loop_list = [self.v.loop_table, self.v.upper_loop_table]
        # for table in loop_list:
        #     header_loop = table.horizontalHeader()
        #     for header_col_loop in range(0,7):
        #         header_loop.setSectionResizeMode(header_col_loop,QHeaderView.Stretch)

        # I've forgotten what this was specifically about, but I remember it had something to do with spacing or centering text or something.
        delegate = AlignDelegate(self.v.variable_table)
        delegate_loop = AlignDelegate(self.v.loop_table)
        # delegate_loop_up = AlignDelegate(self.v.upper_loop_table)
        self.v.variable_table.setItemDelegate(delegate)
        self.v.loop_table.setItemDelegate(delegate_loop)
        # self.v.upper_loop_table.setItemDelegate(delegate_loop_up)

        # Setting the number of rows in each table upon opening the window:
        self.v.variable_table.setRowCount(len(self.breath_df))
        self.v.loop_table.setRowCount(1)
        # self.v.upper_loop_table.setRowCount(1)
        
        row = 0
        # Establishing the dictionary in which the table contents will be stored for delivery to r_config.csv:
        # self.buttonDict_variable = {}
        # print(self.breath_df)
        # Grabbing every item in breath_df and making a row for each:
        for item in self.breath_df:
            # Establishing each row as its own group to ensure mutual exclusivity for each row within the table:
            self.buttonDict_variable[item]={"group": QButtonGroup()}
            # self.buttonDict_variable[item]["group"].buttonClicked.connect(self.check_buttons)

            # The first two columns are the text of the variable name. Alias should be text editable.
            self.buttonDict_variable[item]["orig"] = QTableWidgetItem(item)
            self.buttonDict_variable[item]["Alias"] = QTableWidgetItem(item)

            # Creating the radio buttons that will populate the cells in each row:
            self.buttonDict_variable[item]["Independent"] = QRadioButton("Independent")
            self.buttonDict_variable[item]["Dependent"] = QRadioButton("Dependent")
            self.buttonDict_variable[item]["Covariate"] = QRadioButton("Covariate")
            self.buttonDict_variable[item]["Ignore"] = QRadioButton("Ignore")
            self.buttonDict_variable[item]["Ignore"].setChecked(True)

            # Adding those radio buttons to the group to ensure mutual exclusivity across the row:
            self.buttonDict_variable[item]["group"].addButton(self.buttonDict_variable[item]["Independent"])
            self.buttonDict_variable[item]["group"].addButton(self.buttonDict_variable[item]["Dependent"])
            self.buttonDict_variable[item]["group"].addButton(self.buttonDict_variable[item]["Covariate"])
            self.buttonDict_variable[item]["group"].addButton(self.buttonDict_variable[item]["Ignore"])
            
            # Populating the table widget with the row:
            self.v.variable_table.setItem(row,0,self.buttonDict_variable[item]["orig"])
            self.v.variable_table.setItem(row,1,self.buttonDict_variable[item]["Alias"])

            self.v.variable_table.setCellWidget(row,2,self.buttonDict_variable[item]["Independent"])
            self.v.variable_table.setCellWidget(row,3,self.buttonDict_variable[item]["Dependent"])
            self.v.variable_table.setCellWidget(row,4,self.buttonDict_variable[item]["Covariate"])
            self.v.variable_table.setCellWidget(row,5,self.buttonDict_variable[item]["Ignore"])

            # self.buttonDict_variable[item]["role"] = QComboBox()
            # self.buttonDict_variable[item]["static"] = QComboBox()

            # self.buttonDict_variable[item]["role"].addItems(["","xvar","pointdodge","facet1","facet2"])
            # self.buttonDict_variable[item]["static"].addItems(["","Start Body Temp","Mid Body Temp","End Body Temp","Post Body Temp","Body Weight"])

            # self.v.variable_table.setCellWidget(row,6,self.buttonDict_variable[item]["role"])
            # self.v.variable_table.setCellWidget(row,7,self.buttonDict_variable[item]["static"])

            row += 1
            # you have to iteratively create the widgets for each row, not just iteratively
            # add the widgets for each row because it'll only do the last row
            # so every row's radio button will 
            # self.buttonDict_variable[item]["static"].activated.connect(self.v.replace)
            # self.buttonDict_variable[item]["role"].activated.connect(self.v.replace)
            self.buttonDict_variable[item]["Independent"].toggled.connect(self.v.add_combos)
            self.buttonDict_variable[item]["Covariate"].toggled.connect(self.v.add_combos)
            # self.v.variable_table.itemChanged.connect(self.v.update_alias)
            # self.buttonDict_variable[item]["Covariate"].toggled.connect(self.v.populate_combos(self.buttonDict_variable[item].))
        # Creating the dictionary that will store the cells' statuses based on user selection. The table's need separate dictionaries because they'll be yielding separate csvs:
        self.loop_menu = {}
        # self.v.transform_combo = CheckableComboBox()
        # self.v.transform_combo.addItems(["raw","log10","ln","sqrt"])
        # self.v.verticalLayout_25.addWidget(self.v.transform_combo)
        self.show_loops(self.v.loop_table,0)
        # self.show_loops(self.v.upper_loop_table,0)
        # print(self.buttonDict_variable)
        print("self.variable_configuration() has finished")
    # def show_upper_loops(self,table,row):
    #     self.loop_menu.update({table:{row:{}}})
    #     # Creating the widgets within the above dictionary that will populate the cells of each row:
    #     self.loop_menu[table][row]["graph"] = QLineEdit()
    #     for role in self.v.role_list[0:5]:
    #         self.loop_menu[table][row][role] = QComboBox()
    #         self.loop_menu[table][row][role].addItems([""])
    #         self.loop_menu[table][row][role].addItems([x for x in self.breath_df])
    #     self.loop_menu[table][row]["poincare"] = QComboBox()

    #     # Adding the contents based on the variable list of the drop down menus for the combo box widgets:
    #     # for role in self.v.role_list:
    #         # self.loop_menu[table][self.row_loop][role].addItems([""])
    #         # self.loop_menu[table][self.row_loop][role].addItems([x for x in self.breath_df])
    #     self.loop_menu[table][row]["poincare"].addItems(["","Yes","No"])
        
    #     # Populating the table cells with their widget content stored in the dictionary:
    #     # for n in range(0,7):
    #     #     for role in role_list:
    #     #         table.setCellWidget(self.row_loop,n,self.loop_menu[table][self.row_loop][role])
    #     table.setCellWidget(row,0,self.loop_menu[table][row]["graph"])
    #     table.setCellWidget(row,1,self.loop_menu[table][row]["yaxis"])
    #     table.setCellWidget(row,2,self.loop_menu[table][row]["xvar"])
    #     table.setCellWidget(row,3,self.loop_menu[table][row]["pointdodge"])
    #     table.setCellWidget(row,4,self.loop_menu[table][row]["facet1"])
    #     table.setCellWidget(row,5,self.loop_menu[table][row]["facet2"])
    # else:
    #     self.v.show()

    def show_loops(self,table,row):
        print("pleth.show_loops()")
        self.loop_menu.update({table:{row:{}}})
        # Creating the widgets within the above dictionary that will populate the cells of each row:
        self.loop_menu[table][row]["Graph"] = QLineEdit()
        self.loop_menu[table][row]["Y axis minimum"] = QLineEdit()
        self.loop_menu[table][row]["Y axis maximum"] = QLineEdit()
        for role in self.v.role_list[1:6]:
            self.loop_menu[table][row][role] = QComboBox()
            self.loop_menu[table][row][role].addItems([""])
            self.loop_menu[table][row][role].addItems([x for x in self.breath_df])
        
        # self.loop_menu[table][row]["Poincare"] = QComboBox()
        # self.loop_menu[table][row]["Poincare"].addItems(["Yes","No"])
        # self.loop_menu[table][row]["Y axis minimum"].addItems(["Automatic",""])
        # self.loop_menu[table][row]["Y axis maximum"].addItems(["Automatic",""])
        self.loop_menu[table][row]["Inclusion"] = QComboBox()
        self.loop_menu[table][row]["Inclusion"].addItems(["No","Yes"])
        
        # Adding the contents based on the variable list of the drop down menus for the combo box widgets:
        # for role in self.v.role_list:
            # self.loop_menu[table][self.row_loop][role].addItems([""])
            # self.loop_menu[table][self.row_loop][role].addItems([x for x in self.breath_df])
    
        
        # Populating the table cells with their widget content stored in the dictionary:
        # for n in range(0,7):
        #     for role in role_list:
        #         table.setCellWidget(self.row_loop,n,self.loop_menu[table][self.row_loop][role])
        table.setCellWidget(row,0,self.loop_menu[table][row]["Graph"])
        table.setCellWidget(row,1,self.loop_menu[table][row]["Variable"])
        table.setCellWidget(row,2,self.loop_menu[table][row]["Xvar"])
        table.setCellWidget(row,3,self.loop_menu[table][row]["Pointdodge"])
        table.setCellWidget(row,4,self.loop_menu[table][row]["Facet1"])
        table.setCellWidget(row,5,self.loop_menu[table][row]["Facet2"])
        # table.setCellWidget(row,6,self.loop_menu[table][row]["Poincare"])
        table.setCellWidget(row,6,self.loop_menu[table][row]["Inclusion"])
        table.setCellWidget(row,7,self.loop_menu[table][row]["Y axis minimum"])
        table.setCellWidget(row,8,self.loop_menu[table][row]["Y axis maximum"])

        # if table == self.v.loop_table:
            # self.loop_menu[table][row]["poincare"] = QComboBox()
            # self.loop_menu[table][row]["poincare"].addItems(["","Yes","No"])
            # table.setCellWidget(row,6,self.loop_menu[table][row]["poincare"])



        # self.v.loop_table.setCellWidget(self.row_loop,0,self.loop_menu[self.row_loop]["graph"])
        # self.v.loop_table.setCellWidget(self.row_loop,1,self.loop_menu[self.row_loop]["yaxis"])
        # self.v.loop_table.setCellWidget(self.row_loop,2,self.loop_menu[self.row_loop]["xvar"])
        # self.v.loop_table.setCellWidget(self.row_loop,3,self.loop_menu[self.row_loop]["pointdodge"])
        # self.v.loop_table.setCellWidget(self.row_loop,4,self.loop_menu[self.row_loop]["facet1"])
        # self.v.loop_table.setCellWidget(self.row_loop,5,self.loop_menu[self.row_loop]["facet2"])
        # self.v.loop_table.setCellWidget(self.row_loop,6,self.loop_menu[self.row_loop]["poincare"])

        # self.v.upper_loop_table.setCellWidget(self.row_loop,0,self.loop_menu[self.row_loop]["graph"])
        # self.v.upper_loop_table.setCellWidget(self.row_loop,1,self.loop_menu[self.row_loop]["yaxis"])
        # self.v.upper_loop_table.setCellWidget(self.row_loop,2,self.loop_menu[self.row_loop]["xvar"])
        # self.v.upper_loop_table.setCellWidget(self.row_loop,3,self.loop_menu[self.row_loop]["pointdodge"])
        # self.v.upper_loop_table.setCellWidget(self.row_loop,4,self.loop_menu[self.row_loop]["facet1"])
        # self.v.upper_loop_table.setCellWidget(self.row_loop,5,self.loop_menu[self.row_loop]["facet2"])
        # self.v.upper_loop_table.setCellWidget(self.row_loop,6,self.loop_menu[self.row_loop]["poincare"])

#endregion

#region Automatic selection

    def set_mothership(self):
        if self.gui_config['Dictionaries']['Paths']['mothership'] == "":
            print("no gui mother")
            self.mothership = QFileDialog.getExistingDirectory(self, 'Choose default directory', str(Path.home()), QFileDialog.ShowDirsOnly)
            if not self.mothership:
                print("directory mothership default not selected")
                # self.default_mothership.setChecked(False)
            else:
                self.gui_config['Dictionaries']['Paths'].update({"mothership":self.mothership})
        else:
            print("set mother else")
            self.mothership = self.gui_config['Dictionaries']['Paths']['mothership']

    def mothership_dir(self):
        print("mothership_dir()")
        # self.mothership = "C:/Users/atwit/Desktop/Mothership"
        # if self.default_mothership.isChecked == False:
        #     print("no default")
        #     self.mothership = Path(QFileDialog.getExistingDirectory(self, 'Choose output directory', str(Path.home()), QFileDialog.ShowDirsOnly))
        # elif self.default_mothership.isChecked == True:
            # print("default please")
            # self.mothership = self.gui_config['Dictionaries']['Paths']['mothership']
        # self.mothership = self.gui_config['Dictionaries']['Paths']['mothership']
        # elif self.default_mothership.isChecked == False:
        #     print("no default")
        self.mothership = QFileDialog.getExistingDirectory(self, 'Choose output directory', str(Path.home()), QFileDialog.ShowDirsOnly)
        # if self.mothership != "" and 
        # self.mothership = Path(
        if not self.mothership:
            print(f'mothership after: {self.mothership}')
        else:
          # self.breathcaller_path_list.clear()
        # self.py_output_dir_list.clear()
            self.signal_files_list.clear()
            self.metadata_list.clear()
            self.sections_list.clear()
        # self.py_go.setDisabled(False)
            self.auto_get_output_dir_py()
            self.auto_get_autosections()
            self.auto_get_mansections()
            self.auto_get_metadata()
            # self.auto_get_breath_files()
            self.auto_get_output_dir_r()
            # self.auto_get_signal_files()
            self.auto_get_variable()
            self.auto_get_basic()
            
    # def auto_get_python_module(self):
    #     py_mod_path=self.gui_config['Dictionaries']['Paths']['breathcaller']
    #     # self.breathcaller_path_list.clear()
    #     if Path(py_mod_path).exists():
    #         self.breathcaller_path=py_mod_path
    #         self.breathcaller_path_list.addItem(self.breathcaller_path)
    #     else:
    #         self.breathcaller_path_list.clear()
    #         self.breathcaller_path_list.addItem("Python module not detected.")

    def auto_get_output_dir_py(self):
        print("auto_get_output_dir_py()")
        self.py_output_folder=os.path.join(self.mothership,'BASSPRO_output')
        if Path(self.py_output_folder).exists():
            self.output_dir_py=os.path.join(self.py_output_folder, 'BASSPRO_output_'+datetime.datetime.now().strftime(
                '%Y%m%d_%H%M%S'
            ))
            print(self.output_dir_py)
            # self.py_output_dir_list.clear()
            # self.py_output_dir_list.addItem(self.output_dir_py)
        else:
            Path(self.py_output_folder).mkdir()
            self.output_dir_py=os.path.join(self.py_output_folder,'BASSPRO_output_'+datetime.datetime.now().strftime(
                '%Y%m%d_%H%M%S'
            ))
            # self.py_output_dir_list.clear()
            # self.py_output_dir_list.addItem(self.output_dir_py)
    
    def auto_get_signal_files(self):
        print("auto_get_signal_files()")
        signal_folder=os.path.join(self.mothership,'signals')
        if self.signals != []:
            reply = QMessageBox.information(self, 'Clear signal files list?', 'Would you like to keep the previously selected signal files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                self.signal_files_list.clear()
                self.signals = []
        if Path(signal_folder).exists() and Path(signal_folder).is_dir():
            self.input_dir_py=signal_folder
            # self.signal_files_list.clear()
            # self.signals=[]
            # self.signal_files=[]
            bad_signals = []
            for file in Path(signal_folder).iterdir():
                if file.endswith(".txt"):
                    self.signal_files_list.addItem(str(file))
                    # self.signal_files.append(os.path.basename(file))
                    self.signals.append(file)
                else:
                    bad_signals.append(file)
            if len(bad_signals)>0:
                self.thumb = Thumbass(self)
                self.thumb.show()
                self.thumb.message_received("Incorrect file format",f"One or more of the files selected are not text formatted:\n\n{os.linesep.join([os.path.basename(thumb) for thumb in bad_signals])}\n\nThey will not be included.")
                # reply = QMessageBox.information(self, 'Incorrect file format', 'One or more of the selected signal files are not text formatted: .\nWould you like to select a different signal file directory?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        else:
            if self.signals == []:
                self.signal_files_list.clear()
                self.signal_files_list.addItem("Signal files directory not detected.")
     
    def auto_get_metadata(self):
        print("auto_get_metadata()")
        print(id(self.metadata))
        print(os.path.basename(self.metadata))
        metadata_path=os.path.join(self.mothership, 'metadata.csv')
        if Path(metadata_path).exists():
            # We assign the path detected via mothership to the Plethysmography class attribute that will be an argument for the breathcaller command line.
            if self.metadata == "":
                self.metadata=metadata_path
                self.metadata_list.addItem(self.metadata)
            else:
                self.metadata=metadata_path
                self.metadata_list.addItem(self.metadata)
                if self.breath_df != []:
                    self.update_breath_df()

        else:
            self.metadata_list.clear()
            self.metadata_list.addItem("No metadata file selected.")
        print(id(self.metadata))
        print(os.path.basename(self.metadata))

    def auto_get_basic(self):
        print("auto_get_basic()")
        for item in self.sections_list.findItems("basic",Qt.MatchContains):
            # and we remove them from the widget.
            self.sections_list.takeItem(self.sections_list.row(item))
        basic_path=os.path.join(self.mothership, 'basics.csv')
        if Path(basic_path).exists():
            if self.basicap == "":
                self.basicap=basic_path
                self.sections_list.addItem(self.basicap)
            else:
                self.basicap=basic_path
                self.sections_list.addItem(self.basicap)
                if not self.breath_df.empty:
                    self.update_breath_df()
        else:
            self.sections_list.addItem("Basic parameters settings file not detected.")

    def auto_get_autosections(self):
        print("auto_get_autosections()")
        for item in self.sections_list.findItems("auto",Qt.MatchContains):
            # and we remove them from the widget.
            self.sections_list.takeItem(self.sections_list.row(item))
        autosections_path=os.path.join(self.mothership, 'auto_sections.csv')
        if Path(autosections_path).exists():
            if self.autosections == "":
            # We assign the path detected via mothership to the Plethysmography class attribute that will be an argument for the breathcaller command line.
                self.autosections=autosections_path
                self.sections_list.addItem(self.autosections)
            else:
                self.autosections=autosections_path
                self.sections_list.addItem(self.autosections)
                if not self.breath_df.empty:
                    self.update_breath_df()
        else:
            self.sections_list.addItem("Autosection parameters file not detected.")

    def auto_get_mansections(self):
        print("auto_get_mansections()")
        for item in self.sections_list.findItems("man",Qt.MatchContains):
                # and we remove them from the widget.
                self.sections_list.takeItem(self.sections_list.row(item))
        mansections_path=os.path.join(self.mothership, 'manual_sections.csv')
        if Path(mansections_path).exists():
            if self.mansections == "":
            # We assign the path detected via mothership to the Plethysmography class attribute that will be an argument for the breathcaller command line.
                self.mansections=mansections_path
                self.sections_list.addItem(self.mansections)
            else:
                self.mansections=mansections_path
                self.sections_list.addItem(self.mansections)
                if not self.breath_df.empty:
                    self.update_breath_df()
        else:
            self.sections_list.addItem("Manual sections parameters file not detected.")

    # def auto_get_papr_module(self):
    #     papr_path=papr_path=self.gui_config['Dictionaries']['Paths']['papr']
    #     self.papr_dir_list.clear()
    #     if Path(papr_path).exists():
    #         # We assign the path detected via mothership to the Plethysmography class attribute that will be an argument for the breathcaller command line.
    #         self.papr_dir=papr_path
    #         self.papr_dir_list.addItem(self.papr_dir)
    #     else:
    #         self.papr_dir_list.clear()
    #         self.papr_dir_list.addItem("SG-Runner module not detected.")
    def get_variable_config(self):
        print("get_variable_config()")
        print("self.get_variable_config() has started")
        
        self.v.check_load_variable_config("yes")
        # self.variable_configuration()
        # self.v.show()
        print("self.get_variable_config() has finished")
        
    def auto_get_variable(self):
        print("self.auto_get_variable() has started")
        # Because we are using one list widget (self.variable_list) to give signs of life regarding the self.graph_settings_path and self.variable_config attributes,
        # the clearing of the widget's previous messages or paths is less straightforward. 
        # We create a directory path for a file named variable_configuration.csv and again for one named graph_settings.csv in the mothership folder.
        self.variable_list.clear()
        # for file in os.listdir(os.path.join(self.mothership,'STAGG_config')):
        #     if str(file[0]).endswith("config.csv"):
        # self.v.configs['variable_config']['variable'] = self.variable_config
        # self.v.configs['graph_config']['variable'] = self.graph_config
        # self.v.configs['other_config']['variable'] = self.other_config
        
        self.variable_config = os.path.join(self.mothership, 'STAGG_config/variable_config.csv')
        self.graph_config = os.path.join(self.mothership, 'STAGG_config/graph_config.csv')
        self.other_config = os.path.join(self.mothership, 'STAGG_config/other_config.csv')
        self.v.configs['variable_config']['path'] = self.variable_config
        self.v.configs['graph_config']['path'] = self.graph_config
        self.v.configs['other_config']['path'] = self.other_config
        # self.variable_configuration()
        
        # self.v.check_load_variable_config("no")
        # We first prove that the directory paths we just created actually exist.
        # if Path(variable_path).exists():
            # We assign the path detected via mothership to the Plethysmography class attribute that will be an argument for the breathcaller command line.
            # self.variable_config = variable_path
        # print(self.v.configs)
        for item in self.variable_list.findItems("Configuration files not detected.",Qt.MatchExactly):
            self.variable_list.takeItem(self.variable_list.row(item))
        for f in self.v.configs:
            for item in self.variable_list.findItems(f,Qt.MatchContains):
                self.variable_list.takeItem(self.variable_list.row(item))
            self.variable_list.addItem(self.v.configs[f]['path'])
            # We look for any previous "file not detected" messages in the self.variable_list widget...
            for item in self.variable_list.findItems("Configuration files not detected.",Qt.MatchExactly):
                # and we remove them from the widget.
                self.variable_list.takeItem(self.variable_list.row(item))
            # If we are changing a previous choice of directory path, here we remove the evidence of that choice from the widget.
            for item in self.variable_list.findItems("variable_configuration",Qt.MatchContains):
                self.variable_list.takeItem(self.variable_list.row(item))

            # We add the path to the self.variable_list widget in the MainGUI to indicate successful assignation of the Plethysmography class attribute.
            # self.variable_list.addItem(self.variable_config)

        # else:
        #     # We look for any previous "file not detected" messages in the self.variable_list widget...
        #     for item in self.variable_list.findItems("Configuration files not detected.",Qt.MatchExactly):
        #         # and we remove them from the widget.
        #         self.variable_list.takeItem(self.variable_list.row(item))
        #     # If the variable_config.csv path we created doesn't exist, we add a "file not detected" massage to the self.variable_list widget to indicate unsuccessfuly assignation of the Plethysmography class attribute.
        #     self.variable_list.addItem("Configuration files not detected.")
        #     # If we are changing a previous choice of directory path, here we remove the evidence of that choice from the widget to avoid the user thinking 
        #     # the new path they chose worked when they are actually just looking at the previous choice's path.
        #     for item in self.variable_list.findItems("variable_configuration",Qt.MatchContains):
        #         self.variable_list.takeItem(self.variable_list.row(item))
        print("self.auto_get_variable() has finished")

    def auto_get_breath_files(self):
        print("auto_get_breath_files()")
        if self.output_dir_py == "":
            self.breath_list.addItem("Breathcaller output directory not detected.")
        else:
            self.breath_list.addItem(self.output_dir_py)
            self.input_dir_r = self.output_dir_py
        # breath_files_path=self.output_dir_py
        # self.breath_list.clear()
        # if not breath_files_path:
        #     self.breath_list.clear()
        #     self.breath_list.addItem("Breathcaller output directory not detected.")
        # else:
        #     self.input_dir_r=breath_files_path
        #     self.breath_list.addItem(self.input_dir_r)

    def auto_get_output_dir_r(self):
        print("auto_get_output_dir_r()")
        self.r_output_folder=os.path.join(self.mothership,'STAGG_output')
        if Path(self.r_output_folder).exists():
            self.output_dir_r=os.path.join(self.r_output_folder, 'STAGG_output_'+datetime.datetime.now().strftime(
                '%Y%m%d_%H%M%S'
            ))
            print(self.output_dir_r)
            # self.r_output_dir_list.clear()
            # self.r_output_dir_list.addItem(self.output_dir_r)
        else:
            Path(self.r_output_folder).mkdir()
            self.output_dir_r=os.path.join(self.r_output_folder, 'STAGG_output_'+datetime.datetime.now().strftime(
                '%Y%m%d_%H%M%S'
            ))
            print(self.output_dir_r)
            # Path(self.output_dir_r).mkdir()
            # self.r_output_dir_list.clear()
            # self.r_output_dir_list.addItem(self.output_dir_r)

#endregion

#region Manual selection
    # def keyPressEvent(self, event):
    #     # print(item.text())
    #     if event.key() == QtCore.Qt.Key_Delete:
    #         self.on_key(event)
    #         # for r in panel.selectedItems():
    #         #     .takeItem(r)
    #     else:
    #         super().keyPressEvent(event)

    # def keyPressEvent(self, event):
    #     super(Plethysmography,self).keyPressEvent(event)
    #     self.emit(event.key())
    
    # def on_key(key):
    #     # if key == QtCore.Qt.Key_Delete:
    #     for r in panel.selectedItems():
    #         panel.takeItem(r)

    def open_click(self,item):
        print("open_click()")
        try:
            if Path(item.text()).exists():
                os.startfile(item.text())
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            pass

    # def open_dir(self,item):
    #     if 

    def get_signal_files(self):
        print("get_signal_files()")
        if not self.input_dir_py:
            if not self.mothership:
                try:
                    self.mothership = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output")
                    file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(self.mothership))
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print('self.mothership = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output") no longer working')
            else:
                file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(self.mothership))
        else:
            file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(self.input_dir_py))
        if not file_name[0]:
            if self.signals == []:
                self.signal_files_list.clear()
                self.signal_files_list.addItem("No signal files selected.")
        else:
            if self.signals != []:
                reply = QMessageBox.information(self, 'Clear signal files list?', 'Would you like to keep the previously selected signal files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    self.signal_files_list.clear()
                    self.signals = []
            # self.signal_files_list.clear()
            bad_signals = []
            for x in range(len(file_name[0])):
                if file_name[0][x].endswith(".txt"):
                    self.signal_files_list.addItem(file_name[0][x])
                    # self.signal_files.append(os.path.basename(file_name[0][x]))
                    self.signals.append(file_name[0][x])
                else:
                    bad_signals.append(file_name[0][x])
            if len(bad_signals)>0:
                self.thumb = Thumbass(self)
                self.thumb.show()
                self.thumb.message_received("Incorrect file format",f"One or more of the files selected are not text formatted:\n\n{os.linesep.join([os.path.basename(thumb) for thumb in bad_signals])}\n\nThey will not be included.")
            else:  
                self.input_dir_py = os.path.dirname(self.signals[0])
            print(self.input_dir_py)

    def get_metadata(self):
        print("get_metadata()")
        if self.mothership != "":
            print("exists")
            file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(self.mothership))
        else:
            print("not exist")
            # self.pleth.mothership = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output")
            file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(os.path.join(Path(__file__).parent.parent.parent,"PAPR Output")))
        if not file_name[0]:
            if self.metadata == "":
                self.metadata_list.clear()
                self.metadata_list.addItem("No metadata file selected.")
        else:
            self.metadata_list.clear()
            for x in range(len(file_name[0])):
                self.metadata_list.addItem(file_name[0][x])
            self.metadata = file_name[0][0]
            
            if len(self.breath_df)>0:
                self.update_breath_df()
            # self.pleth.hangar.append("Metadata file saved.")
    
    def mp_parser(self):
        print("mp_parser()")
        self.mp_parsed={'MUIDLIST':[],'PLYUIDLIST':[],'MUID_PLYUID_tuple':[]}
        self.mp_parserrors=[]
        muid_plyuid_re=re.compile('M(?P<muid>.+?(?=_|\.txt))(_Ply)?(?P<plyuid>.*).txt')
        for file in self.signals:
            try:
                parsed_filename=re.search(muid_plyuid_re,os.path.basename(file))
                if parsed_filename['muid']!='' and parsed_filename['plyuid']!='':
                    self.mp_parsed['MUIDLIST'].append(int(parsed_filename['muid']))
                    self.mp_parsed['PLYUIDLIST'].append(int(parsed_filename['plyuid']))
                    self.mp_parsed['MUID_PLYUID_tuple'].append(
                        (int(parsed_filename['muid']),int(parsed_filename['plyuid']))
                        )
                elif parsed_filename['muid']!='':
                    self.mp_parsed['MUIDLIST'].append(int(parsed_filename['muid']))
                    self.mp_parsed['MUID_PLYUID_tuple'].append(
                        (int(parsed_filename['muid']),'')
                        )
                elif parsed_filename['plyuid']!='':
                    self.mp_parsed['PLYUIDLIST'].append(int(parsed_filename['plyuid']))
                    self.mp_parsed['MUID_PLYUID_tuple'].append(
                            ('',int(parsed_filename['plyuid']))
                            )
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                self.mp_parserrors.append(file)

    def connect_database(self):
        print("connect_database()")
        if self.input_dir_py == "":
            reply = QMessageBox.information(self, 'Unable to connect to database', 'No signal files selected.\nWould you like to select a signal file directory?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.get_signal_files()
        else:
            self.metadata_warnings={}
            self.metadata_list.addItem("Gauging Filemaker connection...")
            try:
                dsn = 'DRIVER={FileMaker ODBC};Server=128.249.80.130;Port=2399;Database=MICE;UID=Python;PWD='
                self.mousedb = pyodbc.connect(dsn)
                self.mousedb.timeout=1
                self.mp_parser()
                self.get_study()
                self.dir_checker(self.output_dir_py,self.py_output_folder,"BASSPRO")
                self.save_filemaker()
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                self.metadata_list.addItem("Unable to connect to Filemaker.")
                # if self.metadata == "":
                reply = QMessageBox.information(self, 'Unable to connect to database', 'PAPR is unable to connect to the database.\nWould you like to select another metadata file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                if reply == QMessageBox.Ok:
                    self.get_metadata()
                # if reply == QMessageBox.Cancel:
                    # self.metadata_list.clear()
                    # for item in self.metadata_list.findItems("file not detected.",Qt.MatchEndsWith):
                    # and we remove them from the widget.
                        # self.metadata_list.takeItem(self.metadata_list.row(item))
                    # self.metadata_list.addItem("No metadata file selected.")
                # self.get_metadata()
            # for item in self.metadata_list.findItems("connection",Qt.MatchContains):
            #     self.metadata_list.takeItem(self.metadata_list.row(item))
            # self.metadata_list.addItem("Building query...")

    def get_study(self, fixformat=True):
        print("get_study()")
        # self.metadata_warnings={}
        # self.metadata_list.addItem("Gauging Filemaker connection...")
        # try:
        #     dsn = 'DRIVER={FileMaker ODBC};Server=128.249.80.130;Port=2399;Database=MICE;UID=Python;PWD='
        #     self.mousedb = pyodbc.connect(dsn)
        #     self.mousedb.timeout=5
        # except:
        #     self.metadata_list.addItem("Unable to connect to Filemaker.")
        self.metadata_list.addItem("Building query...")
        try:
            FieldDict={"MUID":['Mouse_List','Plethysmography'],
                "PlyUID":['Plethysmography'],
                "Misc. Variable 1 Value":['Plethysmography'],
                "Sex":['Mouse_List'],
                "Genotype":['Mouse_List'],
                "Group":['Plethysmography'],
                "Weight":['Plethysmography'],
                # "Age":[],
                "Comments":['Mouse_List'],
                "Date of Birth":['Mouse_List'],
                "Experiment_Name":['Plethysmography'],
                "Researcher":['Plethysmography'],
                "Experimental_Date":['Plethysmography'],
                "time started":['Plethysmography'],
                "Rig":['Plethysmography'],
                # "Plate":['Mouse_List'],
                # "Row":['Mouse_List'],
                # "Column":['Mouse_List'],
                "Tag Number":['Mouse_List'],
                "Start_body_temperature":['Plethysmography'],
                "Mid_body_temperature":['Plethysmography'],
                "End_body_temperature":['Plethysmography'],
                "post30_body_temperature":['Plethysmography'],
                "Room_Temp":['Plethysmography'],
                "Bar_Pres":['Plethysmography'],
                "Rotometer_Flowrate":['Plethysmography'],
                "Pump Flowrate":['Plethysmography'],
                "Calibration_Volume":['Plethysmography'],
                "Experimental_Date":['Plethysmography'],
                "Calibration_Condition":['Plethysmography'],
                "Experimental_Condition":['Plethysmography'],
                "Experimental_Treatment":['Plethysmography'],
                "Gas 1":['Plethysmography'],
                "Gas 2":['Plethysmography'],
                "Gas 3":['Plethysmography'],
                "Tank 1":['Plethysmography'],
                "Tank 2":['Plethysmography'],
                "Tank 3":['Plethysmography'],
                "Dose":['Plethysmography'],
                "Habituation":['Plethysmography'],
                "Plethysmography":['Plethysmography'],
                "PlyUID":['Plethysmography'],
                "Notes":['Plethysmography'],
                "Project Number":['Plethysmography'],
                }
            
            #assemble fields for SQL query
            m_FieldText='"'+'","'.join(
                [i for i in list(
                    FieldDict.keys()
                    ) if 'Mouse_List' in FieldDict[i]]
                )+'"'
            p_FieldText='"'+'","'.join(
                [i for i in list(
                    FieldDict.keys()
                    ) if 'Plethysmography' in FieldDict[i]]
                )+'"'
            
            # filter sql query based on muid and plyuid info if provided
            if self.mp_parsed['MUIDLIST']!=[] and self.mp_parsed['PLYUIDLIST']!=[]:
                m_cursor = self.mousedb.execute(
                    """select """+m_FieldText+
                    """ from "Mouse_List" where "MUID" in ("""+
                    ','.join([str(i) for i in self.mp_parsed['MUIDLIST']])+
                    """) """)    
                p_cursor = self.mousedb.execute(
                    """select """+p_FieldText+
                    """ from "Plethysmography" where "PLYUID" in ("""+
                    ','.join([str(i) for i in self.mp_parsed['PLYUIDLIST']])+
                    """) and "MUID" in ("""+
                    ','.join(["'M{}'".format(int(i)) for i in self.mp_parsed['MUIDLIST']])+
                    """) """)
            elif self.mp_parsed['PLYUIDLIST']!=[]:
                m_cursor = self.mousedb.execute(
                    """select """+m_FieldText+
                    """ from "Mouse_List" """)    
                p_cursor = self.mousedb.execute(
                    """select """+p_FieldText+
                    """ from "Plethysmography" where "PLYUID" in ("""+
                    ','.join([str(i) for i in self.mp_parsed['PLYUIDLIST']])+
                    """) """)
            elif self.mp_parsed['MUIDLIST']!=[]:
                m_cursor = self.mousedb.execute(
                    """select """+m_FieldText+
                    """ from "Mouse_List" where "MUID" in ("""+
                    ','.join([str(i) for i in self.mp_parsed['MUIDLIST']])+
                    """) """)    
                p_cursor = self.mousedb.execute(
                    """select """+p_FieldText+
                    """ from "Plethysmography" where "MUID" in ("""+
                    ','.join(["'M{}'".format(int(i)) for i in self.mp_parsed['MUIDLIST']])+
                    """) """)
            else:
                m_cursor = self.mousedb.execute(
                    """select """+m_FieldText+
                    """ from "Mouse_List" """)    
                p_cursor = self.mousedb.execute(
                    """select """+p_FieldText+
                    """ from "Plethysmography" """)
                
            self.metadata_list.addItem("Fetching metadata...")
            m_mouse_list = m_cursor.fetchall()
            p_mouse_list = p_cursor.fetchall()
            m_head_list = [i[0] for i in m_cursor.description]
            p_head_list = [i[0] for i in p_cursor.description]
            self.mousedb.close()
            for i in p_mouse_list:
                self.p_mouse_dict['Ply{}'.format(int(i[p_head_list.index('PlyUID')]))]=dict(zip(p_head_list,i))
            for i in m_mouse_list:
                self.m_mouse_dict['M{}'.format(int(i[p_head_list.index('MUID')]))]=dict(zip(m_head_list,i))
            for z in self.p_mouse_dict:
                if self.p_mouse_dict[z]['Mid_body_temperature'] == 0.0:
                    self.p_mouse_dict[z]['Mid_body_temperature'] = None
            #%
            self.metadata_checker_filemaker()
            plys={}
            for k in self.metadata_warnings:
                for v in self.metadata_warnings[k]:
                    if v in self.metadata_warnings[k]:
                        if v in plys.keys():
                            plys[v].append(k)
                        else:
                            plys[v] = [k]
            for w,x in plys.items():
                self.hangar.append(f"plys.items{w}: {[x for x in plys[w]]}")
                # self.hangar.append(f"{k}: {self.metadata_warnings[k][0]}")
            #%
            p_df=pd.DataFrame(self.p_mouse_dict).transpose()
            m_df=pd.DataFrame(self.m_mouse_dict).transpose()
        
            #% fix field formatting
            if fixformat==True:
                p_df['PlyUID']='Ply'+p_df['PlyUID'].astype(int).astype(str)
                p_df['Experimental_Date']=pd.to_datetime(p_df['Experimental_Date'], errors='coerce')
                m_df['MUID']='M'+m_df['MUID'].astype(int).astype(str)
                m_df['Date of Birth']=pd.to_datetime(m_df['Date of Birth'], errors='coerce')
                
                
            self.assemble_df=pd.merge(p_df,m_df, how='left', 
                            left_on='MUID', right_on='MUID')
            self.assemble_df['Age']=(self.assemble_df['Experimental_Date']-self.assemble_df['Date of Birth']).dt.days
        # print(self.assemble_df)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            new_error='unable to assemble metadata'
            meta_assemble_errors = []
            meta_assemble_errors.append(new_error)
            # return pd.DataFrame(),errors
            print(meta_assemble_errors)

    def metadata_checker_filemaker(self):
        print("metadata_checker_filemaker()")
        self.essential_fields = self.gui_config['Dictionaries']['metadata']['essential_fields']
        self.metadata_list.addItem("Checking metadata...")
        # For the MUID and PlyUID pair taken from the signal files provided by the user:
        for m,p in self.mp_parsed["MUID_PLYUID_tuple"]:
            # Check if the PlyUID is in the metadata:
            if f"Ply{p}" not in self.p_mouse_dict:
                # If the PlyUID isn't in the metadata, check if its associated MUID is:
                # (We check for the MUID in the m_mouse_dict because its populated regardless of the status of 
                # a MUID's associated PlyUID)
                if f"M{m}" not in self.m_mouse_dict:
                    self.metadata_warnings[f"Ply{p}"] = [f"Neither Ply{p} nor M{m} were found in metadata."]
                # If the PlyUID isn't in the metadata, but its associated MUID is:
                else:
                    self.metadata_warnings[f"Ply{p}"] = [f"Ply{p} of M{m} not found in metadata."]
                    # Should we consider showing what PlyUIDs are associated with that MUID?
            else:
                # Check if the MUID of the signal file matches that found in the metadata:
                if self.p_mouse_dict[f"Ply{p}"]["MUID"] != f"M{m}":
                    # If there is no MUID associated with the PlyUID in the metadata:
                    if self.p_mouse_dict[f"Ply{p}"]["MUID"] == "":
                        # Check if the provided MUID is even in the metadata:
                        if f"M{m}" not in self.m_mouse_dict:
                            self.metadata_warnings[f"Ply{p}"] = [f"M{m} of Ply{p} not found in metadata."]
                        else:
                            self.metadata_warnings[f"Ply{p}"] = [f"M{m} of Ply{p} found in Mouse_List, but no MUID was found in Plethysmography."]
                    else:
                        db_meta = self.p_mouse_dict[f"Ply{p}"]["MUID"]     
                        self.metadata_warnings[f"Ply{p}"] = [f"Unexpected MUID: M{m} provided by file, {db_meta} found in metadata."]
                else:
                    for fm in self.essential_fields["mouse"]:
                        if fm not in self.m_mouse_dict[f"M{m}"].keys():
                            if f"Ply{p}" in self.metadata_warnings.keys():
                                self.metadata_warnings[f"Ply{p}"].append(f"Missing metadata for {fm}.")
                            else:
                                self.metadata_warnings[f"Ply{p}"] = [f"Missing metadata for {fm}."]
                        elif self.m_mouse_dict[f"M{m}"][fm] == None:
                            if f"Ply{p}" in self.metadata_warnings.keys():
                                self.metadata_warnings[f"Ply{p}"].append(f"Empty metadata for {fm}.")
                            else:
                                self.metadata_warnings[f"Ply{p}"] = [f"Empty metadata for {fm}."]
                    for fp in self.essential_fields["pleth"]:
                        if fp not in self.p_mouse_dict[f"Ply{p}"].keys():
                            if f"Ply{p}" in self.metadata_warnings.keys():
                                self.metadata_warnings[f"Ply{p}"].append(f"Missing metadata for {fp}.")
                            else:
                                self.metadata_warnings[f"Ply{p}"] = [f"Missing metadata for {fp}."]
                        elif self.p_mouse_dict[f"Ply{p}"][fp] == None:
                            if f"Ply{p}" in self.metadata_warnings.keys():
                                self.metadata_warnings[f"Ply{p}"].append(f"Empty metadata for {fp}.")
                            else:
                                self.metadata_warnings[f"Ply{p}"] = [f"Empty metadata for {fp}."]
            if f"Ply{p}" not in self.metadata_warnings.keys(): 
                self.metadata_passlist.append(f"M{m}_Ply{p}")
     
    def save_filemaker(self):
        print("save_filemaker()")
        # self.mp_parser()
        # self.get_study()
    
        self.metadata_list.addItem("Creating csv file...")
        # If a mothership directory has yet to be selected...
        # if self.mothership == "":
            # A save file dialog pops up in the Plethysmography folder (should this change?) as indicated by self, the first argument of the QFileDialog function. The proffered filename is metadata_{the same timestamp
            # given to self.output_dir_py} - if self.output_dir_py has yet to be specificed, then the file is proffered as metadata_. This saved .csv file's path is assigned to self.metadata_path.
            # self.metadata_path = QFileDialog.getSaveFileName(self, 'Save File', f"metadata_{os.path.basename(self.output_dir_py).lstrip('py_output_')}", ".csv(*.csv))")[0]
        self.metadata = os.path.join(self.mothership,"metadata.csv")
        # If the user presses cancel in the save file dialog, the widget clears and says "No file selected."
        # if not self.metadata_path:
            # self.metadata_list.clear()
            # self.metadata_list.addItem("No file selected.")
        # If self.metadata_path is populated successfully by the file saved via the dialog, the widget is cleared and the path is added to the widget.
        # else:
        try:
            self.assemble_df.to_csv(self.metadata, index = False)
            self.metadata_list.clear()
            self.metadata_list.addItem(self.metadata)
            # shutil.copy(self.metadata, os.path.join(self.mothership, "metadata.csv"))
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            reply = QMessageBox.information(self, 'File in use', 'One or more of the files you are trying to save is open in another program.', QMessageBox.Ok)
        
        # else:
            # If a mothership directory exists, then a path for self.output_dir_py has been generated. The directory needs to actually be created because the metadata file needs to be written to it. Normally, the directory
            # isn't made until pything_to_do is called.
            # if not os.path.exists(self.output_dir_py):
                # Path(self.output_dir_py).mkdir()
            # self.metadata_path = os.path.join(self.output_dir_py, f"metadata_{os.path.basename(self.output_dir_py).lstrip('py_output_')}.csv")
            # self.assemble_df.to_csv(self.metadata_path, index = False)
            # self.metadata_list.clear()
            # self.metadata_list.addItem(self.metadata_path)
            # shutil.copy(self.metadata_path, os.path.join(self.mothership, "metadata.csv"))
        # self.metadata_path = self.metadata

        # except:
        #     self.metadata_list.addItem("No Filemaker connection.")
        #     file_name = QFileDialog.getOpenFileNames(self, 'Select files', self.output_dir_py)
        #     if not file_name[0]:
        #         self.metadata_list.clear()
        #         self.metadata_list.addItem("No file selected.")
        #     else:
        #         self.metadata_list.clear()
        #         for x in range(len(file_name[0])):
        #             self.metadata_list.addItem(file_name[0][x])
        #         self.metadata = file_name[0][0]

    # def get_configs(self):


    def get_autosections(self):
        print("get_autosections()")
        try:
            file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(self.mothership))
        # for f in ["auto_sections","manual_sections","basics"]:
            # for item in self.sections_list.findItems(f,Qt.MatchContains):
                # self.sections_list.takeItem(self.sections_list.row(item))
        
            if not file_name[0]:
                if self.autosections == "" and self.basicap == "" and self.mansections == "":
                    self.sections_list.addItem("No BASSPRO settings files selected.")
            else:
                # self.sections_list.clear()
                print("files chosen")
                for x in range(len(file_name[0])):
                    if file_name[0][x].endswith('.csv'):
                        # print(file_name[0][x])
                        if os.path.basename(file_name[0][x]).startswith("auto_sections") | os.path.basename(file_name[0][x]).startswith("autosections"):
                            print(file_name[0][x])
                            self.autosections = file_name[0][x]
                            print(self.autosections)
                            for item in self.sections_list.findItems("auto_sections",Qt.MatchContains):
                                self.sections_list.takeItem(self.sections_list.row(item))
                            self.sections_list.addItem(self.autosections)
                        elif os.path.basename(file_name[0][x]).startswith("manual_sections"):
                            print(file_name[0][x])
                            self.mansections = file_name[0][x]
                            for item in self.sections_list.findItems("manual_sections",Qt.MatchContains):
                                self.sections_list.takeItem(self.sections_list.row(item))
                            self.sections_list.addItem(self.mansections)
                        elif os.path.basename(file_name[0][x]).startswith("basics"):
                            print(file_name[0][x])
                            self.basicap = file_name[0][x]
                            for item in self.sections_list.findItems("basics",Qt.MatchContains):
                                self.sections_list.takeItem(self.sections_list.row(item))
                            self.sections_list.addItem(self.basicap)
                    else:
                        self.thumb = Thumbass(self)
                        self.thumb.show()
                        self.thumb.message_received("The settings files for BASSPRO must be in csv format. Please convert your settings files or choose another file.")
                
                        

            
            # for p in [self.autosections,self.mansections,self.basicap]:
            #     self.sections_list.clear()
            #     self.sections_list.addItem(p)
            for item in self.sections_list.findItems("settings files selected",Qt.MatchContains):
                self.sections_list.takeItem(self.sections_list.row(item))
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            # reply = QMessageBox.information(self, 'File in use', 'One or more you are trying to save is open in another program.', QMessageBox.Ok)
    # def papr_directory(self):
    #     self.papr_dir = QFileDialog.getExistingDirectory(self, 'Select papr directory', str(Path.home()))
    #     if not self.papr_dir:
    #         self.papr_dir_list.clear()
    #         self.papr_dir_list.addItem("No folder selected.")
    #     else:
    #         self.papr_dir_list.clear()
    #         self.papr_dir_list.addItem(self.papr_dir)

    def input_directory_r(self):
        print("input_directory_r()")
        folder = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/BASSPRO_output")
        self.input_dir_r = QFileDialog.getExistingDirectory(self, 'Choose breathlist directory', str(folder))
        if not self.input_dir_r:
            self.breath_list.clear()
            self.breath_list.addItem("No folder selected.")
        else:
            self.breath_list.clear()
            self.breath_list.addItem(self.input_dir_r)
    
    def input_directory_r_env(self):
        print("input_directory_r_env()")
        folder = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/STAGG_output")
        file_name = QFileDialog.getOpenFileNames(self, 'Select R environment', str(folder))
        if not file_name[0]:
            self.breath_list.clear()
            self.breath_list.addItem("No file selected.")
        elif not os.path.basename(file_name[0][0]).endswith("RData"):
            self.thumb = Thumbass(self)
            self.thumb.show()
            self.thumb.message_received("The file you selected is not the correct format for an R environment (.RData). Please check the format of your file or choose another one.")
        else:
            self.breath_list.clear()
            for x in range(len(file_name[0])):
                self.breath_list.addItem(file_name[0][x])
            self.input_dir_r = file_name[0][0]

    # def output_directory_r(self):
    #     if Path(self.mothership).exists():
    #         path = self.mothership
    #     else:
    #         path = str(Path.home())
    #     self.output_dir_r = QFileDialog.getExistingDirectory(self, 'Choose output directory', path)
    #     if not self.output_dir_r:
    #         self.r_output_dir_list.clear()
    #         self.r_output_dir_list.addItem("No folder selected.")
    #     else:
    #         self.r_output_dir_list.clear()
    #         self.r_output_dir_list.addItem(self.output_dir_r)

#endregion

#region Go methods

    def go_r(self):
        print("go_r()")
        papr_cmd='"{rscript}" "{pipeline}" -d "{d}" -J "{j}" -R "{r}" -G "{g}" -O "{o}" -T "{t}" -S "{s}" -M "{m}" -B "{b}"'.format(
            rscript = self.gui_config['Dictionaries']['Paths']['rscript1'],
            pipeline = os.path.join(self.papr_dir, "pipeline.R"),
            d = self.mothership,
            # j = os.path.join(self.mothership, "JSON"),
            j = self.input_dir_r,
            r = self.variable_config,
            # r = os.path.join(self.mothership, "R_config/sava_config_copied.csv"),
            g = self.graph_config,
            f = self.other_config,
            # g = os.path.join(self.mothership, "G_config/sava_graph_copied.csv"),
            # o = os.path.join(self.mothership, "Output")
            # o = "C:/Users/atwit/Desktop/Mothership/STAGG_output/r_output20201016_171213",
            o = self.output_dir_r,
            t = os.path.join(self.papr_dir, "tibblemaker.R"),
            s = os.path.join(self.papr_dir, "stat_runner.R"),
            m = os.path.join(self.papr_dir, "graph_maker.R"),
            b = os.path.join(self.papr_dir, "other_graphs.R")
        )
        self.hangar.append(papr_cmd)
        print('go_r thread id',threading.get_ident())
        print("go_r process id",os.getpid())
        self.py_proc_r=subprocess.Popen(papr_cmd, stdout= subprocess.PIPE, stderr = subprocess.STDOUT)
     
    def go_py(self):
        print("go_py()")
        # log=os.path.join(self.output_dir_py,'log_"{bob}"'.format(bob=os.path.basename(os.path.normpath(self.output_dir_py))))
        breathcaller_cmd = 'python -u "{module}" -i "{id}" {filelist} -o "{output}" -a "{metadata}" -m "{manual}" -c "{auto}" -p "{basic}"'.format(
            module = self.breathcaller_path,
            id = self.input_dir_py,
            output = self.output_dir_py,
            # signal = os.path.basename(file_py),
            filelist= '-f "'+'" -f "'.join([os.path.basename(i) for i in self.signals])+'"',
            metadata = self.metadata,
            # manual = Plethysmography.mansections,
            manual = "", 
            auto = self.autosections,
            basic = self.basicap
        )

        print(breathcaller_cmd)
        self.hangar.append("Breathcaller command: "+breathcaller_cmd)
        print('go_py thread id',threading.get_ident())
        print("go_py process id",os.getpid())
        self.py_proc=subprocess.Popen(breathcaller_cmd, stdout= subprocess.PIPE, stderr = subprocess.STDOUT)

    def go_super(self):
        print("super!")

#endregion

#region Go checking

# See GUIv7

#endregion

#region Progress

    def _parse_results(self, output):
        print('parsing results')
        # Output has one row of headers, all single words.  The
        # remaining rows are one per filesystem, with columns
        # matching the headers (assuming that none of the
        # mount points have whitespace in the names).
        if not output:
            return []
        lines = output.splitlines()
        headers = lines[0].split()
        devices = lines[1:]
        results = [
            dict(zip(headers, line.split()))
            for line in devices
        ]
        return results
    
    def parse_progress(self,line):
        compiled_re=re.compile('PROGRESS: (?P<pct>.+)% - ETC: (?P<eta>.+) (remaining )?of (?P<ert>.+) minutes - File (?P<curfile_no>.+) of (?P<totfile_no>.+)')
        parsed_line=re.search(compiled_re,line)
        self.mp_parsed={
            'percent_complete':parsed_line['pct'],
            'time_remaining':parsed_line['eta'],
            'estimated_total_time':parsed_line['ert'],
            'current_file_no':parsed_line['curfile_no'],
            'total_file_no':parsed_line['totfile_no']
            }
        return self.mp_parsed

    def update_Rprogress(self):
        print('Rprogress thread id',threading.get_ident())
        print("Rprogress process id",os.getpid())
        self.go_r()
        print("post")
        # self.completed = 0
        while True:
            output = self.py_proc_r.stdout.readline().decode('utf8')
            # errput = self.py_proc_r.stderr.readline().decode('utf8')
            if output=='' and self.py_proc_r.poll() is not None:
                break
            if output!='': 
                print(output.strip())
                
            # if 'PROGRESS:' in output.strip():
            #     current_progress=self.parse_progress(output.strip())
            #     print('***  {percent_complete}  |  {time_remaining}  |  {estimated_total_time}  |  {current_file_no}  |  {total_file_no}  ********'.format(**current_progress))
            #     self.completed = float(current_progress['percent_complete'])
            # if 'Adding file:' in output.strip():
            #     self.completed =+ 1
            self.hangar.append(str(output.strip()))
            QApplication.processEvents()
            time.sleep(0.2)
            # self.progressBar_r.setValue(self.completed)

    def updateProgress(self):
        print("bob")

    def update_Pyprogress(self):
        print("pre go")
        print('Pyprogress thread id',threading.get_ident())
        print("Pyprogress process id",os.getpid())
        self.go_py()
        print("post go")
        self.completed = 0
        while True:
            output = self.py_proc.stdout.readline().decode('utf8')
            if output=='' and self.py_proc.poll() is not None:
                break
            if output!='': 
                print(output.strip())
            #     for line in output.strip():
            #         self.completed += 1
            # if 'PROGRESS:' in output.strip():
            #     current_progress=self.parse_progress(output.strip())
            #     print('***  {percent_complete}  |  {time_remaining}  |  {estimated_total_time}  |  {current_file_no}  |  {total_file_no}  ********'.format(**current_progress))
                # self.completed = float(current_progress['percent_complete'])
                
            self.hangar.append(str(output.strip()))
            QApplication.processEvents()
            time.sleep(0.2)
            # self.progressBar_py.setValue(self.completed)

#endregion

#region Threading

# Concurrency is a nightmare. I'll do my best to explain what's going on. Currently, there are two types of concurrency enabled for both the breathcaller and papr.
# I'm in the process of exploring the black box. Fear is the mind killer.

    def py_message(self):
        print("py_message()")
        self.hangar.append("BASSPRO analyzing signal files...")
        if self.parallel_box.isChecked() == True:
            self.pything_to_do()
        else:
            self.pything_to_do_single()
        self.auto_get_breath_files()

    def r_message(self):
        print("r_message()")
        self.hangar.append("STAGG analyzing BASSPRO output...")
        print(f'configs: {self.v.configs}')
        print(f'v:{self.variable_config}')
        print(f'g:{self.graph_config}')
        print(f'o:{self.other_config}')
        self.variable_config = self.v.configs["variable_config"]["path"]
        self.graph_config = self.v.configs["graph_config"]["path"]
        self.other_config = self.v.configs["other_config"]["path"]
        # if self.variable_config == "" or self.graph_config == "" or self.other_config == "":
        if any([self.v.configs[key]['path'] == "" for key in self.v.configs]):
            if os.path.basename(self.input_dir_r).endswith("RData"):
                reply = QMessageBox.question(self, 'Configuration settings', 'One or more configuration settings files not provided.\n\nWould you like to continue?\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    for key in self.v.configs:
                        if self.v.configs[key]["path"] == "":
                            print("r_config path is empty")
                            self.v.configs[key]["path"] == "None"
                            print(self.v.configs[key]["path"])
                    # self.variable_config = "None"
                    # self.graph_config = "None"
                    # self.other_config = "None"
                    if self.parallel_r.isChecked() == True:
                        self.rthing_to_do_single()
                    else:
                        self.rthing_to_do()
            else:
                self.thumb = Thumbass(self)
                self.thumb.show()
                self.thumb.message_received("No variable or graphing configuration files were selected - please choose or create configuration files. You may also select a previously built R environment that includes such settings.")
        else:
            if self.parallel_r.isChecked() == True:
                self.rthing_to_do_single()
            else:
                self.rthing_to_do()

    def dir_checker(self,output_folder,output_folder_parent,text):
        print("dir_checker()")
        self.output_folder = ""
        self.output_folder_parent = ""
        if output_folder == "":
            if output_folder_parent == "":
                if self.mothership == "":
                    self.mothership = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output")
                    print(self.mothership)
                    print(f'no mothership so detected as: {self.mothership}')
                    if not os.path.exists(self.mothership):
                        print("mothership is empty and the provided default nonexistent - this shouldn't happen")
                        try:
                            output_folder = QFileDialog.getExistingDirectory(self, f'Choose directory for {text} output', str(self.mothership))
                            output_folder_parent = os.path.dirname(output_folder)
                            self.output_folder_parent = output_folder_parent
                        except Exception as e:
                            print(f'{type(e).__name__}: {e}')
                            print("if you've made it this far, you're screwed")
                    else:
                        output_folder_parent = os.path.join(self.mothership,f"{text}_output")
                        print(output_folder_parent)
                        print(f'mothership is empty but the default exists, so pointing out {text} output folder')
                        if not os.path.exists(output_folder_parent):
                            print(f"trying to make {text} output folder cause it doesn't exist")
                            try:
                                print(f'making {text} output folder cause it not exists')
                                os.makedirs(output_folder_parent)
                                self.output_folder_parent = output_folder_parent
                            except Exception as e:
                                print(f'{type(e).__name__}: {e}')
                                print("apparently os.path.exists says no but os.makedirs says yes it exists")
                        else:
                            self.output_folder_parent = output_folder_parent
                        output_folder = os.path.join(output_folder_parent, f'{text}_output_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
                        print(output_folder)
                        print('pointed out where output_folder is, now checking it exists')
                        if not os.path.exists(output_folder):
                            print("trying to make output folder cause it doesn't exist")
                            try:
                                print('making output folder cause it not exist')
                                os.makedirs(output_folder)
                                self.output_folder = output_folder
                            except Exception as e:
                                print(f'{type(e).__name__}: {e}')
                                print('apparently os.path.exists says no but os.makedirs says yes exists')
                        else:
                            self.output_folder = output_folder
                else:
                    if not os.path.exists(self.mothership):
                        print("mothership is not empty but doesn't exist")
                        try:
                            output_folder = QFileDialog.getExistingDirectory(self, f'Choose directory for {text} output', str(self.mothership))
                            output_folder_parent = os.path.dirname(output_folder)
                            self.output_folder_parent = output_folder_parent
                            self.output_folder = output_folder
                        except Exception as e:
                            print(f'{type(e).__name__}: {e}')
                            print("if you've made it this far, you're screwed")
                    else:
                        output_folder_parent = os.path.join(self.mothership,f"{text}_output")
                        print(output_folder_parent)
                        print(f'mothership exists and is not empty, so checking on the {text} output folder')
                        if not os.path.exists(output_folder_parent):
                            print(f"trying to make {text} output folder cause it doesn't exist")
                            try:
                                print(f'making {text} output folder cause it not exists')
                                os.makedirs(output_folder_parent)
                                self.output_folder_parent = output_folder_parent
                            except Exception as e:
                                print(f'{type(e).__name__}: {e}')
                                print("apparently os.path.exists says no but os.makedirs says yes it exists")
                        else:
                            self.output_folder_parent = output_folder_parent
                        output_folder = os.path.join(output_folder_parent, f'{text}_output_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
                        print(output_folder)
                        print('pointed out where output_folder is, now checking it exists')
                        if not os.path.exists(output_folder):
                            print("trying to make output folder cause it doesn't exist")
                            try:
                                print('making output folder cause it not exist')
                                os.makedirs(output_folder)
                                self.output_folder = output_folder
                            except Exception as e:
                                print(f'{type(e).__name__}: {e}')
                                print('apparently os.path.exists says no but os.makedirs says yes exists')
                        else:
                            self.output_folder = output_folder
            else:
                output_folder = os.path.join(output_folder_parent, f'{text}_output_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
                print(output_folder)
                print('pointed out where output_folder is, now checking it exists')
                if not os.path.exists(output_folder):
                    print("trying to make output folder cause it doesn't exist")
                    try:
                        print('making output folder cause it not exist')
                        os.makedirs(output_folder)
                        self.output_folder = output_folder
                    except Exception as e:
                        print(f'{type(e).__name__}: {e}')
                        print('apparently os.path.exists says no but os.makedirs says yes exists')
        else:
            if not os.path.exists(output_folder):
                print("trying to make output folder cause it's not empty but it still doesn't exist")
                try:
                    print('making output folder that is not empty but doesnt exist')
                    os.makedirs(output_folder)
                    self.output_folder = output_folder
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print('apparently os.path.exists says no but os.makedirs says yes exists')
            else:
                self.output_folder = output_folder
            if any(Path(self.output_folder).iterdir()) == True:
                reply = QMessageBox.question(self, f'Confirm {text} output directory', 'The current output directory has files in it that may be overwritten.\n\nWould you like to create a new output folder?\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    output_folder_parent = os.path.dirname(output_folder)
                    self.output_folder = os.path.join(output_folder_parent, f'{text}_output_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
                    print(output_folder_parent)
                    print(os.path.join(output_folder_parent, f'{text}_output_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')))
                    print(self.output_folder)
                    os.makedirs(self.output_folder)
                elif reply == QMessageBox.No:
                    print("kept old output folder: {output_folder}")

                    
    
    def pything_to_do(self):
        print("pything_to_do()")
        self.dir_checker(self.output_dir_py,self.py_output_folder,"BASSPRO")
        if self.output_folder != "":
            self.output_dir_py = self.output_folder
        print(self.output_dir_py)
        # This conditional essentially checks whether or not a copy of the metadata already exists because if the metadat was pulled directly from Filemaker, then that function automatically makes the output py directory and places the pulled metadata in there before the launch button. I should change this and isolate the creation and copying to just the launch.
        # if self.metadata_path == "":
        shutil.copyfile(self.metadata, os.path.join(self.output_dir_py, f"metadata_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv"))
        # self.get_parameter()
        shutil.copyfile(f'{Path(__file__).parent}/breathcaller_config.json', os.path.join(self.output_dir_py, f"breathcaller_config_{os.path.basename(self.output_dir_py).lstrip('py_output')}.txt"))
        # if self.a.auto_df != "":
        #     self.a.auto_df.to_csv(self.autosections,index=False)
        if self.autosections != "":
            shutil.copyfile(self.autosections, os.path.join(self.output_dir_py, f"auto_sections_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv"))
        # if self.m.manual_df != "":
        #     self.m.manual_df.to_csv(self.mansections,index=False)
        if self.mansections != "":
            shutil.copyfile(self.mansections, os.path.join(self.output_dir_py, f"manual_sections_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv"))
        # A copy of the basic parameters is not included because that's found in the breathcaller_config file. But so are all the other settings...
        if self.basicap != "":
            shutil.copyfile(self.basicap, os.path.join(self.output_dir_py, f"basics_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv"))
        with open(f'{Path(__file__).parent}/gui_config.json','w') as gconfig_file:
            json.dump(self.gui_config,gconfig_file)
        shutil.copyfile(f'{Path(__file__).parent}/gui_config.json', os.path.join(self.output_dir_py, f"gui_config_{os.path.basename(self.output_dir_py).lstrip('py_output')}.txt"))


        print('pything_to_do thread id',threading.get_ident())
        print("pything_to_do process id",os.getpid())
        # self.thready(self.update_Pyprogress)
        self.worker = threading.Thread(target = MainGUIworker.futurama_py(self))
        self.worker.daemon = True
        self.worker.start()
        # Note that this isn't printed until the very end, after all files have been processed and everything is basically done.
        print("worker started?")
    
    def rthing_to_do(self):
        # self.hangar.append("STAGG analyzing breath files...")
        print("rthing_to_do()")
        self.dir_checker(self.output_dir_r,self.r_output_folder,"STAGG")
        if self.output_folder != "":
            self.output_dir_r = self.output_folder
        print(f'after:{self.output_dir_r}')
        if self.svg_radioButton.isChecked() == True:
            self.image_format = ".svg"
        elif self.jpeg_radioButton.isChecked() == True:
            self.image_format = ".jpeg"
        if os.path.isdir(os.path.join(self.output_dir_r,"StatResults")):
            print("no stat results folder")
            os.makedirs(os.path.join(self.output_dir_r,"StatResults"))
        try:
            print("shutil is trying to happen for configs")
            if datetime.datetime.now().strftime('%Y%m%d_%H%M%S') == os.path.basename(self.output_dir_r).lstrip('STAGG_output'):
                print("output folder timestamp and config timestamp are equal")
            else:
                print("output and config timestamp not equal:\nconfig: {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}\noutput: {os.path.basename(self.output_dir_r).lstrip('STAGG_output')}")
            shutil.copyfile(self.variable_config, os.path.join(self.output_dir_r, f"variable_config_{os.path.basename(self.output_dir_r).lstrip('STAGG_output')}.csv"))
            # {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}
            shutil.copyfile(self.graph_config, os.path.join(self.output_dir_r, f"graph_config_{os.path.basename(self.output_dir_r).lstrip('STAGG_output')}.csv"))
            shutil.copyfile(self.other_config, os.path.join(self.output_dir_r, f"other_config_{os.path.basename(self.output_dir_r).lstrip('STAGG_output')}.csv"))
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print("No variable or graph configuration files copied to STAGG output folder.")
        print('rthing_to_do thread id',threading.get_ident())
        print("rthing_to_do process id",os.getpid())
        self.worker = threading.Thread(target = MainGUIworker.futurama_r(self))
        self.worker.daemon = True
        self.worker.start()
        # shutil.copyfile(os.path.join(self.mothership,"Summary.html"),os.path.join(self.output_dir_r, f"Summary_{os.path.basename(self.output_dir_r).lstrip('r_output')}.html"))
        print("worker started?")
        # if self.renv_check.isChecked() == 1:
            # shutil.copyfile(os.path.join(self.mothership, "myEnv.RData"), os.path.join(self.output_dir_r, f"myEnv_{os.path.basename(self.output_dir_r).lstrip('r_output')}.RData"))
        # shutil.copyfile(os.path.join(self.output_dir_r,"Summary.html"), os.path.join(self.output_dir_r, f"summary_{os.path.basename(self.output_dir_r).lstrip('r_output')}.html"))
    
    def stamp_to_do(self):
        print('stamp_to_do thread id',threading.get_ident())
        print("stamp_to_do process id",os.getpid())
        worker = threading.Thread(target = MainGUIworker.futurama_stamp(self))
        worker.daemon = True
        worker.start()
        # Note that this isn't printed until the very end, after all files have been processed and everything is basically done.
        print("worker started?")

    def rthing_to_do_single(self):
        print("rthing_to_do is happening")
        print('rthing_single thread id',threading.get_ident())
        print("rthing_single process id",os.getpid())
        self.dir_checker(self.output_dir_r,self.r_output_folder,"STAGG")
        if self.output_folder != "":
            self.output_dir_r = self.output_folder
        self.thready(self.update_Rprogress)
    
    def pything_to_do_single(self):
        print("pything_single thread id", threading.get_ident())
        print("pything_single process id", os.getpid())
        self.dir_checker(self.output_dir_py,self.py_output_folder,"BASSPRO")
        if self.output_folder != "":
            self.output_dir_py = self.output_folder
        # This conditional essentially checks whether or not a copy of the metadata already exists because if the metadat was pulled directly from Filemaker, then that function automatically makes the output py directory and places the pulled metadata in there before the launch button. I should change this and isolate the creation and copying to just the launch.
        # if self.metadata_path == "":
        shutil.copyfile(self.metadata, os.path.join(self.output_dir_py, f"metadata_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv"))
        # self.get_parameter()
        shutil.copyfile(f'{Path(__file__).parent}/breathcaller_config.json', os.path.join(self.output_dir_py, f"breathcaller_config_{os.path.basename(self.output_dir_py).lstrip('py_output')}.txt"))
        # if self.a.auto_df != "":
        #     self.a.auto_df.to_csv(self.autosections,index=False)
        shutil.copyfile(self.autosections, os.path.join(self.output_dir_py, f"autosections_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv"))
        # if self.m.manual_df != "":
        #     self.m.manual_df.to_csv(self.mansections,index=False)
        #     shutil.copyfile(self.mansections, os.path.join(self.output_dir_py, f"mansections_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv"))
        # A copy of the basic parameters is not included because that's found in the breathcaller_config file. But so are all the other settings...
        shutil.copyfile(self.basicap, os.path.join(self.output_dir_py, f"basics_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv"))
        with open(f'{Path(__file__).parent}/gui_config.json','w') as gconfig_file:
            json.dump(self.gui_config,gconfig_file)
        shutil.copyfile(f'{Path(__file__).parent}/gui_config.json', os.path.join(self.output_dir_py, f"gui_config_{os.path.basename(self.output_dir_py).lstrip('py_output')}.txt"))
        # self.thready(self.update_Pyprogress)
        self.update_Pyprogress()

    def superthing_to_do(self):
        # self.thready(self.super_go)
        self.py_message()
        self.rthing_to_do
        print("worker started?")

    def thready(self,thing_to_do):
        print('thready thread id',threading.get_ident())
        print("thready process id",os.getpid())
        testy = QtCore.QThread()
        # give self to QThread so that the thread isn't garbage-collected
        # now QThread is destroyed while thread is still running when I destroy the
        # thread by closing the GUI. Before it was destroyed when the program left the 
        # MainWindow's __init__.
        
        worker = Worker_Single(thing_to_do)
        
        worker.moveToThread(testy)
        worker.start.emit()

        # testy.started.connect(lambda: worker.run())
        # the above is hacky. Essentially this functions indicates that once testy is started,
        # a signal should be sent to make worker.run() happen.
        # Inside of the parentheses, we're trying to make worker.run() but it yields the following error:
        # testy.started.connect(worker.run())
        # TypeError: argument 1 has unexpected type 'NoneType'
        # Adding lambda makes it happy. We don't know why other than it converts worker.run()
        # into a callable function. Which worker.run() apparently is not.
        testy.start()
        worker.finished.connect(testy.quit)
        self.threadpool.append(testy)
        self.worker = worker
        # worker.start.connect(worker.run())
        # the above makes no idea

        print("thready is happening")
        # in this order, we're moving the worker to the thread before starting the thread


#endregion

#region Whimsify

# see GUIv7

#endregion

# %%
