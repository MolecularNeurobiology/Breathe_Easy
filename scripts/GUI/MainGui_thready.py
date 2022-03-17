#%%
#region Libraries
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5 import uic
import resource
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
import MainGUImain
import csv
import queue
import glob
import traceback
from pathlib import Path, PurePath
import subprocess
from subprocess import PIPE, Popen
import datetime
import time
import os
import sys
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
import MainGUIworker_thready
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
            self.n = 0
            self.pleth.v.variable_table.cellChanged.connect(self.pleth.v.no_duplicates)
            self.pleth.v.variable_table.cellChanged.connect(self.pleth.v.update_loop)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
        self.pleth.v.show()
    
    def output(self):
        print("thinbass.output()")
        try:
            # first = next(file for file in glob.glob(f'{self.pleth.input_dir_r}/*.json'))
            with open(self.pleth.stagg_list[0]) as first_json:
                bp_output = json.load(first_json)
            for k in bp_output.keys():
                self.pleth.breath_df.append(k)
            try:
                self.pleth.variable_configuration()
                self.n = 0
                self.pleth.v.variable_table.cellChanged.connect(self.pleth.v.no_duplicates)
                self.pleth.v.variable_table.cellChanged.connect(self.pleth.v.update_loop)
                self.pleth.v.show()
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            pass

