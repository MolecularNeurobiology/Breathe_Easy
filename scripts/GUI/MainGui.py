#%%
#region Libraries
from typing import Callable
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtCore import *
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
import csv
import queue
import traceback
from pathlib import Path
import subprocess
import datetime
import time
import os
import json
import pyodbc
import shutil
import pandas as pd
import threading
import re
import MainGUIworker
import AnnotGUI
from bs4 import BeautifulSoup as bs

#endregion

#%%
#region classes
class AlignDelegate(QStyledItemDelegate):
    """
    This class assigns delegates to Config.variable_table and Config.loop_table TableWidgets and and centers the delegate items.
    """
    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter

class Thinbass(QDialog,Ui_Thinbass):
    """
    This class is used when the user has metadata and BASSPRO settings files as well as JSON files - either can be a source for building the variable list that populates the STAGG Settings subGUI. This dialog prompts them to decide which source they'd like to use.
    """
    def __init__(self,Plethysmography):
        """"
        Instantiate the Thinbass class in the method Plethysmography.show_variable_config().

        Parameters
        --------
        Ui_Thinbass: class
            Thinbass inherits widgets and layouts of Ui_Thinbass.
        Plethysmography: class
            Thinbass inherits Plethysmography's methods, attributes, and widgets.
        """
        super(Thinbass, self).__init__()
        self.pleth = Plethysmography
        self.setupUi(self)
        self.setWindowTitle("Variables list sources")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    
    def settings(self):
        """
        Populate Config.variable_table and the comboBoxes in Config.loop_table with the list of variables (Plethysmography.breath_df) compiled from BASSPRO settings and metadata and show the STAGG settings subGUI.

        Parameters
        --------
        Plethysmography: class
            Thinbass inherits Plethysmography's methods, attributes, and widgets.
        Plethysmography.Config: class
            Thinbass inherits Config methods, attributes, and widget via its Plethysmography inheritance. Config defines the STAGG settings subGUI.
        Plethysmography.Config.variable_table: QTableWidget
            This TableWidget is defined in the Config class, displayed in the STAGG settings subGUI, and populated with rows based on the list of variables (Plethysmography.breath_df). 

        Outputs
        --------
        Plethysmography.n: int
            This integer is incremented when variables are given duplicate names and appended to the existing variable's name so that the edited variable retains the user's edits.
        Plethysmography.Config.variable_table: QTableWidget
            cellChanged signals are assigned to the TableWidgets cells for two slots: Plethysmography.Config.no_duplicates() and Plethysmography.Config.update_loop().
        
        Outcomes
        --------
        Plethysmography.test_configuration()
            This Plethysmography method ensures that the file paths that populate the attributes required to show the STAGG settings subGUI exist and their contents are accessible, and provide feedback to the user on what is missing if anything.
        Plethysmography.variable_configuration()
            This Plethysmography method populates self.buttonDict_variable with widgets and text and populates Config.variable_table with the contents of self.buttonDict_variable.
        Plethysmography.Config.show()
            This Plethysmography method displays the STAGG settings subGUI.
        """
        print("thinbass.settings()")
        self.pleth.test_configuration()
        try:
            self.pleth.variable_configuration()
            self.pleth.n = 0
            self.pleth.v.variable_table.cellChanged.connect(self.pleth.v.no_duplicates)
            self.pleth.v.variable_table.cellChanged.connect(self.pleth.v.update_loop)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
        self.pleth.v.show()
    
    def output(self):
        # This method was written before we developed the means to accept .RData files are STAGG input. We need to add functionality that checks to make sure that Plethysmography.stagg_list[0] is actually a JSON file and not an .RData file and nexts until it finds one.
        """
        Populate Config.variable_table and the comboBoxes in Config.loop_table with the list of variables (Plethysmography.breath_df) compiled from BASSPRO output JSON file and show the STAGG settings subGUI.

        Parameters
        --------
        Plethysmography: class
            Thinbass inherits Plethysmography's methods, attributes, and widgets.
        Plethysmography.Config: class
            Thinbass inherits Config methods, attributes, and widget via its Plethysmography inheritance. Config defines the STAGG settings subGUI.
        Plethysmography.Config.variable_table: QTableWidget
            This TableWidget is defined in the Config class, displayed in the STAGG settings subGUI, and populated with rows based on the list of variables (Plethysmography.breath_df). 

        Outputs
        --------
        Plethysmography.breath_df: list
            This Plethysmography class attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file. Thinbass.output() populates Plethysmography.breath_df using the third option.
        Pletheysmography.stagg_list: list
            The list of one of the following: JSON files produced by the most recent run of BASSPRO in the same session; JSON files produced by BASSPRO selected by user with a FileDialog; an .RData file produced by a previous run of STAGG and JSON files produced by BASSPRO.
        Plethysmography.n: int
            This integer is incremented when variables are given duplicate names and appended to the existing variable's name so that the edited variable retains the user's edits.
        Plethysmography.Config.variable_table: QTableWidget
            cellChanged signals are assigned to the TableWidgets cells for two slots: Plethysmography.Config.no_duplicates() and Plethysmography.Config.update_loop().
        
        Outcomes
        --------
        Plethysmography.variable_configuration()
            This Plethysmography method populates self.buttonDict_variable with widgets and text and populates Config.variable_table with the contents of self.buttonDict_variable.
        Plethysmography.Config.show()
            This Plethysmography method displays the STAGG settings subGUI.
        """
        print("thinbass.output()")
        try:
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
    This class defines a simple dialog that displays information to the user.
    """
    def __init__(self,Plethysmography):
        """
        Instantiate the Thumbass class.

        Parameters
        --------
        Plethysmography: class
            Thinbass inherits Plethysmography's methods, attributes, and widgets.
        Ui_Thumbass: class
            Thinbass inherits widgets and layouts from the Ui_Thumbass class 
    
        Outputs
        --------
        Thumbass: QDialog
            The Dialog displays the output of Thumbass.message_received() and its window title is the text of the "title" argument of Thumbass.message_received().
        Thumbass.label: QLabel
            The label displays the text provided as the argument "words" of Thumbass.message_received().
        """
        super(Thumbass, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Nailed it.")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.label.setOpenExternalLinks(True)
    
    def message_received(self,title,words):
        self.setWindowTitle(title)
        self.label.setText(words)
#endregion

#region Thorbass
class Thorbass(QDialog,Ui_Thorbass):
    """
    This class defines a specialized dialog that prompts the user to provide the necessary input for the function they are trying to use. It's instantiated by Manual.manual_merge() or Plethysmography.show_variable_config().
    """
    def __init__(self,Plethysmography):
        """"
        Instantiate the Thorbass class.

        Parameters
        --------
        Ui_Thorbass: class
            Thorbass inherits widgets and layouts of Ui_Thorbass.
        Plethysmography: class
            Thorbass inherits Plethysmography's methods, attributes, and widgets.
        
        Outputs
        --------
        self.pleth: class
            Shorthand for the Plethysmography class.
        """
        super(Thorbass, self).__init__()
        self.pleth = Plethysmography
        self.setupUi(self)
        self.setWindowTitle("Nailed it.")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    
    def message_received(self, title: str, words: str, new: callable, opens: callable):
        """
        Set the Dialog's window title as the text of "title", set the text of Label as the text of "words", assign the clicked signal and slot defined by "new" to Thorbass.new_button, and assign the clicked signal and slot defined by "opens" to Thorbass.open_button.

        Parameters
        --------
        title: str
            This argument is a string intended to be the Dialog's window title.
        words: str
            This argument is a string intended to be set as Thorbass.label's text.
        new: callable
            This argument is a callable to either Manual.new_manual_file() or Plethysmography.new_variable_config().
        opens: callable
            This argument is a callable to either Manual.open_manual_file() or Plethysmography.get_variable_config().


        Outputs
        --------
        Thorbass.label: QLabel
            The label displays the text provided as the argument "words" of Thorbass.message_received().
        Thorbass.new_button: QPushButton
            This PushButton is assigned the clicked signal and the slot defined by "new".
        Thorbass.open_button: QPushButton
            This PushButton is assigned the clicked signal and the slot defined by "opens".
        """
        print("thorbass.message_received()")
        self.setWindowTitle(title)
        self.label.setText(words)
        self.new_button.clicked.connect(new)
        self.open_button.clicked.connect(opens)
#endregion

#region class Basic Parameters
class Basic(QWidget, Ui_Basic):
    """
    The Basic class defines the the properties, attributes, and methods used by the basic BASSPRO settings subGUI.

    Parameters
    --------
    QWidget: class
        The Basic class inherits properties and methods from the QWidget class. 
    Ui_Basic: class
        The Basic class inherits widgets and layouts defined in the Ui_Basic class.
    """
    def __init__(self,Plethysmography):
        """
        Instantiate the Basic class.

        Parameters
        --------
        Plethysmography: class
            The Basic class inherits properties, attributes and methods of the Plethysmography class.
        
        Outputs
        --------
        self.pleth: class
            Shorthand for the Plethysmography class.
        self.path: str
            This attribute is set as an empty string.

        Outcomes
        --------
        self.setup_variables()
            This method organizes widgets in dictionaries and assigns signals and slots to certain widgets.
        self.setup_tabs()
            This method populates the basic BASSPRO settings subGUI widgets with default values derived from Plethysmography.bc_config (breathcaller_config.json).
        """
        super(Basic, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Basic BASSPRO settings")
        self.pleth = Plethysmography
        self.isMaximized()
        self.setup_variables()
        self.setup_tabs()
        self.path = ""
        
    def setup_variables(self):
        """
        Organize widgets in dictionaries and assign signals and slots to relevant buttons.

        Parameters
        --------
        Plethysmography.bc_config: dict
            This Plethysmography class attribute is a nested dictionary loaded from breathcaller_config.json. It contains the default settings of multiple experimental setups for basic, automated, and manual BASSPRO settings and  the most recently saved settings for automated and basic BASSPRO settings. See the README file for more detail.
        self.{tab}_reference: QTextBrowser
            These TextBrowsers display the definition, description, and default value of the user-selected setting. There is a TextBrowser for each of the first three tabs of the subGUI.
        self.help_{setting}: QToolButton
            These are buttons intended to provide helpful information to the user about the relevant setting.
        self.lineEdit_{setting}: QLineEdit
            These LineEdits widgets display the values of the basic settings. They are editable.
        self.reset_{setting}: QToolButton
            These ToolButtons revert the value of the setting displayed in the corresponding LineEdit to the default value stored in Plethysmography.bc_config.
        
        Outputs
        --------
        self.basic_dict: dict
            This attribute stores the nested dictionary in Plethysmography.bc_config that contains the default basic BASSPRO settings.
        self.widgy: dict
            This dictionary relates the self.help_{setting} widgets with the appropriate TextBrowser.
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.
        self.resets: list
            This list makes it easier to iteratively assign signals and slots to all the self.reset_{setting} widgets.
        self.help_{setting}: QToolButton
            These buttons are assigned clicked signals and slotted for self.reference_event().
        self.lineEdit_{setting}: QLineEdit
            These LineEdits are assigned textChanged signals and slotted for self.update_table_event().
        self.reset_{setting}: QToolButton
            These buttons are assigned clicked signals and slotted for self.reset_event().
        """
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

    def setup_tabs(self):
        """
        Populate widgets in each tab with appropriate values for the default basic BASSPRO settings stored in self.basic_dict.

        Parameters
        --------
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.
        self.basic_dict: dict
            This attribute stores the nested dictionary in Plethysmography.bc_config that contains the default basic BASSPRO settings.
        Plethysmography.basicap: str
            The path of the user-selected basic BASSPRO settings file.
        self.view_tab: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        
        Outputs
        --------
        self.lineEdit_{setting}: QLineEdit
            The LineEdits' values are iteratively set as the values of the corresponding keys in self.basic_dict.
        self.basic_df: Dataframe
            This attribute stores a dataframe derived either from self.basic_dict or from the .csv file indicated by the user-selected file path (self.basicap).
        
        Outcomes
        --------
        self.populate_table()
            This method populates self.view_tab (TableWidget) with the self.basic_df dataframe.
        """
        print("basic.setup_tabs()")
        # Populate lineEdit widgets with default basic parameter values from breathcaller configuration file:
        for widget in self.lineEdits:
            widget.setText(str(self.basic_dict[self.lineEdits[widget]]))
        if self.pleth.basicap != "":
            if Path(self.pleth.basicap).exists():
                self.basic_df = pd.read_csv(self.pleth.basicap)
        else:
            self.basic_df = pd.DataFrame.from_dict(self.basic_dict,orient='index').reset_index()
            self.basic_df.columns = ['Parameters','Settings']
            # Populate table of summary tab:
        self.populate_table(self.basic_df,self.view_tab)
    
    def reference_event(self):
        """
        Respond to the signal emitted by the self.help_{setting} ToolButton clicked by the user by calling self.populate_reference(self.sender.objectName()) to populate the appropriate TextBrowser with the definition, description, and default value of corresponding setting.
        """
        sbutton = self.sender()
        self.populate_reference(sbutton.objectName())
    
    def reset_event(self):
        """
        Respond to the signal emitted by the self.reset_{setting} ToolButton clicked by the user by calling self.reset_parameters(self.sender.objectName()) to revert the LineEdit value to the default value in the default basic BASSPRO settings dictionary (self.basic_dict).
        """
        sbutton = self.sender()
        self.reset_parameter(sbutton.objectName())
    
    def update_table_event(self):
        """
        Respond to the signal emitted by the self.lineEdit_{setting} LineEdit edited by the user by calling self.update_table(self.sender.objectName()) to update self.view_tab to reflect changes made to LineEdits in other tabs.
        """
        sbutton = self.sender()
        self.update_table(sbutton.objectName())

    def populate_reference(self,buttoned):
        """
        Populate the appropriate reference TextBrowser with the definition, description, and default values of the appropriate setting as indicated by the suffix of the ToolButton's objectName(), e.g. "help_{setting}" from Plethysmography.rc_config (reference_config.json).
        """
        for k,v in self.widgy.items():
            for vv in v:
                if vv.objectName() == str(buttoned):
                    k.setPlainText(self.pleth.rc_config['References']['Definitions'][buttoned.replace("help_","")])
                    k.setOpenExternalLinks(True)
   
    def populate_table(self,frame,table):
        """
        Populate self.view_tab (TableWidget) with the self.basic_df dataframe.

        Parameters
        --------
        frame: Dataframe
            This variable refers to the self.basic_df dataframe.
        table: QTableWidget
            This variable refers to self.view_tab (TableWidget).

        Outputs
        --------
        self.view_tab: QTableWidget
            The TableWidget is populated by the contents of the self.basic_df dataframe, assigned cellChanged signals slotted to self.update_tabs, and cell dimensions adjusted to accommodate the text.
        """
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

    def update_table(self, donor: QObject.objectName):
        """
        Update self.view_tab (TableWidget) to reflect changes to LineEdits.

        Parameters
        --------
        donor: QObject.objectName
            This variable is the objectName of the LineEdit that emitted the signal self.update_table_event that called this method. Its suffix is used to identify the appropriate cell in self.view_tab (TableWidget).
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.
        self.view_tab: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.

        Outputs
        --------
        self.view_tab: QTableWidget
            The cell that contains the value of the setting that was updated by the user editing a LineEdit is updated to reflect the edit.
        """
        print("basic.update_table()")
        # The first loop grabs the widget with the text we need because donor is passed to this method as a QObject.objectName(), not the actual object.
        for l in self.lineEdits:
            if donor == l.objectName():
                d = l
        for row in range(self.view_tab.rowCount()):
            if self.view_tab.item(row,0).text() == donor.replace("lineEdit_",""):
                self.view_tab.item(row,1).setText(d.text())
        
    def update_tabs(self):
        """
        Update the LineEdits to reflect changes to self.view_tab (TableWidget).

        Parameters
        --------
        self.view_tab: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.
        
        Outputs
        --------
        self.lineEdit_{settings}: QLineEdit
            The LineEdit whose objectName suffix matches the setting that was edited by the user in self.view_tab (TableWidget) is updated to reflect the edit.
        """
        print("basic.update_tabs()")
        for row in range(self.view_tab.rowCount()):
            for l in self.lineEdits:
                if self.view_tab.item(row,0).text() == l.objectName().replace("lineEdit_",""):
                    l.setText(self.view_tab.item(row,1).text())

    def reset_parameter(self,butts):
        """
        Revert the settings to its corresponding default value in the basic BASSPRO settings stored in the self.basic_dict.

        Parameters
        --------
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.
        self.basic_df: Dataframe
            This attribute stores a dataframe derived either from self.basic_dict or from the .csv file indicated by the user-selected file path (self.basicap).

        Outputs
        --------
        self.lineEdit_{settings}: QLineEdit
            The LineEdit whose objectName suffix matches the setting that was edited by the user in self.view_tab (TableWidget) is updated to reflect the edit.
        """
        print("basic.reset_parameter()")
        for widget in self.lineEdits:
            if widget.objectName().replace("lineEdit_","") == str(butts).replace("reset_",""):
                widget.setText(str(self.basic_dict[self.lineEdits[widget]]))

    def get_parameter(self):
        """
        Scrape the values of the LineEdits to update the "current" dictionary in the basic BASSPRO settings dictionary in Plethysmography.bc_config.

        Parameters
        --------
        Plethysmography.bc_config: dict
            This attribute is a nested dictionary loaded from breathcaller_config.json. It contains the default settings of multiple experimental setups for basic, automated, and manual BASSPRO settings and  the most recently saved settings for automated and basic BASSPRO settings. See the README file for more detail.
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.

        Outputs
        --------
        self.basic_df: Dataframe
            This attribute stores a dataframe made from the "current" dictionary that was updated with the values of the corresponding LineEdits.
        """
        print("basic.get_parameter()")
        for k,v in self.lineEdits.items():
            self.pleth.bc_config['Dictionaries']['AP']['current'].update({v:k.text()})
        self.basic_df = pd.DataFrame.from_dict(self.pleth.bc_config['Dictionaries']['AP']['current'],orient='index').reset_index()
        self.basic_df.columns = ['Parameter','Setting']
    
    def save_checker(self,folder,title):
        """
        Check the existence of the file being saved and the directory it's being saved to - if an output folder has not been selected, prompt the user to save as via FileDialog. 

        Parameters
        --------
        folder: str
            The directory in which the .csv file for basic BASSPRO settings will be saved.
        title: str
            The name of the file being saved.
        path: str
            This variable stores the path of the file the user saved via the FileDialog.
        
        Outputs
        --------
        self.path: str
            The path of the file being saved.
        """
        print("basic.save_checker()")
        if folder == "":
            path = QFileDialog.getSaveFileName(self, 'Save BASSPRO basic parameters file', f"basics", ".csv(*.csv))")[0]
            if os.path.exists(path):
                self.path = path
        else:
            self.path = os.path.join(folder, f"{title}.csv")
    
    def saveas_basic_path(self):
        """
        Call self.get_parameter(), prompt the user to save as via FileDialog, and then call self.actual_saving().

        Parameters
        --------
        path: str
            The file path selected by the user via FileDialog.
        
        Outputs
        --------
        self.path: str
            This attribute stores the file path selected by the user via FileDialog.

        Outcomes
        --------
        self.get_parameter()
            Scrape the values of the LineEdits to update the "current" dictionary in the basic BASSPRO settings dictionary in Plethysmography.bc_config.
        self.actual_saving()
            Write self.basic_df dataframe to a .csv file, dump the nested dictionary stored in Plethysmography.bc_config to breathcaller_config.json to save changes made to the "current" dictionary in the basic BASSPRO settings dictionary in Plethysmography.bc_config, and add the file path self.basicap to the ListWidget self.sections_list for display in the main GUI.
        """
        print("basic.saveas_basic_path()")
        self.get_parameter()
        path = QFileDialog.getSaveFileName(self, 'Save BASSPRO basic parameters file', f"basics", ".csv(*.csv))")[0]
        try:
            self.path = path
            self.actual_saving()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            print("saveas_basic_path didn't work")

    def save_basic_path(self):
        """
        Call self.get_parameter to update "current" dictionary in Plethysmography.bc_config, check the existence of a user-selected output directory - if an output folder has not been selected, call self.saveas_basic_path() to prompt the user to save as via FileDialog, check the existance of the file path, and call self.actual_saving(). 

        Parameters
        --------
        path: str
            This variable stores the file path automatically generated based on the user-selected output directory.
        
        Outputs
        --------
        self.path: str
            This attribute stores the file path automatically generated based on the user-selected output directory.
        
        Outcomes
        --------
        self.get_parameter()
            Scrape the values of the LineEdits to update the "current" dictionary in the basic BASSPRO settings dictionary in Plethysmography.bc_config.
        self.saveas_basic_path()
            Call self.get_parameter(), prompt the user to save as via FileDialog, and then call self.actual_saving().
        self.actual_saving()
            Write self.basic_df dataframe to a .csv file, dump the nested dictionary stored in Plethysmography.bc_config to breathcaller_config.json to save changes made to the "current" dictionary in the basic BASSPRO settings dictionary in Plethysmography.bc_config, and add the file path self.basicap to the ListWidget self.sections_list for display in the main GUI.
        """
        print("basic.save_basic_path()")
        self.get_parameter()
        if self.pleth.mothership == "":
            self.saveas_basic_path()
        else:
            path = os.path.join(self.pleth.mothership, f"basics.csv")
        if not path:
            print("dialog cancelled")
        else:
            self.path = path
            self.actual_saving()
    
    def actual_saving(self):
        """
        Write self.basic_df dataframe to a .csv file, dump the nested dictionary stored in Plethysmography.bc_config to breathcaller_config.json to save changes made to the "current" dictionary in the basic BASSPRO settings dictionary in Plethysmography.bc_config, and add the file path self.basicap to the ListWidget self.sections_list for display in the main GUI.

        Parameters
        --------
        self.path: str
            This attribute stores the file path automatically generated based on the user-selected output directory.
        Plethysmography.basicap: str
            This Plethysmography class attribute stores the file path of the .csv file that the basic BASSPRO settings are saved to.
        self.basic_df: Dataframe
            This attribute stores a dataframe made from the "current" dictionary that was updated with the values of the corresponding LineEdits.
        Plethysmography.bc_config: dict
            This Plethysmography class attribute is a nested dictionary loaded from breathcaller_config.json. It contains the default settings of multiple experimental setups for basic, automated, and manual BASSPRO settings and  the most recently saved settings for automated and basic BASSPRO settings. See the README file for more detail.
        Plethysmography.sections_list: QListWidget
            This Plethysmography class ListWidget displays the file paths of the .csv files defining the BASSPRO settings.
        Plethysmography.hangar: QTextEdit
            This TextEdit displays feedback on user activity and feedback on BASSPRO or STAGG processing.

        Outputs
        --------
        Plethysmography.basicap: str
            This Plethysmography class attribute stores the file path of the .csv file that the basic BASSPRO settings are saved to.
        Plethysmography.sections_list: QListWidget
            This Plethysmography class ListWidget is updated to display the path to the basic BASSPRO settings .csv file.
        Plethysmography.hangar: QTextEdit
            This TextEdit is updated to describe the user's activity.
        
        basic.csv: CSV file
            The .csv file that the basic BASSPRO settings are saved to.
        breathcaller_config.json: JSON file
            The JSON file that the updated Plethysmography.bc_config dictionary is dumped to.
        """
        print("basic.actual_saving_basic()")
        self.pleth.basicap = self.path
        # Saving the dataframes holding the configuration preferences to csvs and assigning them their paths:
        try:
            self.basic_df.set_index('Parameter').to_csv(self.pleth.basicap)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
    
        with open(f'{Path(__file__).parent}/breathcaller_config.json','w') as bconfig_file:
            json.dump(self.pleth.bc_config,bconfig_file)
        
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
        """
        Prompt the user to indicate the location of a previously made file - either .csv, .xlsx, or .json formatted file - detailing the basic BASSPRO settings of a previous run, populate self.basic_df with a dataframe from that file, call self.populate_table(), and warn the user if they chose files in formats that are not accepted and ask if they would like to select a different file.

        Parameters
        --------
        file: QFileDialog
            This variable stores the path of the file the user selected via the FileDialog.
        yes: int
            This variable is used to indicate whether or not self.basic_df was successfully populated with a dataframe from the user-selected file.
        Plethysmography.mothership: str
            The path to the user-selected directory for all output.
        self.basic_df: Dataframe
            This attribute stores a dataframe derived from the .csv file indicated by the user-selected file path (Plethysmography.basicap).
        self.view_tab: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        reply: QMessageBox
            This specialized dialog communicates information to the user.

        Outputs
        --------
        self.basic_df: Dataframe
            This attribute stores a dataframe derived from the .csv file indicated by the user-selected file path (Plethysmography.basicap).
        self.view_tab: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        
        Outcomes
        --------
        self.populate_table()
            Populate self.view_tab (TableWidget) with the self.basic_df dataframe.
        self.load_basic_file()
            Prompt the user to indicate the location of a previously made file - either .csv, .xlsx, or .json formatted file - detailing the basic BASSPRO settings of a previous run, populate self.basic_df with a dataframe from that file, call self.populate_table(), and warn the user if they chose files in formats that are not accepted and ask if they would like to select a different file.
        """
        print("basic.load_basic_file()")
        # Opens open file dialog
        yes = 0
        file = QFileDialog.getOpenFileName(self, 'Select breathcaller configuration file to edit basic parameters:', str(self.pleth.mothership))
        if os.path.exists(file[0]):
            try:
                if Path(file[0]).suffix == ".json":
                    with open(file[0]) as config_file:
                        basic_json = json.load(config_file)
                    self.basic_df = pd.DataFrame.from_dict(basic_json['Dictionaries']['AP']['current'],orient='index').reset_index()
                    self.basic_df.columns = ['Parameter','Setting']
                    yes = 1
                elif Path(file[0]).suffix == ".csv":
                    self.basic_df = pd.read_csv(file[0])
                    yes = 1
                elif Path(file[0]).suffix == ".xlsx":
                    self.basic_df = pd.read_excel(file[0])
                    yes = 1
                if yes == 1:
                    self.populate_table(self.basic_df,self.view_tab)
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
                reply = QMessageBox.information(self, 'Incorrect file format', 'The selected file is not in the correct format. Only .csv, .xlsx, or .JSON files are accepted.\nWould you like to select a different file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                if reply == QMessageBox.Ok:
                    self.load_basic_file()
        
#endregion

#region class Auto Sections
class Auto(QWidget, Ui_Auto):
    """
    The Auto class defines the the properties, attributes, and methods used by the automated BASSPRO settings subGUI.

    Parameters
    --------
    QWidget: class
        The Basic class inherits properties and methods from the QWidget class. 
    Ui_Auto: class
        The Auto class inherits widgets and layouts defined in the Ui_Auto class.
    """
    def __init__(self,Plethysmography):
        """
        Instantiate the Auto class.

        Parameters
        --------
        Plethysmography: class
            The Auto class inherits properties, attributes and methods of the Plethysmography class.
        Plethysmography.bc_config: dict
            This Plethysmography class attribute is a nested dictionary loaded from breathcaller_config.json. It contains the default settings of multiple experimental setups for basic, automated, and manual BASSPRO settings and  the most recently saved settings for automated and basic BASSPRO settings. See the README file for more detail.
        Plethysmography.rc_config: dict
            This attribute is a shallow dictionary loaded from reference_config.json. It contains definitions, descriptions, and recommended values for every basic, manual, and automated BASSPRO setting.
        self.{tab}_reference: QTextBrowser
            These widgets display the definition, description, and default value of the user-selected setting. There is a TextBrowser for each of the first four tabs of the subGUI.
        self.help_{setting}: QToolButton
            These are buttons intended to provide helpful information to the user about the relevant setting.
        self.auto_setting_combo: QComboBox
            A comboBox that serves as a drop-down menu of the available experimental setups to choose the appropriate default settings.

        Outputs
        --------
        self.pleth: class
            Shorthand for the Plethysmography class.
        self.refs: dict
            This dictionary relates the self.help_{setting} ToolButtons with the appropriate self.{tab}_reference TextBrowser.
        self.help_{setting}: QToolButton
            These buttons are assigned clicked signals and slotted for self.reference_event().
        self.auto_setting_combo: QComboBox
            A comboBox that is populated with the experimental setups for which the GUI has default automated BASSPRO settings. These experimental setups are sourced from the keys of the "default" dictionary nested in the "Auto Settings" dictionary from Plethysmography.bc_config.
        
        Outcomes
        --------
        self.choose_dict()
            This method populates the automated BASSPRO settings subGUI widgets with default values derived from Plethysmography.bc_config (breathcaller_config.json).
        """
        super(Auto, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Automated sections file creation")
        self.pleth = Plethysmography
        self.isMaximized()

        self.refs = {self.sections_reference:[self.help_key,self.help_cal_seg,self.help_auto_ind_include,self.help_auto_ind_injection,self.help_startpoint,self.help_midpoint,self.help_endpoint],
        self.cal_reference:[self.help_auto_ind_cal,self.help_auto_ind_gas_cal,self.help_cal_co2,self.help_cal_o2],
        self.thresh_reference: [self.help_min_co2,self.help_max_co2,self.help_min_o2,self.help_max_calibrated_TV,self.help_max_VEVO2,self.help_max_o2,self.help_within_start,self.help_within_end,self.help_after_start,self.help_before_end],
        self.inc_reference: [self.help_min_TT,self.help_max_TT,self.help_max_dvtv,self.help_X,self.help_max_pX,self.help_vol_mov_avg_drift,self.help_min_tv,self.help_min_bout,self.help_include_apnea,self.help_include_sigh,self.help_include_high_chamber_temp]}

        for v in self.refs.values():
            for vv in v:
                vv.clicked.connect(self.reference_event)

        self.auto_setting_combo.addItems([x for x in self.pleth.bc_config['Dictionaries']['Auto Settings']['default'].keys()])
        self.choose_dict()

    def choose_dict(self):
        """
        This method populates the automated BASSPRO settings subGUI widgets with default values derived from Plethysmography.bc_config (breathcaller_config.json).

        Parameters
        --------
        self.auto_setting_combo: QComboBox
            A comboBox that is populated with the experimental setups for which the GUI has default automated BASSPRO settings. These experimental setups are sourced from the keys of the "default" dictionary nested in the "Auto Settings" dictionary from Plethysmography.bc_config.
        
        Outputs
        --------
        self.auto_dict: dict
            This attribute stores the nested dictionary in Plethysmography.bc_config that contains the default automated BASSPRO settings of multiple experimental setups.
        self.frame: Dataframe
            This attribute stores the dataframe converted from self.auto_dict.
        
        Outcomes
        --------
        self.setup_tabs()
            This method populates the automated BASSPRO settings subGUI widgets with default values of the experimental setup derived from Plethysmography.bc_config (breathcaller_config.json).
        """
        print("auto.choose_dict()")
        # Get the appropriate template based on user's choice of experimental condition:
        if self.auto_setting_combo.currentText() in self.pleth.bc_config['Dictionaries']['Auto Settings']['default'].keys():
            self.auto_dict = self.pleth.bc_config['Dictionaries']['Auto Settings']['default'][self.auto_setting_combo.currentText()]
        else:
            self.auto_dict = self.pleth.bc_config['Dictionaries']['Auto Settings']['default']['5% Hypercapnia']
            self.auto_setting_combo.setCurrentText('5% Hypercapnia')
        self.frame = pd.DataFrame(self.auto_dict).reset_index()
        self.setup_tabs()

    def setup_tabs(self):
        """
        This method populates the automated BASSPRO settings subGUI widgets with default values of the experimental setup derived from Plethysmography.bc_config (breathcaller_config.json).
        
        Parameters
        --------
        self.pleth.gui_config: dict
            This attribute is a nested dictionary loaded from gui_config.json. It contains paths to the BASSPRO and STAGG modules and the local Rscript.exe file, the fields of the database accessed when building a metadata file, and settings labels used to organize the populating of the TableWidgets in the BASSPRO settings subGUIs. See the README file for more detail.
        self.frame: Dataframe
            This attribute stores the dataframe converted from self.auto_dict.
        self.{division}_table: QTableWidget
            These TableWidgets display the automated BASSPRO settings is in the appropriate TableWidgets over multiple tabs.
        self.view_tab: QTableWidget
            The TableWidget displays the automated BASSPRO settings in one table on the fifth tab.
        
        Outcomes
        --------
        self.populate_table(frame,table)
            This method populates the self.{division}_table widgets with the appropriate portions of the self.frame dataframe based on the relationship of particular rows to particular divisions as defined in the "Settings Names" dictionary within self.pleth.gui_config.
        """
        print("auto.setup_tabs()")
        # Populate table of threshold tab:
        auto_labels = self.pleth.gui_config['Dictionaries']['Settings Names']['Auto Settings']
        sec_char_df = self.frame.loc[(self.frame['index'].isin(auto_labels['Section Characterization']['Section Identification and Settings'].values())),:]
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
    
    def reference_event(self):
        """
        Respond to the signal emitted by the self.help_{setting} ToolButton clicked by the user by calling self.populate_reference(self.sender.objectName()) to populate the appropriate TextBrowser with the definition, description, and default value of corresponding setting.
        """
        sbutton = self.sender()
        self.populate_reference(sbutton.objectName())

    def populate_reference(self,buttoned):
        """
        Populate the appropriate reference TextBrowser with the definition, description, and default values of the appropriate setting as indicated by the suffix of the ToolButton's objectName(), e.g. "help_{setting}" from Plethysmography.rc_config (reference_config.json).
        """
        for k,v in self.refs.items():
            for vv in v:
                if vv.objectName() == str(buttoned):
                    k.setPlainText(self.pleth.rc_config['References']['Definitions'][buttoned.replace("help_","")])
   
    def populate_table(self,frame,table):
        """
        This method populates the self.{division}_table widgets with the appropriate portions of the self.frame dataframe based on the relationship of particular rows to particular divisions as defined in the "Settings Names" dictionary within self.pleth.gui_config.

        Parameters
        --------
        frame: Dataframe
            This variable refers to the appropriate portion of the self.frame dataframe.
        table: QTableWidget
            This variable refers to the appropriate self.{division}_table.

        Outputs
        --------
        self.{division}_table: QTableWidget
            The TableWidget referred to by the argument "table" is populated with the appropriate settings from self.frame dataframe as contained in the argument "frame".
        """
        print("auto.populate_table()")
        # Populate tablewidgets with views of uploaded csv. Currently editable.
        table.setColumnCount(len(frame.columns))
        table.setRowCount(len(frame))
        for col in range(table.columnCount()):
            for row in range(table.rowCount()):
                table.setItem(row,col,QTableWidgetItem(str(frame.iloc[row,col])))
        table.setHorizontalHeaderLabels(frame.columns)
        table.resizeColumnsToContents()
        table.resizeRowsToContents()

    def save_as(self):
        """
        Prompt the user to select a file path to save the .csv file of the automated BASSPRO settings to.

        Parameters
        --------
        path: str
            This variable stores the file path selected by the user to which the .csv file of the automated BASSPRO settings wll be saved.

        Outputs
        --------
        self.path: str
            This attribute stores the file path.
        
        Outcomes
        --------
        self.save_auto_file()
            This methods writes the contents of the self.view_tab TableWidget to .csv file as indicated in the file path self.pleth.auto_sections, calls self.pleth.update_breath_df(), and adds self.pleth.auto_sections to self.pleth.sections_list (ListWidget) for display in the main GUI. 
        """
        print("auto.save_as()")
        path = QFileDialog.getSaveFileName(self, 'Save File', "auto_sections", ".csv(*.csv))")[0]
        if os.path.exists(path):
            self.path = path
            self.save_auto_file()
    
    def save_checker(self):
        """
        Ensure the existence of a user-selected output directory, prompt the user to select one if they have not, and call self.save_auto_file().

        Parameters
        --------
        self.pleth.mothership: str
            The path to the user-selected directory for all output.
        path: str
            This variable stores the file path selected by the user to which the .csv file of the automated BASSPRO settings wll be saved.

        Outputs
        --------
        self.path: str
            This attribute stores the file path.

        Outcomes
        --------
        self.save_auto_file()
            This methods writes the contents of the self.view_tab TableWidget to .csv file as indicated in the file path self.pleth.auto_sections, calls self.pleth.update_breath_df(), and adds self.pleth.auto_sections to self.pleth.sections_list (ListWidget) for display in the main GUI.
        """
        print("auto.save_checker()")
        if self.pleth.mothership == "":
            path = QFileDialog.getSaveFileName(self, 'Save File', "auto_sections", ".csv(*.csv))")[0]
            if os.path.exists(path):
                self.path = path
                self.save_auto_file()
        else:
            self.path = os.path.join(self.pleth.mothership, "auto_sections.csv")
            self.save_auto_file()

    def save_auto_file(self):
        """
        Write the contents of the self.view_tab TableWidget to .csv file as indicated in the file path self.pleth.auto_sections, call self.pleth.update_breath_df(), and add self.pleth.auto_sections to self.pleth.sections_list (ListWidget) for display in the main GUI. 

        Parameters
        --------
        self.path: str
            This attribute stores the file path selected by the user to which the .csv file of the automated BASSPRO settings wll be saved.
        self.pleth.breath_df: list
            This Plethysmography class attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        self.view_tab: QTableWidget
            The TableWidget displays the automated BASSPRO settings in one table on the fifth tab.
        self.pleth.autosections: str
            This Plethysmography class attribute is either an empty string or stores a file path.

        Outputs
        --------
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        self.pleth.autosections: str
            This attribute is updated with self.path, the file path to the .csv file of automated BASSPRO settings.
        self.pleth.sections_list: QListWidget
            This Plethysmography class ListWidget displays the file paths of the .csv files defining the BASSPRO settings. It is updated to display self.pleth.autosections.
        autosections.csv: CSV file
            The .csv file that the automated BASSPRO settings are saved to.
        
        Outcomes
        --------
        self.update_breath_df()
            This Plethysmography class method updates the Plethysmography class attribute self.pleth.breath_df to reflect the changes to the metadata.
        """
        print("auto.save_auto_file()")
        self.pleth.autosections = self.path
        try:
        # Saving the dataframes holding the configuration preferences to csvs and assigning them their paths:
            with open(self.pleth.autosections,'w',newline = '') as stream:
                    writer = csv.writer(stream)
                    header = []
                    for row in range(self.view_tab.rowCount()):
                        item = self.view_tab.item(row,0)
                        if item.text() == "nan":
                            header.append("")
                        else:
                            header.append(item.text())
                    for column in range(self.view_tab.columnCount()):
                        coldata = []
                        for row in range(self.view_tab.rowCount()):
                            item = self.view_tab.item(row, column)
                            if item.text() == "nan":
                                coldata.append("")
                            else:
                                coldata.append(item.text())
                        writer.writerow(coldata)
            # This is ridiculous.
            auto = pd.read_csv(self.pleth.autosections)
            auto['Key'] = auto['Alias']
            auto.to_csv(self.pleth.autosections,index=False)
            if self.pleth.breath_df != []:
                self.pleth.update_breath_df("automated settings")

            # Clearing the sections panel of the mainGUI and adding to it to reflect changes:
            for item in self.pleth.sections_list.findItems("auto_sections",Qt.MatchContains):
                self.pleth.sections_list.takeItem(self.pleth.sections_list.row(item))
            self.pleth.sections_list.addItem(self.pleth.autosections)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            if type(e) == PermissionError:
                reply = QMessageBox.information(self, 'File in use', 'One or more of the files you are trying to save is open in another program.', QMessageBox.Ok)

    def load_auto_file(self):
        """
        Prompt the user to indicate the location of a previously made file - either .csv, .xlsx, or .json formatted file - detailing the basic BASSPRO settings of a previous run, populate self.basic_df with a dataframe from that file, call self.populate_table(), and warn the user if they chose files in formats that are not accepted and ask if they would like to select a different file.

        Parameters
        --------
        file: QFileDialog
            This variable stores the path of the file the user selected via the FileDialog.
        yes: int
            This variable is used to indicate whether or not self.basic_df was successfully populated with a dataframe from the user-selected file.
        Plethysmography.mothership: str
            The path to the user-selected directory for all output.
        self.basic_df: Dataframe
            This attribute stores a dataframe derived from the .csv file indicated by the user-selected file path (Plethysmography.basicap).
        self.view_tab: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        reply: QMessageBox
            This specialized dialog communicates information to the user.

        Outputs
        --------
        self.basic_df: Dataframe
            This attribute stores a dataframe derived from the .csv file indicated by the user-selected file path (Plethysmography.basicap).
        self.view_tab: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        
        Outcomes
        --------
        self.setup_tabs()
            This method populates the automated BASSPRO settings subGUI widgets with default values of the experimental setup derived from Plethysmography.bc_config (breathcaller_config.json).
        """
        print("auto.load_auto_file()")
        # Opens open file dialog
        file = QFileDialog.getOpenFileName(self, 'Select automatic selection file to edit:', str(self.pleth.mothership))
        try:
            self.frame = pd.read_csv(file[0],index_col='Key').transpose().reset_index()
            self.setup_tabs()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())

#endregion

#region class Manual Sections
# YOu need to make the columns reflect the headers of the dataframes
class Manual(QWidget, Ui_Manual):
    def __init__(self,Plethysmography):
        """
        Instantiates the Manual class.
        
        Parameters
        --------
        Plethysmography: class
            The Manual class inherits Plethysmography's methods, attributes, and widgets.
        Ui_Manual: class
            The Manual class inherits the widget and layouts of the manual BASSPRO settings subGUI of the Ui_Manual class.
        
        Outputs
        --------
        self.pleth: class
            Shorthand for the Plethysmography class.
        self.datapad: Dataframe | None
            This attribute is set as None.
        self.preset: Dataframe | None
            This attribute is set as None.
        self.manual_df: Dataframe | str
            This attribute is set as an empty string.
        self.vals: list
            This attribute is a list of the headers of the dataframe in the .txt files produced when exporting the LabChart Datapad views of the signal files the user wants to analyze.
        """
        super(Manual, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Manual sections file creation")
        self.pleth = Plethysmography
        self.isMaximized()
        self.datapad = None
        self.preset = None
        self.manual_df = ""
        self.vals = ['animal id','PLYUID','start','stop','duration','mFrequency_Hz','mPeriod_s','mHeight_V','mO2_V','mCO2_V','mTchamber_V','segment']

    def get_datapad(self):
        """
        Retrieve and concatenate the user-selected .txt files produced when exporting the LabChart Datapad views of the user-selected signal files to be analyzed in BASSPRO.

        Parameters
        --------
        file: QFileDialog
            This variable stores the paths of the files the user selected via the FileDialog.
        self.datapad_view: QTableWidget
            This TableWidget is inherited from Ui_Manual and displays the dataframe formed when the user-selected LabChart Datapad view exports are concatenated.

        Outputs
        --------
        self.datapad: Dataframe
            This attribute stores the dataframe produced by concatenating the dataframes read in from each exported LabChart Datapad view of the signal files selected by the user.
        Thumbass: class
            This dialog gives the user information. It appears when an error is thrown while creating the self.datapad dataframe.
        self.datapad_view: QTableWidget
            This TableWidget is populated with self.datapad.
        
        Outcomes
        --------
        self.populate_table(self.datapad, self.datapad_view)
            This method populates self.datapad_view (TableWidget) with the self.datapad dataframe.
        """
        print("manual.get_datapad()")
        file = QFileDialog.getOpenFileNames(self, 'Select Labchart datapad export file')
        if os.path.exists(file[0]):
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
                    bob=dc[dc['start'].isna()][['animal id','PLYUID']].drop_duplicates()
                    if self.pleth.signals != []:
                        for file in self.pleth.signals:
                            print(f"{bob['animal id']}_{bob['PLYUID']}")
                self.datapad = dc
                self.populate_table(self.datapad, self.datapad_view)
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
                self.thumb = Thumbass(self)
                self.thumb.show()
                self.thumb.message_received(f"{type(e).__name__}: {e}",f"Please ensure that the datapad is formatted as indicated in the documentation.\n\n{traceback.format_exc()}")

    def get_preset(self):
        """
        Retrieve the default settings for the experimental setup selected by the user in the self.preset_menu comboBox from the corresponding dictionary in self.pleth.bc_config (dict).

        Parameters
        --------
        self.preset_menu: QComboBox
            A comboBox of the Manual class inherited from Ui_Manual that is populated with the experimental setups for which the GUI has default manual BASSPRO settings that will be concatenated with the user's manual selections of breaths to produce the final manual_sections.csv file. These experimental setups are sourced from the keys of the "default" dictionary nested in the "Manual Settings" dictionary loaded from the breathcaller_config.json file.
        self.pleth.bc_config: dict
            This Plethysmography class attribute is a nested dictionary loaded from breathcaller_config.json. It contains the default settings of multiple experimental setups for basic, automated, and manual BASSPRO settings and  the most recently saved settings for automated and basic BASSPRO settings. See the README file for more detail.
        self.settings_view: QTableWidget
            This TableWidget is inherited from Ui_Manual and displays the dataframe formed from the dictionary selected.
        
        Outputs
        --------
        self.preset: Dataframe
            This attribute is the dataframe formed from the dictionary from self.pleth.bc_config (dict) based on the user's selection of experimental setup in self.preset_menu (ComboBox).
        self.settings_view: QTableWidget
            This TableWidget is populated with the dataframe formed from the dictionary selected. 
        
        Outcomes
        --------
        self.populate_table(self.preset, self.settings_view)
            This method populates self.settings_view (TableWidget) with the self.preset dataframe.
        """
        print("manual.get_preset()")
        self.preset = pd.DataFrame.from_dict(self.pleth.bc_config['Dictionaries']['Manual Settings']['default'][self.preset_menu.currentText()].values())
        self.populate_table(self.preset, self.settings_view)    
    
    def manual_merge(self):
        """
        Merge the dataframes in self.datapad and self.preset to form self.manual_df (dataframe) and populate self.manual_view (TableWidget) with the new dataframe.

        Parameters
        --------
        self.datapad: Dataframe | None
            This attribute stores the dataframe produced by concatenating the dataframes read in from each exported LabChart Datapad view of the signal files selected by the user.
        self.preset: Dataframe | None
            This attribute is the dataframe formed from the dictionary from self.pleth.bc_config (dict) based on the user's selection of experimental setup in self.preset_menu (ComboBox).
        self.manual_view: QTableWidget
            This TableWidget is inherited from Ui_Manual and displays the self.manual_df dataframe.
        
        Outputs
        --------
        Thorbass: class
            Specialized dialog that guides the user through the process of selecting the necessary files.
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        self.manual_df: Dataframe
            This attribute stores the dataframe formed by merging the dataframes of self.datapad and self.preset.
        self.manual_view: QTableWidget
            This TableWidget is populated with the self.manual_df dataframe.
        
        Outcomes
        --------
        self.populate_table(self.manual_df, self.manual_view)
            This method populates self.manual_view (TableWidget) with the self.manual_df dataframe.
        self.get_datapad()
            This method is triggered if self.datapad is None but self.preset has a dataframe.
        self.new_manual_file()
            This method is one of two that can be selected by the user in the Thorbass dialog.
        self.load_manual_file()
            This methods one of two that can be selected by the user in the Thorbass dialog.
        """
        print("manual.manual_merge()")
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
         
    def new_manual_file(self):
        """
        Guide user through selecting LabChart Datapad view exported .txt files and/or an experimental setup from the drop-down menu. 
        """
        print("manual.new_manual_file()")
        if self.datapad == None:
            reply = QMessageBox.information(self, 'Missing datapad file', 'You need to select a LabChart datapad exported as a text file. Would you like to select a file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Yes:
                self.get_datapad()
        if self.preset == None:
            reply = QMessageBox.information(self, 'Missing sections settings', 'Please select one of the options from the dropdown menu above.', QMessageBox.Ok)

    def populate_table(self,frame,view):
        """
        Populate the TableWidget with the dataframe.

        Parameters
        --------
        frame: Dataframe
        view: QTableWidget

        Outputs
        --------
        view: QTableWidget
            The view TableWidget is populated with the frame dataframe.
        """
        print("manual.populate_table()")
        # Populate tablewidgets with views of uploaded csv. Currently editable.
        view.setColumnCount(len(frame.columns))
        view.setRowCount(len(frame))
        for col in range(view.columnCount()):
            for row in range(view.rowCount()):
                view.setItem(row,col,QTableWidgetItem(str(frame.iloc[row,col])))
        view.setHorizontalHeaderLabels(frame.columns)

    def save_checker(self,folder,title):
        """
        Check the existence of the file being saved and the directory it's being saved to.

        Parameters
        --------
        folder: str
            The directory in which the manual_sections.csv file will be saved.
        title: str
            The name of the file being saved.
        path: str
            This variable stores the path of the file the user saved via the FileDialog.
        
        Outputs
        --------
        self.path: str
            The path of the file being saved.
        """
        print("manual.save_checker()")
        if folder == "":
            path = QFileDialog.getSaveFileName(self, 'Save File', f"{title}", ".csv(*.csv))")[0]
            if os.path.exists(path):
                self.path = path
        else:
            self.path = os.path.join(folder, f"{title}.csv")

    def save_manual_file(self):
        """
        Call self.save_check(), assign the file path determined in self.save_checker() to self.pleth.mansections (str), save self.manual_df dataframe as a .csv file to the file path location, populate self.pleth.sections_list (ListWidget) with the file path (self.pleth.mansections), and update self.breath_df (list).

        Parameters
        ---------
        self.path: str
            This variable stores the path of the file the user saved via the FileDialog in self.save_checker().
        self.pleth.mansections: str
            The path to the manual BASSPRO settings file. It is either an empty string or a file path.
        self.pleth.breath_df: list
            This Plethysmography class attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        self.manual_df: Dataframe
            This attribute stores the dataframe formed by merging the dataframes of self.datapad and self.preset.

        Outputs
        --------
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        self.pleth.mansections: str
            This attribute is updated with self.path, the file path to the .csv file of manual BASSPRO settings.
        self.pleth.sections_list: QListWidget
            This Plethysmography class ListWidget displays the file paths of the .csv files defining the BASSPRO settings. It is updated to display self.pleth.mansections.
        
        manual_sections.csv: CSV file
            The .csv file that the manual BASSPRO settings are saved to.
        
        Outcomes
        --------
        self.update_breath_df()
            This Plethysmography class method updates the Plethysmography class attribute self.pleth.breath_df to reflect the changes to the manual BASSPRO settings.
        """
        print("manual.save_manual_file()")
        try:
            self.save_checker(self.pleth.mothership,"manual_sections")
            self.pleth.mansections = self.path
        
        # Saving the dataframes holding the configuration preferences to csvs and assigning them their paths:
            self.manual_df.to_csv(self.pleth.mansections,index=False)

            if self.pleth.breath_df != []:
                self.pleth.update_breath_df("manual settings")
        
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
        """
        Read a user-selected, previously made manual BASSPRO settings .csv file, populate self.datapad, self.preset, and self.manual_df with their corresponding pieces of the dataframe, and populate the corresponding tables.

        Parameters
        --------
        file: QFileDialog
            This variable stores the paths of the file the user selected via the FileDialog.

        Outputs
        --------
        self.manual_df: Dataframe
            This attribute stores the dataframe derived from the user-selected .csv file storing previously made manual BASSPRO settings.
        self.datapad: Dataframe
            This attribute stores the dataframe produced by slicing self.manual_df dataframe to include only the columns with headers found in self.vals (list).
        self.preset: Dataframe
            This attribute stores the dataframe produced by slicing the self.manual_df dataframe to include the columns not included in self.datapad dataframe.
        
        Outcomes
        --------
        self.populate_table(self.datapad, self.datapad_view)
            This method populates self.datapad_view (TableWidget) with the self.datapad dataframe.
        self.populate_table(self.preset, self.settings_view)
            This method populates self.settings_view (TableWidget) with the self.preset dataframe.
        self.populate_table(self.manual_df, self.manual_view)
            This method populates self.manual_view (TableWidget) with the self.manual_df dataframe.
        """
        print("manual.load_manual_file()")
        file = QFileDialog.getOpenFileName(self, 'Select manual sections file to edit:')

        if os.path.exists(file[0]):
            try:
                self.manual_df = pd.read_csv(file[0])
                self.datapad = self.manual_df.loc[:,[x for x in self.vals]]
                self.preset = self.manual_df.loc[:,[x for x in self.manual_df.columns if x not in self.datapad.columns]].drop_duplicates()
                self.populate_table(self.manual_df,self.manual_view)
                self.populate_table(self.datapad, self.datapad_view)
                self.populate_table(self.preset, self.settings_view)
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
#endregion

class CheckableComboBox(QComboBox):
    # source: https://gis.stackexchange.com/questions/350148/qcombobox-multiple-selection-pyqt5

    # Subclass Delegate to increase item height
    class Delegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
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
                data = datalist[i]
            except Exception as e:
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
    """
    This class inherits widgets and layouts of Ui_Custom and defines the subGUI within the STAGG settings subGUI that allows users to customize the settings for each dependent variable.

    Parameters
    --------
    QWidget: class
        The Custom class inherits properties and methods from the QWidget class. 
    Ui_Custom: class
        The Custom class inherits widgets and layouts defined in the Ui_Custom class.
    """
    def __init__(self,Config):
        """
        Instantiate the Custom class.

        Parameters
        --------
        Config: class
            The Custom class inherits properties, attributes, and methods from the Config class.
        
        Outputs
        --------
        self.config: class
            Shorthand for the Config class.
        self.custom_alias: list
            This attribute is set as an empty list.
        self.ymin: list
            This attribute is set as an empty list.
        self.ymax: list
            This attribute is set as an empty list.
        self.custom_transform: list
            This attribute is set as an empty list.
        self.custom_poincare: list
            This attribute is set as an empty list.
        self.custom_spectral: list
            This attribute is set as an empty list.
        self.custom_irreg: list
            This attribute is set as an empty list.
        """
        super(Custom, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Custom graph settings configuration")
        self.config = Config
        self.isMaximized()
        self.custom_alias = []
        self.ymin = []
        self.ymax = []
        self.custom_transform = []
        self.custom_poincare = []
        self.custom_spectral = []
        self.custom_irreg = []

    def extract_variable(self):
        """
        Check if Config.deps (list) is empty. If it is, prompt a MessageBox informing the user. If it isn't, populate self.custom_table (TableWidget) using Config.deps.

        Parameters
        --------
        self.config.deps: list
            This list contains the Aliases of the dependent variables the user has selected in Config.variable_table (TableWidget).
        self.custom_table: QTableWidget
            This TableWidget displays the text and widgets that allows the user to customize the STAGG settings for each dependent variable on the main model.

        Outputs
        --------
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        self.custom_table: QTableWidget
            This TableWidget is populated based on the number of dependent variables selected by the user in Config.variable_table.
        
        Outcomes
        --------
        self.populate_table(self.config.deps, self.custom_table)
            This method populates self.custom_table TableWidget with rows corresponding to the items in the self.config.deps list.
        self.show()
            This method displays the STAGG settings subGUI.
        """
        print("custom.extract_variable()")
        if self.config.deps.empty:
            reply = QMessageBox.information(self, 'Choose variables', 'Please select response variables to be modeled.', QMessageBox.Ok)
        else:
            self.populate_table(self.config.deps,self.custom_table)
            self.adjustSize()
            self.show()

    def populate_table(self,frame: list,table: QTableWidget):
        """
        Populate an empty self.config.custom_dict as a nested dictionary based on the items in self.config.deps (list) or update an existing self.config.custom_dict by appending keys and establishing widgets, update self.config.custom_port if it's populated, and populate self.custom_table with the contents of self.config.custom_dict, with the number of rows corresponding to the number of items in self.config.deps.

        Parameters
        --------
        frame: list
            This argument passes self.config.deps, a list of user-selected dependent variables.
        table: QTableWidget
            This argument passes self.custom_table TableWidget.
        self.config.custom_dict: dict
            This attribute inherited from the Config class is either empty or a nested dictionary defining widgets.
        self.config.custom_port: dict
            This attribute inherited from the Config class is either empty or a deep copy of self.config.custom_dict.
        
        Outputs
        --------
        self.config.custom_dict: dict
            This attribute inherited from the Config class is either populated or updated to include newly-selected dependent variables.
        self.custom_table: QTableWidget
            This TableWidget is populated with the text and widgets stored in self.config.custom_dict.
        """
        print("custom started populating table")
        # Populate tablewidgets with dictionary holding widgets. 
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
                # Creating the combo boxes that will populate the cells in each row:
                self.config.custom_dict[item_1]["Transformation"]=CheckableComboBox()
                self.config.custom_dict[item_1]["Transformation"].addItems(["raw","log10","ln","sqrt"])
        for entry in self.config.custom_dict:    
            print("setting widgets in table")
            table.setItem(row,0,self.config.custom_dict[entry]["Alias"])
            table.item(row,0).setFlags(table.item(row,0).flags() ^ Qt.ItemIsEditable)
            table.setItem(row,1,self.config.custom_dict[entry]["ymin"])
            table.setItem(row,2,self.config.custom_dict[entry]["ymax"])
            
            table.setCellWidget(row,3,self.config.custom_dict[entry]["Transformation"])
            table.setCellWidget(row,4,self.config.custom_dict[entry]["Poincare"])
            table.setCellWidget(row,5,self.config.custom_dict[entry]["Spectral"])
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
        table.resizeColumnsToContents()
        table.resizeRowsToContents()

    def save_custom(self):
        """
        Save the contents of Config.custom_dict to Config.custom_port. Update the status of the comboBoxes corresponding to Poincare, Spectral, and Transformation settings made in the Custom subGUI.

        Parameters
        --------
        self.config.custom_dict: dict
            This attribute inherited from the Config class is either empty or a nested dictionary defining rows and corresponding widgets that will populate self.custom_table TableWidget.
        self.config.Poincare_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to produce Poincare plots for all or none of the selected dependent variables.
        self.config.Spectral_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to produce Spectral plots for all or none of the selected dependent variables.
        self.config.transform_combo: CheckableComboBox
            This CheckableComboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to run STAGG on different model transformations.
        
        Outputs
        --------
        self.config.custom_port: dict
            This nested dictionary is a deep copy of self.config.custom_port.
        self.config.Poincare_combo: QComboBox
            The comboBox in the STAGG settings subGUI that allows the user to choose to produce Poincare plots for all or none of the selected dependent variables is set to "Custom" to indicate customized settings regarding Poincare plots.
        self.config.Spectral_combo: QComboBox
            The comboBox in the STAGG settings subGUI that allows the user to choose to produce Spectral plots for all or none of the selected dependent variables is set to "Custom" to indicate customized settings regarding Poincare plots.
        
        self.
        """
        print("custom.save_custom()")
        self.config.custom_port = {item: {col: None for col in self.config.custom_dict[item]} for item in self.config.custom_dict}
        try:
            for item in self.config.custom_dict:
                for col in self.config.custom_dict[item]:
                    if "QTableWidgetItem" in str(type(self.config.custom_dict[item][col])):
                        self.config.custom_port[item].update({col:self.config.custom_dict[item][col].text()})
                    elif "QCheckBox" in str(type(self.config.custom_dict[item][col])):
                        self.config.custom_port[item].update({col:int(self.config.custom_dict[item][col].isChecked())})
                    elif "QComboBox" in str(type(self.config.custom_dict[item][col])):
                        self.config.custom_port[item].update({col:self.config.custom_dict[item][col].currentText()})
                    elif "CheckableComboBox" in str(type(self.config.custom_dict[item][col])):
                        self.config.custom_port[item].update({col:self.config.custom_dict[item][col].currentData()})
            for key,value in {self.config.Poincare_combo:"Poincare",self.config.Spectral_combo:"Spectral"}.items():
                if all([self.config.custom_port[var][value] == 1 for var in self.config.custom_port]):
                    key.setCurrentText("All")
                if any([self.config.custom_port[var][value] == 1 for var in self.config.custom_port]):
                    key.setCurrentText("Custom")
                else:
                    key.setCurrentText("None")
                
            if any(th for th in [self.config.custom_port[t]["Transformation"] for t in self.config.custom_port])==True:
                self.config.transform_combo.setCurrentText("Custom")
            else:
                self.config.transform_combo.setCurrentText("None")
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
        try:
            self.hide()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
        print(f"save_custom: {self.config.custom_port}")
            
#endregion

#region class Variable
class Config(QWidget, Ui_Config):
    """
    This class inherits widgets and layouts of Ui_Config and defines the STAGG settings subGUI that allows users to define the STAGG settings.
    """
    def __init__(self,Plethysmography):
        super(Config, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("STAGG Variable Configuration")
        self.pleth = Plethysmography
        self.isMaximized()
        self.deps = []
        
        self.setup_variables_config()
    
    def minus_loop(self):
        """
        Remove the selected row from self.loop_table and its corresponding data from self.pleth.loop_menu (dict).
        """
        print("config.minus_loop()")
        try:
            self.pleth.loop_menu[self.loop_table].pop(self.loop_table.currentRow())
            for p in self.pleth.loop_menu[self.loop_table]:
                if p > self.loop_table.currentRow():
                    self.pleth.loop_menu[self.loop_table][p-1] = self.pleth.loop_menu[self.loop_table].pop(p)
            self.loop_table.removeRow(self.loop_table.currentRow())
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
        
    def reference_event(self):
        """
        Respond to the signal emitted by the self.help_{setting} ToolButton clicked by the user by calling self.populate_reference(self.sender.objectName()) to populate the self.config_reference TextBrowser with the definition, description, and default value of corresponding setting.
        """
        sbutton = self.sender()
        self.populate_reference(sbutton.objectName())

    def populate_reference(self,buttoned: QObject.objectName):
        """
        Populate self.config_reference (TextBrowser) with the definition, description, and default values of the appropriate setting as indicated by the suffix of the ToolButton's objectName(), e.g. "help_{setting}" from Plethysmography.rc_config (reference_config.json).

        Parameters
        --------
        buttoned: QObject.objectName
            This variable is the objectName of the ToolButton that emitted the signal self.reference_event that called this method. Its suffix is used to identify the appropriate cell in self.view_tab (TableWidget).
        self.widgy: dict
            This attribute relates the self.help_{setting} ToolButtons to self.reference_config TableWidget.
        Plethysmography.rc_config: dict
            This attribute is a shallow dictionary loaded from reference_config.json. It contains definitions, descriptions, and recommended values for every basic, manual, and automated BASSPRO setting.

        Outputs
        --------
        self.config_reference: QTableWidget
            This TableWidget displays the definition, description, and default value of the user-selected setting.
        """
        for k,v in self.widgy.items():
            for vv in v:
                if vv.objectName() == str(buttoned):
                    k.setPlainText(self.pleth.rc_config['References']['Definitions'][buttoned.replace("help_","")])

    def no_duplicates(self):
        """
        Automatically rename the variable in the "Alias" column of self.variable_table (TableWidget) to avoid duplicate variable names.

        Parameters
        --------
        self.variable_table: QTableWidget
            This TableWidget displays the text and widgets needed to allow the user to indicate the type of a selected variable.
        """
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
        """
        Update the contents of self.clades_other_dict with the contents of self.pleth.loop_menu and then update the contents of self.loop_table with the newly updated contents of self.clades_other_dict.
        
        Parameters
        --------
        self.clades: Dataframe
            This attribute is a dataframe that containts the states of the self.variable_table widgets for each variable.
        self.loop_table: QTableWidget
            This TableWidget displays the settings for additional models either via widgets or loading previously made other_config.csv with previous STAGG run's settings for additional models.
        self.pleth.loop_menu: dict
            The nested dictionary used to populate and save the text, CheckBox, ComboBox, and CheckableComboBox states of Config.loop_table (TableWidget) in the Config subGUI.
        self.clades_other_dict: dict
            This dictionary is populated and updated with the current states of the widgets stored in self.pleth.loop_menu.
        
        Outputs
        --------
        self.deps: Series
            This attribute is a Series of the variables, specifically the "Alias" column of dataframe self.clades derived from self.variable_table.
        self.loop_table: QTableWidget
            This TableWidget is populated with the settings for additional models either via widgets or loading previously made other_config.csv with previous STAGG run's settings for additional models.
        self.clades_other_dict: dict
            This dictionary is populated and updated with the current states of the widgets stored in self.pleth.loop_menu.
        
        Outcomes
        --------
        self.show_loops(self.loop_table, len(self.clades_other_dict))
            Populate self.pleth.loop_menu with the appropriate widgets and populated self.loop_table with self.clades_other_dict.
        """
        print("config.update_loop()")
        try:
            self.classy()
            self.deps = self.clades["Alias"]
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
                self.clades_other_dict[row].update({"Y axis minimum": self.pleth.loop_menu[self.loop_table][row]["Y axis minimum"].text()})
                self.clades_other_dict[row].update({"Y axis maximum": self.pleth.loop_menu[self.loop_table][row]["Y axis maximum"].text()})

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
                if self.clades_other_dict[row_1]['Covariates'] != "":
                    self.pleth.loop_menu[self.loop_table][row_1]['Covariates'].loadCustom([w for w in self.clades_other_dict[row_1]['Covariates'].split('@')])
                    self.pleth.loop_menu[self.loop_table][row_1]['Covariates'].updateText()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())

    def setup_transform_combo(self):
        """
        Add widget from custom class CheckableComboBox to STAGG settings subGUI layout to serve as drop-down menu for data transformation options.
        """
        spacerItem64 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_25.addItem(spacerItem64)
        self.transform_combo = CheckableComboBox()
        self.transform_combo.addItems(["raw","log10","ln","sqrt","Custom","None"])
        self.verticalLayout_25.addWidget(self.transform_combo)
        spacerItem65 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_25.addItem(spacerItem65)

    def setup_variables_config(self): 
        """
        Add the CheckableComboBox to the STAGG settings subGUI layout and establish attributes.

        Parameters
        --------
        self.clades: Dataframe
            This attribute is a dataframe that containts the states of the self.variable_table widgets for each variable.
        self.clades_graph: Dataframe
            This attribute is a dataframe that containts the states of the many comboBoxes that define graph roles for selected variables.
        self.clades_other: Dataframe
            This attribute is a dataframe that containts the states of the self.loop_table widgets for each variable as well as the states for self.feature_combo comboBox..
        self.feature_combo: QCombobBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to produce plots of respiratory features such as sighs and apneas.
        self.Poincare_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to produce Poincare plots for all or none of the selected dependent variables.
        self.Spectral_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to produce Spectral plots for all or none of the selected dependent variables.
        self.transform_combo: CheckableComboBox
            This CheckableComboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to run STAGG on different model transformations.
        self.Xvar_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose which independent or covariate variable should determine the x axis of figures of the main model.
        self.Pointdodge_combbo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose which independent or covariate variable should determine the groups of symbol of figures of the main model.
        self.Facet1_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose which independent or covariate variable should determine the splitting of the x axis if at all.
        self.Facet2_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose which independent or covariate variable should determine the splitting of the y axis if at all.
        self.config_reference: QTextBrowser
            This TableWidget displays the definition, description, and default value of the user-selected setting.
        self.help_{setting}: QToolButton
            These buttons are assigned clicked signals and slotted for self.reference_event().
        self.pleth.variable_config: str
            This Plethysmography class attribute is the file path to one of the STAGG settings files.
        self.plethg.graph_config: str
            This Plethysmography class attribute is the file path to one of the STAGG settings files.
        self.pleth.other_config: str
            This Plethysmography class attribute is the file path to one of the STAGG settings files.

        Outputs
        --------
        self.role_list: list
            This attribute is a list of strings that are the headers of the self.loop_table.
        self.additional_dict: dict
            This dictionary relates certain header strings to their corresponding comboBoxes.
        self.settings_dict: dict
            A nested dictionary that relates the graph settings comboBoxes to their headers.
        self.widgy: dict
            This dictionary relates the self.help_{setting} widgets to self.config_reference (TextBrowser).
        self.alias: list
            This attribue is set as an empty list.
        self.independent: list
            This attribue is set as an empty list.
        self.dependent: list
            This attribue is set as an empty list.
        self.covariate: list
            This attribue is set as an empty list.
        self.custom_dict: dict
            This attribue is set as an empty dictionary.
        self.custom_port: dict
            This attribue is set as an empty dictionary.
        self.clades_other_dict
            This dictionary is populated and updated with the current states of the widgets stored in self.pleth.loop_menu.
        Outcomes
        --------
        self.setup_transform_combo()
            Add widget from custom class CheckableComboBox to STAGG settings subGUI layout to serve as drop-down menu for data transformation options.
        """
        print("config.setup_variables_config()")
        try:
            if not self.transform_combo:
                print("no transform_combo")
        except Exception as e:
            self.setup_transform_combo()
        self.role_list = ["Graph","Variable","Xvar","Pointdodge","Facet1","Facet2","Inclusion","Y axis minimum","Y axis maximum"]
        self.additional_dict = {self.feature_combo:"Feature",self.Poincare_combo:"Poincare",self.Spectral_combo:"Spectral",self.transform_combo:"Transformation"}
        self.settings_dict = {"role": {self.Xvar_combo:1,self.Pointdodge_combo:2,self.Facet1_combo:3,self.Facet2_combo:4}, 
                              "rel": {"Xvar":self.Xvar_combo,"Pointdodge":self.Pointdodge_combo,"Facet1":self.Facet1_combo,"Facet2":self.Facet2_combo}}
        self.widgy = {self.config_reference:[self.help_xvar,self.help_pointdodge,self.help_facet1,self.help_facet2,self.help_feature,self.help_poincare,self.help_spectral,self.help_transformation]}
        self.alias = []
        self.independent = []
        self.dependent = []
        self.covariate = []

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
    
    def setup_table_config(self):
        """
        Populate self.variable_table (TableWidget) with the contents of self.pleth.buttonDict_variable (dict).
        """
        print("config.setup_table_config()")
        self.stack = []

        # I've forgotten what this was specifically about, but I remember it had something to do with spacing or centering text or something.
        delegate = AlignDelegate(self.variable_table)
        delegate_loop = AlignDelegate(self.loop_table)
        self.variable_table.setItemDelegate(delegate)
        self.loop_table.setItemDelegate(delegate_loop)

        # Setting the number of rows in each table upon opening the window:
        self.variable_table.setRowCount(len(self.pleth.breath_df))
        self.loop_table.setRowCount(1)
        
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

            row += 1
            # you have to iteratively create the widgets for each row, not just iteratively
            # add the widgets for each row because it'll only do the last row
        for item_1 in self.pleth.breath_df:
            self.pleth.buttonDict_variable[item_1]["Independent"].toggled.connect(self.add_combos)
            self.pleth.buttonDict_variable[item_1]["Covariate"].toggled.connect(self.add_combos)
        
        self.variable_table.resizeColumnsToContents()
        self.variable_table.resizeRowsToContents()
    
    def show_loops(self,table,r):
        """
        Populate self.pleth.loop_menu with the appropriate widgets and populated self.loop_table with self.pleth.loop_menu.
        """
        # Almost redundant. See Main.show_loops().
        print("config.show_loops()")
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
            
            self.pleth.loop_menu[table][row]["Inclusion"] = QComboBox()
            self.pleth.loop_menu[table][row]["Inclusion"].addItems(["No","Yes"])
            self.pleth.loop_menu[table][row]["Covariates"] = CheckableComboBox()
            self.pleth.loop_menu[table][row]["Covariates"].addItems([b for b in self.deps])
        
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
        
        table.resizeColumnsToContents()
        table.resizeRowsToContents()

    def show_custom(self):
        """
        Check self.variable_table Alias selections, update rows in Custom.custom_table accordingly, and show the custom subGUI.
        """
        print("config.show_custom()")
        self.old_deps = self.deps
        self.classy()
        self.deps = self.clades.loc[(self.clades["Dependent"] == 1)]["Alias"]
        if self.custom_dict == {}:
            # custom dict apparently empty
            self.pleth.c = Custom(self)
            self.pleth.c.extract_variable()
        elif set(self.deps) != set(self.old_deps):
            # custom dict is not empty but new variables chosen
            d = [c for c in self.custom_dict]
            for c in d:
                if c not in self.deps:
                    self.custom_dict.pop(c,None)
            self.pleth.c = Custom(self)
            self.pleth.c.extract_variable()
        else:
            print("custom dict not empty")
            self.pleth.c.show()

    def classy(self):
        """
        Store the statuses of the self.variable_table (TableWidget) widgets held in self.pleth.buttonDict_variable (dict) in list attributes and dataframe attributes. Create columns for self.clades_graph and self.clades_other.
        """
        # This method is OLD
        print("config.classy()")
        self.clades = pd.DataFrame(columns= ["Column","Alias","Independent","Dependent","Covariate","ymin","ymax","Poincare","Spectral","Transformation"])
        self.clades_graph = pd.DataFrame(columns = ["Alias","Role"])
        self.clades_other = pd.DataFrame(columns = ["Graph","Variable","Xvar","Pointdodge","Facet1","Facet2","ymin","ymax","Filter"])
        origin = []
        self.alias = []
        self.independent = []
        self.dependent = []
        self.covariate = []

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

    def add_combos(self):
        """
        Update the Xvar, Pointdodge, Facet1, and Facet2 comboBoxes whenever the user selects a new independent variable or covariate variable.
        """
        print("add_combos()")
        self.classy()
        for c in self.settings_dict['role'].keys():
            c.clear()
            c.addItem("Select variable:")
            c.addItems([x for x in self.clades.loc[(self.clades["Independent"] == 1) | (self.clades['Covariate'] == 1)]['Alias']])

    def graphy(self):
        """
        Populate self.clades_graph with a dataframe containing the settings selected in the Xvar, Pointdodge, Facet1, and Facet2 comboBoxes.
        """
        print("config.graphy()")
        clades_role_dict = {}
        for col in self.role_list[2:6]:
            if self.settings_dict["rel"][col].currentText() == "Select variable:":
                clades_role_dict.update({self.settings_dict["role"][self.settings_dict["rel"][col]]:""})
            else:
                clades_role_dict.update({self.settings_dict["role"][self.settings_dict["rel"][col]]: self.settings_dict["rel"][col].currentText()})
        self.clades_graph = pd.DataFrame.from_dict(clades_role_dict,orient='index').reset_index()
        self.clades_graph.columns = ['Role','Alias']
    
    def othery(self):
        """
        Populate self.clades_other with a dataframe derived from the contents of self.clades_other_dict after the latter was updated with the current states of the widgets stored in self.pleth.loop_menu (dict).
        """
        print("config.othery()")
        self.clades_other_dict = {}
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
            if self.clades_other_dict[row]['Inclusion'] == 'Yes':
                self.clades_other_dict[row]['Inclusion'] = 1
            else:
                self.clades_other_dict[row]['Inclusion'] = 0  
            self.clades_other_dict[row].update({"Y axis minimum": self.pleth.loop_menu[self.loop_table][row]["Y axis minimum"].text()})
            self.clades_other_dict[row].update({"Y axis maximum": self.pleth.loop_menu[self.loop_table][row]["Y axis maximum"].text()})
            
        self.clades_other = pd.DataFrame.from_dict(self.clades_other_dict)
        self.clades_other = self.clades_other.transpose()

        if self.feature_combo.currentText() != "None":
            if self.feature_combo.currentText() == "All":
                self.clades_other.at[self.loop_table.rowCount(),"Graph"] = "Apneas"
                self.clades_other.at[self.loop_table.rowCount()+1,"Graph"] = "Sighs"
            else:
                self.clades_other.at[self.loop_table.rowCount()-1,"Graph"] = self.feature_combo.currentText()
        self.clades_other.drop(self.clades_other.loc[(self.clades_other["Graph"]=="") & (self.clades_other["Variable"]=="")].index, inplace=True)
     
    def classy_save(self):
        """
        Updating the relevant cells in self.clades with any custom settings stored in self.custom_port, updating the self.configs dictionary with the new dataframe for "variable_config", "graph_config", and "other_config", and calling self.graphy() and self.othery() to populating self.clades_graph and self.clades_other.
        """
        print("config.classy_save()")
        # Grabbing the user's selections from the widgets and storing them in dataframes:
        self.classy()
        if self.custom_port == {}:
            self.pleth.c = Custom(self)
            self.pleth.c.save_custom()
        for cladcol in self.clades:
            for item in self.custom_port:
                for col in self.custom_port[item]:
                    try:
                        if self.custom_port[item][col] != None:
                            if col is "Transformation":
                                self.custom_port[item][col] = [x.replace("raw","non") for x in self.custom_port[item][col]]
                                self.custom_port[item][col] = [x.replace("ln","log") for x in self.custom_port[item][col]]
                                self.clades.loc[(self.clades["Alias"] == self.custom_port[item]["Alias"]) & (cladcol == col),cladcol] = "@".join(self.custom_port[item][col])
                            else:
                                self.clades.loc[(self.clades["Alias"] == self.custom_port[item]["Alias"]),col] = self.custom_port[item][col]
                    except Exception as e:
                        print(f'{type(e).__name__}: {e}')
                        print(traceback.format_exc())
        
        self.configs["variable_config"].update({"df":self.clades})
        self.graphy()
        self.configs["graph_config"].update({"df":self.clades_graph})
        self.othery()
        self.configs["other_config"].update({"df":self.clades_other})
        
    def save_config(self):
        """
        Save the dataframes self.clades, self.clades_graph, and self.clades_other as .csv files to the default STAGG_config folder held in the user-selected output folder (self.pleth.mothership) and as timestamped .csv files to the timestamped STAGG output folder (self.pleth.output_dir_r) in the STAGG_output folder (self.pleth.r_output_folder) in the user-selected output folder (self.pleth.mothership).
        """
        print("config.save_config()")
        thumbholes = []
        self.classy_save()
        self.pleth.dir_checker(self.pleth.output_dir_r,self.pleth.r_output_folder,"STAGG")
        if self.pleth.output_folder != "":
            self.pleth.output_dir_r = self.pleth.output_folder
        for key in self.configs:
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
    
    def saveas_config(self):
        """Save the settings stored in self.clades, self.clades_graph, and/or self.clades_other to .csv files at the paths selected by the user with a standard FileDialog as well as at the default paths in the STAGG_config folder in the user-selected output folder (self.pleth.mothership), populate the display widget self.pleth.variable_list (ListWidget) in the Main GUI with the timestamped file paths, update self.configs (dict) with the timestamped file paths, and assign self.pleth.output_folder_r and self.pleth.input_dir_r according to the user-selected location of the STAGG settings files."""
        print("config.saveas_config()")
        thumbholes = []
        self.classy_save()
        save_dir = QFileDialog.getExistingDirectory(self, 'Choose directory for STAGG configuration files', self.mothership)

        if not save_dir:
            print("saveas_config canceled")
        else:
            self.configs['variable_config']['path'] = os.path.join(save_dir, 'variable_config_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')
            self.configs['graph_config']['path'] = os.path.join(save_dir, 'graph_config_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')
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

    def add_loop(self):
        """
        Update self.pleth.loop_menu with another key corresponding to the additional row, add another row to self.loop_table, and populate the row with the text and widgets stored in self.pleth.loop_menu.
        """
        print("config.add_loop()")
        loop_row = self.loop_table.rowCount()
        self.loop_table.insertRow(loop_row)
        self.pleth.loop_menu[self.loop_table].update({loop_row: {"Graph": QLineEdit()}})
        self.loop_table.setCellWidget(loop_row,0,self.pleth.loop_menu[self.loop_table][loop_row]["Graph"])
        self.pleth.loop_menu[self.loop_table][loop_row].update({"Y axis minimum": QLineEdit()})
        self.loop_table.setCellWidget(loop_row,7,self.pleth.loop_menu[self.loop_table][loop_row]["Y axis minimum"])
        self.pleth.loop_menu[self.loop_table][loop_row].update({"Y axis maximum": QLineEdit()})
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
        """
        Reset attributes, clear Xvar, Pointdode, Facet1, and Facet2 comboBoxes, set Poincare, Spectral, feature, and Transformation comboBoxes to None, repopulate self.loop_table and self.variable_table with the updated (rebuilt) dictionaries self.pleth.loop_menu and self.pleth.buttonDict_variable respectively.
        """
        print("config.reset_config()")
        try:
            self.setup_variables_config()
            self.setup_table_config()
            self.n = 0
            self.variable_table.cellChanged.connect(self.no_duplicates)
            self.variable_table.cellChanged.connect(self.update_loop)
            self.pleth.show_loops(self.loop_table,1)
            for s in self.settings_dict['role']:
                s.clear()
                s.addItem("Select variable:")
            for p in self.additional_dict:
                p.setCurrentText("None")
            self.deps = []
            self.classy()
            self.deps = self.clades.loc[(self.clades["Dependent"] == 1)]["Alias"]
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            print("Apparently reset_config only knows how to land by crashing into objects like my bird. I don't understand why this except makes things work, and that makes me uncomfortable.")

    def to_check_load_variable_config(self):
        # I think I made this exist so that I could assign the method to the slot via QtDesigner but still provide the argument "yes", which is absurd but moving on.
        self.check_load_variable_config("yes")

    def check_load_variable_config(self,open_file):
        """
        Check the user-selected files to ensure they exist and they are the correct file format and they begin with either "variable_config", "graph_config", or "other_config", triggering a MessageBox or dialog to inform the user if any do not and loading the file as a dataframe if they do.
        """
        paths = []
        print("self.check_load_variable_config has started")
        if open_file == "yes":
            # Opens open file dialog
            file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/STAGG_config")))
            paths = file_name[0]
        elif open_file == "no":
            paths = [self.configs[p]["path"] for p in self.configs]
        if paths != []:
            for x in range(len(paths)):
                for key in self.configs:
                    if key in paths[x]:
                        if Path(paths[x]).is_file():
                            # paths[x] is a real file
                            if paths[x].endswith('.csv') or paths[x].endswith('.xlsx'):
                                # paths[x] ends with .csv or .xlsx
                                if os.path.basename(paths[x]).startswith(key):
                                    # paths[x] starts with key
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
                                    # paths[x] does not start with key
                                    if paths[x] in self.baddies:
                                        self.baddies.remove(paths[x])
                                    self.baddies.append(paths[x])
                                    if len(self.baddies)>0:
                                        self.thumb = Thumbass(self.pleth)
                                        self.thumb.show()
                                        self.thumb.message_received("Wrong file name",f"""One or more of the files selected is cannot be recognized:\n{os.linesep.join([b for b in self.baddies])}\nPlease rename the file(s) as described in the <a href="https://github.com/">documentation</a> or select a different file.""")
                                    
                            else:
                                # paths[x] does not end with .xlsx or .csv
                                if paths[x] in self.baddies:
                                    self.baddies.remove(paths[x])
                                self.baddies.append(paths[x])
                                if len(self.baddies)>0:
                                    self.thumb = Thumbass(self.pleth)
                                    self.thumb.show()
                                    self.thumb.message_received("Incorrect file format",f"One or more of the files selected is not in the correct file format:\n{os.linesep.join([b for b in self.baddies])}\nOnly .csv or .xlsx are accepted.")
                        else:
                            # if paths[x] is not a real file:
                            if paths[x] in self.baddies:
                                self.baddies.remove(paths[x])
                            self.baddies.append(paths[x])
                            if len(self.baddies)>0:
                                print(f'baddies got {paths[x]} cause it is not a real file')
                                self.thumb = Thumbass(self.pleth)
                                self.thumb.show()
                                self.thumb.message_received("Files not found", f"One or more of the files selected cannot be found:\n{os.linesep.join([b for b in self.baddies])}")
            if "variable_config" in self.goodies:
                try:
                    self.load_variable_config()
                    for item in self.pleth.variable_list.findItems("variable_config",Qt.MatchContains):
                        self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                    self.pleth.variable_list.addItem(self.configs["variable_config"]['path'])
                except KeyError as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
                    self.goodies.remove("variable_config")
                    self.baddies.append("variable_config")
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

    def load_variable_config(self):
        """
        Load the variable_config file as a dataframe, populate self.pleth.breath_df with the list values in the "Column" column of the dataframe, populate self.variable_table (TableWidget) with a row for each variable in the variable_config dataframe, and load the custom settings.
        """
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
        for a in self.vdf:
            self.pleth.buttonDict_variable[a]['Alias'].setText(self.vdf[a]['Alias'])
            for k in ["Independent","Dependent","Covariate"]:
                if self.vdf[a][k] == '1':
                    self.pleth.buttonDict_variable[a][k].setChecked(True)
        self.load_custom_config()

    def load_custom_config(self):
        """
        Populate Custom.custom_table based on the dependent variables selected by the user according to the dataframe derived from the variable config .csv file the user selected. 
        """
        print("loading custom config")
        for p in self.additional_dict:
            p.setCurrentText("None")
        self.deps = [self.vdf[a]['Alias'] for a in self.vdf if self.vdf[a]['Dependent'] == '1']
        self.custom_dict = {}
        self.pleth.c = Custom(self)
        self.pleth.c.populate_table(self.deps,self.pleth.c.custom_table)
        for k in self.vdf:
            if self.vdf[k]['Poincare'] == "1":
                self.custom_dict[k]['Poincare'].setChecked(True)
            if self.vdf[k]['Spectral'] == "1":
                self.custom_dict[k]['Spectral'].setChecked(True)
            for y in ['ymin','ymax']:
                if self.vdf[k][y] != "":
                    self.custom_dict[k][y].setText(self.vdf[k][y])
            if self.vdf[k]['Transformation'] != "":
                transform = [s.replace("non","raw") and s.replace("log","ln") for s in self.vdf[k]['Transformation'].split('@')]
                transform = [z.replace("ln10","log10") for z in transform]
                self.custom_dict[k]['Transformation'].loadCustom(transform)
                self.custom_dict[k]['Transformation'].updateText()
        self.pleth.c.save_custom()
        
    def load_graph_config(self):
        """
        Populate the Xvar, Pointdodge, Facet1, and Facet2 comboBoxes with the variables selected as independent or covariate according to the variable_config .csv file; if there is no variable_config file, then populate those comboBoxes with the variables in the dataframe read from the graph_config file and set the comboBoxes current text.
        """
        print("loading graph config")
        gdf = pd.read_csv(self.configs["graph_config"]["path"], index_col=False)
        if "variable_config" in self.goodies:
            for c in self.settings_dict['role']:
                c.clear()
                c.addItem("Select variable:")
                c.addItems([[self.vdf[k]["Alias"] for k in self.vdf if self.vdf[k][v] == "1"] for v in ["Independent","Covariate"]][0])
                try:
                    c.setCurrentText([x for x in gdf.loc[(gdf['Role'] == self.settings_dict['role'][c])]['Alias'] if pd.notna(x) == True][0])
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
                    pass
        else:
            for c in self.settings_dict['role']:
                c.clear()
                c.addItem("Select variable:")
                c.addItems([x for x in gdf['Alias'] if pd.notna(x) == True])
                try:
                    c.setCurrentText([x for x in gdf.loc[(gdf['Role'] == self.settings_dict['role'][c])]['Alias'] if pd.notna(x) == True][0])
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
                    pass
            try:
                for c in self.settings_dict['role']:
                    c.setCurrentText([x for x in gdf.loc[(gdf['Role'] == self.settings_dict['role'][c])]['Alias'] if pd.notna(x) == True])
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
            

    def load_other_config(self):
        """
        Set the current text of the feature plots comboBox according to the other_config .csv file loaded and populate self.loop_table with the contents of the dataframe derived from the other_config .csv file.
        """
        print("loading other config")
        odf = pd.read_csv(self.configs["other_config"]['path'], index_col=False)
        self.feature_combo.setCurrentText("None")
        if "Apneas" in set(odf["Graph"]):
            self.feature_combo.setCurrentText("Apneas")
        if "Sighs" in set(odf["Graph"]):
            self.feature_combo.setCurrentText("Sighs") 
        if ("Apneas" and "Sighs") in set(odf["Graph"]):
            self.feature_combo.setCurrentText("All")
        odf.drop(odf.loc[(odf["Graph"]=="Apneas") | (odf["Graph"]=="Sighs")].index, inplace = True)
        self.show_loops(self.loop_table,len(odf))
        if len(odf)>0:
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

    def checkable_ind(self,state):
        """
        Change the RadioButton status for every column in the selected rows so that only the "Independent" RadioButton is set as checked.
        """
        try:
            print("true")
            for selected_rows in self.variable_table.selectedRanges():
                for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
                    self.variable_table.cellWidget(row,2).setChecked(True)
        except:
            print("nope")
        # 
    def checkable_dep(self):
        """
        Change the RadioButton status for every column in the selected rows so that only the "Dependent" RadioButton is set as checked.
        """
        try:
            for selected_rows in self.variable_table.selectedRanges():
                for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
                    self.variable_table.cellWidget(row,3).setChecked(True)
        except:
            print("nope")
        
    def checkable_cov(self):
        """
        Change the RadioButton status for every column in the selected rows so that only the "Covariate" RadioButton is set as checked.
        """
        try:
            for selected_rows in self.variable_table.selectedRanges():
                for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
                    self.variable_table.cellWidget(row,4).setChecked(True)
        except:
            print("nope")

    def checkable_ign(self):
        """
        Change the RadioButton status for every column in the selected rows so that only the "Ignore" RadioButton is set as checked.
        """
        try:
            for selected_rows in self.variable_table.selectedRanges():
                for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
                    self.variable_table.cellWidget(row,5).setChecked(True)
        except:
            print("nope")
#endregion

class Plethysmography(QMainWindow, Ui_Plethysmography):
    def __init__(self):
        """
        Instantiate the Plethysmography class.

        Parameters
        --------
        Config: class
            This class defines the STAGG settings subGUI.
        Annot: class
            This class defines the variable configuration subGUI.
        Basic: class
            This class defines the basic BASSPRO settings subGUI.
        Auto: class
            This class defines the automated BASSPRO settings subGUI.
        Manual: class
            This class defines the manual BASSPRO settings subGUI.
        
        self.gui_config: dict
            This attribute is a nested dictionary loaded from gui_config.json. It contains paths to the BASSPRO and STAGG modules and the local Rscript.exe file, the fields of the database accessed when building a metadata file, and settings labels used to organize the populating of the TableWidgets in the BASSPRO settings subGUIs. See the README file for more detail.
        self.stamp: dict
            This attribute is a nested dictionary loaded from timestamps.json. It contains a populated dictionary with the default timestamps of multiple experimental setups and an empty dictionary that will be populated by the timestamps of signal files selected by the user.
        self.bc_config: dict
            This attribute is a nested dictionary loaded from breathcaller_config.json. It contains the default settings of multiple experimental setups for basic, automated, and manual BASSPRO settings and  the most recently saved settings for automated and basic BASSPRO settings. See the README file for more detail.
        self.rc_config: dict
            This attribute is a shallow dictionary loaded from reference_config.json. It contains definitions, descriptions, and recommended values for every basic, manual, and automated BASSPRO setting.
        self.q: Queue
            A first-in, first-out queue constructor for safely exchanging information between threads.
        self.counter: int
            The worker's number.
        self.finished_count: int
            The number of finished workers.
        self.qThreadpool: QThreadPool
        self.threads: dict
        self.workers: dict
            Workers spawned.
        
        self.breathcaller_path: str
            The path to the BASSPRO module script. Required input for BASSPRO.
        self.output_dir_py: str
            The path to the BASSPRO output directory. Required input for BASSPRO.
        self.autosections: str
            The path to the automated BASSPRO settings file. BASSPRO requires either an automated BASSPRO settings file or a manual BASSPRO settings file. It can also be given both as input.
        self.mansections: str
            The path to the manual BASSPRO settings file. BASSPRO requires either an automated BASSPRO settings file or a manual BASSPRO settings file. It can also be given both as input.
        self.basicap: str
            The path to the basic BASSPRO settings file. Required input for BASSPRO.
        self.metadata: str
            The path to the metadata file. Required input for BASSPRO.
        self.signals: list
            The list of file paths of the user-selected .txt signal files that are analyzed by BASSPRO. Required input for BASSPRO.
        self.mothership: str
            The path to the user-selected directory for all output. Required input for BASSPRO and STAGG.
        self.stagg_list: list
            The list of one of the following: JSON files produced by the most recent run of BASSPRO in the same session; JSON files produced by BASSPRO selected by user with a FileDialog; an .RData file produced by a previous run of STAGG; an .RData file produced by a previous run of STAGG and JSON files produced by BASSPRO.
        self.output_dir_r: str
            The path to the STAGG output directory. Required input for STAGG.
        self.input_dir_r: str
            The path to the STAGG input directory. Derived from os.path.dirname() of the JSON  output files from BASSPRO. Required input for STAGG.
        self.variable_config: str
            The path to the variable_config.csv file. Required input for STAGG.
        self.graph_config: str
            The path to the graph_config.csv file. Required input for STAGG.
        self.other_config: str
            The path to the other_config.csv file. Required input for STAGG.
        self.image_format: str
            The file format of the figures produced by STAGG. Either ".svg" or ".jpeg". Required input for STAGG.
        self.papr_dir: str
            The path to the STAGG scripts directory derived from self.gui_config. Required input for STAGG.
        self.rscript_des: str
            The path to the Rscript.exe file on the user's device. Required input for STAGG.
        self.pipeline_des: str
            The path to the appropriate .R script in the STAGG scripts directory. Required input for STAGG.
        sef.py_output_folder: str
            The path to the directory containing the BASSPRO output directories.
        self.r_output_folder: str
            The path to the directory containing the STAGG output directories. 
        self.buttonDict_variable: dict
            The nested dictionary used to populate and save the text and RadioButton states of Config.variable_table (TableWidget) in the Config subGUI.
        self.loop_menu: dict
            The nested dictionary used to populate and save the text, CheckBox, ComboBox, and CheckableComboBox states of Config.loop_table (TableWidget) in the Config subGUI.
        
        Outputs
        --------
        self.necessary_timestamp_box: QComboBox
            A comboBox inherited from Ui_Plethysmography that is populated with the experimental setups for which the GUI has default automated BASSPRO settings. These experimental setups are sourced from the keys of the "default" dictionary nested in the "Auto Settings" dictionary loaded from the breathcaller_config.json file.
        self.parallel_combo: QComboBox
            A comboBox inherited from Ui_Plethysmography that is populated with the number of CPU's available on the user's device.
        Manual.preset_menu: QComboBox
            A comboBox of the Manual class inherited from Ui_Manual that is populated with the experimental setups for which the GUI has default manual BASSPRO settings that will be concatenated with the user's manual selections of breaths to produce the final manual_sections.csv file. These experimental setups are sourced from thekeys of the "default" dictionary nested in the "Manual Settings" dictionary loaded from the breathcaller_config.json file. 
        Auto.auto_setting_combo: QComboBox
            A comboBox of the Auto class inherited from Ui_Auto that is populated with the experimental setups for which the GUI has default automated BASSPRO settings. These experimental setups are sourced from the keys of the "default" dictionary nested in the "Auto Settings" dictionary loaded from the breathcaller_config.json file.
        
        Outcomes
        --------
        self.v()
            This method instantiates the Config class.
        self.m()
            This method instantiates the Manual class.
        self.a()
            This method instantiates the Auto class.
        self.b()
            This method instantiates the Basic class.
        self.g()
            This method instantiates the Annot class.
        """
        super(Plethysmography, self).__init__()

#region class methods
        # Access configuration settings for GUI in gui_config.json:
        with open(f'{Path(__file__).parent}/gui_config.json') as config_file:
            self.gui_config = json.load(config_file)
        print(f'{Path(__file__).parent}/gui_config.json')

        # Access timestamp settings for storing timestamper results in timestamps.json:
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

        # Load variables with paths for BASSPro and StaGG stored in gui_config dictionary:
        self.gui_config['Dictionaries']['Paths'].update({'breathcaller':str(Path(f'{Path(__file__).parent.parent}/python_module.py'))})
        print(self.gui_config['Dictionaries']['Paths']['breathcaller'])
        self.gui_config['Dictionaries']['Paths'].update({'papr':str(Path(f'{Path(__file__).parent.parent}/papr'))})
        print(self.gui_config['Dictionaries']['Paths']['papr'])

#endregion

#region class attributes
        self.mothership=""
        self.breathcaller_path = self.gui_config['Dictionaries']['Paths']['breathcaller']
        self.output_dir_py=""
        self.input_dir_r=""
        self.output_dir_r=""
        self.autosections=""
        self.mansections=""
        self.basicap=""
        self.metadata=""
        self.papr_dir = self.gui_config['Dictionaries']['Paths']['papr']
        self.py_output_folder=""
        self.r_output_folder=""
        self.variable_config=""
        self.graph_config=""
        self.other_config=""
        self.signals = []
        self.mp_parsed = {}
        self.mp_parserrors = []
        self.p_mouse_dict={}
        self.m_mouse_dict={}
        self.metadata_warnings = {}
        self.metadata_pm_warnings = []
        self.missing_plyuids = []
        self.metadata_passlist = []
        self.tsbyfile = {}
        self.image_format = ""
        self.buttonDict_variable = {}
        self.stagg_list = []
        self.rscript_des = ""
        self.pipeline_des = ""
        self.loop_menu = {}

        # Initiating subGUIs
        self.v = Config(self)
        self.m = Manual(self)
        self.a = Auto(self)
        self.b = Basic(self)
        self.g = AnnotGUI.Annot(self)

        self.v.graphic.setStyleSheet("border-image:url(:resources/graphic.png)")

         # Populate GUI widgets with experimental condition choices: 
        self.necessary_timestamp_box.addItems([x for x in self.bc_config['Dictionaries']['Auto Settings']['default'].keys()])
        self.parallel_combo.addItems([str(num) for num in list(range(1,os.cpu_count()+1))])

        # Populate GUI widgets with experimental condition choices:
        self.m.preset_menu.addItems([x for x in self.bc_config['Dictionaries']['Manual Settings']['default'].keys()])
        self.a.auto_setting_combo.addItems([x for x in self.bc_config['Dictionaries']['Auto Settings']['default'].keys()])
        
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

#region Timestamper methods...

    def timestamp_dict(self):
        print("timestamp_dict()")
        self.stamp['Dictionaries']['Data'] = {}
        combo_need = self.necessary_timestamp_box.currentText()
        if self.signals == []:
            reply = QMessageBox.information(self, 'Missing signal files', 'No signal files selected.\nWould you like to select a signal file directory?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.get_signal_files()
        elif combo_need == "Select dataset...":
            reply = QMessageBox.information(self, 'Missing dataset', 'Please select one of the options from the dropdown menu above.', QMessageBox.Ok)
        elif not all(x.endswith(".txt") for x in self.signals)==True:
            reply = QMessageBox.information(self, 'Incorrect file format', 'The selected signal files are not text formatted.\nWould you like to select a different signal file directory?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.get_signal_files()
        else:
            epoch = [os.path.basename(Path(self.signals[0]).parent.parent)]
            condition = [os.path.basename(Path(self.signals[0]).parent)]
            
            for f in self.signals:
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

            self.need = self.bc_config['Dictionaries']['Auto Settings']['default'][combo_need]

            self.grabTimeStamps()
            self.checkFileTimeStamps()

            for e in epoch:
                for c in condition:
                    self.stamp['Dictionaries']['Data'][e][c]["tsbyfile"] = self.tsbyfile
                    for notable in self.check:
                        self.stamp['Dictionaries']['Data'][e][c][notable] = self.check[notable]  
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
            miss = []
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

    def grabTimeStamps(self):
        """
        Iterate through user-selected signal files to compare the signal file's timestamps to the timestamps of one of multiple experimental setups.

        Parameters
        --------
        self.signals: list
            The list of file paths of the user-selected .txt signal files that are analyzed by BASSPRO.
        self.tsbyfile: dict
            This attribute is set as an empty dictionary.
        
        Outputs
        --------
        self.tsbyfile: dict
            This attribute stores a nested dictionary containing the timestamps for every signal file, as well as listing the file and the offending timestamp for duplicate timestamps, missing timestamps, and novel timestamps.
        
        """
        timestamps = []
        self.tsbyfile = {}
        
        for CurFile in self.signals:
            self.tsbyfile[CurFile]=[]
            with open(CurFile,'r') as opfi:
                i=0
                for line in opfi:
                    if '#' in line:
                        print('{} TS AT LINE: {} - {}'.format(os.path.basename(CurFile),i,line.split('#')[1][2:]))
                        timestamps.append(line.split('#')[1][2:])
                        c = line.split('#')[1][2:].split(' \n')[0]
                        self.tsbyfile[CurFile].append(f"{c}")
                    i+=1
            self.tsbyfile[CurFile] = [i for i in self.tsbyfile[CurFile]]
        timestamps=list(set(timestamps))
        timestamps=[i.split(' \n')[0] for i in timestamps]
        timestamps.sort()

    def checkFileTimeStamps(self):
        """
        Iterate through contents of self.tsbyfile (dict) to compare them to the default timestamps of the user-selected experimental set-up and populate self.new_check (dict) with offending timestamps and their signals.
        """
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

#endregion

#region show subGUIs
    def show_annot(self):
        self.g.show()
        self.g.show_metadata_file()

    def show_manual(self):
        self.m.show()

    def show_auto(self):
        self.a.show()

    def show_basic(self):
        self.b.show()
        
#endregion
#region Variable configuration
    def check_metadata_file(self,direction):
        """
        Ensure the user-selected metadata is the correct file format, contains metadata for the signal files that were selected, and is named correctly. This method depends on the presence of a column named MUID and a column named PlyUID in the metadata and depends on the file being named as either MUID or MUID_PlyUID. 
        """
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
        """
        Ensure that the user has provided metadata, basic BASSPRO settings, and either automated or manual BASSPRO settings before launching BASSPRO.
        """
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
        """
        Run self.get_bp_reqs() and self.test_configuration() to ensure that BASSPRO has the required input, run self.variable_configuration() to populate Config.variable_table (TableWidget), and show the STAGG settings subGUI.
        """
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
        """
        Ensure that there is a source of variables to populate Config.variable_table with and run test_configuration() to ensure that those sources are viable, run self.variable_configuration() to populate Config.variable_table (TableWidget), and either show the STAGG settings subGUI or show a Thorbass dialog to guide the user through providing the required input if there is no input.
        """
        if self.buttonDict_variable == {}:
            if self.v.configs["variable_config"]["path"] != "":
                self.v.check_load_variable_config("no")
                self.v.show()
            elif self.stagg_list != [] and any(a.endswith(".json") for a in self.stagg_list):
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
                self.thorb = Thorbass(self)
                self.thorb.show()
                self.thorb.message_received('Missing source files', f"One or more of the files used to build the variable list has not been selected.\nWould you like to open an existing set of variable configuration files or create a new one?",self.new_variable_config,self.get_variable_config)
        else:
            self.v.show()
            
    def update_breath_df(self,updated_file):
        """
        Ask the user if they want to update the self.breath_df list to include the latest updates to the metadata and/or the automated or manual BASSPRO settings and if so, reset and repopulate the STAGG settings subGUI widgets, namely Config.variable_table.
        """
        print("update_breath_df()")
        self.old_bdf = self.breath_df
        self.breath_df = []
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
        if set(self.breath_df) != set(self.old_bdf):
            non_match_old = set(self.old_bdf) - set(self.breath_df)
            non_match_new = set(self.breath_df) - set(self.old_bdf)
            non_match = list(non_match_old) + list(non_match_new)
            if len(non_match)>0:
                reply = QMessageBox.question(self, f'New {updated_file} selected', 'Would you like to update the variable list in STAGG configuration settings?\n\nUnsaved changes may be lost.\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.v.setup_table_config()
                    try:
                        for a in self.v.vdf:
                            self.buttonDict_variable[a]['Alias'].setText(self.v.vdf[a]['Alias'])
                            for k in ["Independent","Dependent","Covariate"]:
                                if self.v.vdf[a][k] == '1':
                                    try:
                                        self.buttonDict_variable[a][k].setChecked(True)
                                    except:
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

    def try_open(self,path):
        """
        Ensure that the file and its contents are accessible.
        """
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
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            self.missing_meta.append(path)

    def test_configuration(self):
        """
        Ensure that the file paths that populate the attributes required to show the STAGG settings subGUI exist and their contents are accessible, and provide feedback to the user on what is missing if anything.
        """
        print("test_configuration() has started")
        self.missing_meta = []
        for p in [self.metadata,self.autosections,self.mansections]:
            if p != "":
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
        if len(self.missing_meta)>0:
            reply = QMessageBox.information(self, 'Missing source files', f"One or more of the files used to build the variable list was not found:\n{os.linesep.join([m for m in self.missing_meta])}\nWould you like to select a different file?", QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                for m in self.missing_meta:
                    if m is self.mothership:
                        reply = QMessageBox.information(self, 'Missing metadata', 'Please select a metadata file.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                        if reply == QMessageBox.Ok:
                            self.get_metadata()
                        if reply == QMessageBox.Cancel:
                            self.metadata_list.clear()
                    if m is self.autosections or m is self.mansections:
                        reply = QMessageBox.information(self, 'Missing BASSPRO settings', 'Please select BASSPRO settings files.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                        if reply == QMessageBox.Ok:
                            self.get_autosections()
                    if m is self.breathcaller_path:
                        reply = QMessageBox.information(self, "How is this program even running?", f"The program cannot find the following file: \n{self.breathcaller_path}\nPlease reinstall BASSPRO-STAGG.", QMessageBox.Ok)

    def variable_configuration(self):
        """
        Populate self.buttonDict_variable with widgets and text and populate Config.variable_table with the contents of self.buttonDict_variable.
        """
        print("self.variable_configuration() has started")
        self.stack = []

        # I've forgotten what this was specifically about, but I remember it had something to do with spacing or centering text or something.
        delegate = AlignDelegate(self.v.variable_table)
        delegate_loop = AlignDelegate(self.v.loop_table)
        self.v.variable_table.setItemDelegate(delegate)
        self.v.loop_table.setItemDelegate(delegate_loop)

        # Setting the number of rows in each table upon opening the window:
        self.v.variable_table.setRowCount(len(self.breath_df))
        self.v.loop_table.setRowCount(1)
        
        row = 0
        for item in self.breath_df:
            # Establishing each row as its own group to ensure mutual exclusivity for each row within the table:
            self.buttonDict_variable[item]={"group": QButtonGroup()}

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

            row += 1

        self.v.n = 0
        for item_1 in self.breath_df:
            self.buttonDict_variable[item_1]["Independent"].toggled.connect(self.v.add_combos)
            self.buttonDict_variable[item_1]["Covariate"].toggled.connect(self.v.add_combos)
        self.v.variable_table.resizeColumnsToContents()
        self.v.variable_table.resizeRowsToContents()
        self.loop_menu = {}
        self.show_loops(self.v.loop_table,1)
        print("self.variable_configuration() has finished")

    def show_loops(self,table,r):
        # This method is almost redundant. Config.show_loops() is almost the same, but populates comboBoxes based on a list of Aliases scraped from the tableWidget Config.variable_table instead of the list of Aliases derived from self.breath_df, which is in turn derived from either the dataframe from Main.variable_config.to_csv() or Main.input_dir_r[0].to_dict() (JSON file) or the compilation of variables from Main.metadata, Main.autosections or Main.mansections, and Main.basic. Config.show_loops() also establishes an empty Main.loop_menu within Config.show_loops instead of before it's called.
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
            
            self.loop_menu[table][row]["Inclusion"] = QComboBox()
            self.loop_menu[table][row]["Inclusion"].addItems(["No","Yes"])
            self.loop_menu[table][row]["Covariates"] = CheckableComboBox()
            self.loop_menu[table][row]["Covariates"].addItems([b for b in self.breath_df])
             
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
#endregion

#region Automatic selection

    def mothership_dir(self):
        """
        Prompt the user to choose an output directory where both BASSPRO and STAGG output will be written to, detect any relevant input that may already be present in that directory, ask the user if they would like to keep previous selections for input or replace them with the contents of the selected directory if there are previous selections for input and update self.breath_df (list).
        """
        print("mothership_dir()")
        self.mothership = QFileDialog.getExistingDirectory(self, 'Choose output directory', str(Path.home()), QFileDialog.ShowDirsOnly)
        if os.path.exists(self.mothership):
            self.output_path_display.setText(self.mothership)
            if self.breath_df != [] or self.metadata != "" or self.autosections != "" or self.basicap != "" or self.mansections != "":
                reply = QMessageBox.question(self, f'Input detected', 'The selected directory has recognizable input.\n\nWould you like to overwrite your current input selection?\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.auto_get_output_dir_py()
                    self.auto_get_autosections()
                    self.auto_get_mansections()
                    self.auto_get_metadata()
                    self.auto_get_output_dir_r()
                    self.auto_get_basic()
                    
            else:
                self.auto_get_output_dir_py()
                self.auto_get_autosections()
                self.auto_get_mansections()
                self.auto_get_metadata()
                self.auto_get_output_dir_r()
                self.auto_get_basic()
                if len(self.breath_df)>0:
                    self.update_breath_df("settings")
        
    def auto_get_output_dir_py(self):
        """
        Check whether or not a BASSPRO_output directory exists in the user-selected directory and make it if it does not exist, and make a timestamped BASSPRO output folder for the current session's next run of BASSPRO.
        """
        print("auto_get_output_dir_py()")
        self.py_output_folder=os.path.join(self.mothership,'BASSPRO_output')
        if Path(self.py_output_folder).exists():
            self.output_dir_py=os.path.join(self.py_output_folder, 'BASSPRO_output_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
        else:
            Path(self.py_output_folder).mkdir()
            self.output_dir_py=os.path.join(self.py_output_folder,'BASSPRO_output_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    
    def auto_get_metadata(self):
        """
        Detect a metadata file.
        """
        print("auto_get_metadata()")
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
        else:
            print("No metadata file selected.")
        if self.signals != []:
            self.check_metadata_file("metadata")

    def auto_get_basic(self):
        """
        Detect a basic file.
        """
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
        else:
            print("Basic parameters settings file not detected.")

    def auto_get_autosections(self):
        """
        Detect an automated BASSPRO settings file.
        """
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
        else:
            print("Autosection parameters file not detected.")

    def auto_get_mansections(self):
        """
        Detect a manual BASSPRO settings file.
        """
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
        else:
            print("Manual sections parameters file not detected.")

    def get_variable_config(self):
        print("self.get_variable_config()")
        self.v.check_load_variable_config("yes")

    def auto_get_breath_files(self):
        """
        Detect JSON BASSPRO output files.
        """
        print("auto_get_breath_files()")
        if self.stagg_list != []:
            reply = QMessageBox.information(self, 'Clear STAGG input list?', 'Would you like to keep the previously selected STAGG input files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                self.breath_list.clear()
                self.stagg_list = []
        self.stagg_list = [os.path.join(self.output_dir_py,file) for file in os.listdir(self.output_dir_py) if file.endswith(".json")==True]
        for x in self.stagg_list:
            self.breath_list.addItem(x)
           
    def auto_get_output_dir_r(self):
        """
        Check whether or not a STAGG_output directory exists in the user-selected directory and make it if it does not exist, and make a timestamped STAGG output folder for the current session's next run of STAGG.
        """
        print("auto_get_output_dir_r()")
        self.r_output_folder=os.path.join(self.mothership,'STAGG_output')
        if Path(self.r_output_folder).exists():
            self.output_dir_r=os.path.join(self.r_output_folder, 'STAGG_output_'+datetime.datetime.now().strftime(
                '%Y%m%d_%H%M%S'
            ))
        else:
            Path(self.r_output_folder).mkdir()
            self.output_dir_r=os.path.join(self.r_output_folder, 'STAGG_output_'+datetime.datetime.now().strftime(
                '%Y%m%d_%H%M%S'
            ))
#endregion

    def open_click(self,item):
        """
        Open the double-clicked ListWidgetItem in the default program for the user's device.
        """
        print("open_click()")
        try:
            if Path(item.text()).exists():
                os.startfile(item.text())
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            pass

    def get_signal_files(self):
        """
        Prompt the user to select signal files via FileDialog.
        """
        print("get_signal_files()")
        file_name = QFileDialog.getOpenFileNames(self, 'Select signal files')
        if not file_name[0]:
            if self.signals == []:
                self.signal_files_list.clear()
        else:
            if self.signals != []:
                reply = QMessageBox.information(self, 'Clear signal files list?', 'Would you like to keep the previously selected signal files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    self.signal_files_list.clear()
                    self.signals = []
            bad_signals = []
            self.hangar.append("Signal files selected.")
            for x in range(len(file_name[0])):
                if file_name[0][x].endswith(".txt"):
                    self.signal_files_list.addItem(file_name[0][x])
                    self.signals.append(file_name[0][x])
                else:
                    bad_signals.append(file_name[0][x])
            if len(bad_signals)>0:
                self.thumb = Thumbass(self)
                self.thumb.show()
                self.thumb.message_received("Incorrect file format",f"One or more of the files selected are not text formatted:\n\n{os.linesep.join([os.path.basename(thumb) for thumb in bad_signals])}\n\nThey will not be included.")
        if self.metadata != "":
            if os.path.exists(self.metadata):
                self.check_metadata_file("signal")

    def get_metadata(self):
        """
        Prompt the user to select a previously made metadata file.
        """
        print("get_metadata()")
        if self.mothership != "":
            file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(self.mothership))
        else:
            file_name = QFileDialog.getOpenFileNames(self, 'Select metadata file')
        if not file_name[0]:
            if self.metadata == "":
                self.metadata_list.clear()
        else:
            self.metadata_list.clear()
            for x in range(len(file_name[0])):
                self.metadata_list.addItem(file_name[0][x])
            self.metadata = file_name[0][0]
            
            if len(self.breath_df)>0:
                self.update_breath_df("metadata")
        if self.signals != []:
            self.check_metadata_file("metadata")
    
    def mp_parser(self):
        """
        Grab MUIDs and PlyUIDs from signal file names.
        """
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
        """
        Collect relevant metadata for the mice and their runs as indicated by their MUID and PlyUID in the signal file name as sourced via self.mp_parser().
        """
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
                reply = QMessageBox.information(self, 'Unable to connect to database', 'You were unable to connect to the database.\nWould you like to select another metadata file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                if reply == QMessageBox.Ok:
                    self.get_metadata()

    def get_study(self, fixformat=True):
        """
        Scrape the values from the relevant fields of the database for the metadata.
        """
        print("get_study()")
        self.metadata_list.addItem("Building query...")
        try:
            FieldDict={"MUID":['Mouse_List','Plethysmography'],
                "PlyUID":['Plethysmography'],
                "Misc. Variable 1 Value":['Plethysmography'],
                "Sex":['Mouse_List'],
                "Genotype":['Mouse_List'],
                "Group":['Plethysmography'],
                "Weight":['Plethysmography'],
                "Comments":['Mouse_List'],
                "Date of Birth":['Mouse_List'],
                "Experiment_Name":['Plethysmography'],
                "Researcher":['Plethysmography'],
                "Experimental_Date":['Plethysmography'],
                "time started":['Plethysmography'],
                "Rig":['Plethysmography'],
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
            p_df=pd.DataFrame(self.p_mouse_dict).transpose()
            m_df=pd.DataFrame(self.m_mouse_dict).transpose()
            if fixformat==True:
                p_df['PlyUID']='Ply'+p_df['PlyUID'].astype(int).astype(str)
                p_df['Experimental_Date']=pd.to_datetime(p_df['Experimental_Date'], errors='coerce')
                m_df['MUID']='M'+m_df['MUID'].astype(int).astype(str)
                m_df['Date of Birth']=pd.to_datetime(m_df['Date of Birth'], errors='coerce')
            self.assemble_df=pd.merge(p_df,m_df, how='left', 
                            left_on='MUID', right_on='MUID')
            self.assemble_df['Age']=(self.assemble_df['Experimental_Date']-self.assemble_df['Date of Birth']).dt.days
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            new_error='unable to assemble metadata'
            meta_assemble_errors = []
            meta_assemble_errors.append(new_error)

    def metadata_checker_filemaker(self):
        """
        Ensure the metadata collected from the database matches the signal files.
        """
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
        """
        Save the dataframe derived from the database to a csv file and assign the file path to self.metadata attribute.
        """
        print("save_filemaker()")
        self.metadata_list.addItem("Creating csv file...")
        self.metadata = os.path.join(self.mothership,"metadata.csv")
        try:
            self.assemble_df.to_csv(self.metadata, index = False)
            self.metadata_list.clear()
            self.metadata_list.addItem(self.metadata)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            if type(e) == PermissionError:
                reply = QMessageBox.information(self, 'File in use', 'One or more of the files you are trying to save is open in another program.', QMessageBox.Ok)
      
    def get_autosections(self):
        """
        Prompt the user to select a previously made automated BASSPRO settings file.
        """
        print("get_autosections()")
        try:
            file_name = QFileDialog.getOpenFileNames(self, 'Select files', str(self.mothership))
            n = 0
            for x in range(len(file_name[0])):
                if file_name[0][x].endswith('.csv'):
                    if os.path.basename(file_name[0][x]).startswith("auto_sections") | os.path.basename(file_name[0][x]).startswith("autosections"):
                        self.autosections = file_name[0][x]
                        n += 1
                        for item in self.sections_list.findItems("auto_sections",Qt.MatchContains):
                            self.sections_list.takeItem(self.sections_list.row(item))
                        self.sections_list.addItem(self.autosections)
                    elif os.path.basename(file_name[0][x]).startswith("manual_sections"):
                        self.mansections = file_name[0][x]
                        n += 1
                        for item in self.sections_list.findItems("manual_sections",Qt.MatchContains):
                            self.sections_list.takeItem(self.sections_list.row(item))
                        self.sections_list.addItem(self.mansections)
                    elif os.path.basename(file_name[0][x]).startswith("basics"):
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

    def input_directory_r(self):
        """
        Prompt the user to select input files for STAGG.
        """
        print("input_directory_r()")
        input_dir_r = QFileDialog.getOpenFileNames(self, 'Choose STAGG input files from BASSPRO output', self.mothership)
        if all(file.endswith(".json") or file.endswith(".RData") for file in input_dir_r[0]):
            if self.stagg_list != []:
                reply = QMessageBox.information(self, 'Clear STAGG input list?', 'Would you like to keep the previously selected STAGG input files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    self.breath_list.clear()
                    self.stagg_list = []
            self.stagg_list = [file for file in input_dir_r[0] if file.endswith(".json")==True or file.endswith(".RData")==True]
            for x in self.stagg_list:
                self.breath_list.addItem(x)
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
    
#endregion
    def py_message(self):
        """
        Ensure the user has selected an output directory and prompt them to do so if they haven't, check that the required input for BASSPRO has been selected, launch BASSPRO, detect the JSON files produced after BASSPRO has finished and populate self.stagg_list with the file paths to those JSON files.
        """
        print("py_message()")
        try:
            self.dir_checker(self.output_dir_py,self.py_output_folder,"BASSPRO")
            self.get_bp_reqs()
            self.pything_to_do()
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
        """
        Assign the file paths to the attributes, ensure that all required STAGG input has been selected and prompt the user to select whatever is missing, and launch STAGG.
        """
        print("r_message()")
        self.variable_config = self.v.configs["variable_config"]["path"]
        self.graph_config = self.v.configs["graph_config"]["path"]
        self.other_config = self.v.configs["other_config"]["path"]
        if any([self.v.configs[key]['path'] == "" for key in self.v.configs]):
            if self.stagg_list == []:
                print("no stagg for you")
            else:
                QMessageBox.question(self, 'Missing STAGG settings', f"One or more STAGG settings files are missing.", QMessageBox.OK, QMessageBox.OK)
        else:
            self.rthing_to_do()

    def dir_checker(self,output_folder,output_folder_parent,text):
        """
        Ensure the user has selected an output directory and prompt them to do so if they haven't.
        """
        print("dir_checker()")
        self.output_folder = ""
        self.output_folder_parent = ""
        if self.mothership == "":
            # If the variable that stores the user-chosen output directory path is empty, open a dialog that prompts the user to choose the directory:
            try:
                self.mothership = QFileDialog.getExistingDirectory(self, f'Choose directory for {text} output', str(self.mothership))
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
        if not os.path.exists(self.mothership):
            # If the variable that stores the user-chosen output directory path is NOT empty, but that path does not exist (as would occur if the output directory chosen was located on an external hard drive that was unplugged at some point or located on a server that the user lost connection to), open a dialog that prompts the user to choose the directory:
            try:
                self.mothership = QFileDialog.getExistingDirectory(self, f'Previously chosen directory does not exist. Choose a different directory for {text} output', str(self.mothership))
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
        if output_folder_parent == "":
            # If the variable holding the output directory's directory path (either Main.py_output_folder or Main.r_output_folder) is empty, populate it with the path to either BASSPRO_output or STAGG_output;
            output_folder_parent = os.path.join(self.mothership,f"{text}_output")
            try:
                # If that path doesn't exist, make it:
                os.makedirs(output_folder_parent)
                self.output_folder_parent = output_folder_parent
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
        else:
            self.output_folder_parent = output_folder_parent
            # If that variable is populated with a path, test its existence:
            if not os.path.exists(self.output_folder_parent):
                try:
                    os.makedirs(self.output_folder_parent)
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
        if output_folder == "":
            output_folder = os.path.join(self.output_folder_parent, f'{text}_output_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
            # If the variable holding the output directory's path (either Main.output_dir_py or Main.output_dir_r) is empty, populate it with the timestamped path within either BASSPRO_output folder or STAGG_output folder:
            if not os.path.exists(output_folder):
                # If the path doesn't exist, make it:
                try:
                    os.makedirs(output_folder)
                    self.output_folder = output_folder
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
        else:
            self.output_folder = output_folder
            # If that variable is populated with a path, test its existence:
            if not os.path.exists(self.output_folder):
                try:
                    os.makedirs(self.output_folder)
                except Exception as e:
                    print(f'{type(e).__name__}: {e}')
                    print(traceback.format_exc())
        if any(Path(self.output_folder).iterdir()) == True:
            if all("config" in file for file in os.listdir(self.output_folder)):
                print("just configs")
            else:
                reply = QMessageBox.question(self, f'Confirm {text} output directory', 'The current output directory has files in it that may be overwritten.\n\nWould you like to create a new output folder?\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    output_folder_parent = os.path.dirname(output_folder)
                    self.output_folder = os.path.join(output_folder_parent, f'{text}_output_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
                    os.makedirs(self.output_folder)
    
    def pything_to_do(self):
        """
        Copy the required BASSPRO input other than the signal files and the breathcaller_config.json file to the timestamped BASSPRO output folder (self.output_dir_py) and run self.launch_worker().
        """
        print("pything_to_do()")
        if self.output_folder != "":
            self.output_dir_py = self.output_folder

            # Copying the relevant config files to the output directory:
            shutil.copyfile(self.metadata, os.path.join(self.output_dir_py, f"metadata_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv"))
            shutil.copyfile(f'{Path(__file__).parent}/breathcaller_config.json', os.path.join(self.output_dir_py, f"breathcaller_config_{os.path.basename(self.output_dir_py).lstrip('py_output')}.txt"))
           
            if self.autosections != "":
                shutil.copyfile(self.autosections, os.path.join(self.output_dir_py, f"auto_sections_{os.path.basename(self.output_dir_py).lstrip('BASSPRO_output')}.csv"))
      
            if self.mansections != "":
                shutil.copyfile(self.mansections, os.path.join(self.output_dir_py, f"manual_sections_{os.path.basename(self.output_dir_py).lstrip('BASSPRO_output')}.csv"))
            if self.basicap != "":
                shutil.copyfile(self.basicap, os.path.join(self.output_dir_py, f"basics_{os.path.basename(self.output_dir_py).lstrip('py_output')}.csv"))
            with open(f'{Path(__file__).parent}/gui_config.json','w') as gconfig_file:
                json.dump(self.gui_config,gconfig_file)
            shutil.copyfile(f'{Path(__file__).parent}/gui_config.json', os.path.join(self.output_dir_py, f"gui_config_{os.path.basename(self.output_dir_py).lstrip('BASSPRO_output')}.txt"))
            
            print('pything_to_do thread id',threading.get_ident())
            print("pything_to_do process id",os.getpid())

            # Start the BASSPRO module:
            self.launch_worker("py")
            try:
                # Check the BASSPRO output to see which signal files successfully produced JSON files:
                self.output_check()
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
    
    def launch_worker(self,branch):
        """
        Run parallel processes capped at the number of CPU's selected by the user to devote to BASSPRO or STAGG.
        """
        print('launch_worker thread id',threading.get_ident())
        print("launch_worker process id",os.getpid())
        if branch == "py":
            for job in MainGUIworker.get_jobs_py(self):
                # create a Worker
                self.workers[self.counter] = MainGUIworker.Worker(
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
            for job in MainGUIworker.get_jobs_r(self):
                # create a Worker
                self.workers[self.counter] = MainGUIworker.Worker(
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
        """
        Find the signal files that did not produce BASSPRO output.
        """
        if len(self.stagg_list) != len(self.signals):
            goodies = []
            baddies = []
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
            self.hangar.append(f"\nThe following signals files did not pass BASSPRO:\n\n{', '.join([os.path.basename(thumb) for thumb in baddies])}\n")

    def rthing_to_do(self):
        """
        Copy STAGG input to timestamped STAGG output folder, determine which STAGG scripts to use based on the presence or absence of an .RData file, and determine if self.input_dir_r needs to be a str path to directory instead of list because the list has more than 200 files, and run self.rthing_to_do_cntd().
        """
        print("rthing_to_do()")
        self.dir_checker(self.output_dir_r,self.r_output_folder,"STAGG")
        if self.output_folder != "":
            self.output_dir_r = self.output_folder
            if self.svg_radioButton.isChecked() == True:
                self.image_format = ".svg"
            elif self.jpeg_radioButton.isChecked() == True:
                self.image_format = ".jpeg"
            try:
                shutil.copyfile(self.variable_config, os.path.join(self.output_dir_r, f"variable_config_{os.path.basename(self.output_dir_r).lstrip('STAGG_output')}.csv"))
                shutil.copyfile(self.graph_config, os.path.join(self.output_dir_r, f"graph_config_{os.path.basename(self.output_dir_r).lstrip('STAGG_output')}.csv"))
                shutil.copyfile(self.other_config, os.path.join(self.output_dir_r, f"other_config_{os.path.basename(self.output_dir_r).lstrip('STAGG_output')}.csv"))
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
            if any(os.path.basename(b).endswith("RData") for b in self.stagg_list):
                self.pipeline_des = os.path.join(self.papr_dir, "Pipeline_env_multi.R")
            else:
                self.pipeline_des = os.path.join(self.papr_dir, "Pipeline.R")
            if len(self.stagg_list)>200:
                # If there are more than 200 files in Main.stagg_list, STAGG has troubles importing all of them when provided as a list of file paths, so in these cases, we would want args$JSON to be a directory path instead:
                if len(set([os.path.dirname(y) for y in self.stagg_list]))>1:
                    # If there are more than 200 files in Main.stagg_list and they come from more than one directory, we would need to have a different command line, so instead we'll regulate the user:
                    reply = QMessageBox.information(self, "That's a lot of JSON", 'The STAGG input provided consists of more than 200 files from multiple directories.\nPlease condense the files into one directory for STAGG to analyze.', QMessageBox.Ok, QMessageBox.Ok)
                else:
                    # If there are more than 200 files in Main.stagg_list but they all come from the same directory, then args$JSON (Main.input_dir_r on our end) needs to be a directory path instead.
                    self.input_dir_r = os.path.dirname(self.stagg_list[0])
                    self.rthing_to_do_cntd()
            else:
                # If there aren't a ridiculous number of json files in Main.stagg_list, then we just need to render the list of file paths into an unbracketed string so that STAGG can recognize it as a list. STAGG didn't like the brackets.
                self.input_dir_r = ','.join(item for item in self.stagg_list)
                self.rthing_to_do_cntd()
    
    def rthing_to_do_cntd(self):
        """
        Ensure the STAGG script exists, prompt the user to indicate where the Rscript.exe file is, and run self.launch_worker().
        """
        if Path(self.pipeline_des).is_file():
            # Make sure the path stored in gui_config.json is an Rscript executable file:
            if os.path.basename(self.gui_config['Dictionaries']['Paths']['rscript']) == "Rscript.exe":
                if os.path.exists(self.gui_config['Dictionaries']['Paths']['rscript']):
                    # If it is an executable file, then that's the path we'll deliver as an argument to the command line.
                    self.rscript_des = self.gui_config['Dictionaries']['Paths']['rscript']
                else:
                    reply = QMessageBox.information(self, 'Rscript not found', 'Rscript.exe path not defined. Would you like to select the R executable?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                    if reply == QMessageBox.Ok:
                        # User provides the path to the Rscript executable and it's saved as a string in gui_config.json:
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
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
        else:
            # If Main.pipeline_des (aka the first STAGG script file path) isn't a file, then the STAGG scripts aren't where they're supposed to be.
            reply = QMessageBox.information(self, 'STAGG scripts not found', 'BASSPRO-STAGG cannot find the scripts for STAGG. Check the BASSPRO-STAGG folder for missing files or directories.', QMessageBox.Ok, QMessageBox.Ok)

#endregion

# %%
