#%%
#region Libraries

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5 import uic
from form import Ui_Plethysmography
from config_form import Ui_Config
import csv
from pathlib import Path, PurePath
import subprocess
from subprocess import PIPE, Popen
import datetime
import time
import os
import json
import pyodbc
import tkinter
import tkinter.filedialog
import tkinter as tk 
from tkinter import ttk
import shutil
import pandas as pd
import threading
import re
# import asyncio
import multiprocessing
import MainGUIworker
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

#region class Variable
class Config(QWidget, Ui_Config):
    def __init__(self,Plethysmography):
        super(Config, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("PAPR Variable Configuration")
        self.Plethysmography = Plethysmography
        # self.isActiveWindow()
        self.isMaximized()
        self.role = []
        self.static = {"Start Body Temp": [], "Mid Body Temp": [], "End Body Temp": [], "Post Body Temp": [], "Body Weight": []}
        self.settings_dict = {"role": {"xvar":1,"pointdodge":2,"facet1":3,"facet2":4,"":""}}

    def classy(self):
        self.role = []
        self.static = {"Start Body Temp": [], "Mid Body Temp": [], "End Body Temp": [], "Post Body Temp": [], "Body Weight": []}
        self.settings_dict = {"role": {"xvar":1,"pointdodge":2,"facet1":3,"facet2":4,"":""}}
        file = QFileDialog.getSaveFileName(self, 'Save File', '', ".csv(*.csv))")
        self.clades = pd.DataFrame(columns= ["Column","Alias","Independent","Dependent","Covariate","Ignore",])
        self.clades_role = pd.DataFrame(columns = ["Alias","Role"])
        # self.mega = self.signals[0].removesuffix(".txt")
        # the above function only works in 3.9 which I have but it throws tantrums so for the sake of having a functioning subwindow:
        origin = []
        alias = []
        independent = []
        dependent = []
        covariate = []
        ignore = []

        for item in self.Plethysmography.buttonDict_variable:
            origin.append(item)
            alias.append(self.Plethysmography.buttonDict_variable[item]["alias"].text())
            independent.append(self.Plethysmography.buttonDict_variable[item]["ind"].isChecked())
            dependent.append(self.Plethysmography.buttonDict_variable[item]["dep"].isChecked())
            covariate.append(self.Plethysmography.buttonDict_variable[item]["cov"].isChecked())
            ignore.append(self.Plethysmography.buttonDict_variable[item]["ign"].isChecked())
            # if self.Plethysmography.buttonDict_variable[item]["dynamic"].currentText() != "":
            self.role.append(self.Plethysmography.buttonDict_variable[item]["role"].currentText())
            # self.static.append(self.Plethysmography.buttonDict_variable[item]["self.static"].currentText())

            if self.Plethysmography.buttonDict_variable[item]["self.static"].currentText() == "Start Body Temp":
                self.static["Start Body Temp"].append(int(1))
            else:
                self.static["Start Body Temp"].append(int(0))

            if self.Plethysmography.buttonDict_variable[item]["self.static"].currentText() == "Mid Body Temp":
                self.static["Mid Body Temp"].append(int(1))
            else:
                self.static["Mid Body Temp"].append(int(0))

            if self.Plethysmography.buttonDict_variable[item]["self.static"].currentText() == "End Body Temp":
                self.static["End Body Temp"].append(int(1))
            else:
                self.static["End Body Temp"].append(int(0))

            if self.Plethysmography.buttonDict_variable[item]["self.static"].currentText() == "Post Body Temp":
                self.static["Post Body Temp"].append(int(1))
            else:
                self.static["Post Body Temp"].append(int(0))

            if self.Plethysmography.buttonDict_variable[item]["self.static"].currentText() == "Body Weight":
                self.static["Body Weight"].append(int(1))
            else:
                self.static["Body Weight"].append(int(0))

        self.clades["Column"] = origin
        self.clades["Alias"] = alias
        self.clades["Independent"] = independent
        self.clades["Dependent"] = dependent
        self.clades["Covariate"] = covariate
        self.clades["Ignore"] = ignore
        self.clades["Start Body Temp"] = self.static["Start Body Temp"]
        self.clades["Mid Body Temp"] = self.static["Mid Body Temp"]
        self.clades["End Body Temp"] = self.static["End Body Temp"]
        self.clades["Post Body Temp"] = self.static["Post Body Temp"]
        self.clades["Body Weight"] = self.static["Body Weight"]
       
        self.clades[["Independent","Dependent","Covariate","Ignore"]] = self.clades[["Independent","Dependent","Covariate","Ignore"]].astype(int)

        self.clades_role["Alias"] = alias
        self.clades_role["Role"] = [self.settings_dict["role"][item] for item in self.role]
        self.clades_role = self.clades_role[self.clades_role["Role"]!=""]
        for num in range(1,5):
            if num not in list(self.clades_role["Role"]):
                self.clades_role.loc[num] = ["",num]

        
        self.Plethysmography.graph_config_path = os.path.join(self.Plethysmography.mothership, "R_config\graph_config.csv")
        self.clades_role.to_csv(self.Plethysmography.graph_config_path, index=False)
        # having columns named true or false will fuck up our code

        self.clades.to_csv(file[0],index=False)
        self.clades.to_csv()
        self.Plethysmography.variable_config = file[0]
        
        for item in self.Plethysmography.variable_list.findItems("variable_configuration.csv",Qt.MatchEndsWith):
            self.Plethysmography.variable_list.takeItem(self.Plethysmography.variable_list.row(item))
        for item in self.Plethysmography.variable_list.findItems("Variable configuration file not detected.",Qt.MatchExactly):
            self.Plethysmography.variable_list.takeItem(self.Plethysmography.variable_list.row(item))
        self.Plethysmography.variable_list.addItem(file[0])
    
    def load_variable_config(self):
        # Groping around to find a convenient directory:
        if Path(self.Plethysmography.py_output_folder).exists():
            load_path = self.Plethysmography.py_output_folder
        elif Path(self.Plethysmography.mothership).exists():
            load_path = self.Plethysmography.mothership
        else:
            load_path = str(Path.home())

        # Opens open file dialog
        file = QFileDialog.getOpenFileNames(self, 'Select files', load_path)

        # If you the file you chose sucks, the GUI won't crap out.
        if not file[0]:
            print("nope")
        else:
            self.Plethysmography.variable_configuration()
            tic=datetime.datetime.now()
            # Creating a dataframe of the variable configuration settings:
            vdf = pd.read_csv(file[0][0], index_col=False)
            # We iterate over the rows of the table widget in the variable configuration subGUI to put the correct values in the correct cells:
            for row in range(self.variable_table.rowCount()):
                # We iterate over the rows of the graph configuration settings to retrieve the data:
                with open(os.path.join(self.Plethysmography.mothership, "R_config\graph_config.csv")) as graph_path:
                    next(csv.reader(graph_path))
                    for row_1 in csv.reader(graph_path):
                        # We iterate over the rows of the variable configuration dataframe because we need to match the alias given in the graph settings file to its respective original variable name, which is available
                        # in the variable configuration file:
                        for row_2 in range(len(vdf.index)):
                            # If the variable name shown in the first column of our current row (row_2) doesn't match the alias shown in the second column of our current row of the variable configuration dataframe:
                            if vdf.iloc[row_2][0] != vdf.iloc[row_2][1]:
                                # If the variable name shown in first column of a row (row) of the table widget matches the variable name shown in the first column of our current row (row_2) of the variable configuration dataframe:
                                if self.variable_table.item(row,0).text() == vdf.iloc[row_2][0]:
                                    # In summary, if any of the aliases were different from the variable names, we took that alias from the variable configuration dataframe, matched it with its variable name in the table widget,
                                    # and changed the table widget's alias to the one provided.
                                    self.variable_table.item(row,1).setText(vdf.iloc[row_2][1])
                            # We iterate over the keys in the "role" dictionary (the same dictionary that populates the combo boxes in the penultimate column of the subGUI):
                            for key in self.settings_dict["role"]:
                                # If the value of the second column of our current row (row_1) in the graph settings file is equal to a value in the "dynamic" dictionary:
                                if self.settings_dict["role"][key] == int(row_1[1]):
                                    # If the alias shown in the first column of our current row (row_1) in the graph settings file is equal to the alias shown in the second column of a row (row_2) in the variable configuration dataframe:
                                    if row_1[0] == vdf.iloc[row_2][1]:
                                        # If the variable name shown in the first column of a row (row_2) in the variable configuration dataframe is equal to the variable name shown in the first column of a row (row) in the table widget:
                                        if vdf.iloc[row_2][0] == self.variable_table.item(row,0).text():
                                        # [key for key in self.settings_dict["dynamic"] if self.settings_dict["dynamic"][key] == row_1[1]]):
                                # what row in the widget matches the value of row10
                                # upon knowing that row, we need to have the pulldown value match the word version of the number
                                        # print("key")
                                            # In summary, we took the values in the second column of the graph settings file, and matched them to their respective keys in the "role" dictionary to get (key). To ensure that the
                                            #combobox value of the correct row in the table widget is changed to this key, we match the alias given in graph settings to its variable name in the variable configuration settings,
                                            # and then match that variable name to its equivalent in the table widget. 
                                            self.variable_table.cellWidget(row,6).setCurrentText(key)
                                            # The code below may be helpful if I end up needing to proactively enforce alias exclusivity:
                                            # if self.variable_table.item(row,1).text() == row_1[0]:
                                                # print("bob")
                                                # self.variable_table.item(row,1).setText("bob")
                                                # self.variable_table.item(row,1).setText(f"{self.variable_table.item(row,1).text()}_x")

                            # You should have something where if you've loaded variable list from the normal metadata, sections, etc. compilation but your loaded specs don't match, then failsafes.
                            # We iterate over the columns that designate variable role (ind,dep,cov,ign):
                            for col in range(2,6):
                                # If the value shown in the current column (col) of our current row (row_2) in the variable configuration dataframe is equal to 1:
                                if vdf.iloc[row_2][col] == 1:
                                    # If the variable name shown in the first column of a row (row) in the table widget is equal to the variable name shown in the first column of our current row (row_2) in the variable configuration dataframe:
                                    if self.variable_table.item(row,0).text() == vdf.iloc[row_2][0]:
                                        # In summary, for every variable designation column, we iterate over the rows and if any cells have 1 in them, then the corresponding cell in the table widget should have their radio checked.
                                        self.variable_table.cellWidget(row,col).setChecked(True)
                            # We iterate over the keys in the "static" dictionary (the same dictionary that populates the combo boxes in the ultimate column of the subGUI):
                            for entry in self.static:
                                # If the value shown in the column with the same name as the key (entry) of our current row (row_2) is equal to 1:
                                if vdf[entry].iloc[row_2] == 1:
                                    # If the variable name shown in the first column of a row (row) in the table widget is equal to the variable name shown in the first column of our current row (row_2) in the variable configuration daataframe:
                                    if self.variable_table.item(row,0).text() == vdf.iloc[row_2][0]:
                                        # In summary, for any cell in the variable configuration dataframe in a column with the same name as entry that equals 1, we match that cell with the corresponding cell in the table widget and check its radio button.
                                        self.variable_table.cellWidget(row,7).setCurrentText(entry)
            # Iterating over everything and their grandmother takes forever. I should look into a more efficient way of populating the table from loaded specs.
            toc=datetime.datetime.now()
            print(toc-tic)

    def replace(self):
        current_combo = self.variable_table.cellWidget(self.variable_table.currentRow(), self.variable_table.currentColumn())
        if current_combo.currentText() in self.Plethysmography.stack:
            for item in self.Plethysmography.buttonDict_variable:
                if self.Plethysmography.buttonDict_variable[item]["role"] != current_combo:
                    if self.Plethysmography.buttonDict_variable[item]["role"].currentText() == current_combo.currentText():
                        self.Plethysmography.buttonDict_variable[item]["role"].setCurrentText("") 
                if self.Plethysmography.buttonDict_variable[item]["self.static"] != current_combo:
                    if self.Plethysmography.buttonDict_variable[item]["self.static"].currentText() == current_combo.currentText():
                        self.Plethysmography.buttonDict_variable[item]["self.static"].setCurrentText("")
        #     stack.append(self.Plethysmography.buttonDict_variable)[item]["dynamic"].currentText())
        #     dynamic.append(self.Plethysmography.buttonDict_variable[item]["dynamic"].currentText())
            # self.static.append(self.Plethysmography.buttonDict_variable[item]["self.static"].currentText())
        else:
            self.Plethysmography.stack.append(current_combo.currentText())
        # 


#endregion

#region checkable functions
# ideally these functions would be one function that would just find the relevant column with the same text as the header instead of explicitly coding the same function for each checkbox.
# but for the sake of getting things done, I'm going to take the stairs instead of spending ten minutes finding the elevator
# I'll make this an elevator later
    def checkable_ind(self,state):
        try:
            print("true")
            for selected_rows in self.variable_table.selectedRanges():
                for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
                    self.variable_table.cellWidget(row,2).setChecked(True)
                    # that took me an hour to figure out WOOOOO 
        except:
            print("nope")
        # else:
        #     try:
        #         print("flase")
        #         for selected_rows in self.variable_table.selectedRanges():
        #             for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
        #                 self.variable_table.cellWidget(row,5).setChecked(True)
        #     except:
        #         print("nope2")

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

    def checkable_emp(self):
        try:
            for selected_rows in self.variable_table.selectedRanges():
                for col in range(selected_rows.leftColumn(),selected_rows.rightColumn()+1):
                    # for col in range(6,11):
                    self.variable_table.cellWidget(0,col).setChecked(True)
        except:
            print("nope")

#endregion

class Plethysmography(QMainWindow, Ui_Plethysmography):
    def __init__(self):
        super(Plethysmography, self).__init__()

#region class methods
        self.v = Config(self)
        self.GUIpath=os.path.realpath(__file__)
        self.setupUi(self)
        self.threadpool = []

        self.setWindowTitle("Plethysmography Analysis Pipeline")
        self.isActiveWindow()
        self.showMaximized()

        self.breath_df = []

        self.variable_config = ""

        # with open(f'{Path(__file__).parent.parent.parent}/config.json') as config_file:
        #     self.config = json.load(config_file)
        # print(f'{Path(__file__).parent.parent.parent}/config.json')
        # self.config['Dictionaries']['Paths'].update({'breathcaller':str(Path(f'{Path(__file__).parent.parent.parent.parent}/python_module.py'))})
        # print(self.config['Dictionaries']['Paths']['breathcaller'])
        # self.config['Dictionaries']['Paths'].update({'papr':str(Path(f'{Path(__file__).parent.parent.parent.parent}/papr'))})
        # print(self.config['Dictionaries']['Paths']['papr'])
        
        with open(f'{Path(__file__).parent}/config.json') as config_file:
            self.config = json.load(config_file)
        print(f'{Path(__file__).parent}/config.json')
        self.config['Dictionaries']['Paths'].update({'breathcaller':str(Path(f'{Path(__file__).parent.parent}/python_module.py'))})
        print(self.config['Dictionaries']['Paths']['breathcaller'])
        self.config['Dictionaries']['Paths'].update({'papr':str(Path(f'{Path(__file__).parent.parent}/papr'))})
        print(self.config['Dictionaries']['Paths']['papr'])

        with open(f'{Path(__file__).parent}/timestamps.json') as stamp_file:
            self.stamp = json.load(stamp_file)
        self.necessary_timestamp_box.addItems([need for need in self.stamp['Dictionaries']['Necessary_Timestamps']])
        # self.necessary_timestamp_box.activated.connect(self.replace)
        
        # self.output_dir_py="C:/Users/atwit/Desktop/Mothership/"
        # self.signals = ["M17023.txt", "M17025.txt", "M17026.txt", "M17028.txt", "M17030.txt",
                        # "M17256.txt", "M17718.txt", "M17722.txt", "M17723.txt", "M17725.txt"]

#endregion

#region class attributes
    # def create_attributes(self):
    #     # self.ETTC=""
        self.mothership=""
        self.breathcaller_path=""
        self.output_dir_py=""
        self.input_dir_py=""
        self.input_dir_r=""
        self.output_dir_r=""
        self.autosections=""
        self.mansections=""
        self.metadata=""
        self.graph_toggle="None"
        # self.signals=["M17023.txt", "M17025.txt", "M17026.txt"]
        self.papr_dir=""
        self.py_output_folder=""
        self.variable_config=""
        self.graph_config_path=""
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

    def current(self):
        print("bob")
        
        # self.AnalysisParameters = self.config['Dictionaries']['AP']['current']

    def reset_parameter(self):
        self.AnalysisParameters = self.config['Dictionaries']['AP']['default']
        lineEdits = {self.lineEdit_minTI: "minTI", 
                    self.lineEdit_minPIF: "minPIF",
                    self.lineEdit_minPEF: "minPEF", 
                    self.lineEdit_TTwin: "TTwin", 
                    self.lineEdit_per500win: "per500win", 
                    self.lineEdit_maxper500: "maxPer500", 
                    self.lineEdit_maxDVTV: "maxDVTV",
                    self.lineEdit_minApSec: "minApSec",
                    self.lineEdit_minApsTT: "minApsTT",
                    self.lineEdit_minAplTT: "minAplTT",
                    self.lineEdit_sighwin: "SIGHwin",
                    self.lineEdit_smoothfilt: "SmoothFilt",
                    self.lineEdit_converttemp: "convert_temp",
                    self.lineEdit_convertco2: "convert_co2",
                    self.lineEdit_converto2: "convert_o2",
                    self.lineEdit_flowrate: "flowrate",
                    self.lineEdit_roto_x: "roto_x",
                    self.lineEdit_roto_y: "roto_y"}

        for widget in lineEdits:
            widget.setText(str(self.AnalysisParameters[lineEdits[widget]]))

    def get_parameter(self):

        minTI=self.lineEdit_minTI.text()
        minPIF=self.lineEdit_minPIF.text()
        minPEF=self.lineEdit_minPEF.text()
        TTwin=self.lineEdit_TTwin.text()
        per500win=self.lineEdit_per500win.text()
        maxper500=self.lineEdit_maxper500.text()
        maxDVTV=self.lineEdit_maxDVTV.text()
        minApSec=self.lineEdit_minApSec.text()
        minApsTT=self.lineEdit_minApsTT.text()
        minAplTT=self.lineEdit_minAplTT.text()
        SIGHwin=self.lineEdit_sighwin.text()
        SmoothFilt=self.lineEdit_smoothfilt.text()
        ConvertTemp=self.lineEdit_converttemp.text()
        ConvertCO2=self.lineEdit_convertco2.text()
        ConvertO2=self.lineEdit_converto2.text()
        Flowrate=self.lineEdit_flowrate.text()
        Roto_x=self.lineEdit_roto_x.text()
        Roto_y=self.lineEdit_roto_y.text()

        self.AnalysisParameters.update({"minTI":minTI})
        self.AnalysisParameters.update({"minPIF":minPIF})
        self.AnalysisParameters.update({"minPEF":minPEF})
        self.AnalysisParameters.update({"TTwin":TTwin})
        self.AnalysisParameters.update({"per500win":per500win})
        self.AnalysisParameters.update({"maxPer500":maxper500})
        self.AnalysisParameters.update({"maxDVTV":maxDVTV})
        self.AnalysisParameters.update({"minApSec":minApSec})
        self.AnalysisParameters.update({"minApsTT":minApsTT})
        self.AnalysisParameters.update({"minAplTT":minAplTT})
        self.AnalysisParameters.update({"SIGHwin":SIGHwin})
        self.AnalysisParameters.update({"SmoothFilt":SmoothFilt})
        self.AnalysisParameters.update({"convert_temp":ConvertTemp})
        self.AnalysisParameters.update({"convert_co2":ConvertCO2})
        self.AnalysisParameters.update({"convert_o2":ConvertO2})
        self.AnalysisParameters.update({"flowrate":Flowrate})
        self.AnalysisParameters.update({"roto_x":Roto_x})
        self.AnalysisParameters.update({"roto_y":Roto_y})

        self.config['Dictionaries']['AP']['current'].update(self.AnalysisParameters)
    
        with open(f'{Path(__file__).parent}/config.json','w') as config_file:
            json.dump(self.config, config_file)

    def print_parameters(self):
        print(self.AnalysisParameters)
        print(self.signals)
        print(os.path.join(self.mothership, "JSON"))

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

#endregion

#region Timestamper...

    def timestamp_dict(self):
        tic=datetime.datetime.now()
        print(tic)
        self.stamp['Dictionaries']['Data'] = {}
        combo_need = self.necessary_timestamp_box.currentText()
        if self.signals == []:
            self.hangar.append("Please choose signal files to check for timestamps.")
            # self.setAnimated(self.signal_files)
        elif combo_need == "Choose dataset...":
            self.hangar.append("Please choose a set of timestamps.")
        else:
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
                        
            print(f"bob: {self.stamp['Dictionaries']['Data']}")
            with open(os.path.join(Path(self.signals[0]).parent,f"timestamp_{os.path.basename(Path(self.signals[0]).parent)}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"),"w") as tspath:
                tspath.write(json.dumps(self.stamp))
                tspath.close()
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

#region Variable configuration

    def show_variable_config(self):
        if self.metadata != "" and self.autosections != "":
            self.test_configuration()
        else:
            if self.metadata == "":
                for item in self.metadata_list.findItems("file not detected.",Qt.MatchEndsWith):
                # and we remove them from the widget.
                    self.metadata_list.takeItem(self.metadata_list.row(item))
                self.metadata_list.addItem("No metadata file selected.")
            if self.autosections == "" and self.mansections == "":
                for item in self.sections_list.findItems("file not detected.",Qt.MatchEndsWith):
                # and we remove them from the widget.
                    self.sections_list.takeItem(self.sections_list.row(item))
                self.sections_list.addItem("No sections file selected.")
            
    def test_configuration(self):
        with open(self.metadata) as meta_file:
            metadata_columns = next(csv.reader(meta_file))
        with open(self.autosections) as auto_file:
            auto_columns = next(csv.reader(auto_file))
        # with open(self.mansections) as man_file:
        #     man_columns = next(csv.reader(man_file))
        with open(self.breathcaller_path) as bc:
            soup = bs(bc, 'html.parser')

        for column in metadata_columns:
            self.breath_df.append(column)
        for column_1 in auto_columns:
            if "AUTO_" in column_1:
                self.breath_df.append(column_1)
        # for column_2 in man_columns:
        #     if "MAN_" in column_2:
        #         self.breath_df.append(column_2)
        for child in soup.breathcaller_outputs.stripped_strings:
            self.breath_df.append(child)
        print(self.breath_df)
        if len(self.breath_df) != len(set(self.breath_df)):
            self.hangar.append("Duplicate values found in list of variables. Fix it.")
            self.variable_configuration()
        else:
            self.variable_configuration()
            
    def variable_configuration(self):
        self.v.show()
        # self.breath_df = pd.read_excel("C:/Users/atwit/Desktop/Mothership/breathcaller_output/py_output20201113_135540/M17023_megax.xlsx",header=0,nrows=1).columns
        self.stack = []

        header = self.v.variable_table.horizontalHeader()
        header.setSectionResizeMode(0,QHeaderView.Stretch)
        header.setSectionResizeMode(1,QHeaderView.Stretch)
        header.setSectionResizeMode(2,QHeaderView.Stretch)
        header.setSectionResizeMode(3,QHeaderView.Stretch)
        header.setSectionResizeMode(4,QHeaderView.Stretch)
        header.setSectionResizeMode(5,QHeaderView.Stretch)
        header.setSectionResizeMode(6,QHeaderView.Stretch)
        header.setSectionResizeMode(7,QHeaderView.Stretch)

        delegate = AlignDelegate(self.v.variable_table)
        self.v.variable_table.setItemDelegate(delegate)
        self.v.variable_table.setRowCount(len(self.breath_df))
        
        row = 0
        self.buttonDict_variable = {}

        for item in self.breath_df:
            self.buttonDict_variable[item]={"group": QButtonGroup()}
            # self.buttonDict_variable[item]["group"].buttonClicked.connect(self.check_buttons)

            self.buttonDict_variable[item]["orig"] = QTableWidgetItem(item)
            self.buttonDict_variable[item]["alias"] = QTableWidgetItem(item)

            self.buttonDict_variable[item]["ind"] = QRadioButton("Independent")
            self.buttonDict_variable[item]["dep"] = QRadioButton("Dependent")
            self.buttonDict_variable[item]["cov"] = QRadioButton("Covariate")
            self.buttonDict_variable[item]["ign"] = QRadioButton("Ignore")
            self.buttonDict_variable[item]["ign"].setChecked(True)

            self.buttonDict_variable[item]["group"].addButton(self.buttonDict_variable[item]["ind"])
            self.buttonDict_variable[item]["group"].addButton(self.buttonDict_variable[item]["dep"])
            self.buttonDict_variable[item]["group"].addButton(self.buttonDict_variable[item]["cov"])
            self.buttonDict_variable[item]["group"].addButton(self.buttonDict_variable[item]["ign"])
            
            self.v.variable_table.setItem(row,0,self.buttonDict_variable[item]["orig"])
            self.v.variable_table.setItem(row,1,self.buttonDict_variable[item]["alias"])

            self.v.variable_table.setCellWidget(row,2,self.buttonDict_variable[item]["ind"])
            self.v.variable_table.setCellWidget(row,3,self.buttonDict_variable[item]["dep"])
            self.v.variable_table.setCellWidget(row,4,self.buttonDict_variable[item]["cov"])
            self.v.variable_table.setCellWidget(row,5,self.buttonDict_variable[item]["ign"])

            self.buttonDict_variable[item]["role"] = QComboBox()
            self.buttonDict_variable[item]["self.static"] = QComboBox()

            self.buttonDict_variable[item]["role"].addItems(["","xvar","pointdodge","facet1","facet2"])
            self.buttonDict_variable[item]["self.static"].addItems(["","Start Body Temp","Mid Body Temp","End Body Temp","Post Body Temp","Body Weight"])

            self.v.variable_table.setCellWidget(row,6,self.buttonDict_variable[item]["role"])
            self.v.variable_table.setCellWidget(row,7,self.buttonDict_variable[item]["self.static"])

            row += 1
            # you have to iteratively create the widgets for each row, not just iteratively
            # add the widgets for each row because it'll only do the last row
            # so every row's radio button will 
            self.buttonDict_variable[item]["self.static"].activated.connect(self.v.replace)
            self.buttonDict_variable[item]["role"].activated.connect(self.v.replace)

#endregion

#region Automatic selection

    def mothership_dir(self):
        # self.mothership = "C:/Users/atwit/Desktop/Mothership"
        self.mothership = Path(QFileDialog.getExistingDirectory(self, 'Choose output directory', str(Path.home()), QFileDialog.ShowDirsOnly))
        self.breathcaller_path_list.clear()
        self.py_output_dir_list.clear()
        self.signal_files_list.clear()
        self.metadata_list.clear()
        self.sections_list.clear()
        self.py_go.setDisabled(False)

    def auto_get_python_module(self):
        py_mod_path=self.config['Dictionaries']['Paths']['breathcaller']
        self.breathcaller_path_list.clear()
        if Path(py_mod_path).exists():
            self.breathcaller_path=py_mod_path
            self.breathcaller_path_list.addItem(self.breathcaller_path)
        else:
            self.breathcaller_path_list.clear()
            self.breathcaller_path_list.addItem("Python module not detected.")

    def auto_get_output_dir_py(self):
        self.py_output_folder=os.path.join(self.mothership,'breathcaller_output')
        if Path(self.py_output_folder).exists():
            self.output_dir_py=os.path.join(self.py_output_folder, 'py_output'+datetime.datetime.now().strftime(
                '%Y%m%d_%H%M%S'
            ))
            print(self.output_dir_py)
            self.py_output_dir_list.clear()
            self.py_output_dir_list.addItem(self.output_dir_py)
        else:
            Path(self.py_output_folder).mkdir()
            self.output_dir_py=os.path.join(self.py_output_folder,'py_output'+datetime.datetime.now().strftime(
                '%Y%m%d_%H%M%S'
            ))
            self.py_output_dir_list.clear()
            self.py_output_dir_list.addItem(self.output_dir_py)
    
    def auto_get_signal_files(self):
        signal_folder=os.path.join(self.mothership,'signals')
        self.input_dir_py=signal_folder
        if Path(signal_folder).exists() and Path(signal_folder).is_dir():
            self.signal_files_list.clear()
            self.signals=[]
            # self.signal_files=[]
            for file in Path(signal_folder).iterdir():
                self.signal_files_list.addItem(str(file))
                # self.signal_files.append(os.path.basename(file))
                self.signals.append(file)
        else:
            self.signal_files_list.clear()
            self.signal_files_list.addItem("Signal files directory not detected.")
     
    def auto_get_metadata(self):
        metadata_path=os.path.join(self.mothership, 'metadata.csv')
        if Path(metadata_path).exists():
            # We assign the path detected via mothership to the Plethysmography class attribute that will be an argument for the breathcaller command line.
            self.metadata=metadata_path
            self.metadata_list.addItem(self.metadata)
        else:
            self.metadata_list.addItem("Metadata file not detected.")
            
    def auto_get_autosections(self):
        autosections_path=os.path.join(self.mothership, 'auto_sections.csv')
        if Path(autosections_path).exists():
            # We assign the path detected via mothership to the Plethysmography class attribute that will be an argument for the breathcaller command line.
            self.autosections=autosections_path
            self.sections_list.addItem(self.autosections)
        else:
            self.sections_list.addItem("Autosection parameters file not detected.")

    def auto_get_mansections(self):
        mansections_path=os.path.join(self.mothership, 'manual_sections.csv')
        if Path(mansections_path).exists():
            # We assign the path detected via mothership to the Plethysmography class attribute that will be an argument for the breathcaller command line.
            self.mansections=mansections_path
            self.sections_list.addItem(self.mansections)
        else:
            self.sections_list.addItem("Manual sections parameters file not detected.")

    def auto_get_papr_module(self):
        papr_path=papr_path=self.config['Dictionaries']['Paths']['papr']
        self.papr_dir_list.clear()
        if Path(papr_path).exists():
            # We assign the path detected via mothership to the Plethysmography class attribute that will be an argument for the breathcaller command line.
            self.papr_dir=papr_path
            self.papr_dir_list.addItem(self.papr_dir)
        else:
            self.papr_dir_list.clear()
            self.papr_dir_list.addItem("SG-Runner module not detected.")
        
    def auto_get_variable(self):
        # Because we are using one list widget (self.variable_list) to give signs of life regarding the self.graph_settings_path and self.variable_config attributes,
        # the clearing of the widget's previous messages or paths is less straightforward. 
        # We create a directory path for a file named variable_configuration.csv and again for one named graph_settings.csv in the mothership folder.
        variable_path=os.path.join(self.mothership, 'variable_configuration.csv')
        # We first prove that the directory paths we just created actually exist.
        if Path(variable_path).exists():
            # We assign the path detected via mothership to the Plethysmography class attribute that will be an argument for the breathcaller command line.
            self.variable_config = variable_path

            # We look for any previous "file not detected" messages in the self.variable_list widget...
            for item in self.variable_list.findItems("Variable configuration file not detected.",Qt.MatchExactly):
                # and we remove them from the widget.
                self.variable_list.takeItem(self.variable_list.row(item))
            # If we are changing a previous choice of directory path, here we remove the evidence of that choice from the widget.
            for item in self.variable_list.findItems("variable_configuration",Qt.MatchContains):
                self.variable_list.takeItem(self.variable_list.row(item))

            # We add the path to the self.variable_list widget in the MainGUI to indicate successful assignation of the Plethysmography class attribute.
            self.variable_list.addItem(self.variable_config)

        else:
            # We look for any previous "file not detected" messages in the self.variable_list widget...
            for item in self.variable_list.findItems("Variable configuration file not detected.",Qt.MatchExactly):
                # and we remove them from the widget.
                self.variable_list.takeItem(self.variable_list.row(item))
            # If the variable_config.csv path we created doesn't exist, we add a "file not detected" massage to the self.variable_list widget to indicate unsuccessfuly assignation of the Plethysmography class attribute.
            self.variable_list.addItem("Variable configuration file not detected.")
            # If we are changing a previous choice of directory path, here we remove the evidence of that choice from the widget to avoid the user thinking 
            # the new path they chose worked when they are actually just looking at the previous choice's path.
            for item in self.variable_list.findItems("variable_configuration",Qt.MatchContains):
                self.variable_list.takeItem(self.variable_list.row(item))

    def auto_get_breath_files(self):
        breath_files_path=self.output_dir_py
        self.breath_list.clear()
        if not breath_files_path:
            self.breath_list.clear()
            self.breath_list.addItem("Breathcaller output directory not detected.")
        else:
            self.input_dir_r=breath_files_path
            self.breath_list.addItem(self.output_dir_py)

    def auto_get_output_dir_r(self):
        r_output_folder=os.path.join(self.mothership,'papr_output')
        if Path(r_output_folder).exists():
            self.output_dir_r=os.path.join(r_output_folder, 'r_output'+datetime.datetime.now().strftime(
                '%Y%m%d_%H%M%S'
            ))
            self.r_output_dir_list.clear()
            self.r_output_dir_list.addItem(self.output_dir_r)
        else:
            Path(r_output_folder).mkdir()
            self.output_dir_r=os.path.join(r_output_folder, 'r_output'+datetime.datetime.now().strftime(
                '%Y%m%d_%H%M%S'
            ))
            # Path(self.output_dir_r).mkdir()
            self.r_output_dir_list.clear()
            self.r_output_dir_list.addItem(self.output_dir_r)

#endregion

#region Manual selection

    def breathcaller_directory(self):
        file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(Path.home()))
        if not file_name[0]:
            self.breathcaller_path_list.clear()
            self.breathcaller_path_list.addItem("No file selected.")
        else:
            self.breathcaller_path_list.clear()
            for x in range(len(file_name[0])):
                self.breathcaller_path_list.addItem(file_name[0][x])
            self.breathcaller_path = file_name[0][0]

    def output_directory_py(self):
        self.output_dir_py = QFileDialog.getExistingDirectory(self, 'Choose output directory', str(Path.home()), QFileDialog.ShowDirsOnly)
        if not self.output_dir_py:
            self.py_output_dir_list.clear()
            self.py_output_dir_list.addItem("No folder selected.")
        else:
            self.py_output_dir_list.clear()
            self.py_output_dir_list.addItem(self.output_dir_py) 

    def get_signal_files(self):
        if not self.input_dir_py:
            if not self.mothership:
                file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(Path.home()))
            else:
                file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(self.mothership))
        else:
            file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(self.input_dir_py))
        self.signal_files_list.clear()
        self.signals=[]
        # self.signal_files=[]
        if not file_name[0]:
            self.signal_files_list.clear()
            self.signal_files_list.addItem("No file selected.")
        else:
            for x in range(len(file_name[0])):
                self.signal_files_list.addItem(file_name[0][x])
                # self.signal_files.append(os.path.basename(file_name[0][x]))
                self.signals.append(file_name[0][x])
            self.input_dir_py = os.path.dirname(self.signals[0])

    def get_metadata(self):
        file_name = QFileDialog.getOpenFileNames(self, 'Select files', self.output_dir_py)
        if not file_name[0]:
            self.metadata_list.clear()
            self.metadata_list.addItem("No file selected.")
        else:
            self.metadata_list.clear()
            for x in range(len(file_name[0])):
                self.metadata_list.addItem(file_name[0][x])
            self.metadata = file_name[0][0]
    
    def mp_parser(self):
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
            except:
                self.mp_parserrors.append(file)

    def get_study(self, fixformat=True):
        self.metadata_warnings={}
        self.metadata_list.addItem("Gauging Filemaker connection...")
        try:
            dsn = 'DRIVER={FileMaker ODBC};Server=128.249.80.130;Port=2399;Database=MICE;UID=Python;PWD='
            mousedb = pyodbc.connect(dsn)
        except:
            self.metadata_list.addItem("Unable to connect to Filemaker.")
        self.metadata_list.addItem("Building query...")
        # try:
        FieldDict={"MUID":['Mouse_List','Plethysmography'],
            "PlyUID":['Plethysmography'],
            "Misc. Variable 1 Value":['Plethysmography'],
            "Sex":['Mouse_List'],
            "Genotype":['Mouse_List'],
            "Group":['Plethysmography'],
            "Weight":['Plethysmography'],
            # "Age":[],
            "Date of Birth":['Mouse_List'],
            "Experiment_Name":['Plethysmography'],
            "Researcher":['Plethysmography'],
            "Experimental_Date":['Plethysmography'],
            "time started":['Plethysmography'],
            "Rig":['Plethysmography'],
            "Plate":['Mouse_List'],
            "Row":['Mouse_List'],
            "Column":['Mouse_List'],
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
            m_cursor = mousedb.execute(
                """select """+m_FieldText+
                """ from "Mouse_List" where "MUID" in ("""+
                ','.join([str(i) for i in self.mp_parsed['MUIDLIST']])+
                """) """)    
            p_cursor = mousedb.execute(
                """select """+p_FieldText+
                """ from "Plethysmography" where "PLYUID" in ("""+
                ','.join([str(i) for i in self.mp_parsed['PLYUIDLIST']])+
                """) and "MUID" in ("""+
                ','.join(["'M{}'".format(int(i)) for i in self.mp_parsed['MUIDLIST']])+
                """) """)
        elif self.mp_parsed['PLYUIDLIST']!=[]:
            m_cursor = mousedb.execute(
                """select """+m_FieldText+
                """ from "Mouse_List" """)    
            p_cursor = mousedb.execute(
                """select """+p_FieldText+
                """ from "Plethysmography" where "PLYUID" in ("""+
                ','.join([str(i) for i in self.mp_parsed['PLYUIDLIST']])+
                """) """)
        elif self.mp_parsed['MUIDLIST']!=[]:
            m_cursor = mousedb.execute(
                """select """+m_FieldText+
                """ from "Mouse_List" where "MUID" in ("""+
                ','.join([str(i) for i in self.mp_parsed['MUIDLIST']])+
                """) """)    
            p_cursor = mousedb.execute(
                """select """+p_FieldText+
                """ from "Plethysmography" where "MUID" in ("""+
                ','.join(["'M{}'".format(int(i)) for i in self.mp_parsed['MUIDLIST']])+
                """) """)
        else:
            m_cursor = mousedb.execute(
                """select """+m_FieldText+
                """ from "Mouse_List" """)    
            p_cursor = mousedb.execute(
                """select """+p_FieldText+
                """ from "Plethysmography" """)
            
        self.metadata_list.addItem("Fetching metadata...")
        m_mouse_list = m_cursor.fetchall()
        p_mouse_list = p_cursor.fetchall()
        m_head_list = [i[0] for i in m_cursor.description]
        p_head_list = [i[0] for i in p_cursor.description]
        mousedb.close()
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
            self.hangar.append(f"{w}: {[x for x in plys[w]]}")
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
        # except:
        #     new_error='unable to assemble metadata'
        #     meta_assemble_errors = []
        #     meta_assemble_errors.append(new_error)
        #     # return pd.DataFrame(),errors
        #     print(meta_assemble_errors)

    def metadata_checker_filemaker(self):
        self.essential_fields = self.config['Dictionaries']['metadata']['essential_fields']
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
     
    def get_filemaker(self):
        self.mp_parser()
        self.get_study()
    
        self.metadata_list.addItem("Creating csv file...")
        # If a mothership directory has yet to be selected...
        if self.mothership == "":
            # A save file dialog pops up in the Plethysmography folder (should this change?) as indicated by self, the first argument of the QFileDialog function. The proffered filename is metadata_{the same timestamp
            # given to self.output_dir_py} - if self.output_dir_py has yet to be specificed, then the file is proffered as metadata_. This saved .csv file's path is assigned to self.metadata_path.
            self.metadata_path = QFileDialog.getSaveFileName(self, 'Save File', f"metadata_{os.path.basename(self.output_dir_py).lstrip('py_output')}", ".csv(*.csv))")[0]
            # If the user presses cancel in the save file dialog, the widget clears and says "No file selected."
            if not self.metadata_path:
                self.metadata_list.clear()
                self.metadata_list.addItem("No file selected.")
            # If self.metadata_path is populated successfully by the file saved via the dialog, the widget is cleared and the path is added to the widget.
            else:
                self.assemble_df.to_csv(self.metadata_path, index = False)
                self.metadata_list.clear()
                self.metadata_list.addItem(self.metadata_path)
        else:
            # If a mothership directory exists, then a path for self.output_dir_py has been generated. The directory needs to actually be created because the metadata file needs to be written to it. Normally, the directory
            # isn't made until pything_to_do is called.
            if not os.path.exists(self.output_dir_py):
                Path(self.output_dir_py).mkdir()
            self.metadata_path = os.path.join(self.output_dir_py, f"metadata_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv")
            self.assemble_df.to_csv(self.metadata_path, index = False)
            self.metadata_list.clear()
            self.metadata_list.addItem(self.metadata_path)
        shutil.copy(self.metadata_path, os.path.join(self.mothership, "metadata.csv"))
        self.metadata_path = self.metadata

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

    # def metadata_checker(self):

    def get_autosections(self):
        file_name = QFileDialog.getOpenFileNames(self, 'Select files', self.output_dir_py)
        if not file_name[0]:
            self.sections_list.addItem("No sections parameters file(s) selected.")
        else:
            # self.sections_list.clear()
            for x in range(len(file_name[0])):
                self.sections_list.clear()
                self.sections_list.addItem(file_name[0][x])
            self.autosections = file_name[0][0]

    def papr_directory(self):
        self.papr_dir = QFileDialog.getExistingDirectory(self, 'Select papr directory', str(Path.home()))
        if not self.papr_dir:
            self.papr_dir_list.clear()
            self.papr_dir_list.addItem("No folder selected.")
        else:
            self.papr_dir_list.clear()
            self.papr_dir_list.addItem(self.papr_dir)

    def input_directory_r(self):
        self.input_dir_r = QFileDialog.getExistingDirectory(self, 'Choose breathlist directory', str(Path.home()))
        if not self.input_dir_r:
            self.breath_list.clear()
            self.breath_list.addItem("No folder selected.")
        else:
            self.breath_list.clear()
            self.breath_list.addItem(self.input_dir_r)

    def output_directory_r(self):
        self.output_dir_r = QFileDialog.getExistingDirectory(self, 'Choose output directory', str(Path.home()))
        if not self.output_dir_r:
            self.r_output_dir_list.clear()
            self.r_output_dir_list.addItem("No folder selected.")
        else:
            self.r_output_dir_list.clear()
            self.r_output_dir_list.addItem(self.output_dir_r)

#endregion

#region Go methods

    def go_r(self):
        papr_cmd='"{rscript}" "{pipeline}" -d "{d}" -J "{j}" -R "{r}" -G "{g}" -O "{o}" -T "{t}" -S "{s}" -M "{m}" -B "{b}"'.format(
            rscript = self.config['Dictionaries']['Paths']['rscript'],
            pipeline = os.path.join(self.papr_dir, "pipeline.R"),
            d = self.mothership,
            # j = os.path.join(self.mothership, "JSON"),
            j = self.input_dir_r,
            r = self.variable_config,
            # r = os.path.join(self.mothership, "R_config/sava_config_copied.csv"),
            g = self.graph_config_path,
            # g = os.path.join(self.mothership, "G_config/sava_graph_copied.csv"),
            # o = os.path.join(self.mothership, "Output")
            # o = "C:/Users/atwit/Desktop/Mothership/papr_output/r_output20201016_171213",
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
        log=os.path.join(self.output_dir_py,'log_"{bob}"'.format(bob=os.path.basename(os.path.normpath(self.output_dir_py)))+".txt")

        breathcaller_cmd = 'python -u "{module}" --minTI "{minTI}" --minPIF "{minPIF}" --minPEF "{minPEF}" --TTwin "{TTwin}" --per500win "{per500win}" --maxPer500 "{maxPer500}" --maxDVTV "{maxDVTV}" --minApSec "{minApSec}" --minApsTT "{minApsTT}" --minAplTT "{minAplTT}" --SIGHwin "{SIGHwin}" --SmoothFilt "{SmoothFilt}" --id "{id}" {filelist} --of "{of_arg}" --sf "{sf}" --md "{md}" --cf "{cf}" --convert_temp "{convert_temp}" --convert_co2 "{convert_co2}" --convert_o2 "{convert_o2}" --flowrate "{flowrate}" --roto_x "{roto_x}" --roto_y "{roto_y}" --g None'.format(
            module = self.breathcaller_path,
            minTI = self.AnalysisParameters['minTI'],
            minPIF = self.AnalysisParameters['minPIF'],
            minPEF = self.AnalysisParameters['minPEF'],
            TTwin = self.AnalysisParameters['TTwin'],
            per500win = self.AnalysisParameters['per500win'],
            maxPer500 = self.AnalysisParameters['maxPer500'],
            maxDVTV = self.AnalysisParameters['maxDVTV'],
            minApSec = self.AnalysisParameters['minApSec'],
            minApsTT = self.AnalysisParameters['minApsTT'],
            minAplTT = self.AnalysisParameters['minAplTT'],
            SIGHwin = self.AnalysisParameters['SIGHwin'],
            SmoothFilt = self.AnalysisParameters['SmoothFilt'],
            id = self.input_dir_py,
            # signal = file_py,
            filelist= '-f "'+'" -f "'.join([os.path.basename(i) for i in self.signals])+'"',
            # of_arg = f"C:/Users/atwit/Desktop/Mothership/breathcaller_output/py_output20201113_135540/log_py_output20201113_135540.txt",
            of_arg = f"{self.output_dir_py}/log_{os.path.basename(self.output_dir_py)}.txt",
            sf = self.mansections,
            md = self.metadata,
            cf = self.autosections,
            convert_temp = self.AnalysisParameters['convert_temp'],
            convert_co2 = self.AnalysisParameters['convert_co2'],
            convert_o2 = self.AnalysisParameters['convert_o2'],
            flowrate = self.AnalysisParameters['flowrate'],
            roto_x="50,75,80,90,95,100,110,125,150",
            roto_y="0.0724,0.13476,0.14961,0.18137,0.19811,0.21527,0.2504,0.30329,0.38847")

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
                for line in output.strip():
                    self.completed += 1
            if 'PROGRESS:' in output.strip():
                current_progress=self.parse_progress(output.strip())
                print('***  {percent_complete}  |  {time_remaining}  |  {estimated_total_time}  |  {current_file_no}  |  {total_file_no}  ********'.format(**current_progress))
                # self.completed = float(current_progress['percent_complete'])
                
            self.hangar.append(str(output.strip()))
            QApplication.processEvents()
            time.sleep(0.2)
            self.progressBar_py.setValue(self.completed)

#endregion

#region Threading

# Concurrency is a nightmare. I'll do my best to explain what's going on. Currently, there are two types of concurrency enabled for both the breathcaller and papr.
# I'm in the process of exploring the black box. Fear is the mind killer.

    def py_message(self):
        print("message")
        self.hangar.append("Breathcaller analyzing signal files...")
        self.pything_to_do()

    def pything_to_do(self):
        if os.path.isdir(self.output_dir_py):
            print(self.output_dir_py)
        else:
            Path(self.output_dir_py).mkdir()
        if self.metadata_path == "":
            shutil.copyfile(self.metadata, os.path.join(self.output_dir_py, f"metadata_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv"))
        self.get_parameter()
        shutil.copyfile(f'{Path(__file__).parent}/config.json', os.path.join(self.output_dir_py, f"config_{os.path.basename(self.output_dir_py).lstrip('py_output')}.json"))
        shutil.copyfile(self.autosections, os.path.join(self.output_dir_py, f"autosections_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv"))
        print('pything_to_do thread id',threading.get_ident())
        print("pything_to_do process id",os.getpid())
        # self.thready(self.update_Pyprogress)
        self.worker = threading.Thread(target = MainGUIworker.futurama_py(self))
        self.worker.daemon = True
        self.worker.start()
        # Note that this isn't printed until the very end, after all files have been processed and everything is basically done.
        print("worker started?")
    
    def rthing_to_do(self):
        if os.path.isdir(self.output_dir_r):
            print(self.output_dir_r)
        else:
            Path(self.output_dir_r).mkdir()
        self.hangar.append("SG-Runner analyzing breath files...")
        shutil.copyfile(f'{Path(__file__).parent}/config.json', os.path.join(self.output_dir_r, f"config_{os.path.basename(self.output_dir_r).lstrip('r_output')}.json"))
        shutil.copyfile(self.variable_config, os.path.join(self.output_dir_r, f"r_config_{os.path.basename(self.output_dir_r).lstrip('r_output')}.csv"))
        shutil.copyfile(self.graph_config_path, os.path.join(self.output_dir_r, f"g_config_{os.path.basename(self.output_dir_r).lstrip('r_output')}.csv"))
        print('rthing_to_do thread id',threading.get_ident())
        print("rthing_to_do process id",os.getpid())
        self.worker = threading.Thread(target = MainGUIworker.futurama_r(self))
        self.worker.daemon = True
        self.worker.start()
        print("worker started?")
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
        self.thready(self.update_Rprogress)
    
    def pything_to_do_single(self):
        print("pything_single thread id", threading.get_ident())
        print("pything_single process id", os.getpid())
        self.thready(self.update_Pyprogress)

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