#region Thumbass
class Thumbass(QDialog, Ui_Thumbass):
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
        # if self.pleth.mothership == "":
        #     dire = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/")
        # else:
        #     dire = self.pleth.mothership
        path = QFileDialog.getSaveFileName(self, 'Save BASSPRO basic parameters file', f"basics_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}", ".csv(*.csv))")[0]
        try:
            print(path)
            self.path = path
            self.actual_saving()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            print("saveas_basic_path didn't work")

    def save_basic_path(self):
        print("basic.save_basic_path()")
        self.get_parameter()
        # self.save_checker(self.pleth.mothership,"basics")
        if self.pleth.mothership == "":
            # path = os.path.realpath("./basics.csv")
            # print(path)
            self.saveas_basic_path()
        else:
            path = os.path.join(self.pleth.mothership, f"basics.csv")
        if not path:
            print("dialog cancelled")
        else:
            self.path = path
            self.actual_saving()
        # except Exception as e:
        #     print(f'{type(e).__name__}: {e}')
        #     self.saveas_basic_path()
    
    def actual_saving(self):
        print("basic.actual_saving_basic()")
        print(self.pleth.basicap)
        self.pleth.basicap = self.path
        # Saving the dataframes holding the configuration preferences to csvs and assigning them their paths:
        try:
            self.basic_df.set_index('Parameter').to_csv(self.pleth.basicap)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            print("actual saving basic to designated path (be it save or saveas) didn't work")
        
        # Copying current settings for appropriate entry in breathcaller_config:
        # new_current = pd.DataFrame.to_json(self.basic_df.set_index("index"))
        # self.pleth.bc_config['Dictionaries']['AP']['current'].update(new_current)

        with open(f'{Path(__file__).parent}/breathcaller_config.json','w') as bconfig_file:
            json.dump(self.pleth.bc_config,bconfig_file)
        
        print(self.pleth.breath_df)
        if self.pleth.breath_df != []:
            self.pleth.update_breath_df("basic parameters")
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
            print(traceback.format_exc())
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
        self.refs = {self.sections_reference:[self.help_key,self.help_cal_seg,self.help_auto_ind_include,self.help_auto_ind_injection,self.help_startpoint,self.help_midpoint,self.help_endpoint],
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
            self.auto_dict = self.pleth.bc_config['Dictionaries']['Auto Settings']['default']['5% Hypercapnia']
            print("generic dictionary accessed")
            self.auto_setting_combo.setCurrentText('5% Hypercapnia')
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

    def update_table(self,donor):
        for l in self.lineEdits:
            if donor == l.objectName():
                d = l
        for row in range(self.view_tab.rowCount()):
            if self.view_tab.item(row,0).text() == donor.replace("lineEdit_",""):
                self.view_tab.item(row,1).setText(d.text())
        
    def update_tabs(self):
        for row in range(self.view_tab.rowCount()):
            for l in self.lineEdits:
                if self.view_tab.item(row,0).text() == l.objectName().replace("lineEdit_",""):
                    l.setText(self.view_tab.item(row,1).text())

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
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
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
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
    
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
        # if self.pleth.mothership == "":
        #     dire = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/")
        # self.pleth.hangar.append("Saving autosections file...")
        path = QFileDialog.getSaveFileName(self, 'Save File', "auto_sections", ".csv(*.csv))")[0]
        if not path:
            print("dialog cancelled")
        else:
            self.path = path
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
                self.save_auto_file()
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
                    # header.append("Key")
                    for row in range(self.view_tab.rowCount()):
                        item = self.view_tab.item(row,0)
                        if item.text() == "nan":
                            header.append("")
                        # elif item.text() == "index":
                        #     print("found index column")
                        else:
                            print(item.text())
                            header.append(item.text())
                    print(header)
                    # writer.writerow(header)
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
            auto = pd.read_csv(self.pleth.autosections)
            auto['Key'] = auto['Alias']
            auto.to_csv(self.pleth.autosections,index=False)
            print(auto)
            if self.pleth.breath_df != []:
                self.pleth.update_breath_df("automated settings")
        # DO NOT KEEP THIS NONSENSE JUST INVERSE THE ROWS AND COLUMNS IN THE NESTING ABOVE
        # QUICK FIX
        # self.auto_df.transpose().to_csv(self.pleth.autosections)

            # Clearing the sections panel of the mainGUI and adding to it to reflect changes:
            for item in self.pleth.sections_list.findItems("auto_sections",Qt.MatchContains):
                self.pleth.sections_list.takeItem(self.pleth.sections_list.row(item))
            self.pleth.sections_list.addItem(self.pleth.autosections)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            if type(e) == PermissionError:
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
                    self.thumb.message_received("Naming","Please name the configuration files so that their file basename begins with variable_config, graph_config, and other_config. Otherwise, please load the settings files individually.")

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
            print(traceback.format_exc())
            reply = QMessageBox.information(self, 'File in use', 'One or more of the files you are trying to save is open in another program.', QMessageBox.Ok)
        
        # Clearing the config panel of the mainGUI and adding to it to reflect changes:
        for f in ["variable_config","graph_config","other_config"]:
            for item in self.pleth.variable_list.findItems(f,Qt.MatchContains):
                self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
        for p in [self.pleth.variable_config,self.pleth.graph_config,self.pleth.other_config]:
            self.pleth.variable_list.addItem(self.pleth.variable_config)
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
        # bob=os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/")
        file = QFileDialog.getOpenFileNames(self, 'Select Labchart datapad export file')
        print(len(file))
        print(len(file[0]))
        # If you the file you chose sucks, the GUI won't crap out.
        if not file[0]:
            print("nope")
        else:
            dfs=[]
            try:
                for f in file[0]:
                    try:
                        if f.endswith('.csv'):
                            df = pd.read_csv(f,header=[2])
                            mp = os.path.basename(f).rsplit(".csv")[0]
                        elif f.endswith('.txt'):
                            df = pd.read_csv(f,sep="\t",header=[2])
                            mp = os.path.basename(f).rsplit(".txt")[0]
                        elif f.endswith('.xlsx'):
                            df = pd.read_excel(f,header=[0])
                            mp = os.path.basename(f).rsplit(".xlsx")[0]
                    except Exception as e:
                        print(f'{type(e).__name__}: {e}')
                        print(traceback.format_exc())
                        print("manual datapad load balking at suffix")
                        pass
                    try:
                        if "_" in mp:
                            df['animal id'] = mp.rsplit("_")[0]
                            df['PLYUID'] = mp.rsplit("_")[1]
                        else:
                            df['animal id'] = mp
                            df['PLYUID'] = ""
                    except Exception as e:
                        print(f'{type(e).__name__}: {e}')
                        print(traceback.format_exc())
                        print("parsing file names for muid and plyuid balked")
                        pass
                    dfs.append(df)
                dc = pd.concat(dfs, ignore_index=True)
                dc.insert(0,'PLYUID',dc.pop('PLYUID'))
                dc.insert(0,'animal id',dc.pop('animal id'))
                keys = dc.columns
                mand = {}
                for key,val in zip(keys,self.vals):
                    mand.update({key: val})
                dc = dc.rename(columns = mand)
                dc['start_time'] = pd.to_timedelta(dc['start'],errors='coerce')
                dc['start'] = dc['start_time'].dt.total_seconds()
                dc['stop_time'] = pd.to_timedelta(dc['stop'],errors='coerce')
                dc['stop'] = dc['stop_time'].dt.total_seconds()
                if len(dc['start'].isna())>0:
                    print("not cool")
                    bob=dc[dc['start'].isna()][['animal id','PLYUID']].drop_duplicates()
                    if self.pleth.signals != []:
                        print("signals aren't empty")
                        for file in self.pleth.signals:
                            # if os.path.basename(file) == f"{bob['animal id']}_{bob['PLYUID']}.txt":
                            print(f"{bob['animal id']}_{bob['PLYUID']}")
                    # dc = dc.loc[(dc['start'] != "nan") & (dc['stop'] != "nan"),:]
                else:
                    print("cool")
                self.datapad = dc
                self.populate_table(self.datapad, self.datapad_view)
                self.datapad.to_csv("C:/Users/atwit/Desktop/datapad.csv")
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
                self.thumb = Thumbass(self)
                self.thumb.show()
                self.thumb.message_received(f"{type(e).__name__}: {e}",f"Please ensure that the datapad is formatted as indicated in the documentation.\n\n{traceback.format_exc()}")
                self.pleth.save_bug(e)
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
            print(traceback.format_exc())
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
                self.pleth.update_breath_df("manual settings")
        
        # current = pd.DataFrame.to_dict(self.manual_df.set_index("index"))
        # print(current)
        # new_current = {}
        # new_current[self.preset_menu.currentText()]=current
        # print(new_current)
        # self.pleth.bc_config['Dictionaries']['Auto Settings']['current'] = new_current

        # with open(f'{Path(__file__).parent}/breathcaller_config.json','w') as bconfig_file:
        #     json.dump(self.pleth.bc_config,bconfig_file)
        
        # Clearing the sections panel of the mainGUI and adding to it to reflect changes:
            for item in self.pleth.sections_list.findItems("manual_sections",Qt.MatchContains):
                self.pleth.sections_list.takeItem(self.pleth.sections_list.row(item))
            self.pleth.sections_list.addItem(self.pleth.mansections)
            self.pleth.hangar.append("Manual sections file saved.")
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
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
        # bob=os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/")
        file = QFileDialog.getOpenFileName(self, 'Select manual sections file to edit:')

        # If you the file you chose sucks, the GUI won't crap out.
        if not file[0]:
            print("nope")
        else:
            try:
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
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())

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
        # self.adjustSize()
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
            self.adjustSize()
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
        if self.config.custom_dict == {}:
            for item in frame:
                self.config.custom_dict[item] = {}
                # The first two columns are the name of the dependent variables selected and empty strings for ymin and ymax:
                self.config.custom_dict[item]["Alias"]=QTableWidgetItem(item)
                self.config.custom_dict[item]["ymin"]=QTableWidgetItem("")
                self.config.custom_dict[item]["ymax"]=QTableWidgetItem("")
                # Creating the radio buttons that will populate the cells in each row:
                self.config.custom_dict[item]["Poincare"]=QCheckBox()
                self.config.custom_dict[item]["Spectral"]=QCheckBox()
                # self.custom_dict[item]["Inclusive"].setAlignment(Qt.AlignHCenter)
                # Creating the combo boxes that will populate the cells in each row:
                self.config.custom_dict[item]["Transformation"]=CheckableComboBox()
                self.config.custom_dict[item]["Transformation"].addItems(["raw","log10","ln","sqrt"])
        else:
            diff = list(set(self.deps) - set(self.old_deps))
            for item_1 in diff:
                self.config.custom_dict[item_1] = {}
                # The first two columns are the name of the dependent variables selected and empty strings for ymin and ymax:
                self.config.custom_dict[item_1]["Alias"]=QTableWidgetItem(item_1)
                self.config.custom_dict[item_1]["ymin"]=QTableWidgetItem("")
                self.config.custom_dict[item_1]["ymax"]=QTableWidgetItem("")
                # Creating the radio buttons that will populate the cells in each row:
                self.config.custom_dict[item_1]["Poincare"]=QCheckBox()
                self.config.custom_dict[item_1]["Spectral"]=QCheckBox()
                # self.custom_dict[item_1]["Inclusive"].setAlignment(Qt.AlignHCenter)
                # Creating the combo boxes that will populate the cells in each row:
                self.config.custom_dict[item_1]["Transformation"]=CheckableComboBox()
                self.config.custom_dict[item_1]["Transformation"].addItems(["raw","log10","ln","sqrt"])
        for entry in self.config.custom_dict:    
            print("setting widgets in table")
            table.setItem(row,0,self.config.custom_dict[entry]["Alias"])
            table.item(row,0).setFlags(table.item(row,0).flags() ^ Qt.ItemIsEditable)
            # for col in range(table.columnCount()):
                # Populating the table widget with the row:
            table.setItem(row,1,self.config.custom_dict[entry]["ymin"])
            table.setItem(row,2,self.config.custom_dict[entry]["ymax"])
            
            # table.setCellWidget(row,3,self.custom_dict[item]["Filter"])
            table.setCellWidget(row,3,self.config.custom_dict[entry]["Transformation"])
            # table.setCellWidget(row,4,self.config.custom_dict[item]["Inclusive"])
            table.setCellWidget(row,4,self.config.custom_dict[entry]["Poincare"])
            table.setCellWidget(row,5,self.config.custom_dict[entry]["Spectral"])
            # table.setCellWidget(row,6,self.config.custom_dict[item]["Irregularity"])
                # table.item(row,0).setFlags(Qt.ItemIsEditable)
        # table.setHorizontalHeaderLabels(frame.columns)
            if entry in self.config.custom_port:
                if self.config.custom_port[entry]["Poincare"] == 1:
                    self.config.custom_dict[entry]["Poincare"].setChecked(True)
                if self.config.custom_port[entry]["Spectral"] == 1:
                    self.config.custom_dict[entry]["Spectral"].setChecked(True)
                for y in ['ymin','ymax']:
                    if self.config.custom_port[entry][y] != "":
                        self.config.custom_dict[entry][y].setText(self.config.custom_port[entry][y])
                if self.config.custom_port[entry]["Transformation"] != []:
                    self.config.custom_dict[entry]["Transformation"].loadCustom(self.config.custom_port[entry]["Transformation"])
                    self.config.custom_dict[entry]["Transformation"].updateText()
            else:
                if list(self.config.clades.loc[(self.config.clades["Alias"] == entry)]["Column"])[0] in self.config.custom_port:
                    self.config.custom_port[entry] = self.config.custom_port.pop(list(self.config.clades.loc[(self.config.clades["Alias"] == entry)]["Column"])[0])
                    if self.config.custom_port[entry]["Poincare"] == 1:
                        self.config.custom_dict[entry]["Poincare"].setChecked(True)
                    if self.config.custom_port[entry]["Spectral"] == 1:
                        self.config.custom_dict[entry]["Spectral"].setChecked(True)
                    for y in ['ymin','ymax']:
                        if self.config.custom_port[entry][y] != "":
                            self.config.custom_dict[entry][y].setText(self.config.custom_port[entry][y])
                    if self.config.custom_port[entry]["Transformation"] != []:
                        self.config.custom_dict[entry]["Transformation"].loadCustom(self.config.custom_port[entry]["Transformation"])
                        self.config.custom_dict[entry]["Transformation"].updateText()
            row += 1
        # self.view_tab.cellChanged.connect(self.update_tabs)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        print("custom finished populating table")

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
        try:
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
            print(any(th for th in [self.config.custom_port[t]["Transformation"] for t in self.config.custom_port]))
            if any(th for th in [self.config.custom_port[t]["Transformation"] for t in self.config.custom_port])==True:
                print("hay transformation custom")
                self.config.transform_combo.setCurrentText("Custom")
            else:
                print("no hay transformation apparently")
                self.config.transform_combo.setCurrentText("None")
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
        # print(f'port after: ID {id(self.config.custom_port)}')
        # print(f'{self.config.custom_port}')
        # print(f'dict after: ID {id(self.config.custom_dict)}')
        # print(f'{self.config.custom_dict}')
        # self.custom_dict[k]['Transformation'].loadCustom(transform)
        # self.custom_dict[k]['Transformation'].updateText()
        # self.transform_combo.setCurrentText("Custom")
        try:
            self.hide()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
        print(f"save_custom: {self.config.custom_port}")
            
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
        try:
            print(f"minus before: {self.pleth.loop_menu}")
            print(self.loop_table.currentRow())
            self.pleth.loop_menu[self.loop_table].pop(self.loop_table.currentRow())
            for p in self.pleth.loop_menu[self.loop_table]:
                if p > self.loop_table.currentRow():
                    self.pleth.loop_menu[self.loop_table][p-1] = self.pleth.loop_menu[self.loop_table].pop(p)
            self.loop_table.removeRow(self.loop_table.currentRow())
            print(f"minus after: {self.pleth.loop_menu}")
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())

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

    def no_duplicates(self):
        print("config.no_duplicates()")
        try:
            for row in range(self.variable_table.rowCount()):
                if row != self.variable_table.currentRow():
                    if self.variable_table.item(row,1).text() == self.variable_table.currentItem().text():
                        self.n += 1
                        self.variable_table.item(row,1).setText(f"{self.variable_table.item(row,1).text()}_{self.n}")
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
    
    def update_loop(self):
        print("config.update_loop()")
        print(f"before: {self.deps}")
        try:
            self.classy()
            self.deps = self.clades["Alias"]
            print(f"after: {self.deps}")
            print(f"before loop table rowcount: {self.loop_table.rowCount()}")
            for row in range(self.loop_table.rowCount()):
                self.clades_other_dict.update({row:{}})
                self.clades_other_dict[row].update({"Graph": self.pleth.loop_menu[self.loop_table][row]["Graph"].text()})
                self.clades_other_dict[row].update({"Variable": self.pleth.loop_menu[self.loop_table][row]["Variable"].currentText()})
                self.clades_other_dict[row].update({"Xvar": self.pleth.loop_menu[self.loop_table][row]["Xvar"].currentText()})
                self.clades_other_dict[row].update({"Pointdodge": self.pleth.loop_menu[self.loop_table][row]["Pointdodge"].currentText()})
                self.clades_other_dict[row].update({"Facet1": self.pleth.loop_menu[self.loop_table][row]["Facet1"].currentText()})
                self.clades_other_dict[row].update({"Facet2": self.pleth.loop_menu[self.loop_table][row]["Facet2"].currentText()})
                self.clades_other_dict[row].update({"Covariates": '@'.join(self.pleth.loop_menu[self.loop_table][row]["Covariates"].currentData())})
                self.clades_other_dict[row].update({"Inclusion": self.pleth.loop_menu[self.loop_table][row]["Inclusion"].currentText()})
                # if self.clades_other_dict[row]['Inclusion'] == 'Yes':
                #     self.clades_other_dict[row]['Inclusion'] = 1
                # else:
                #     self.clades_other_dict[row]['Inclusion'] = 0  
                self.clades_other_dict[row].update({"Y axis minimum": self.pleth.loop_menu[self.loop_table][row]["Y axis minimum"].text()})
                self.clades_other_dict[row].update({"Y axis maximum": self.pleth.loop_menu[self.loop_table][row]["Y axis maximum"].text()})
            print(f"other dict:{self.clades_other_dict}")
            print(len(self.clades_other_dict))
            self.show_loops(self.loop_table,len(self.clades_other_dict))
            for row_1 in range(len(self.clades_other_dict)):
                self.loop_table.cellWidget(row_1,0).setText(self.clades_other_dict[row_1]['Graph'])
                self.loop_table.cellWidget(row_1,7).setText(self.clades_other_dict[row_1]['Y axis minimum'])
                self.loop_table.cellWidget(row_1,8).setText(self.clades_other_dict[row_1]['Y axis maximum'])
                self.loop_table.cellWidget(row_1,1).setCurrentText(self.clades_other_dict[row_1]['Variable'])
                self.loop_table.cellWidget(row_1,2).setCurrentText(self.clades_other_dict[row_1]['Xvar'])
                self.loop_table.cellWidget(row_1,3).setCurrentText(self.clades_other_dict[row_1]['Pointdodge'])
                self.loop_table.cellWidget(row_1,4).setCurrentText(self.clades_other_dict[row_1]['Facet1'])
                self.loop_table.cellWidget(row_1,5).setCurrentText(self.clades_other_dict[row_1]['Facet2'])
                # if odf.at[row_1,'Inclusion'] == 1:
                #     self.loop_table.cellWidget(row_1,9).setCurrentText("Yes")
                # else:
                #     self.loop_table.cellWidget(row_1,9).setCurrentText("No")
                if self.clades_other_dict[row_1]['Covariates'] != "":
                    # if self.deps != []:
                    self.pleth.loop_menu[self.loop_table][row_1]['Covariates'].loadCustom([w for w in self.clades_other_dict[row_1]['Covariates'].split('@')])
                    self.pleth.loop_menu[self.loop_table][row_1]['Covariates'].updateText()
        
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
        print(f"after after: {self.deps}")

    def setup_transform_combo(self):
        spacerItem64 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_25.addItem(spacerItem64)
        self.transform_combo = CheckableComboBox()
        self.transform_combo.addItems(["raw","log10","ln","sqrt","Custom","None"])
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

        # gr = os.path.abspath('../GUI/graphic.png')
        
        # self.graphic.setStyleSheet("border-image:url(../GUI/graphic.png)")
        # os.path.join(Path(__file__).parent.parent.parent,"scripts/graphic.png")

        self.custom_dict = {}
        self.custom_port = {}
        self.clades_other_dict = {}
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
        # header = self.variable_table.horizontalHeader()
        # for header_col in range(0,6):
        #     header.setSectionResizeMode(header_col,QHeaderView.Stretch)

        # header_loop = self.loop_table.horizontalHeader()
        # for header_loop_col in range(0,6):
        #     header_loop.setSectionResizeMode(header_loop_col,QHeaderView.Stretch)

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
        for item_1 in self.pleth.breath_df:
            self.pleth.buttonDict_variable[item_1]["Independent"].toggled.connect(self.add_combos)
            self.pleth.buttonDict_variable[item_1]["Covariate"].toggled.connect(self.add_combos)
        # self.n = 0
        # self.variable_table.cellChanged.connect(self.no_duplicates)
        # self.variable_table.cellChanged.connect(self.update_loop)
        
        # self.variable_table.resizeColumnsToContents()
        # self.variable_table.resizeRowsToContents()
        # for item_1 in self.pleth.breath_df:
            # self.pleth.buttonDict_variable[item_1]["Alias"].textEdited.connect(self.no_duplicates)
            # self.buttonDict_variable[item]["Covariate"].toggled.connect(self.v.populate_combos(self.buttonDict_variable[item].))
        # Creating the dictionary that will store the cells' statuses based on user selection. The table's need separate dictionaries because they'll be yielding separate csvs:
        # self.loop_menu = {}

        # self.show_loops(self.loop_table,0)
    
    def show_loops(self,table,r):
        print("config.show_loops()")
        # self.loop_table.clear()
        self.pleth.loop_menu = {}
        for row in range(r):
            self.pleth.loop_menu.update({table:{row:{}}})
            # Creating the widgets within the above dictionary that will populate the cells of each row:
            self.pleth.loop_menu[table][row]["Graph"] = QLineEdit()
            self.pleth.loop_menu[table][row]["Y axis minimum"] = QLineEdit()
            self.pleth.loop_menu[table][row]["Y axis maximum"] = QLineEdit()
            for role in self.role_list[1:6]:
                self.pleth.loop_menu[table][row][role] = QComboBox()
                self.pleth.loop_menu[table][row][role].addItems([""])
                self.pleth.loop_menu[table][row][role].addItems([x for x in self.deps])
            
            # self.pleth.loop_menu[table][row]["Poincare"] = QComboBox()
            # self.pleth.loop_menu[table][row]["Poincare"].addItems(["Yes","No"])
            # self.pleth.loop_menu[table][row]["Y axis minimum"].addItems(["Automatic",""])
            # self.pleth.loop_menu[table][row]["Y axis maximum"].addItems(["Automatic",""])
            self.pleth.loop_menu[table][row]["Inclusion"] = QComboBox()
            self.pleth.loop_menu[table][row]["Inclusion"].addItems(["No","Yes"])
            self.pleth.loop_menu[table][row]["Covariates"] = CheckableComboBox()
            self.pleth.loop_menu[table][row]["Covariates"].addItems([b for b in self.deps])
            # Adding the contents based on the variable list of the drop down menus for the combo box widgets:
            # for role in self.v.role_list:
                # self.pleth.loop_menu[table][self.row_loop][role].addItems([""])
                # self.pleth.loop_menu[table][self.row_loop][role].addItems([x for x in self.breath_df])
        
            
            # Populating the table cells with their widget content stored in the dictionary:
            # for n in range(0,7):
            #     for role in role_list:
            #         table.setCellWidget(self.row_loop,n,self.pleth.loop_menu[table][self.row_loop][role])
            table.setCellWidget(row,0,self.pleth.loop_menu[table][row]["Graph"])
            table.setCellWidget(row,1,self.pleth.loop_menu[table][row]["Variable"])
            table.setCellWidget(row,2,self.pleth.loop_menu[table][row]["Xvar"])
            table.setCellWidget(row,3,self.pleth.loop_menu[table][row]["Pointdodge"])
            table.setCellWidget(row,4,self.pleth.loop_menu[table][row]["Facet1"])
            table.setCellWidget(row,5,self.pleth.loop_menu[table][row]["Facet2"])
            table.setCellWidget(row,6,self.pleth.loop_menu[table][row]["Covariates"])
            table.setCellWidget(row,7,self.pleth.loop_menu[table][row]["Y axis minimum"])
            table.setCellWidget(row,8,self.pleth.loop_menu[table][row]["Y axis maximum"])
            table.setCellWidget(row,9,self.pleth.loop_menu[table][row]["Inclusion"])
        
        # table.resizeColumnsToContents()
        table.resizeRowsToContents()

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
            d = [c for c in self.custom_dict]
            for c in d:
                if c not in self.deps:
                    self.custom_dict.pop(c,None)
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


    def add_xvar_combo(self):
        print("add_xvar_combo()")
        self.classy()
        self.Xvar_combo.clear()
        self.Xvar_combo.addItem("Select variable:")
        self.Xvar_combo.addItems([x for x in self.clades.loc[(self.clades["Independent"] == 1) | (self.clades['Covariate'] == 1)]['Alias']])
    
    def add_pointdodge_combo(self):
        print("add_pointdodge_combo()")
        self.classy()
        self.Pointdodge_combo.clear()
        self.Pointdodge_combo.addItem("Select variable:")
        self.Pointdodge_combo.addItems([x for x in self.clades.loc[(self.clades["Independent"] == 1) | (self.clades['Covariate'] == 1)]['Alias']])

    def add_facet1_combo(self):
        print("add_pointdodge_combo()")
        self.classy()
        self.Facet1_combo.clear()
        self.Facet1_combo.addItem("Select variable:")
        self.Facet1_combo.addItems([x for x in self.clades.loc[(self.clades["Independent"] == 1) | (self.clades['Covariate'] == 1)]['Alias']])
    
    def add_facet2_combo(self):
        print("add_pointdodge_combo()")
        self.classy()
        self.Facet2_combo.clear()
        self.Facet2_combo.addItem("Select variable:")
        self.Facet2_combo.addItems([x for x in self.clades.loc[(self.clades["Independent"] == 1) | (self.clades['Covariate'] == 1)]['Alias']])

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
        self.clades_other_dict = {}
        for row in range(self.loop_table.rowCount()):
            print(row)
            self.clades_other_dict.update({row:{}})
            self.clades_other_dict[row].update({"Graph": self.pleth.loop_menu[self.loop_table][row]["Graph"].text()})
            self.clades_other_dict[row].update({"Variable": self.pleth.loop_menu[self.loop_table][row]["Variable"].currentText()})
            self.clades_other_dict[row].update({"Xvar": self.pleth.loop_menu[self.loop_table][row]["Xvar"].currentText()})
            self.clades_other_dict[row].update({"Pointdodge": self.pleth.loop_menu[self.loop_table][row]["Pointdodge"].currentText()})
            self.clades_other_dict[row].update({"Facet1": self.pleth.loop_menu[self.loop_table][row]["Facet1"].currentText()})
            self.clades_other_dict[row].update({"Facet2": self.pleth.loop_menu[self.loop_table][row]["Facet2"].currentText()})
            self.clades_other_dict[row].update({"Covariates": '@'.join(self.pleth.loop_menu[self.loop_table][row]["Covariates"].currentData())})
            self.clades_other_dict[row].update({"Inclusion": self.pleth.loop_menu[self.loop_table][row]["Inclusion"].currentText()})
            if self.clades_other_dict[row]['Inclusion'] == 'Yes':
                self.clades_other_dict[row]['Inclusion'] = 1
            else:
                self.clades_other_dict[row]['Inclusion'] = 0  
            self.clades_other_dict[row].update({"Y axis minimum": self.pleth.loop_menu[self.loop_table][row]["Y axis minimum"].text()})
            self.clades_other_dict[row].update({"Y axis maximum": self.pleth.loop_menu[self.loop_table][row]["Y axis maximum"].text()})
            
        
        print(self.clades_other_dict)
        self.clades_other = pd.DataFrame.from_dict(self.clades_other_dict)
        print(self.clades_other)
        # self.clades_other.dropna
        self.clades_other = self.clades_other.transpose()
        print(self.clades_other)
        if self.feature_combo.currentText() != "None":
            if self.feature_combo.currentText() == "All":
                self.clades_other.at[self.loop_table.rowCount(),"Graph"] = "Apneas"
                self.clades_other.at[self.loop_table.rowCount()+1,"Graph"] = "Sighs"
            else:
                self.clades_other.at[self.loop_table.rowCount()-1,"Graph"] = self.feature_combo.currentText()
        self.clades_other.drop(self.clades_other.loc[(self.clades_other["Graph"]=="") & (self.clades_other["Variable"]=="")].index, inplace=True)
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
        print(f"custom port: {self.custom_port}")
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
            # self.show_custom()
            self.pleth.c.save_custom()
        # else:
            # Custom.save_custom(self)
        for cladcol in self.clades:
            for item in self.custom_port:
                for col in self.custom_port[item]:
                    # if col is "Irregularity":
                    #     if self.custom_port[item][col] == 1:
                    #         print("irregularity is 1")
                    #         # print(self.clades.loc[(self.clades["Alias"] == self.pleth.c.custom_port[item]["Alias"]),"Column"].values)
                    #         print(f'Irreg_Score_{self.clades.loc[(self.clades["Alias"] == self.custom_port[item]["Alias"]),"Column"].values[0]}')
                    #         irr = f'Irreg_Score_{self.clades.loc[(self.clades["Alias"] == self.custom_port[item]["Alias"]),"Column"].values[0]}'
                    #         print(irr)
                    #         if irr in self.clades["Column"]:
                    #             print("irreg found")
                    #             self.clades.loc[(self.clades["Column"] == f'Irreg_Score_{self.clades.loc[(self.clades["Alias"] == self.custom_port[item]["Alias"]),"Column"].values[0]}'),"Dependent"] == 1 
                    #         else:
                    #             print("no irreg")
                    try:
                        if self.custom_port[item][col] != None:
                            if col is "Transformation":
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
                    except Exception as e:
                        print(f'{type(e).__name__}: {e}')
                        print(traceback.format_exc())
        
        
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
        print(f"custom port: {self.custom_port}")
        
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
                    print(traceback.format_exc())
                    thumbholes.append(self.configs[key]["path"])
                    pass
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
                self.saveas_config()
            if Path(self.pleth.mothership).exists():
                try:
                    if Path(os.path.join(self.pleth.mothership,'STAGG_config')).exists():
                        self.configs[key]["df"].to_csv(os.path.join(self.pleth.mothership, f'STAGG_config/{key}.csv'),index=False)
                    else:
                        Path(os.path.join(self.pleth.mothership,'STAGG_config')).mkdir()
                        self.configs[key]["df"].to_csv(os.path.join(self.pleth.mothership, f'STAGG_config/{key}.csv'),index=False)
                except PermissionError as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
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
        print(self.pleth.output_dir_r)
    # If I load previously made things, I have paths but they haven't been assigned. I assign them above. They'll overwrite the files they're editing. 
    
    def saveas_config(self):
        print("config.saveas_config()")
        thumbholes = []
        self.classy_save()
        # self.pleth.dir_checker(self.pleth.output_dir_r,self.pleth.r_output_folder,"STAGG")
        # for p in [self.pleth.variable_config,self.pleth.graph_config,self.pleth.other_config]:
        #     for c in self.pleth.cons:
        #         if os.path.basename(self.pleth.cons[c]).startswith(str(p).split('.')[2]):
        #             p = self.pleth.cons[c]
            
        # if Path(os.path.join(self.pleth.mothership,'STAGG_config')).exists():
        #     auto_save_path = os.path.join(self.pleth.mothership,'STAGG_config')
        
        save_dir = QFileDialog.getExistingDirectory(self, 'Choose directory for STAGG configuration files', self.mothership)

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
                    print(traceback.format_exc())
                    thumbholes.append(self.configs[key]["path"])
                    pass
                if Path(self.pleth.mothership).exists():
                    try:
                        if Path(os.path.join(self.pleth.mothership,'STAGG_config')).exists():
                            self.configs[key]["df"].to_csv(os.path.join(self.pleth.mothership, f'STAGG_config/{key}.csv'),index=False)
                        else:
                            Path(os.path.join(self.pleth.mothership,'STAGG_config')).mkdir()
                            self.configs[key]["df"].to_csv(os.path.join(self.pleth.mothership, f'STAGG_config/{key}.csv'),index=False)
                    except PermissionError as e:
                        print(f'{type(e).__name__}: {e}')
                        print(traceback.format_exc())
                        thumbholes.append(self.configs[key]["path"])
                        pass
            self.pleth.output_dir_r = save_dir
            self.pleth.output_folder_r = os.path.dirname()
            if len(thumbholes)>0:
                self.thumb = Thumbass(self)
                self.thumb.show()
                self.thumb.message_received("File in use",f"One or more of the files selected is open in another program:\n{os.linesep.join([os.path.basename(thumb) for thumb in set(thumbholes)])}")
            
            # Clearing the config panel of the mainGUI and adding to it to reflect changes:
            for f in self.configs:
                for item in self.pleth.variable_list.findItems(f,Qt.MatchContains):
                    self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                self.pleth.variable_list.addItem(self.configs[f]['path'])

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
        self.loop_table.setCellWidget(loop_row,9,self.pleth.loop_menu[self.loop_table][loop_row]["Inclusion"])
        self.pleth.loop_menu[self.loop_table][loop_row].update({"Covariates": CheckableComboBox()})
        self.pleth.loop_menu[self.loop_table][loop_row]["Covariates"].addItems([b for b in self.pleth.breath_df])
        self.loop_table.setCellWidget(loop_row,6,self.pleth.loop_menu[self.loop_table][loop_row]["Covariates"])

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
            self.n = 0
            self.variable_table.cellChanged.connect(self.no_duplicates)
            self.variable_table.cellChanged.connect(self.update_loop)
            print(self.pleth.loop_menu)
            self.pleth.show_loops(self.loop_table,1)
            print(self.pleth.loop_menu)
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
            self.classy()
            self.deps = self.clades.loc[(self.clades["Dependent"] == 1)]["Alias"]
            # self.pleth.c.populate_table(self.deps,self.pleth.c.custom_table)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            print("Apparently reset_config only knows how to land by crashing into objects like my bird. I don't understand why this except makes things work, and that makes me uncomfortable.")

    def to_check_load_variable_config(self):
        self.check_load_variable_config("yes")

    def check_load_variable_config(self,open_file):
        paths = []
        print("self.check_load_variable_config has started")
        if open_file == "yes":
        # Groping around to find a convenient directory:
        
            # if Path(os.path.join(self.pleth.mothership,'STAGG_config')).exists():
            #     load_path = os.path.join(self.pleth.mothership,'STAGG_config')
            # elif Path(self.pleth.mothership).exists():
            #     load_path = self.pleth.mothership
            # else:
            #     load_path = str(os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/STAGG_config"))

            # Opens open file dialog
            file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/STAGG_config")))
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
                    for item in self.pleth.variable_list.findItems("variable_config",Qt.MatchContains):
                        self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                    self.pleth.variable_list.addItem(self.configs["variable_config"]['path'])
                except KeyError as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
                    self.goodies.remove("variable_config")
                    self.baddies.append("variable_config")
                    print(f'baddies got "variable_config" because of a key error')
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
            if "graph_config" in self.goodies:
                try:
                    self.load_graph_config()
                    for item in self.pleth.variable_list.findItems("graph_config",Qt.MatchContains):
                        self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                    self.pleth.variable_list.addItem(self.configs["graph_config"]['path'])
                except KeyError as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
                    self.goodies.remove("graph_config")
                    self.baddies.append("graph_config")
                    print(f'baddies got "graph_config" because of a key error')
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
            if "other_config" in self.goodies:
                try:
                    self.load_other_config()
                    for item in self.pleth.variable_list.findItems("other_config",Qt.MatchContains):
                        self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                    self.pleth.variable_list.addItem(self.configs["other_config"]['path'])
                except KeyError as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
                    self.goodies.remove("other_config")
                    self.baddies.append("other_config")
                    print(f'baddies got "other_config" because of a key error')
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
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
        self.n = 0
        self.variable_table.cellChanged.connect(self.no_duplicates)
        self.variable_table.cellChanged.connect(self.update_loop)
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
                # self.Poincare_combo.setCurrentText("Custom")
            if self.vdf[k]['Spectral'] == "1":
                self.custom_dict[k]['Spectral'].setChecked(True)
                # self.Spectral_combo.setCurrentText("Custom")
            for y in ['ymin','ymax']:
                if self.vdf[k][y] != "":
                    self.custom_dict[k][y].setText(self.vdf[k][y])
            if self.vdf[k]['Transformation'] != "":
                # if not self.transform_combo:
                #     print("no transform_combo")
                #     self.setup_transform_combo()
                # else:
                #     print(self.transform_combo)
                print("there is a transformation")
                transform = [s.replace("non","raw") and s.replace("log","ln") for s in self.vdf[k]['Transformation'].split('@')]
                transform = [z.replace("ln10","log10") for z in transform]
                print("transform")
                # print(','.join([t for t in transform]))
                self.custom_dict[k]['Transformation'].loadCustom(transform)
                self.custom_dict[k]['Transformation'].updateText()
        self.pleth.c.save_custom()
        # for key,value in {self.Poincare_combo:"Poincare",self.Spectral_combo:"Spectral"}.items():
        #     if all([self.custom_port[var][value] == 1 for var in self.custom_port]):
        #         key.setCurrentText("All")
        #     if any([self.custom_port[var][value] == 1 for var in self.custom_port]):
        #         key.setCurrentText("Custom")
        #     else:
        #         key.setCurrentText("None")
        # if any(th for th in [self.custom_port[t]["Transformation"] for t in self.custom_port])==True:
        #     print("hay transformation custom")
        #     self.transform_combo.setCurrentText("Custom")
        # else:
        #     print("no hay transformation apparently")
        #     self.transform_combo.setCurrentText("None") 
                
                # self.transform_combo.setCurrentText("custom")


        #         for th in self.config.custom_port:
        #     for thh in self.config.custom_port[th]["Transformation"]:
        #         print(thh)
        # print(any(th for th in [self.config.custom_port[t]["Transformation"] for t in self.config.custom_port]))
        # if any(th for th in [self.config.custom_port[t]["Transformation"] for t in self.config.custom_port])==True:
        #     print("hay transformation custom")
        #     self.config.transform_combo.setCurrentText("Custom")
        # else:
        #     print("no hay transformation apparently")
        #     self.config.transform_combo.setCurrentText("None")
        
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
                    print(traceback.format_exc())
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
                    print(traceback.format_exc())
                    print("program can't handle nan in gdf for some reason. so if there aren't four graph roles chosen, current text doesn't indicate selections. nvm i just fixed it. it needed a hallpass")
                    pass
            try:
                for c in self.settings_dict['role']:
               # print([x for x in gdf.loc[(gdf['Role'] == self.settings_dict['role'][c])]['Alias'] if pd.notna(x) == True][0])
                    c.setCurrentText([x for x in gdf.loc[(gdf['Role'] == self.settings_dict['role'][c])]['Alias'] if pd.notna(x) == True])
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
            

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
        print(f"odf before: {odf}")
        # odf = odf[odf["Graph"] != "Apneas" or odf["Graph"] != "Sighs"]
        odf.drop(odf.loc[(odf["Graph"]=="Apneas") | (odf["Graph"]=="Sighs")].index, inplace = True)
        print(f"odf after:{odf}")
        print(len(odf))
        self.show_loops(self.loop_table,len(odf))
        print(self.pleth.loop_menu)
        # self.clades_other_dict[row].update({"Facet2": self.pleth.loop_menu[self.loop_table][row]["Facet2"].currentText()})
        if len(odf)>0:
            print(len(odf))
            print(odf.at[0,'Graph'])
            try:
                print(odf.at[1,'Graph'])
            except:
                print("nope")
            # self.loop_table.setRowCount(len(odf))
            for row_1 in range(len(odf)):
                # self.pleth.loop_menu[self.loop_table][row_1]["Graph"].setText(str(odf.at[row_1,'Graph']))
                # self.loop_table.setCellWidget(row_1,0,self.pleth.loop_menu[self.loop_table][row_1]["Graph"])
                # self.pleth.loop_menu[self.loop_table][row_1]["Y axis minimum"].setText(str(odf.at[row_1,'Y axis minimum']))
                # self.loop_table.setCellWidget(row_1,7,self.pleth.loop_menu[self.loop_table][row_1]["Y axis minimum"])
                # self.pleth.loop_menu[self.loop_table][row_1]["Y axis maximum"].setText(str(odf.at[row_1,'Y axis maximum']))
                # self.loop_table.setCellWidget(row_1,8,self.pleth.loop_menu[self.loop_table][row_1]["Y axis maximum"])
                self.loop_table.cellWidget(row_1,0).setText(str(odf.at[row_1,'Graph']))
                self.loop_table.cellWidget(row_1,7).setText(str(odf.at[row_1,'Y axis minimum']))
                self.loop_table.cellWidget(row_1,8).setText(str(odf.at[row_1,'Y axis maximum']))
                self.loop_table.cellWidget(row_1,1).setCurrentText(str(odf.at[row_1,'Variable']))
                self.loop_table.cellWidget(row_1,2).setCurrentText(str(odf.at[row_1,'Xvar']))
                self.loop_table.cellWidget(row_1,3).setCurrentText(str(odf.at[row_1,'Pointdodge']))
                self.loop_table.cellWidget(row_1,4).setCurrentText(str(odf.at[row_1,'Facet1']))
                self.loop_table.cellWidget(row_1,5).setCurrentText(str(odf.at[row_1,'Facet2']))
                if odf.at[row_1,'Inclusion'] == 1:
                    self.loop_table.cellWidget(row_1,9).setCurrentText("Yes")
                else:
                    self.loop_table.cellWidget(row_1,9).setCurrentText("No")
                if odf.at[row_1, 'Covariates'] != "":
                    if self.deps != []:
                        self.pleth.loop_menu[self.loop_table][row_1]['Covariates'].loadCustom([w for w in odf.at[row_1, 'Covariates'].split('@')])
                        self.pleth.loop_menu[self.loop_table][row_1]['Covariates'].updateText()
                        
                if row_1 < (len(odf)-1):
                    try:
                        self.add_loop()
                    except Exception as e:
                        print("no added loop")
                        print(f'{type(e).__name__}: {e}')
                        print(traceback.format_exc())
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

        self.GUIpath=os.path.realpath(__file__)
        self.setupUi(self)

        self.q = queue.Queue()
        self.counter = 0
        self.finished_count = 0
        self.qthreadpool = QThreadPool()
        self.qthreadpool.setMaxThreadCount(1)
        self.threads = {}
        self.workers = {}

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
        # self.gui_config['Dictionaries']['Paths'].update({'rscript1':str(Path(f'{Path(__file__).parent.parent}/R-Portable-3-6-3/App/R-Portable/bin/Rscript.exe'))})
        # print(self.gui_config['Dictionaries']['Paths']['rscript'])
        

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
        self.metadata_pm_warnings = []
        self.missing_plyuids = []
        self.metadata_passlist = []
        self.tsbyfile = {}
        self.row_loop = ""
        self.image_format = ""
        self.buttonDict_variable = {}
        self.stagg_list = []
        self.rscript_des = ""
        self.pipeline_des = ""
        self.loop_menu = {}

        self.v = Config(self)
        self.s = Stagg(self)
        self.p = Auto(self)
        self.c = ""
        # self.v = Config(self)
        self.m = Manual(self)
        self.a = Auto(self)
        self.b = Basic(self)
        self.g = AnnotGUI.Annot(self)

        # os.path.abspath(os.path.join(Path(__file__).parent.parent.parent,'scripts/GUI/resources/graphic.png'))
        # gr = os.path.abspath("../GUI/resources/graphic.png")
        # self.v.graphic.setStyleSheet("border-image:url('../scripts/GUI/resources/graphic.png')")
        self.v.graphic.setStyleSheet("border-image:url(:resources/graphic.png)")

         # Populate GUI widgets with experimental condition choices: 
        # self.necessary_timestamp_box.addItems([need for need in self.stamp['Dictionaries']['Necessary_Timestamps']])
        self.necessary_timestamp_box.addItems([x for x in self.bc_config['Dictionaries']['Auto Settings']['default'].keys()])
        self.parallel_combo.addItems([str(num) for num in list(range(1,os.cpu_count()+1))])

        # Populate GUI widgets with experimental condition choices:
        self.m.preset_menu.addItems([x for x in self.bc_config['Dictionaries']['Manual Settings']['default'].keys()])
        self.a.auto_setting_combo.addItems([x for x in self.bc_config['Dictionaries']['Auto Settings']['default'].keys()])

        # for widget in [self.variable_list,self.signal_files_list,self.metadata_list,self.sections_list,self.breath_list]:
        #     self.keyPressEvent.connect(self.on_key(widget))
        
#endregion

#region Analysis parameters

        os.chdir(os.path.join(Path(__file__).parent.parent.parent))
        
        
    # method with slot decorator to receive signals from the worker running in
    # a seperate thread...B_run is triggered by the worker's 'progress' signal
    @pyqtSlot(int)
    def B_run(self,worker_id):
        if not self.q.empty():
            self.hangar.append(f'{worker_id} : {self.q.get_nowait()}')
            """
            note that if multiple workers are emitting their signals it is not
            clear which one will trigger the B_run method, though there should 
            be one trigger of the B_run method for each emission. It appears as
            though the emissions collect in a queue as well.
            If we care about matching the worker-id to the emission/queue 
            contents, I recommend loading the queue with tuples that include
            the worker id and the text contents
            """
            
    # method with slot decorator to receive signals from the worker running in
    # a seperate thread...B_Done is triggered by the worker's 'finished' signal
    @pyqtSlot(int)
    def B_Done(self,worker_id):
        self.hangar.append('Worker_{} finished'.format(worker_id))
        self.finished_count += 1   

#endregion

    def save_bug(self,error_name):
        print(error_name)
        # print(trace)
        print(f'save bug:{traceback.format_exc()}')
        bug_string = """
        
        """

#region Timestamper...

    def timestamp_dict(self):
        print("timestamp_dict()")
        tic=datetime.datetime.now()
        print(tic)
        print(self.stamp['Dictionaries']['Data'])
        self.stamp['Dictionaries']['Data'] = {}
        print(self.stamp['Dictionaries']['Data'])
        print(self.tsbyfile)
        combo_need = self.necessary_timestamp_box.currentText()
        # if self.input_dir_py == "":
        if self.signals == []:
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

            # self.need = self.stamp['Dictionaries']['Necessary_Timestamps'][combo_need]
            self.need = self.bc_config['Dictionaries']['Auto Settings']['default'][combo_need]
            print(self.need)

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
                tpath = os.path.join(Path(self.signals[0]).parent,f"timestamp_{os.path.basename(Path(self.signals[0]).parent)}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                with open(tpath,"w") as tspath:
                    tspath.write(json.dumps(self.stamp))
                    tspath.close()
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
                self.thumb = Thumbass(self)
                self.thumb.show()
                self.thumb.message_received(f"{type(e).__name__}: {e}",f"The timestamp file could not be written.")
            self.hangar.append("Timestamp output saved.")
            print(self.check)
            miss = []
            dup = []
            new = []
            # for m in self.check['files_missing_a_ts']:
                # for w in self.check['files_missing_a_ts'][m]:
                    # print(self.check['files_missing_a_ts'][m])
                # print(self.check['files_missing_a_ts'][m])
            # miss.append([[w for w in self.check['files_missing_a_ts'][m]] for m in self.check['files_missing_a_ts']])
            # for d in self.check['files_with_dup_ts']:
                # dup.append(self.check['files_with_dup_ts'][d])
            # for n in self.check['new_ts']:
                # print(self.check['new_ts'][n])
            # new.append([[z for z in self.check['new_ts'][n]] for n in self.check['new_ts']])
            self.hangar.append("---Timestamp Summary---")
            self.hangar.append(f"Files with missing timestamps: {', '.join(set([w for m in self.check['files_missing_a_ts'] for w in self.check['files_missing_a_ts'][m]]))}")
            self.hangar.append(f"Files with duplicate timestamps: {', '.join(set([y for d in self.check['files_with_dup_ts'] for y in self.check['files_with_dup_ts'][d]]))}")
            if len(set([z for n in self.check['new_ts'] for z in self.check['new_ts'][n]])) == len(self.signals):
                self.hangar.append(f"Files with novel timestamps: all signal files")
            else:
                self.hangar.append(f"Files with novel timestamps: {', '.join(set([z for n in self.check['new_ts'] for z in self.check['new_ts'][n]]))}")
            try:
                self.hangar.append(f"Full review of timestamps: {Path(tpath)}")
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
            # for m in self.check['files_missing_a_ts']:
            #     for y in self.check['files_missing_a_ts'][m]:
            #         print(y)
            # self.hangar.append(f"Files with missing timestamps: {miss}\nFiles with duplicate timestamps: {dup}\nFiles with novel timestamps: {[z for z in new]}")
            # \nFiles with duplicate timestamps: {[[', '.join(z) for z in self.check['files_with_dup_ts'][d]] for d in self.check['files_with_dup_ts']]}\nFiles with novel timestamps: {[[', '.join(w) for w in self.check['new_ts'][n]] for n in self.check['new_ts']]}")
            # for e in epoch:
            #     for c in condition:
            #         for d in self.stamp['Dictionaries']['Data'][e][c]:
            #             if d is not 'tsbyfile':
            #                 for x in self.stamp['Dictionaries']['Data'][e][c][d]:
            #                     if self.stamp['Dictionaries']['Data'][e][c][d][x] != {} or self.stamp['Dictionaries']['Data'][e][c][d][x] != [] or self.stamp['Dictionaries']['Data'][e][c][d][x] != 'all signal files':
            #                         if d == 'files_missing_a_ts':
            #                             self.hangar.append(f"Files with missing timestamps | {', '.join(file for file in self.stamp['Dictionaries']['Data'][e][c]['files_missing_a_ts'][x])}")
            #                         elif d == 'files_with_dup_ts':
            #                             self.hangar.append(f"Files with duplicate timestamps | {', '.join(file for file in self.stamp['Dictionaries']['Data'][e][c]['files_with_dup_ts'][x])}")
            #                         elif d == 'new_ts':
            #                             self.hangar.append(f"Files with novel timestamps | {', '.join(file for file in self.stamp['Dictionaries']['Data'][e][c]['new_ts'][x])}")
        
                            # self.hangar.append(f"Files with new timestamps: \n{[d+' | '+','.join(file) for file in self.stamp['Dictionaries']['Data'][e][c]['new_ts'][d] for d in self.stamp['Dictionaries']['Data'][e][c]['new_ts'] for c in self.stamp['Dictionaries']['Data'][e] for e in self.stamp['Dictionaries']['Data']]}")
                            # self.hangar.append(f"Files with missing timestamps | {','.join(file for file in self.stamp['Dictionaries']['Data'][e][c]['files_missing_a_ts'][x])}\nFiles with duplicate timestamps | {','.join(file for file in self.stamp['Dictionaries']['Data'][e][c]['files_with_dup_ts'][x])}\nFiles with novel timestamps | {','.join(file for file in self.stamp['Dictionaries']['Data'][e][c]['new_ts'][x])}")
            
            # self.hangar.append(f"TIMESTAMP OUTPUT\nFiles with missing timestamps: \n{os.linesep.join([d for d in self.stamp['Dictionaries']['Data'][e][c]['files_missing_a_ts']])}\n{self.stamp['Dictionaries']['Data']}")
            # shutil.copy(tspath, os.path.join(os.path.join(Path(self.signals[0]).parent.parent), f"timestamp_{os.path.basename(Path(self.signals[0]).parent.parent)}"))

            toc=datetime.datetime.now()
            print(self.stamp['Dictionaries']['Data'])
            print(self.tsbyfile)
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
        self.tsbyfile = {}
        
        for CurFile in self.signals:
            self.tsbyfile[CurFile]=[]
            print(CurFile)
            # try:
            with open(CurFile,'r') as opfi:
                i=0
                # l=0
                for line in opfi:
                    if '#' in line:
                        # self.hangar.append('{} TS AT LINE: {} - {}'.format(os.path.basename(CurFile),i,line.split('#')[1][2:]))
                        print('{} TS AT LINE: {} - {}'.format(os.path.basename(CurFile),i,line.split('#')[1][2:]))
                        timestamps.append(line.split('#')[1][2:])
                        # self.tsbyfile[CurFile].append(line.split('#* ')[1].split(' \n')[0])
                        c = line.split('#')[1][2:].split(' \n')[0]
                        self.tsbyfile[CurFile].append(f"{c}")
                        # l+=1
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
        for n in filesextrats:
            if len(filesextrats[n]) == len(self.signals):
                filesextrats[n] = ["all signal files"]
        for p in new_ts:
            if len(new_ts[p]) == len(self.signals):
                new_ts[p] = ["all signal files"]
        self.check = {'good_files':goodfiles,'files_missing_a_ts':filesmissingts,
            'files_with_dup_ts':filesextrats,'new_ts':new_ts}
        print(f"miss:{filesmissingts}")
        print(f"extra:{filesextrats}")
        print(f"new:{new_ts}")
        

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
    def x_button(self):
        reply = QMessageBox.information(self, 'Bye!', 'Are you sure you would like to quit?\nAny unsaved changes will be lost.', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            sys.exit(0)

#region Variable configuration
    def check_metadata_file(self,direction):
        baddies = []
        if self.metadata.endswith(".csv"):
            meta = pd.read_csv(self.metadata)
        elif self.metadata.endswith(".xlsx"):
            meta = pd.read_excel(self.metadata)
        for s in self.signals:
            name = os.path.basename(s).split('.')[0]
            if '_' in name:
                if len(meta.loc[(meta['MUID'] == name.split('_')[0])])==0:
                    baddies.append(s)
                elif len(meta.loc[(meta['PlyUID'] == name.split('_')[1])])==0:
                    baddies.append(s)
            elif len(meta.loc[(meta['MUID'] == name)])==0:
                baddies.append(s)
        if len(baddies)>0:
            self.thumb = Thumbass(self)
            self.thumb.show()
            self.thumb.message_received("Metadata and signal files mismatch",f"The following signals files were not found in the selected metadata file:\n\n{os.linesep.join([os.path.basename(thumb) for thumb in baddies])}\n\n")


    def get_bp_reqs(self):
        if self.metadata == "":
            reply = QMessageBox.information(self, 'Missing metadata', 'Please select a metadata file.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.get_metadata()
            if self.autosections == "" and self.mansections == "":
                reply = QMessageBox.information(self, 'Missing BASSPRO automated/manual settings', 'Please select BASSPRO automated or manual settings files.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    self.get_autosections()
                if self.basicap == "":
                    reply = QMessageBox.information(self, 'Missing BASSPRO basic settings', 'Please select BASSPRO basic settings files.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                    if reply == QMessageBox.Ok:
                        self.get_autosections()
        elif self.autosections == "" and self.mansections == "":
            reply = QMessageBox.information(self, 'Missing BASSPRO automated/manual settings', 'Please select BASSPRO automated or manual settings files.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.get_autosections()
                if self.basicap == "":
                    reply = QMessageBox.information(self, 'Missing BASSPRO basic settings', 'Please select BASSPRO basic settings files.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                    if reply == QMessageBox.Ok:
                        self.get_autosections()
        elif self.basicap == "":
            reply = QMessageBox.information(self, 'Missing BASSPRO basic settings', 'Please select BASSPRO basic settings files.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.get_autosections()

    def new_variable_config(self):
        self.get_bp_reqs()
        self.test_configuration()
        try:
            self.variable_configuration()
            self.n = 0
            self.v.variable_table.cellChanged.connect(self.v.no_duplicates)
            self.v.variable_table.cellChanged.connect(self.v.update_loop)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
        try:
            self.v.show()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
        
        
    def show_variable_config(self):
        # print("show configuration")
        if self.buttonDict_variable == {}:
            print("self.buttonDict_variable is apparently empty")
            if self.v.configs["variable_config"]["path"] != "":
                self.v.check_load_variable_config("no")
                self.v.show()
            elif self.stagg_list != [] and os.path.isdir(self.stagg_list[0])==True:
                if self.metadata != "" and (self.autosections != "" or self.mansections != ""):
                    self.thinb = Thinbass(self)
                    self.thinb.show()
                else:
                    self.test_configuration()
                    try:
                        self.variable_configuration()
                        self.n = 0
                        self.v.variable_table.cellChanged.connect(self.v.no_duplicates)
                        self.v.variable_table.cellChanged.connect(self.v.update_loop)
                        self.v.show()
                    except Exception as e:
                        print(f'{type(e).__name__}: {e}')
                        print(traceback.format_exc())
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
                    self.n = 0
                    self.v.variable_table.cellChanged.connect(self.v.no_duplicates)
                    self.v.variable_table.cellChanged.connect(self.v.update_loop)
                    self.v.show()
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
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
            
    def update_breath_df(self,updated_file):
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
            print(traceback.format_exc())
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
                reply = QMessageBox.question(self, f'New {updated_file} selected', 'Would you like to update the variable list in STAGG configuration settings?\n\nUnsaved changes may be lost.\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
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
                    try:
                        for a in self.v.vdf:
                            self.buttonDict_variable[a]['Alias'].setText(self.v.vdf[a]['Alias'])
                            for k in ["Independent","Dependent","Covariate"]:
                                if self.v.vdf[a][k] == '1':
                                    try:
                                        self.buttonDict_variable[a][k].setChecked(True)
                                    except:
                                        print("not checkable match")
                                        pass
                        self.n = 0
                        self.variable_table.cellChanged.connect(self.no_duplicates)
                        self.variable_table.cellChanged.connect(self.update_loop)
                        self.v.load_custom_config()
                        self.v.load_graph_config()
                    except Exception as e:
                        print(f'{type(e).__name__}: {e}')
                        print(traceback.format_exc())
                        pass
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
            print(traceback.format_exc())
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
            print(traceback.format_exc())
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
        # header = self.v.variable_table.horizontalHeader()
        # for header_col in range(0,6):
        #     header.setSectionResizeMode(header_col,QHeaderView.Stretch)

        # header_loop = self.v.loop_table.horizontalHeader()
        # for header_loop_col in range(0,6):
        #     header_loop.setSectionResizeMode(header_loop_col,QHeaderView.Stretch)

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
            # self.buttonDict_variable[item]["Alias"] = QLineEdit(item)

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
            
        # for item_1 in self.breath_df:
        #     self.buttonDict_variable[item_1]["Alias"].textEdited(self.v.no_duplicates)
            # self.v.variable_table.itemChanged.connect(self.v.update_alias)
            # self.buttonDict_variable[item]["Covariate"].toggled.connect(self.v.populate_combos(self.buttonDict_variable[item].))
        # self.v.variable_table.cellChanged.connect(self.v.add_combos)
        # Creating the dictionary that will store the cells' statuses based on user selection. The table's need separate dictionaries because they'll be yielding separate csvs:
        self.v.n = 0
        for item_1 in self.breath_df:
            self.buttonDict_variable[item_1]["Independent"].toggled.connect(self.v.add_combos)
            self.buttonDict_variable[item_1]["Covariate"].toggled.connect(self.v.add_combos)
        # self.v.variable_table.cellChanged.connect(self.v.no_duplicates)
        # self.v.variable_table.cellChanged.connect(self.v.update_loop)
        self.v.variable_table.resizeColumnsToContents()
        self.v.variable_table.resizeRowsToContents()
        self.loop_menu = {}
        # self.v.transform_combo = CheckableComboBox()
        # self.v.transform_combo.addItems(["raw","log10","ln","sqrt"])
        # self.v.verticalLayout_25.addWidget(self.v.transform_combo)
        self.show_loops(self.v.loop_table,1)
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

    def show_loops(self,table,r):
        print("pleth.show_loops()")
        for row in range(r):
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
            self.loop_menu[table][row]["Covariates"] = CheckableComboBox()
            self.loop_menu[table][row]["Covariates"].addItems([b for b in self.breath_df])
                
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
            table.setCellWidget(row,6,self.loop_menu[table][row]["Covariates"])
            table.setCellWidget(row,7,self.loop_menu[table][row]["Y axis minimum"])
            table.setCellWidget(row,8,self.loop_menu[table][row]["Y axis maximum"])
            table.setCellWidget(row,9,self.loop_menu[table][row]["Inclusion"])

        table.resizeColumnsToContents()
        table.resizeRowsToContents()


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
            print("bob")
            print(self.breath_df)
          # self.breathcaller_path_list.clear()
        # self.py_output_dir_list.clear()
            # self.signal_files_list.clear()
            # self.metadata_list.clear()
            # self.sections_list.clear()
        # self.py_go.setDisabled(False)
            if self.breath_df != [] or self.metadata != "" or self.autosections != "" or self.basicap != "" or self.mansections != "":
                reply = QMessageBox.question(self, f'Input detected', 'The selected directory has recognizable input.\n\nWould you like to overwrite your current input selection?\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.auto_get_output_dir_py()
                    self.auto_get_autosections()
                    self.auto_get_mansections()
                    self.auto_get_metadata()
                    # self.auto_get_breath_files()
                    self.auto_get_output_dir_r()
                    # self.auto_get_signal_files()
                    # self.auto_get_variable()
                    self.auto_get_basic()
                    print(self.basicap)
                    print(self.autosections)
                    print(self.metadata)
                    print(self.mansections)
                    print(self.output_dir_py)
                    print(self.output_dir_r)
                    
            else:
                self.auto_get_output_dir_py()
                self.auto_get_autosections()
                self.auto_get_mansections()
                self.auto_get_metadata()
                # self.auto_get_breath_files()
                self.auto_get_output_dir_r()
                # self.auto_get_signal_files()
                # self.auto_get_variable()
                self.auto_get_basic()
                if len(self.breath_df)>0:
                    self.update_breath_df("settings")
        
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
            print(self.signals)
                # reply = QMessageBox.information(self, 'Incorrect file format', 'One or more of the selected signal files are not text formatted: .\nWould you like to select a different signal file directory?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
        else:
            if self.signals == []:
                self.signal_files_list.clear()
                # self.signal_files_list.addItem("Signal files directory not detected.")
     
    def auto_get_metadata(self):
        print("auto_get_metadata()")
        print(id(self.metadata))
        print(os.path.basename(self.metadata))
        metadata_path=os.path.join(self.mothership, 'metadata.csv')
        if Path(metadata_path).exists():
            # We assign the path detected via mothership to the Plethysmography class attribute that will be an argument for the breathcaller command line.
            for item in self.metadata_list.findItems("metadata",Qt.MatchContains):
            # and we remove them from the widget.
                self.metadata_list.takeItem(self.metadata_list.row(item))
            if self.metadata == "":
                self.metadata=metadata_path
                self.metadata_list.addItem(self.metadata)
            else:
                self.metadata=metadata_path
                self.metadata_list.addItem(self.metadata)
                # if self.breath_df != []:
                #     self.update_breath_df("metadata")
        else:
            # self.metadata_list.clear()
            # self.metadata_list.addItem("No metadata file selected.")
            print("No metadata file selected.")
        # print(id(self.metadata))
        if self.signals != []:
            self.check_metadata_file("metadata")

    def auto_get_basic(self):
        print("auto_get_basic()")
        basic_path=os.path.join(self.mothership, 'basics.csv')
        if Path(basic_path).exists():
            for item in self.sections_list.findItems("basic",Qt.MatchContains):
            # and we remove them from the widget.
                self.sections_list.takeItem(self.sections_list.row(item))
            if self.basicap == "":
                self.basicap=basic_path
                self.sections_list.addItem(self.basicap)
            else:
                self.basicap=basic_path
                self.sections_list.addItem(self.basicap)
                # if self.breath_df != []:
                #     self.update_breath_df("basic settings")
        else:
            # self.sections_list.addItem("Basic parameters settings file not detected.")
            print("Basic parameters settings file not detected.")

    def auto_get_autosections(self):
        print("auto_get_autosections()")
        autosections_path=os.path.join(self.mothership, 'auto_sections.csv')
        if Path(autosections_path).exists():
            for item in self.sections_list.findItems("auto",Qt.MatchContains):
            # and we remove them from the widget.
                self.sections_list.takeItem(self.sections_list.row(item))
            if self.autosections == "":
            # We assign the path detected via mothership to the Plethysmography class attribute that will be an argument for the breathcaller command line.
                self.autosections=autosections_path
                self.sections_list.addItem(self.autosections)
            else:
                self.autosections=autosections_path
                self.sections_list.addItem(self.autosections)
                # if self.breath_df != []:
                #     self.update_breath_df("automated settings")
        else:
            # self.sections_list.addItem("Autosection parameters file not detected.")
            print("Autosection parameters file not detected.")

    def auto_get_mansections(self):
        print("auto_get_mansections()")
        mansections_path=os.path.join(self.mothership, 'manual_sections.csv')
        if Path(mansections_path).exists():
            for item in self.sections_list.findItems("man",Qt.MatchContains):
                # and we remove them from the widget.
                self.sections_list.takeItem(self.sections_list.row(item))
            if self.mansections == "":
            # We assign the path detected via mothership to the Plethysmography class attribute that will be an argument for the breathcaller command line.
                self.mansections=mansections_path
                self.sections_list.addItem(self.mansections)
            else:
                self.mansections=mansections_path
                self.sections_list.addItem(self.mansections)
                # if self.breath_df != []:
                #     self.update_breath_df("manual settings")
        else:
            # self.sections_list.addItem("Manual sections parameters file not detected.")
            print("Manual sections parameters file not detected.")

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
        for f in self.v.configs:
            for item in self.variable_list.findItems(f,Qt.MatchContains):
                self.variable_list.takeItem(self.variable_list.row(item))
            self.variable_list.addItem(self.v.configs[f]['path'])
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
        # if self.output_dir_py == "":
        #     if self.stagg_list == []:
        #         self.breath_list.addItem("Breathcaller output directory not detected.")
        # else:
        if self.stagg_list != []:
            reply = QMessageBox.information(self, 'Clear STAGG input list?', 'Would you like to keep the previously selected STAGG input files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                self.breath_list.clear()
                self.stagg_list = []
            # self.breath_list.addItem(self.output_dir_py)
            # self.input_dir_r = self.output_dir_py
        self.stagg_list = [os.path.join(self.output_dir_py,file) for file in os.listdir(self.output_dir_py) if file.endswith(".json")==True]
        for x in self.stagg_list:
            self.breath_list.addItem(x)
        print(self.stagg_list)
            # self.signal_files_list.clear()
           
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
            print(traceback.format_exc())
            pass

    # def open_dir(self,item):
    #     if 

    def get_signal_files(self):
        print("get_signal_files()")
        # if not self.input_dir_py:
        #     if not self.mothership:
        #         try:
        #             file_name = QFileDialog.getOpenFileNames(self, 'Select signal files')
        #         except Exception as e:
        #             print(f'{type(e).__name__}: {e}')
        #             print(traceback.format_exc())
        #     else:
        #         file_name = QFileDialog.getOpenFileNames(self, 'Select signal files')
        # else:
        file_name = QFileDialog.getOpenFileNames(self, 'Select signal files')
        if not file_name[0]:
            if self.signals == []:
                self.signal_files_list.clear()
                # self.signal_files_list.addItem("No signal files selected.")
        else:
            if self.signals != []:
                reply = QMessageBox.information(self, 'Clear signal files list?', 'Would you like to keep the previously selected signal files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    self.signal_files_list.clear()
                    self.signals = []
            # self.signal_files_list.clear()
            bad_signals = []
            # for item in self.sections_list.findItems("signal files selected",Qt.MatchContains):
            #     self.sections_list.takeItem(self.sections_list.row(item))
            self.hangar.append("Signal files selected.")
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
            # self.input_dir_py = os.path.dirname(self.signals[0])
            print(self.signals)
        if self.metadata != "":
            if os.path.exists(self.metadata):
                self.check_metadata_file("signal")

    def get_metadata(self):
        print("get_metadata()")
        if self.mothership != "":
            print("exists")
            file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(self.mothership))
        else:
            print("not exist")
            # self.pleth.mothership = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output")
            file_name = QFileDialog.getOpenFileNames(self, 'Select metadata file')
        if not file_name[0]:
            if self.metadata == "":
                self.metadata_list.clear()
                # self.metadata_list.addItem("No metadata file selected.")
        else:
            self.metadata_list.clear()
            for x in range(len(file_name[0])):
                self.metadata_list.addItem(file_name[0][x])
            self.metadata = file_name[0][0]
            
            if len(self.breath_df)>0:
                self.update_breath_df("metadata")
            # self.pleth.hangar.append("Metadata file saved.")
        if self.signals != []:
            self.check_metadata_file("metadata")
    
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
                print(traceback.format_exc())
                self.mp_parserrors.append(file)

    def connect_database(self):
        print("connect_database()")
        if self.signals == []:
            reply = QMessageBox.information(self, 'Unable to connect to database', 'No signal files selected.\nWould you like to select a signal file directory?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.get_signal_files()
        else:
            self.metadata_warnings={}
            self.metadata_pm_warnings=[]
            self.missing_plyuids=[]
            self.metadata_list.addItem("Gauging Filemaker connection...")
            try:
                dsn = 'DRIVER={FileMaker ODBC};Server=128.249.80.130;Port=2399;Database=MICE;UID=Python;PWD='
                self.mousedb = pyodbc.connect(dsn)
                self.mousedb.timeout=1
                self.mp_parser()
                self.get_study()
                self.dir_checker(self.output_dir_py,self.py_output_folder,"BASSPRO")
                self.metadata_list.clear()
                if os.path.exists(self.mothership):
                    self.save_filemaker()
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
                # self.metadata_list.addItem("Unable to connect to Filemaker.")
                # if self.metadata == "":
                reply = QMessageBox.information(self, 'Unable to connect to database', 'You were unable to connect to the database.\nWould you like to select another metadata file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
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
            print(self.m_mouse_dict)
            print(self.p_mouse_dict)
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
                self.hangar.append(f"{w}: {', '.join(x for x in plys[w])}")
            for u in set(self.metadata_pm_warnings):
                self.hangar.append(u)
            # if len(self.missing_plyuids)>0:
            #     if len(set(self.missing_plyuids)) == len(self.signals):
            #         sub = "all signal files"
            #     else:
            #         sub = ', '.join(m for m in set(self.missing_plyuids))
            #     self.hangar.append(f"The following signals files {', '.join(m for m in set(self.missing_plyuids))}.")
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
            print(traceback.format_exc())
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
                    self.metadata_pm_warnings.append(f"Neither Ply{p} nor M{m} were found in metadata.")
                # If the PlyUID isn't in the metadata, but its associated MUID is:
                else:
                    if p != "":
                        self.metadata_pm_warnings.append(f"Ply{p} of M{m} not found in metadata.")
                    else:
                        self.missing_plyuids.append(f"M{m}")
                    mice = [self.p_mouse_dict[d]['MUID'] for d in self.p_mouse_dict]
                    for c in mice:
                        if mice.count(c)>1:
                            self.metadata_pm_warnings.append(f"More than one PlyUID was found for the following metadata: {', '.join(c for c in set(mice) if mice.count(c)>1)}")
                            

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
                                self.metadata_warnings[f"Ply{p}"].append(f"Missing metadata for {fm}")
                            else:
                                self.metadata_warnings[f"Ply{p}"] = [f"Missing metadata for {fm}"]
                        elif self.m_mouse_dict[f"M{m}"][fm] == None:
                            if f"Ply{p}" in self.metadata_warnings.keys():
                                self.metadata_warnings[f"Ply{p}"].append(f"Empty metadata for {fm}")
                            else:
                                self.metadata_warnings[f"Ply{p}"] = [f"Empty metadata for {fm}"]
                    for fp in self.essential_fields["pleth"]:
                        if fp not in self.p_mouse_dict[f"Ply{p}"].keys():
                            if f"Ply{p}" in self.metadata_warnings.keys():
                                self.metadata_warnings[f"Ply{p}"].append(f"Missing metadata for {fp}")
                            else:
                                self.metadata_warnings[f"Ply{p}"] = [f"Missing metadata for {fp}"]
                        elif self.p_mouse_dict[f"Ply{p}"][fp] == None:
                            if f"Ply{p}" in self.metadata_warnings.keys():
                                self.metadata_warnings[f"Ply{p}"].append(f"Empty metadata for {fp}")
                            else:
                                self.metadata_warnings[f"Ply{p}"] = [f"Empty metadata for {fp}"]
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
            print(traceback.format_exc())
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
                    # self.sections_list.addItem("No BASSPRO settings files selected.")
                    print("No BASSPRO settings files selected.")
            else:
                # self.sections_list.clear()
                print("files chosen")
                n = 0
                for x in range(len(file_name[0])):
                    if file_name[0][x].endswith('.csv'):
                        # print(file_name[0][x])
                        if os.path.basename(file_name[0][x]).startswith("auto_sections") | os.path.basename(file_name[0][x]).startswith("autosections"):
                            print(file_name[0][x])
                            self.autosections = file_name[0][x]
                            n += 1
                            print(self.autosections)
                            for item in self.sections_list.findItems("auto_sections",Qt.MatchContains):
                                self.sections_list.takeItem(self.sections_list.row(item))
                            self.sections_list.addItem(self.autosections)
                        elif os.path.basename(file_name[0][x]).startswith("manual_sections"):
                            print(file_name[0][x])
                            self.mansections = file_name[0][x]
                            n += 1
                            for item in self.sections_list.findItems("manual_sections",Qt.MatchContains):
                                self.sections_list.takeItem(self.sections_list.row(item))
                            self.sections_list.addItem(self.mansections)
                        elif os.path.basename(file_name[0][x]).startswith("basics"):
                            print(file_name[0][x])
                            self.basicap = file_name[0][x]
                            n += 1
                            for item in self.sections_list.findItems("basics",Qt.MatchContains):
                                self.sections_list.takeItem(self.sections_list.row(item))
                            self.sections_list.addItem(self.basicap)
                        if n>0:
                            if len(self.breath_df)>0:
                                self.update_breath_df("settings")
                    else:
                        self.thumb = Thumbass(self)
                        self.thumb.show()
                        self.thumb.message_received("Incorrect file format","The settings files for BASSPRO must be in csv format. \nPlease convert your settings files or choose another file.")
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
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
        # folder = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/BASSPRO_output")
        input_dir_r = QFileDialog.getOpenFileNames(self, 'Choose STAGG input files from BASSPRO output', self.mothership)
        # if not input_dir_r:
        #     if self.input_dir_r == "":
        #         self.breath_list.clear()
                # self.breath_list.addItem("No folder selected.")
        # else:
        print(input_dir_r)
        if all(file.endswith(".json") or file.endswith(".RData") for file in input_dir_r[0]):
            if self.stagg_list != []:
                reply = QMessageBox.information(self, 'Clear STAGG input list?', 'Would you like to keep the previously selected STAGG input files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    self.breath_list.clear()
                    self.stagg_list = []
            # self.breath_list.addItem(self.output_dir_py)
            # self.input_dir_r = self.output_dir_py
            self.stagg_list = [file for file in input_dir_r[0] if file.endswith(".json")==True or file.endswith(".RData")==True]
            for x in self.stagg_list:
                self.breath_list.addItem(x)
            print(self.stagg_list)
        elif any(file_1.endswith(".json") or file_1.endswith(".RData") for file_1 in input_dir_r[0]):
            baddies = []
            for file_2 in input_dir_r[0]:
                if file_2.endswith(".json") == True or file_2.endswith(".RData") == True:
                    self.stagg_list.append(file_2)
                else:
                    baddies.append(file_2)
            for x in self.stagg_list:
                self.breath_list.addItem(x)
            if len(baddies)>0:
                self.thumb = Thumbass(self)
                self.thumb.show()
                self.thumb.message_received("Incorrect file format",f"One or more of the files selected are neither JSON nor RData files:\n\n{os.linesep.join([os.path.basename(thumb) for thumb in baddies])}\n\nThey will not be included.")        
        else:
            reply = QMessageBox.information(self, 'Incorrect file format', 'The selected file(s) are not formatted correctly.\nWould you like to select different files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.input_directory_r()
        
        # if os.path.exists(input_dir_r):
        #     self.st
        #     self.input_dir_r = input_dir_r
        #     self.breath_list.clear()
        #     self.breath_list.addItem(self.input_dir_r)
    
    def input_directory_r_env(self):
        print("input_directory_r_env()")
        # folder = os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/STAGG_output")
        input_dir_r = QFileDialog.getOpenFileName(self, 'Select R environment', "./STAGG_output")
        print(input_dir_r)
        if all(file.endswith(".RData") for file in input_dir_r[0]):
            if self.stagg_list != []:
                reply = QMessageBox.information(self, 'Clear STAGG input list?', 'Would you like to keep the previously selected STAGG input files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    self.breath_list.clear()
                    self.stagg_list = []
            # self.breath_list.addItem(self.output_dir_py)
            # self.input_dir_r = self.output_dir_py
            self.stagg_list = [file for file in input_dir_r[0] if file.endswith(".RData")==True]
            print(self.stagg_list)
            for x in self.stagg_list:
                self.breath_list.addItem(x)
        # elif any(file_1.endswith(".RData") for file_1 in input_dir_r[0]):
        #     baddies = []
        #     for file_2 in input_dir_r[0]:
        #         if file_2.endswith(".RData") == True:
        #             self.stagg_list.append(file_2)
        #         else:
        #             baddies.append[file_2]
        #     if len(baddies)>0:
        #         self.thumb = Thumbass(self)
        #         self.thumb.show()
        #         self.thumb.message_received("Incorrect file format",f"One or more of the files selected are not .RData files:\n\n{os.linesep.join([os.path.basename(thumb) for thumb in baddies])}\n\nThey will not be included.")        
        else:
            reply = QMessageBox.information(self, 'Incorrect file format', 'The selected file(s) are not .RData files.\nWould you like to select different files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.input_directory_r()
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
            rscript = self.rscript_des,
            pipeline = self.pipeline_des,
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
        for d in self.signal_dict:
            # log=os.path.join(self.output_dir_py,'log_"{bob}"'.format(bob=os.path.basename(os.path.normpath(self.output_dir_py))))
            breathcaller_cmd = 'python -u "{module}" -i "{id}" {filelist} -o "{output}" -a "{metadata}" -m "{manual}" -c "{auto}" -p "{basic}"'.format(
                module = self.breathcaller_path,
                id = d,
                output = self.output_dir_py,
                # signal = os.path.basename(file_py),
                filelist= '-f "'+'" -f "'.join([os.path.basename(i) for i in self.signal_dict[d]])+'"',
                metadata = self.metadata,
                manual = self.mansections,
                # manual = "", 
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

    # def update_Stampprogress(self):
    #     print("stamp go")
    #     print("Stamp progress process id",os.getpid())


    def update_Pyprogress(self):
        print("pre go")
        print('Pyprogress thread id',threading.get_ident())
        print("Pyprogress process id",os.getpid())
        signal_dir = []
        self.signal_dict = {}
        for s in self.signals:
            signal_dir.append(os.path.dirname(s))
        # if len(set(signal_dir))>1:
        for d in set(signal_dir):
            self.signal_dict.update({d:[]})
            for l in self.signals:
                if os.path.dirname(l) == d:
                    self.signal_dict[d].append(l)
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
        try:
            self.dir_checker(self.output_dir_py,self.py_output_folder,"BASSPRO")
            self.get_bp_reqs()
            if self.parallel_box.isChecked() == True:
                self.pything_to_do()
            else:
                self.pything_to_do_single()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
        try:
            self.auto_get_breath_files()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
        try:
            self.output_check()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())

    def r_message(self):
        print("r_message()")
        print(f'configs: {self.v.configs}')
        print(f'v:{self.variable_config}')
        print(f'g:{self.graph_config}')
        print(f'o:{self.other_config}')
        self.variable_config = self.v.configs["variable_config"]["path"]
        self.graph_config = self.v.configs["graph_config"]["path"]
        self.other_config = self.v.configs["other_config"]["path"]
        # if self.variable_config == "" or self.graph_config == "" or self.other_config == "":
        if any([self.v.configs[key]['path'] == "" for key in self.v.configs]):
            if self.stagg_list == []:
                print("no stagg for you")
            else:
                QMessageBox.question(self, 'Missing STAGG settings', f"One or more STAGG settings files are missing.", QMessageBox.OK, QMessageBox.OK)
                # \n\n{key.split(' ')[0]}_{key.split(' ')[1]}.csv
                
            # if reply == QMessageBox.Yes:
            #     for key in self.v.configs:
            #         if self.v.configs[key]["path"] == "":
            #             print("r_config path is empty")
            #             self.v.configs[key]["path"] == "None"
            #             print(self.v.configs[key]["path"])
            #     # self.variable_config = "None"
            #     # self.graph_config = "None"
            #     # self.other_config = "None"
            #     self.rthing_to_do()
            # else:
            #     self.thumb = Thumbass(self)
            #     self.thumb.show()
            #     self.thumb.message_received("Missing STAGG settings","One or more STAGG settings files are missing.")
        else:
            self.rthing_to_do()

    def dir_checker(self,output_folder,output_folder_parent,text):
        print("dir_checker()")
        self.output_folder = ""
        self.output_folder_parent = ""
        if self.mothership == "":
            print("mothership is empty so choose a new one")
            try:
                self.mothership = QFileDialog.getExistingDirectory(self, f'Choose directory for {text} output', str(self.mothership))
                # output_folder_parent = os.path.dirname(output_folder)
                # self.output_folder_parent = output_folder_parent
                # self.mothership_dir()
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
        if not os.path.exists(self.mothership):
            print("mothership is empty and doesn't exist")
            try:
                self.mothership = QFileDialog.getExistingDirectory(self, f'Previously chosen directory does not exist. Choose a different directory for {text} output', str(self.mothership))
            # output_folder_parent = os.path.dirname(output_folder)
            # self.output_folder_parent = output_folder_parent
                # self.mothership_dir()
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
                print("Plug your hard drive back in.")
        if output_folder_parent == "":
            output_folder_parent = os.path.join(self.mothership,f"{text}_output")
            try:
                print(f'making {text} output folder parent based on mothership')
                os.makedirs(output_folder_parent)
                self.output_folder_parent = output_folder_parent
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
                print("apparently os.path.exists says no but os.makedirs says yes it exists")
        else:
            self.output_folder_parent = output_folder_parent
            if not os.path.exists(self.output_folder_parent):
                print("trying to make output folder parent cause it doesn't exist")
                try:
                    os.makedirs(self.output_folder_parent)
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
                    print('apparently os.path.exists says no but os.makedirs says yes exists')
        if output_folder == "":
            output_folder = os.path.join(self.output_folder_parent, f'{text}_output_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
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
                    print(traceback.format_exc())
                    print('apparently os.path.exists says no but os.makedirs says yes exists')
        else:
            self.output_folder = output_folder
            if not os.path.exists(self.output_folder):
                print("trying to make output folder cause it doesn't exist")
                try:
                    os.makedirs(self.output_folder)
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
                    print('apparently os.path.exists says no but os.makedirs says yes exists')
        print(self.mothership)
        print(self.output_folder_parent)
        print(self.output_folder)
        if any(Path(self.output_folder).iterdir()) == True:
            if all("config" in file for file in os.listdir(self.output_folder)):
                print("just configs")
            else:
                reply = QMessageBox.question(self, f'Confirm {text} output directory', 'The current output directory has files in it that may be overwritten.\n\nWould you like to create a new output folder?\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    output_folder_parent = os.path.dirname(output_folder)
                    self.output_folder = os.path.join(output_folder_parent, f'{text}_output_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
                    print(output_folder_parent)
                    print(os.path.join(output_folder_parent, f'{text}_output_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')))
                    print(self.output_folder)
                    os.makedirs(self.output_folder)
                elif reply == QMessageBox.No:
                    print(f"kept old output folder: {output_folder}")
    
    def pything_to_do(self):
        print("pything_to_do()")
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
                shutil.copyfile(self.autosections, os.path.join(self.output_dir_py, f"auto_sections_{os.path.basename(self.output_dir_py).lstrip('BASSPRO_output')}.csv"))
            # if self.m.manual_df != "":
            #     self.m.manual_df.to_csv(self.mansections,index=False)
            if self.mansections != "":
                shutil.copyfile(self.mansections, os.path.join(self.output_dir_py, f"manual_sections_{os.path.basename(self.output_dir_py).lstrip('BASSPRO_output')}.csv"))
            # A copy of the basic parameters is not included because that's found in the breathcaller_config file. But so are all the other settings...
            if self.basicap != "":
                shutil.copyfile(self.basicap, os.path.join(self.output_dir_py, f"basics_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv"))
            with open(f'{Path(__file__).parent}/gui_config.json','w') as gconfig_file:
                json.dump(self.gui_config,gconfig_file)
            shutil.copyfile(f'{Path(__file__).parent}/gui_config.json', os.path.join(self.output_dir_py, f"gui_config_{os.path.basename(self.output_dir_py).lstrip('BASSPRO_output')}.txt"))
            print('pything_to_do thread id',threading.get_ident())
            print("pything_to_do process id",os.getpid())
            # self.thready(self.update_Pyprogress)
            self.launch_worker("py")
            try:
                self.output_check()
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
    
    def launch_worker(self,branch):
        print("worker started?")
        print('launch_worker thread id',threading.get_ident())
        print("launch_worker process id",os.getpid())
        if branch == "py":
            for job in MainGUIworker_thready.get_jobs_py(self):
                # create a Worker
                self.workers[self.counter] = MainGUIworker_thready.Worker(
                    job,
                    self.counter,
                    self.q,
                    self
                    )
                self.workers[self.counter].progress.connect(self.B_run)
                self.workers[self.counter].finished.connect(self.B_Done)
                # adjust thread limit for the qthreadpool
                self.qthreadpool.setMaxThreadCount(int(self.parallel_combo.currentText()))
                # Add the 'QRunnable' worker to the threadpool which will manage how
                # many are started at a time
                self.qthreadpool.start(self.workers[self.counter])
                # advance the counter - used to test launching multiple threads
                self.counter+=1
        elif branch == "r":
            for job in MainGUIworker_thready.get_jobs_r(self):
                # create a Worker
                self.workers[self.counter] = MainGUIworker_thready.Worker(
                    job,
                    self.counter,
                    self.q,
                    self
                    )
                self.workers[self.counter].progress.connect(self.B_run)
                self.workers[self.counter].finished.connect(self.B_Done)
                # adjust thread limit for the qthreadpool
                self.qthreadpool.setMaxThreadCount(1)
                # Add the 'QRunnable' worker to the threadpool which will manage how
                # many are started at a time
                self.qthreadpool.start(self.workers[self.counter])
                # advance the counter - used to test launching multiple threads
                self.counter+=1
        elif branch == "stamp":
            print("stamp")
            for job in MainGUIworker_thready.get_jobs_stamp(self):
                # create a Worker
                self.workers[self.counter] = MainGUIworker_thready.Worker(
                    job,
                    self.counter,
                    self.q,
                    self
                    )
                self.workers[self.counter].progress.connect(self.B_run)
                self.workers[self.counter].finished.connect(self.B_Done)
                # adjust thread limit for the qthreadpool
                self.qthreadpool.setMaxThreadCount(int(self.parallel_combo.currentText()))
                # Add the 'QRunnable' worker to the threadpool which will manage how
                # many are started at a time
                self.qthreadpool.start(self.workers[self.counter])
                # advance the counter - used to test launching multiple threads
                self.counter+=1
        
    def launch_r_worker(self):
        print("worker started?")
        print('launch_worker thread id',threading.get_ident())
        print("launch_worker process id",os.getpid())
        for job in MainGUIworker_thready.get_jobs_r(self):
            # create a Worker
            self.workers[self.counter] = MainGUIworker_thready.Worker(
                job,
                self.counter,
                self.q,
                self
                )
            self.workers[self.counter].progress.connect(self.B_run)
            self.workers[self.counter].finished.connect(self.B_Done)
            # adjust thread limit for the qthreadpool
            self.qthreadpool.setMaxThreadCount(1)
            # Add the 'QRunnable' worker to the threadpool which will manage how
            # many are started at a time
            self.qthreadpool.start(self.workers[self.counter])
            # advance the counter - used to test launching multiple threads
            self.counter+=1

    def output_check(self):
        if len(self.stagg_list) != len(self.signals):
            goodies = []
            baddies = []
            # for g in self.stagg_list:
            #     stagg.append(os.path.basename(g).split('_')[0])
            for s in self.signals:
                name = os.path.basename(s).split('.')[0]
                for g in self.stagg_list:
                    if '_' in name:
                        if os.path.basename(g).split('.')[0] == name:
                            goodies.append(name)
                    else:
                        if os.path.basename(g).split('_')[0] == name:
                            goodies.append(name)
                if name not in goodies:
                    baddies.append(name)
        if len(baddies)>0:
            # self.thumb = Thumbass(self)
            # self.thumb.show()
            # self.thumb.message_received("Missing output",f"The following signals files did not pass BASSPRO:\n\n{os.linesep.join([os.path.basename(thumb) for thumb in baddies])}\n\n")
            self.hangar.append(f"\nThe following signals files did not pass BASSPRO:\n\n{', '.join([os.path.basename(thumb) for thumb in baddies])}\n")

    
            # self.hangar.append(f"The following signal files did not yield output: {', '.join(x for x in diff)} \nConsider checking the original LabChart file or the metadata for anomalies.") 

    def rthing_to_do(self):
        print("rthing_to_do()")
        self.dir_checker(self.output_dir_r,self.r_output_folder,"STAGG")
        if self.output_folder != "":
            self.output_dir_r = self.output_folder
            print(f'after:{self.output_dir_r}')
            if self.svg_radioButton.isChecked() == True:
                self.image_format = ".svg"
            elif self.jpeg_radioButton.isChecked() == True:
                self.image_format = ".jpeg"
            # if os.path.isdir(os.path.join(self.output_dir_r,"StatResults")):
            #     print("no stat results folder")
            #     os.makedirs(os.path.join(self.output_dir_r,"StatResults"))
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
                print(traceback.format_exc())
                print("No variable or graph configuration files copied to STAGG output folder.")
            if any(os.path.basename(b).endswith("RData") for b in self.stagg_list):
                self.pipeline_des = os.path.join(self.papr_dir, "Pipeline_env_multi.R")
            else:
                self.pipeline_des = os.path.join(self.papr_dir, "Pipeline.R")
            if len(self.stagg_list)>200:
                print("there are more than 100 files in stagg_list")
                if len(set([os.path.dirname(y) for y in self.stagg_list]))>1:
                    print("hay more than one directory in stagg_list")
                    reply = QMessageBox.information(self, "That's a lot of JSON", 'The STAGG input provided consists of more than 200 files from multiple directories.\nPlease condense the files into one directory for STAGG to analyze.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                    if reply == QMessageBox.Ok:
                        print("more than 200 files from multiple directories warning")
                    # for p in set([os.path.dirname(y) for y in self.stagg_list]):
                    #     self.input_dir_r = p
                    #     print('rthing_to_do thread id',threading.get_ident())
                    #     print("rthing_to_do process id",os.getpid())
                    #     self.worker = threading.Thread(target = MainGUIworker.futurama_r(self))
                    #     self.worker.daemon = True
                    #     self.worker.start()
                else:
                    print("there is only one directory in stagg_list")
                    self.input_dir_r = os.path.dirname(self.stagg_list[0])
                    self.rthing_to_do_cntd()
            else:
                print("there are fewer than 100 files in stagg_list")
                self.input_dir_r = ','.join(item for item in self.stagg_list)
                self.rthing_to_do_cntd()
    
    def rthing_to_do_cntd(self):
        if Path(self.pipeline_des).is_file():
            print("pipeline des is a real boy")
            if os.path.basename(self.gui_config['Dictionaries']['Paths']['rscript']) == "Rscript.exe":
                if os.path.exists(self.gui_config['Dictionaries']['Paths']['rscript']):
                    self.rscript_des = self.gui_config['Dictionaries']['Paths']['rscript']
                else:
                    reply = QMessageBox.information(self, 'Rscript not found', 'Rscript.exe path not defined. Would you like to select the R executable?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                    if reply == QMessageBox.Ok:
                        pre_des = QFileDialog.getOpenFileName(self, 'Find Rscript.exe', str(self.mothership))
                        if os.path.basename(pre_des[0]) == "Rscript.exe":
                            self.rscript_des = pre_des[0]
                            self.gui_config['Dictionaries']['Paths']['rscript'] = pre_des[0]
                            with open(f'{Path(__file__).parent}/gui_config.json','w') as gconfig_file:
                                json.dump(self.gui_config,gconfig_file)
            else:
                reply = QMessageBox.information(self, 'Rscript not found', 'Rscript.exe path not defined. Would you like to select the R executable?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                if reply == QMessageBox.Ok:
                    pre_des = QFileDialog.getOpenFileName(self, 'Find Rscript.exe', str(self.mothership))
                    if os.path.basename(pre_des[0]) == "Rscript.exe":
                        self.rscript_des = pre_des[0]
                        self.gui_config['Dictionaries']['Paths']['rscript'] = pre_des[0]
                        with open(f'{Path(__file__).parent}/gui_config.json','w') as gconfig_file:
                            json.dump(self.gui_config,gconfig_file)
            try:
                print('rthing_to_do thread id',threading.get_ident())
                print("rthing_to_do process id",os.getpid())
                self.launch_worker("r")
                print("worker started?")
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
        else:
            reply = QMessageBox.information(self, 'STAGG scripts not found', 'BASSPRO-STAGG cannot find the scripts for STAGG. Check the BASSPRO-STAGG folder for missing files or directories.', QMessageBox.Ok, QMessageBox.Ok)
        # print('rthing_to_do thread id',threading.get_ident())
        # print("rthing_to_do process id",os.getpid())
        # self.worker = threading.Thread(target = MainGUIworker.futurama_r(self))
        # self.worker.daemon = True
        # self.worker.start()
        # # shutil.copyfile(os.path.join(self.mothership,"Summary.html"),os.path.join(self.output_dir_r, f"Summary_{os.path.basename(self.output_dir_r).lstrip('r_output')}.html"))
        # print("worker started?")
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
        try:
            print("rthing_to_do is happening")
            print('rthing_single thread id',threading.get_ident())
            print("rthing_single process id",os.getpid())
            self.dir_checker(self.output_dir_r,self.r_output_folder,"STAGG")
            if self.output_folder != "":
                self.output_dir_r = self.output_folder
                self.thready(self.update_Rprogress)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
    
    def pything_to_do_single(self):
        print("pything_single thread id", threading.get_ident())
        print("pything_single process id", os.getpid())
        self.dir_checker(self.output_dir_py,self.py_output_folder,"BASSPRO")
        if self.output_folder != "":
            self.output_dir_py = self.output_folder
        # This conditional essentially checks whether or not a copy of the metadata already exists because if the metadat was pulled directly from Filemaker, then that function automatically makes the output py directory and places the pulled metadata in there before the launch button. I should change this and isolate the creation and copying to just the launch.
        # if self.metadata_path == "":
            try:
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
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
            # self.thready(self.update_Pyprogress)
            try:
                self.update_Pyprogress()
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())

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

# %%
