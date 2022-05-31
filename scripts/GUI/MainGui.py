"""
BASSPRO-STAGG GUI

Signficant contributions and help from Chris Ward, Savannah Lusk, Andersen Chang, and Russell Ray.

version 5 trillion
"""



import os
import traceback

# general
from glob import glob
from pathlib import Path
import re
import pyodbc
import shutil
from datetime import datetime, timedelta

# data parsing
import json
import csv
import pandas as pd
from bs4 import BeautifulSoup as bs

# multithreading
import queue
import threading

# pyqt
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtCore import QThreadPool, pyqtSlot, Qt, QTimer

# Local imports
from thinbass_controller import Thinbass
from util import Settings, ask_user_ok, ask_user_yes, generate_unique_id, nonblocking_msg, notify_error, notify_info
from auto import AutoSettings
from basic import BasicSettings
from manual import ManualSettings
from AnnotGUI import MetadataSettings
from config import GraphSettings, OtherSettings, VariableSettings, ConfigSettings
from tools.import_cols_vals_thread import ColValImportThread
import MainGUIworker
from ui.form import Ui_Plethysmography

# Chris's scripts
from tools.columns_and_values_tools import columns_and_values_from_settings

# TODO: only for development!
AUTOLOAD = 'shaun' in os.getcwd()

print(os.getcwd())

CONFIG_DIR = os.path.join("scripts","GUI","config")

class Plethysmography(QMainWindow, Ui_Plethysmography):
    """
    The Plethysmography class inherits widgets and layouts of Ui_Plethysmography and defines the main GUI.

    Parameters
    --------
    QMainWindow: class
        The Plethysmography class inherits properties and methods from the QMainWindow class.
    Ui_Plethysmography: class
        The Plethysmography class inherits widgets and layouts defined in the Ui_Plethysmography class.
    """

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
        self.qThreadpool: QThreadPool
        
        self.basspro_path: str
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
        self.stagg_input_files: list
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
        sef.basspro_output_dir: str
            The path to the directory containing the BASSPRO output directories.
        self.r_output_folder: str
            The path to the directory containing the STAGG output directories. 
        self.buttonDict_variable: dict
            The nested dictionary used to populate and save the text and RadioButton states of Config.variable_table (TableWidget) in the Config subGUI.
        self.loop_menu: dict
            The nested dictionary used to populate and save the text, CheckBox, ComboBox, and CheckableComboBox
            states of Config.loop_table (TableWidget) in the Config subGUI.
        
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
        self.stagg_settings_window()
            This method instantiates the Config class.
        self.manual_settings_window()
            This method instantiates the Manual class.
        self.auto_settings_window()
            This method instantiates the Auto class.
        self.basic_settings_window()
            This method instantiates the Basic class.
        self.metadata_annot_window()
            This method instantiates the Annot class.
        """
        super(Plethysmography, self).__init__()

        self.setupUi(self)
        self.setWindowTitle("Plethysmography Analysis Pipeline")
        self.showMaximized()

        # Analysis parameters
        os.chdir(os.path.join(Path(__file__).parent.parent.parent))

        # Access configuration settings for GUI in gui_config.json:
        with open(os.path.join(CONFIG_DIR, 'gui_config.json'), 'r') as config_file:
            self.gui_config = json.load(config_file)

        # Access timestamp settings for storing timestamper results in timestamps.json:
        with open(os.path.join(CONFIG_DIR, 'timestamps.json'), 'r') as stamp_file:
            self.stamp = json.load(stamp_file)

        # Access configuration settings for the basspro in breathcaller_config.json:
        with open(os.path.join(CONFIG_DIR, 'breathcaller_config.json'), 'r') as bconfig_file:
            self.bc_config = json.load(bconfig_file)

        # Access references for the basspro in breathcaller_config.json:
        with open(os.path.join(CONFIG_DIR, 'reference_config.json'), 'r') as rconfig_file:
            self.rc_config = json.load(rconfig_file)

        # Threading attributes
        self.qthreadpool = QThreadPool()
        self.qthreadpool.setMaxThreadCount(1)
        self.monitors = {}  # store callback loops used to monitor processes
        
        # Use for importing cols/vals from basspro json files
        self.import_thread = None
        self.imported_files = None
        self.col_vals = None


        # Load variables with paths for BASSPro and StaGG stored in gui_config dictionary:
        self.basspro_path = os.path.abspath('scripts/python_module.py')
        self.papr_dir = os.path.abspath('scripts/papr')


        # STAGG Settings
        self.variable_config_df = None
        self.graph_config_df = None
        self.other_config_df = None
        self.breath_df = []
        self.input_dir_r=""

        self.mp_parsed = {}
        self.mp_parserrors = []
        self.p_mouse_dict={}
        self.m_mouse_dict={}
        self.metadata_warnings = {}
        self.metadata_pm_warnings = []
        self.missing_plyuids = []
        self.metadata_passlist = []
        self.tsbyfile = {}

        # Basspro settings
        self.autosections_df = None
        self.mansections_df = None
        self.metadata_df = None
        self.basicap_df = None

         # Populate GUI widgets with experimental condition choices: 
        self.necessary_timestamp_box.addItems(list(self.bc_config['Dictionaries']['Auto Settings']['default'].keys()))
        self.parallel_combo.addItems([str(num) for num in range(1, os.cpu_count()+1)])



        # Autoload configuration
        if AUTOLOAD:
            self.signal_files_list.addItem("/home/shaun/Projects/Freelancing/BASSPRO_STAGG/BASSPRO-STAGG/data/Test Dataset/Text files/M39622.txt")
            self.metadata = "/home/shaun/Projects/Freelancing/BASSPRO_STAGG/BASSPRO-STAGG/data/Test Dataset/metadata.csv"
            self.workspace_dir = "/home/shaun/Projects/Freelancing/BASSPRO_STAGG/BASSPRO-STAGG/output"
            self.autosections = "/home/shaun/Projects/Freelancing/BASSPRO_STAGG/BASSPRO-STAGG/data/Test Dataset/BASSPRO Configuration Files/auto_sections.csv"
            self.basicap = "/home/shaun/Projects/Freelancing/BASSPRO_STAGG/BASSPRO-STAGG/data/Test Dataset/BASSPRO Configuration Files/basics.csv"

            # Pick either RData or json
            if False:
                self.breath_list.addItem("/home/shaun/Projects/Freelancing/BASSPRO_STAGG/BASSPRO-STAGG/data/Test Dataset/R Environment/myEnv_20220324_140527.RData")
            else:
                json_glob = "/home/shaun/Projects/Freelancing/BASSPRO_STAGG/BASSPRO-STAGG/data/Test Dataset/JSON files/*"
                for json_path in glob(json_glob):
                    self.breath_list.addItem(json_path)

    ## Getters & Setters ##
    @property
    def workspace_dir(self):
        return self.output_path_display.text()

    @workspace_dir.setter
    def workspace_dir(self, new_dir):
        self.output_path_display.setText(new_dir)

    @property
    def metadata(self):
        if self.metadata_list.count():
            return self.metadata_list.item(0).text()
        else:
            return None

    @metadata.setter
    def metadata(self, filepath):
        # TODO: handle None or "" input
        if MetadataSettings.validate(filepath):
            self.metadata_df = MetadataSettings.attempt_load(filepath)
            if self.metadata_df is not None:
                self.metadata_list.clear()
                self.metadata_list.addItem(filepath)

    @property
    def signal_files(self):
        return [self.signal_files_list.item(i).text() for i in range(self.signal_files_list.count())]

    @property
    def autosections(self):
        return self.get_settings_file_from_list("auto")

    @autosections.setter
    def autosections(self, filepath):
        # TODO: handle None or "" input
        if AutoSettings.validate(filepath):
            self.autosections_df = AutoSettings.attempt_load(filepath)
            if self.autosections_df is not None:
                # Remove old autosections
                for item in self.sections_list.findItems("auto", Qt.MatchContains):
                    self.sections_list.takeItem(self.sections_list.row(item))
                
                # Add new one
                self.sections_list.addItem(filepath)
                print(self.autosections_df.to_dict())

    @property
    def mansections(self):
        return self.get_settings_file_from_list("manual")

    @mansections.setter
    def mansections(self, filepath):
        # TODO: handle None or "" input
        if ManualSettings.validate(filepath):
            self.mansections_df = ManualSettings.attempt_load(filepath)
            if self.mansections_df is not None:
                # Remove old mansections
                for item in self.sections_list.findItems("manual", Qt.MatchContains):
                    self.sections_list.takeItem(self.sections_list.row(item))

                # Add new one
                self.sections_list.addItem(filepath)

    @property
    def config_data(self):
        # Get all config data collectively
        var_df = self.variable_config_df
        graph_df = self.graph_config_df
        other_df = self.other_config_df
        # If all configs are None, return None
        if all([config is None for config in [var_df, graph_df, other_df]]):
            return None
        # Otherwise return dict of data
        else:
            return {'variable': var_df, 'graph': graph_df, 'other': other_df}
    
    @config_data.setter
    def config_data(self, new_data):
        # Set all config data collectively
        if new_data is None:
            self.variable_config_df = None
            self.graph_config_df = None
            self.other_config_df = None
        else:
            self.variable_config_df = new_data['variable'].copy()
            self.graph_config_df = new_data['graph'].copy()
            self.other_config_df = new_data['other'].copy()

    @property
    def variable_config(self):
        return self.get_config_file_from_list("variable")

    @variable_config.setter
    def variable_config(self, filepath):
        # Setting to None or ""
        if not filepath:
            self.variable_config_df = None
            # Remove old config
            for item in self.variable_list.findItems("variable", Qt.MatchContains):
                self.variable_list.takeItem(self.variable_list.row(item))

        elif VariableSettings.validate(filepath):
            self.variable_config_df = VariableSettings.attempt_load(filepath)
            if self.variable_config_df is not None:
                # Remove old config
                for item in self.variable_list.findItems("variable", Qt.MatchContains):
                    self.variable_list.takeItem(self.variable_list.row(item))

                # Add new one
                self.variable_list.addItem(filepath)

    @property
    def graph_config(self):
        return self.get_config_file_from_list("graph")

    @graph_config.setter
    def graph_config(self, filepath):
        # Setting to None or ""
        if not filepath:
            self.graph_config_df = None
            # Remove old config
            for item in self.variable_list.findItems("graph", Qt.MatchContains):
                self.variable_list.takeItem(self.variable_list.row(item))

        elif GraphSettings.validate(filepath):
            self.graph_config_df = GraphSettings.attempt_load(filepath)
            if self.graph_config_df is not None:
                # Remove old config
                for item in self.variable_list.findItems("graph", Qt.MatchContains):
                    self.variable_list.takeItem(self.variable_list.row(item))

                # Add new one
                self.variable_list.addItem(filepath)

    @property
    def other_config(self):
        return self.get_config_file_from_list("other")

    @other_config.setter
    def other_config(self, filepath):
        # Setting to None or ""
        if not filepath:
            self.other_config_df = None
            # Remove old config
            for item in self.variable_list.findItems("other", Qt.MatchContains):
                self.variable_list.takeItem(self.variable_list.row(item))

        elif OtherSettings.validate(filepath):
            self.other_config_df = OtherSettings.attempt_load(filepath)
            if self.other_config_df is not None:
                # Remove old config
                for item in self.variable_list.findItems("other", Qt.MatchContains):
                    self.variable_list.takeItem(self.variable_list.row(item))

                # Add new one
                self.variable_list.addItem(filepath)

    @property
    def basicap(self):
        return self.get_settings_file_from_list("basic")

    @basicap.setter
    def basicap(self, filepath):
        if BasicSettings.validate(filepath):
            self.basicap_df = BasicSettings.attempt_load(filepath)
            if self.basicap_df is not None:
                # Remove old basic settings
                for item in self.sections_list.findItems("basics",Qt.MatchContains):
                    self.sections_list.takeItem(self.sections_list.row(item))
                
                # Add new one
                self.sections_list.addItem(filepath)

    @property
    def stagg_input_files(self):
        return [self.breath_list.item(i).text() for i in range(self.breath_list.count())]
    ##         ##

    def get_settings_file_from_list(self, type):
        all_settings = [self.sections_list.item(i).text() for i in range(self.sections_list.count())]

        for settings_file in all_settings:

            if (type == 'auto' and AutoSettings.validate(settings_file)) or \
               (type == 'manual' and ManualSettings.validate(settings_file)) or \
               (type == 'basic' and BasicSettings.validate(settings_file)):
                return settings_file
        return None

    def dir_contains_valid_import_files(self, dir):
        """
        Check if `dir` contains any valid files for importing
        """
        files = os.listdir(dir)
        for file in files:
            for checker in [MetadataSettings.validate,
                            AutoSettings.validate,
                            ManualSettings.validate,
                            BasicSettings.validate]:
                if checker(file):
                    return True
        return False

    def delete_setting_file(self):
        a = self.sections_list.currentItem()
        if a:
            self.hangar.append(f"Deleted settings: {a.text()}")
            self.sections_list.takeItem(self.sections_list.row(a))
            del a

    def timestamp_dict(self):
        """
        Check if the user has selected signal files - prompt them with QMessageBox and call self.get_signal_files() if they haven't.
        Check if the user has selected an experimental setup via self.necessary_timestamp_box (ComboBox) to which the timestamps of the signal files selected can be compared - prompt them with QMessageBox.
        Check if the user-selected signal files are text formatted - prompt them with QMessageBox and call self.get_signal_files() if not.
        Populate self.stamp with keys based on directories of signal files.
        Call self.grabTimeStamps() and self.checkFileTimeStamps().
        Populate self.stamp with self.tsbyfile and self.check dictionaries.
        Dump self.stamp into a JSON saved in the same directory as the first signal file listed in self.signals.
        Populate self.hangar (TextEdit) with summary of timestamp review.

        Parameters
        --------
        self.stamp: dict
            This attribute is a nested dictionary loaded from timestamps.json. It contains a populated dictionary with the default timestamps of multiple experimental setups and an empty dictionary that will be populated by the timestamps of signal files selected by the user.
        self.necessary_timestamp_box: QComboBox
            A comboBox inherited from Ui_Plethysmography that is populated with the experimental setups for which the GUI has default automated BASSPRO settings. These experimental setups are sourced from the keys of the "default" dictionary nested in the "Auto Settings" dictionary loaded from the breathcaller_config.json file.
        self.bc_config: dict
            This attribute is a nested dictionary loaded from breathcaller_config.json. It contains the default settings of multiple experimental setups for basic, automated, and manual BASSPRO settings and  the most recently saved settings for automated and basic BASSPRO settings. See the README file for more detail.
        self.signals: list
            The list of file paths of the user-selected .txt signal files that are analyzed by BASSPRO. The timestamps of these files are compared to those of the experimental setup selected by the user via self.necessary_timestamp_box (ComboBox).
        self.tsbyfile: dict
            This attribute stores a nested dictionary containing the timestamps for every signal file, as well as listing the file and the offending timestamp for duplicate timestamps, missing timestamps, and novel timestamps.
        self.check: dict
            This attribute is a nested dictionary populated with the dictionary variables goodfiles, filesmissingts, filesextrats, and new_ts.
        self.hangar: QTextEdit
            This attribute is a QTextEdit inherited from the Ui_Plethysmography class that prints a summary of the timestamp review once completed.
        
        Outputs
        --------
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        self.need: dict
            This attribute refers to the dictionary nested in self.bc_config (breathcaller_config.json) based on the current text of self.necessary_timestamp_box whose keys correspond to timestamps to which the those of the signal files in self.signals (list) will be compared.
        self.stamp: dict
            This attribute is a nested dictionary loaded from timestamps.json and populated by the timestamps of signal files selected by the user via self.tsbyfile and self.check dictionaries.
        self.hangar: QTextEdit
            This attribute is a QTextEdit inherited from the Ui_Plethysmography class that prints a summary of the timestamp review once completed.
        
        Outcomes
        --------
        self.grabTimeStamps()
            This method iterates through user-selected signal files to compare the signal files' timestamps to the timestamps of the user-selected experimental setup.
        self.checkFileTimeStamps()
            This method iterates through contents of self.tsbyfile (dict) to compare them to the default timestamps of the user-selected experimental setup and populate self.new_check (dict) with offending timestamps and their signals.
        """

        self.stamp['Dictionaries']['Data'] = {}
        combo_need = self.necessary_timestamp_box.currentText()
        if self.signal_files_list.count() == 0:
            reply = QMessageBox.information(self, 'Missing signal files', 'No signal files selected.\nWould you like to select a signal file directory?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.get_signal_files()
        elif combo_need == "Select dataset...":
            reply = QMessageBox.information(self, 'Missing dataset', 'Please select one of the options from the dropdown menu above.', QMessageBox.Ok)
        # TODO: This elif below may not be necessary because further upstream, when the user is actually selecting signal files, there's a functionality that rejects any files that don't end in .txt and tells the user what was rejected.
        elif not all(x.endswith(".txt") for x in self.signal_files):
            reply = QMessageBox.information(
                self,
                'Incorrect file format',
                'The selected signal files are not text formatted.\nWould you like to select a different signal file directory?',
                QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.get_signal_files()
        else:
            # wut?
            # I'm leaving this weird epoch, condition stuff in here because I don't want to break anything but I don't remember why I did this. Maybe I thought comparisons for multiple signal file selections would be saved to the same dictionary? T
            epoch = [os.path.basename(Path(self.signal_files[0]).parent.parent)]
            condition = [os.path.basename(Path(self.signal_files[0]).parent)]
            
            for f in self.signal_files:
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

            if combo_need == "Custom":
                self.need = self.autosections_df.to_dict()
            print(self.need)

            self.need = self.bc_config['Dictionaries']['Auto Settings']['default'][combo_need]

            self.hangar.append("Checking timestamps...")
            # TODO: put in separate thread/process
            self.grabTimeStamps()
            self.checkFileTimeStamps()

            for e in epoch:
                for c in condition:
                    self.stamp['Dictionaries']['Data'][e][c]["tsbyfile"] = self.tsbyfile
                    for notable in self.check:
                        self.stamp['Dictionaries']['Data'][e][c][notable] = self.check[notable]  
            try:
                tpath = os.path.join(Path(self.signal_files[0]).parent,f"timestamp_{os.path.basename(Path(self.signal_files[0]).parent)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                with open(tpath,"w") as tspath:
                    tspath.write(json.dumps(self.stamp))
                    tspath.close()
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
                notify_error(title=f"{type(e).__name__}: {e}", msg=f"The timestamp file could not be written.")

            # Print summary of timestamps review to the hangar.
            self.hangar.append("Timestamp output saved.")
            self.hangar.append("---Timestamp Summary---")
            self.hangar.append(f"Files with missing timestamps: {', '.join(set([w for m in self.check['files_missing_a_ts'] for w in self.check['files_missing_a_ts'][m]]))}")
            self.hangar.append(f"Files with duplicate timestamps: {', '.join(set([y for d in self.check['files_with_dup_ts'] for y in self.check['files_with_dup_ts'][d]]))}")

            if len(set([z for n in self.check['new_ts'] for z in self.check['new_ts'][n]])) == len(self.signal_files):
                self.hangar.append(f"Files with novel timestamps: all signal files")
            else:
                self.hangar.append(f"Files with novel timestamps: {', '.join(set([z for n in self.check['new_ts'] for z in self.check['new_ts'][n]]))}")

            self.hangar.append(f"Full review of timestamps: {Path(tpath)}")


    def grabTimeStamps(self):
        """
        This method was adapted from a function written by Chris Ward.

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
        
        for CurFile in self.signal_files:
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
        This method was adapted from a function written by Chris Ward.

        Iterate through contents of self.tsbyfile (dict) to compare them to the default timestamps of the user-selected experimental set-up and populate self.new_check (dict) with offending timestamps and their signals.

        Parameters
        --------
        self.check: dict
            This attribute is set as an empty dictionary.
        new_ts: dict
            This variable is set as an empty dictionary.
        filesmissingts: dict
            This variable is set as an empty dictionary.
        filesextrats: dict
            This variable is set as an empty dictionary.
        goodfiles: list
            This variables is set as an empty list.
        self.tsbyfile: dict
            This attribute stores a nested dictionary containing the timestamps for every signal file, as well as listing the file and the offending timestamp for duplicate timestamps, missing timestamps, and novel timestamps.
        self.need: dict
            This attribute is a dictionary that is populated with the experimental setups for which the GUI has default automated BASSPRO settings based on the user's selection of experimental setup via the self.necessary_timestamp_box comboBox. These experimental setups are sourced from the keys of the "default" dictionary nested in the "Auto Settings" dictionary loaded from the breathcaller_config.json file.
        
        Outputs
        --------
        self.check: dict
            This attribute is a nested dictionary populated with the dictionary variables goodfiles, filesmissingts, filesextrats, and new_ts.
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

            if not error:
                goodfiles.append(os.path.basename(f))

        for m in filesmissingts:
            if len(filesmissingts[m]) == len(self.signal_files):
                filesmissingts[m] = ["all signal files"]

        if len(goodfiles) == len(self.signal_files):
            goodfiles = ["all signal files"]

        for n in filesextrats:
            if len(filesextrats[n]) == len(self.signal_files):
                filesextrats[n] = ["all signal files"]

        for p in new_ts:
            if len(new_ts[p]) == len(self.signal_files):
                new_ts[p] = ["all signal files"]

        self.check = {'good_files':goodfiles,'files_missing_a_ts':filesmissingts,
            'files_with_dup_ts':filesextrats,'new_ts':new_ts} 

    def show_annot(self):
        """
        Show the metadata settings subGUI defined in the Annot class and call Annot.show_metadata_file().

        Outcomes
        --------
        Annot.show()
            This method displays the metadata settings subGUI.
        Annot.show_metadata_file()
            This method determines the source of the metadata that will be manipulated by the user in the Annot subGUI.
        """

        # If no metadata files in play
        if self.metadata_df is None:
            notify_info("Please import a metadata file")
            return

        new_metadata = MetadataSettings.edit(self.metadata_df,
                                             self.workspace_dir)
        if new_metadata is not None:
            self.metadata_df = new_metadata

            #if self.breath_df != []:
            #    self.update_breath_df("metadata")

    def show_manual(self):
        """
        Show the manual BASSPRO settings subGUI defined in the Manual class.

        Outcomes
        --------
        Manual.show()
            This method displays the manual BASSPRO settings subGUI.
        """
        # Populate GUI widgets with experimental condition choices:
        new_settings = ManualSettings.edit(self.bc_config['Dictionaries']['Manual Settings']['default'],
                                           self.mansections_df,
                                           self.workspace_dir)
        if new_settings is not None:
            self.mansections_df = new_settings

            #if self.breath_df != []:
            #    self.update_breath_df("manual settings")

    def show_auto(self):
        """
        Show the automated BASSPRO settings subGUI defined in the Auto class.

        Outcomes
        --------
        Auto.show()
            This method displays the automated BASSPRO settings subGUI.
        """
        new_settings = AutoSettings.edit(self.bc_config['Dictionaries']['Auto Settings']['default'],
                                         self.gui_config['Dictionaries']['Settings Names']['Auto Settings'],
                                         self.rc_config['References']['Definitions'],
                                         self.signal_files,
                                         data=self.autosections_df,
                                         workspace_dir=self.workspace_dir)

        if new_settings is not None:
            self.autosections_df = new_settings

            # TODO: why?
            #if self.breath_df != []:
            #    self.update_breath_df("automated settings")


    def show_basic(self):
        """
        Show the basic BASSPRO settings subGUI defined in the Basic class.

        Outcomes
        --------
        Basic.show()
            This method displays the basic BASSPRO settings subGUI.
        """
        #self.basic_settings_window.show()
        new_settings = BasicSettings.edit(self.bc_config['Dictionaries']['AP']['default'],
                                          self.rc_config['References']['Definitions'],
                                          self.basicap_df,
                                          self.workspace_dir)
        if new_settings is not None:
            self.basicap_df = new_settings
        
        
    def prepare_stagg_settings(self):
        """
        Ensure that there is a source of variables to populate Config.variable_table with,
          then call stagg settings

        Can be sourced from:
          - metadata and (autosections or mansections)
          - self.variable_config   ------------- Get this from the listwidget ???????? ----------
          - self.stagg_input_files[0]

        NOTE: the need for 2 separate functions comes from the potentially longrunning import of
              stagg settings from JSON basspro output files
        """

        # Reset button color in case indicating import completion
        self.stagg_settings_button.setStyleSheet("background-color: #eee")

        # If we already have data for all the configs, use this
        if self.config_data is not None:
            input_data = self.config_data
            self.show_stagg_settings(input_data, self.col_vals)
        
        # Check for import options
        else:

            # Gather input options
            import_options = []
            if self.stagg_input_files:
                import_options.append('basspro_output')
            if self.metadata_df is not None and (self.autosections_df is not None or self.mansections is not None):
                import_options.append('settings')

            # We have no options!
            if len(import_options) == 0:
                error_msg = "Missing settings data!"
                error_msg += "\nPlease add sections files or basspro input"
                notify_info(error_msg)
                return

            # If we only have one option, choose it
            if len(import_options) == 1:
                selected_option = import_options[0]

            # If more than 1 option, ask user what they want to do
            else:
                thinb = Thinbass(self)
                if thinb.exec():
                    selected_option = thinb.get_value()
                else:
                    return

            if selected_option == 'basspro_output':
                # Import currently running
                if self.import_thread:
                    if ask_user_yes("Import in progress",
                                    "An import is currently running. Would you like to terminate the process?"):
                        self.finish_import(kill_thread=True)

                # If we have imported and no selection change and there is data present
                #   - use this data!
                elif self.col_vals and self.imported_files == self.stagg_input_files and len(self.col_vals):
                    # Create default df with imported variables
                    variable_names = self.col_vals.keys()
                    var_config_df = ConfigSettings.get_default_variable_df(variable_names)

                    # graph_df/other_df are None
                    input_data = {
                        'variable': var_config_df,
                        'graph': None,
                        'other': None}
                    self.show_stagg_settings(input_data, self.col_vals)

                # Run a new import!
                else:

                    # If we have an RData file, get jsons from same directory
                    if len(self.stagg_input_files) == 1 and self.stagg_input_files[0].lower().endswith('.rdata'):
                        rdata_dir = os.path.dirname(self.stagg_input_files[0])
                        json_files = glob(os.path.join(rdata_dir, '*.json'))
                        
                        # If no jsons, notify and quit
                        if len(json_files) == 0:
                            notify_error(f"Cannot find json files in RData directory:\n{rdata_dir}")
                            return
                    else:
                        json_files = self.stagg_input_files

                    # load basspro output files
                    self.import_thread = ColValImportThread(json_files)
                    
                    # Print out any progress messages emitted by thread
                    self.import_thread.progress.connect(self.hangar.append)
                    
                    # Call finish method on emitting finished signal
                    self.import_thread.finished.connect(self.finish_import)

                    self.hangar.append("Importing columns and values from json...")

                    # Disable any change in stagg input files
                    self.breath_files_button.setEnabled(False)
                    self.import_thread.start()
                    notify_info("Starting import, try again when import is done")

            elif selected_option == 'settings':
                self.col_vals = columns_and_values_from_settings(self.metadata_df, self.autosections_df, self.mansections_df)

                # Create default df with imported variables
                variable_names = self.col_vals.keys()
                var_config_df = ConfigSettings.get_default_variable_df(variable_names)

                # graph_df/other_df are None
                input_data = {
                    'variable': var_config_df,
                    'graph': None,
                    'other': None}
                self.show_stagg_settings(input_data, self.col_vals)

    @staticmethod
    def get_default_variable_df(self, variable_names):
        default_values = [0, 0, 0, 0, 0, 0, 0, []]
        default_data = [[var_name, var_name] + default_values for var_name in variable_names]
        variable_table_df = pd.DataFrame(
            default_data,
            columns=["Column",
                     "Alias",
                     "Independent",
                     "Dependent",
                     "Covariate",
                     "ymin",
                     "ymax",
                     "Poincare",
                     "Spectral",
                     "Transformation"])
        return variable_table_df

    def finish_import(self, kill_thread=False):
        """
        Called at the conclusion of reading columns and values from Basspro json output
             OR
               at the cancellation of existing import process
        """

        # TODO: Make sure there is no overlap of new thread and an old thread waiting to die
        #   -do proper cleanup!
        if self.import_thread:
            if kill_thread:
                self.hangar.append("Killing thread...")
                # TODO: ensure the thread cleans up properly!
                # Remove finished callback
                self.import_thread.quit()

            else:
                self.hangar.append("Done!")
                self.stagg_settings_button.setStyleSheet("background-color: #0f0")
                self.col_vals = self.import_thread.output
                self.imported_files = self.stagg_input_files

            self.breath_files_button.setEnabled(True)
            self.import_thread = None

    def show_stagg_settings(self, input_data, col_vals):
        """
        Ensure that there is a source of variables to populate Config.variable_table with and run check_stagg_settings_inputs() to ensure that those sources are viable, run self.setup_table_config() to populate Config.variable_table (TableWidget), and either show the STAGG settings subGUI or show a Thorbass dialog to guide the user through providing the required input if there is no input.

        Parameters
        --------
        self.buttonDict_variable: dict
            This attribute is a nested dictionary used to populate and save the text and RadioButton states of Config.variable_table (TableWidget) in the Config subGUI.
        Config.configs: dict
            This attribute is populated with a nested dictionary in which each item contains a dictionary unique to each settings file - variable_config.csv, graph_config.csv, and other_config.csv. Each dictionary has the following key, value items: "variable", the Plethysmography class attribute that refers to the file path to the settings file; "path", the string file path to the settings file; "frame", the Config class attribute that refers to the dataframe; "df", the dataframe.
        self.stagg_input_files: list
            This attribute is a list of user-selected signal file paths.
        self.metadata: str
            This attribute refers to the file path of the metadata file.
        self.autosections: str
            This attribute refers to the file path of the automated BASSPRO settings file.
        self.mansections: str
            This attribute refers to the file path of the manual BASSPRO settings file.
        self.basicap: str
            This attribute refers to the file path of the basic BASSPRO settings file.
        Config.variable_table: QTableWidget
            This TableWidget is defined in the Config class, displayed in the STAGG settings subGUI, and populated with rows based on the list of variables (self.breath_df).
        Thinbass: class
            This class is used when the user has metadata and BASSPRO settings files as well as JSON files - either can be a source for building the variable list that populates the STAGG Settings subGUI. This dialog prompts them to decide which source they'd like to use.
        Thorbass: class
            This class defines a specialized dialog that prompts the user to provide the necessary input for the function they are trying to use.
        
        Outputs
        --------
        Config.variable_table: QTableWidget
            cellChanged signals are assigned to the TableWidgets cells for two slots: Config.no_duplicates() and Config.update_loop().]

        Outcomes
        --------
        self.check_stagg_settings_inputs()
            This method ensures that the file paths that populate the attributes required to show the STAGG settings subGUI exist and their contents are accessible, and provides feedback to the user on what is missing if anything.
        Config.check_load_variable_config()
            This method checks the user-selected STAGG settings files to ensure they exist and they are the correct file format and they begin with either "variable_config", "graph_config", or "other_config", triggering a MessageBox or dialog to inform the user if any do not and loading the file as a dataframe if they do.
        self.setup_table_config()
            This method populates self.buttonDict_variable with widgets and text and populates Config.variable_table with the contents of self.buttonDict_variable.
        Config.no_duplicates()
            This method automatically renames the variable in the "Alias" column of Config.variable_table (TableWidget) to avoid duplicate variable names.
        Config.update_loop()
            This method updates the contents of Config.clades_other_dict with the contents of self.loop_menu and then update the contents of Config.loop_table with the newly updated contents of Config.clades_other_dict.
        Config.show()
            This method displays the STAGG settings subGUI.
        Thinbass.show()
            This method displays the specialized Thinbass dialog.
        Thorbass.show()
            This method displays the specialized Thorbass dialog.
        self.new_variable_config()
            Run self.get_bp_reqs() and self.check_stagg_settings_inputs() to ensure that BASSPRO has the required input, run self.setup_table_config() to populate Config.variable_table (TableWidget), and show the STAGG settings subGUI.
        """
        # Open Config editor GUI
        # TODO: align variable_config name with variable_table name in Config class
        new_config_data = ConfigSettings.edit(self.rc_config['References']['Definitions'],
                                              input_data,
                                              col_vals,
                                              self.workspace_dir)
        if new_config_data is not None:
            self.config_data = new_config_data


    def update_breath_df(self, updated_file):
        """
        Ask the user if they want to update the self.breath_df list to include the
          latest updates to the metadata and/or the automated or manual BASSPRO settings
        If so, reset and repopulate the STAGG settings subGUI widgets, namely Config.variable_table.

        Parameters
        --------
        self.breath_df: list
            This attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        self.metadata: str
            This attribute refers to the file path of the metadata file.
        self.autosections: str
            This attribute refers to the file path of the automated BASSPRO settings file.
        self.mansections: str
            This attribute refers to the file path of the manual BASSPRO settings file.
        self.basspro_path: str
            The path to the BASSPRO module script.
        self.buttonDict_variable: dict
            This attribute is either an empty dictionary or a nested dictionary used to populate and save the text and RadioButton states of Config.variable_table (TableWidget) in the Config subGUI.
        Config.vdf: dict
            This Config attribute is either an empty dictionary or a nested dictionary populated with only those settings from variable_config file that are not null or 0.
        Config.variable_table: QTableWidget
            This TableWidget is defined in the Config class, displayed in the STAGG settings subGUI, and populated with rows based on the list of variables (self.breath_df).
        
        Outputs
        --------
        old_bdf: list
            This attribute is a copy of self.breath_df before it is emptied.
        self.breath_df: list
            This attribute is emptied, repopulated with variables from the BASSPRO module script, the metadata, and the BASSPRO settings, and compared to old_bdf.
        reply: QMessageBox
            If there is a difference between old_bdf and self.breath_df, then this MessageBox asks the user if they would like to update the list of variables presented in the STAGG settings subGUI and warned that unsaved changes may be lost.
        self.missing_meta: list
            This attribute is a list of file paths for files that could not be accessed.
        self.buttonDict_variable: dict
            The relevant items of this nested dictionary are updated based on corresponding values in Config.vdf (dict).
        Config.variable_table: QTableWidget
            cellChanged signals are assigned to the TableWidgets cells for two slots: Config.no_duplicates() and Config.update_loop().

        Outcomes
        --------
        self.try_open(path)
            This method ensures that the file passed and its contents are accessible.
        Config.setup_table_config()
            This Config class method assigns delegates to Config.variable_table and Config.loop_table, sets self.buttonDict_variable as an empty dictionary, repopulates it with text and widgets based on items listed in self.breath_df (list), assigns the RadioButton widgets of each row to a ButtonGroup, populates Config.variable_table (TableWidget) with the contents of self.buttonDict_variable, assigns toggled signals slotted for Config.add_combos() to the RadioButtons in self.buttonDict_variable that correspond to those in the "Independent" and "Covariate" columns of the TableWidget, and adjusts the size of the cells of Config.variable_table.
        Config.no_duplicates()
            This method automatically renames the variable in the "Alias" column of Config.variable_table (TableWidget) to avoid duplicate variable names.
        Config.update_loop()
            This method updates the contents of Config.clades_other_dict with the contents of self.loop_menu and then update the contents of Config.loop_table with the newly updated contents of Config.clades_other_dict.
        Config.load_custom_config()
            This Config class method populates Custom.custom_table based on the dependent variables selected by the user according to the dataframe derived from the variable config .csv file the user selected. 
        Config.load_graph_config()
            This Config class method populates the Xvar, Pointdodge, Facet1, and Facet2 comboBoxes with the variables selected as independent or covariate according to the variable_config .csv file; if there is no variable_config file, then it populates those comboBoxes with the variables in the dataframe read from the graph_config file and sets the comboBoxes current text.
        """
        old_bdf = self.breath_df
        self.breath_df = []
        missing_meta = []
        for p in [self.metadata, self.autosections, self.mansections]:
            if not self.try_open(p):
                missing_meta.append(p)

        try:
            with open(self.basspro_path) as bc:
                soup = bs(bc, 'html.parser')
            for child in soup.basspro_outputs.stripped_strings:
                self.breath_df.append(child)
        except Exception as e:
            missing_meta.append(self.basspro_path)

        if set(self.breath_df) != set(old_bdf):
            non_match_old = set(old_bdf) - set(self.breath_df)
            non_match_new = set(self.breath_df) - set(old_bdf)
            non_match = list(non_match_old) + list(non_match_new)
            if len(non_match)>0:
                reply = QMessageBox.question(self,
                                             f'New {updated_file} selected',
                                             'Would you like to update the variable list in STAGG configuration settings?\n\nUnsaved changes may be lost.\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    stagg_settings_window.setup_table_config()

                    for a in stagg_settings_window.variable_table_df:
                        self.buttonDict_variable[a]['Alias'].setText(stagg_settings_window.vdf[a]['Alias'])
                        for k in ["Independent","Dependent","Covariate"]:
                            if stagg_settings_window.vdf[a][k] == '1':
                                self.buttonDict_variable[a][k].setChecked(True)
                    stagg_settings_window.load_custom_config()
                    stagg_settings_window.load_graph_config()
                else:
                    self.breath_df = old_bdf

    def try_open(self,path):
        """
        Ensure that the file passed and its contents are accessible.

        Parameters
        --------
        path: str
            This argument is a file path stored in either self.metadata, self.autosections, or self.mansections.
        self.breath_df: list
            This attribute is either an empty list or populated with a list of variables derived from the metadata, BASSPRO settings, or STAGG settings.
        self.missing_meta: list
            This attribute is either an empty list or a list of file paths for files that could not be accessed.
        
        Outputs
        --------
        self.breath_df: list
            This attribute is populated with a list of variables read from the passed file.
        self.missing_meta: list
            This attribute is populated with file paths that were not accessible.  
        """
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
            return False
        return True

    def select_workspace_dir(self):
        """
        Prompt the user to choose an output directory where both BASSPRO and STAGG output will be written to, detect any relevant input that may already be present in that directory, ask the user if they would like to keep previous selections for input or replace them with the contents of the selected directory if there are previous selections for input and update self.breath_df (list).
    
        Parameters
        --------
        self.metadata: str
            This attribute refers to the file path of the metadata file.
        self.autosections: str
            This attribute refers to the file path of the automated BASSPRO settings file.
        self.mansections: str
            This attribute refers to the file path of the manual BASSPRO settings file.
        self.basicap: str
            This attribute refers to the file path of the basic BASSPRO settings file.
        self.breath_df: list
            This attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        self.output_path_display: QLineEdit
            This LineEdit inherited from the Ui_Plethysmography class displays the file path of the user-selected output directory.
        
        Outputs
        --------
        self.output_path_display: QLineEdit
            This LineEdit displays the file path of the user-selected output directory.
        reply: QMessageBox
            If there is recognizable input for either BASSPRO or STAGG (namely either metadata, automated and/or manual BASSPRO settings, basic BASSPRO settings, or STAGG settins files) detected in the selected output directory, this MessageBox asks the user if they would like to keep their existing input selections or update the relevant attributes wiht the file paths of the detected settings files.
        
        Outcomes
        --------
        self.auto_get_output_dir_py()
            Check whether or not a BASSPRO_output directory exists in the user-selected directory and make it if it does not exist, and make a timestamped BASSPRO output folder for the current session's next run of BASSPRO.
        self.auto_get_autosections()
            Detect a automated BASSPRO settings file, set self.autosections as its file path, and populate self.sections_list with the file path for display to the user.
        self.auto_get_mansections()
            Detect a manual BASSPRO settings file, set self.mansections as its file path, and populate self.sections_list with the file path for display to the user.
        self.auto_get_metadata()
            Detect a metadata file, set self.metadata as its file path, and populate self.metadata_list with the file path for display to the user.
        self.auto_get_basic()
            Detect a basic BASSPRO settings file, set self.basicap as its file path, and populate self.sections_list with the file path for display to the user.
        self.update_breath_df()
            This method updates self.breath_df to reflect any changes to the variable list used to populate Config.variable_table if the user chooses to replace previously selected input with input detected in the selected output directory.
        """

        # If we already have a workspace dir, set the initial choosing dir to the workspace parent
        if self.workspace_dir:
            selection_dir = str(Path(self.workspace_dir).parent.absolute())
        else:
            selection_dir = None

        output_dir = QFileDialog.getExistingDirectory(self, 'Choose output directory', selection_dir, QFileDialog.ShowDirsOnly)
        # Catch cancel
        if not output_dir:
            return

        # Set output dir
        self.workspace_dir = output_dir
        
        # Try to auto-import
        if self.dir_contains_valid_import_files(output_dir):

            # If any data exists already, ask user before overwriting
            if self.breath_df or self.metadata or self.autosections or self.basicap or self.mansections:

                reply = ask_user_ok('Input detected',
                                    'The selected directory has recognizable input.\n\nWould you like to overwrite your current input selection?')
                if not reply:
                    return
                
            self.auto_get_autosections()
            self.auto_get_mansections()
            self.auto_load_metadata()
            self.auto_get_basic()
            #if len(self.breath_df) > 0:
            #    self.update_breath_df("settings")
        
    def create_output_folder(self, toolname):
        """
        Check whether or not a BASSPRO_output directory exists in the user-selected directory and make it if it does not exist, and make a timestamped BASSPRO output folder for the current session's next run of BASSPRO.

        Parameters
        --------
        
        Outputs
        --------
        self.basspro_output_dir: str
            This attribute is set as a file path to the BASSPRO_output directory in the user-selected directory output_dir and the directory itself is spawned if it does not exist.
        self.output_dir_py: str
            This attribute is set as a file path to the timestamped BASSPRO_output_{time} folder within the BASSPRO_output directory within the user-selected directory output_dir. It is not spawned until self.require_workspace_dir() is called when BASSPRO is launched.

        Returns
        --------
        output_dir_py: str
            Newly created output dir
        """
        basspro_output_dir = os.path.join(self.workspace_dir, f'{toolname}_output')

        if not Path(basspro_output_dir).exists():
            Path(basspro_output_dir).mkdir()

        curr_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir_py = os.path.join(basspro_output_dir, f'{toolname}_output_' + curr_timestamp)
        Path(output_dir_py).mkdir()

        return output_dir_py
    
     
    def auto_load_metadata(self):
        """
        Detect a metadata file, set self.metadata as its file path, and populate self.metadata_list wiht the file path for display to the user.

        Parameters
        --------
        self.workspace_dir: str
            This attribute is set as the file path to the user-selected output directory.
        self.metadata_list: QListWidget
            This ListWidget inherited from the Ui_Plethysmography class displays the file path of the current metadata file intended as input for BASSPRO or as a source of variables for the populating of self.breath_df and the display of the STAGG settings subGUI.
        
        Outputs
        --------
        self.metadata_list: QListWidget
            This ListWidget is populated with the file path of the metadata.csv file detected in the user-selected self.workspace_dir output directory.
        self.metadata: str
            This attribute is set as the file path to the metadata.csv file detected in the user-selected self.workspace_dir output directory.
        """
        metadata_path = os.path.join(self.workspace_dir, 'metadata.csv')
        if MetadataSettings.validate():
            self.metadata = metadata_path
        else:
            print("No metadata file selected.")

    def auto_get_basic(self):
        """
        Detect a basic BASSPRO settings file, set self.basicap as its file path, and populate self.sections_list with the file path for display to the user.

        Parameters
        --------
        self.workspace_dir: str
            This attribute is set as the file path to the user-selected output directory.
        self.sections_list: QListWidget
            This ListWidget inherited from the Ui_Plethysmography class displays the file path of the current BASSPRO settings files intended as input for BASSPRO or as a source of variables for the populating of self.breath_df and the display of the STAGG settings subGUI.
        
        Outputs
        --------
        self.sections_list: QListWidget
            This ListWidget is populated with the file path of the basic.csv file detected in the user-selected self.workspace_dir output directory.
        self.basicap: str
            This attribute is set as the file path to the basic.csv file detected in the user-selected self.workspace_dir output directory.
        """
        basic_path = os.path.join(self.workspace_dir, 'basics.csv')
        if BasicSettings.validate(basic_path):
            self.basicap = basic_path
        else:
            print("Basic parameters settings file not detected.")

    def auto_get_autosections(self):
        """
        Detect an automated BASSPRO settings file, set self.autosections as its file path, and populate self.sections_list with the file path for display to the user.

        Parameters
        --------
        self.workspace_dir: str
            This attribute is set as the file path to the user-selected output directory.
        self.sections_list: QListWidget
            This ListWidget inherited from the Ui_Plethysmography class displays the file path of the current BASSPRO settings files intended as input for BASSPRO or as a source of variables for the populating of self.breath_df and the display of the STAGG settings subGUI.
        
        Outputs
        --------
        self.sections_list: QListWidget
            This ListWidget is populated with the file path of the autosections.csv file detected in the user-selected self.workspace_dir output directory.
        self.autosections: str
            This attribute is set as the file path to the autosections.csv file detected in the user-selected self.workspace_dir output directory.
        """
        autosections_path = os.path.join(self.workspace_dir, 'auto_sections.csv')
        if Path(autosections_path).exists():
            self.autosections = autosections_path
        else:
            print("Autosection parameters file not detected.")

    def auto_get_mansections(self):
        """
        Detect a manual BASSPRO settings file, set self.mansections as its file path, and populate self.sections_list with the file path for display to the user.

        Parameters
        --------
        self.workspace_dir: str
            This attribute is set as the file path to the user-selected output directory.
        self.sections_list: QListWidget
            This ListWidget inherited from the Ui_Plethysmography class displays the file path of the current BASSPRO settings files intended as input for BASSPRO or as a source of variables for the populating of self.breath_df and the display of the STAGG settings subGUI.
        
        Outputs
        --------
        self.sections_list: QListWidget
            This ListWidget is populated with the file path of the manual_sections.csv file detected in the user-selected self.workspace_dir output directory.
        self.mansections: str
            This attribute is set as the file path to the manual_sections.csv file detected in the user-selected self.workspace_dir output directory.
        """
        print("auto_get_mansections()")
        mansections_path = os.path.join(self.workspace_dir, 'manual_sections.csv')
        if ManualSettings.validate(mansections_path):
            self.mansections = mansections_path
        else:
            print("Manual sections parameters file not detected.")

    def auto_get_breath_files(self, basspro_output_dir, clear_files=None):
        """
        Populate self.stagg_input_files with the file paths of the JSON files held in the directory of the most recent BASSPRO run within the same session (the directory file path stored in self.output_dir_py) and populate self.breath_list (ListWidget) with the file paths of those JSON files.

        Parameters
        --------
        self.output_dir_py: str
            This attribute is set as a file path to the timestamped BASSPRO_output_{time} folder within the BASSPRO_output directory within the user-selected directory self.workspace_dir. It is not spawned until self.require_workspace_dir() is called when BASSPRO is launched.
        self.breath_list: QListWidget
            This ListWidget inherited from the Ui_Plethysmography class displays the file paths of the STAGG input.
        self.stagg_input_files: list
            This attribute is either an empty list or is a list of file paths for STAGG input (either JSON files or .RData file or both).
        
        Outputs
        --------
        reply: QMessageBox
            If self.stagg_input_files is not empty, this MessageBox asks the user if they would like to keep the previously selected STAGG input files or replace them.
        self.breath_list: QListWidget
            This ListWidget is either emptied and populated with the file paths of the JSON files from the most recent BASSPRO run within the same session or it appends the files paths from the most recent BASSPRO run to its existing population.
        self.stagg_input_files: list
            This attribute is either emptied and populated with the file paths of the JSON files from the most recent BASSPRO run within the same session or it is SUPPOSED TO append the file paths from the most recent BASSPRO to its existing items but it looks like it just replaces the list of existing items with a new list of the file paths from self.output_dir_py regardless of the user's choice.
        """
        # TODO: message below
        # This method needs fixing. If they say yes, I want to keep them, then what happens? It looks like self.stagg_input_files populates with the new files regardless of the user's choice.
        if len(self.stagg_input_files):
            if clear_files is None:
                reply = ask_user_yes('Clear STAGG input list?', 'Would you like to remove the previously selected STAGG input files?')
            else:
                reply = clear_files

            if reply:
                self.breath_list.clear()

        #stagg_input_files = [os.path.join(basspro_output_dir, file) for file in os.listdir(basspro_output_dir) if file.endswith(".json")==True]
        stagg_input_files = glob(os.path.join(basspro_output_dir, "*.json"))
        for file in stagg_input_files:
            self.breath_list.addItem(file)

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
        Prompt the user to select signal files via FileDialog. They can choose signal files from multiple directories by calling this method multiple times.

        Parameters
        --------
        QFileDialog: class
            A standard FileDialog allows the user to select multiple signal files from one directory.
        self.signals: list
            This attribute is either an empty list or a list of existing file paths of selected signal files.
        self.signal_files_list: QListWidget
            This ListWidget inherited from Ui_Plethysmography displays the file paths of the selected signal files on the main GUI.
        Thumbass: class
            This class defines a simple dialog that gives the user information.
        self.metadata: str
            This attribute is either an empty string or refers to the file path of the metadata file.

        Outputs
        --------
        self.signals: list
            This attribute is either emptied and repopulated with the file paths of the recently selected signal files or it is appended with the recently selected signal files.
        self.signal_files_list: QListWidget
            This ListWidget is either cleared and repopulated with the file paths of the recently selected signal files or it is appended with the recently selected signal files.
        reply: QMessageBox
            If self.signals is not empty, this MessageBox asks the user if they would like to keep the previously selected signal files and add to them with the currently selected signal files or just replace the previous ones.
        
        Outcomes
        --------
        Thumbass.show()
            This method displays the Thumbass dialog.
        self.check_metadata_file()
            This method checks whether or not references to the selected signals files are found in the current metadata file.
        """
        # TODO: Move this logic to Settings sub-class
        # TODO: add setter
        filenames, filter = QFileDialog.getOpenFileNames(self, 'Select signal files', self.workspace_dir, '*.txt')

        # Catch cancel
        if not filenames:
            return

        # Print message to user if there is a mismatch with metadata
        if self.metadata_df is not None and \
            not self.test_signal_metadata_match(filenames, self.metadata_df):
            notify_error("Signal files mismatch with metadata")
            return

        # Overwrite existing files?
        if self.signal_files_list.count() > 0:
            reply = ask_user_yes(title='Clear signal files list?', msg='Would you like to remove the previously selected signal files?')
            if reply:
                self.signal_files_list.clear()

        # Add signal files
        [self.signal_files_list.addItem(file) for file in filenames]


    @staticmethod
    def test_signal_metadata_match(signal_files, meta_df):
        """
        Ensure that the selected metadata file does contain metadata for the signal files selected.
        This method is only called if self.signals is not empty.

        Parameters
        --------
        baddies: list
            This variable is set as an empty list and is populated with the file path(s) of the signal file(s) that failed to meet criteria.
        self.metadata: str
            This attribute refers to the file path of the metadata file selected by the user.
        self.signals: list
            The list of file paths of the user-selected .txt signal files that are analyzed by BASSPRO.
        
        Outputs
        ---------
        baddies: list
            This variable is populated with the file path(s) of the signal file(s) whose IDs were not found in the selected metadata file.
        reply: QMessageBox
            This specialized dialog tells the user of any mismatches and lists the offending signal file path(s).
        """

        baddies = []
        for s in signal_files:
            name = os.path.basename(s).split('.')[0]
            if '_' in name:
                mouse_uid, ply_uid = name.split('_')
                if len(meta_df.loc[(meta_df['MUID'] == mouse_uid)]) == 0:
                    baddies.append(s)
                elif len(meta_df.loc[(meta_df['PlyUID'] == ply_uid)]) == 0:
                    baddies.append(s)
            elif len(meta_df.loc[(meta_df['MUID'] == name)]) == 0:
                baddies.append(s)

        if len(baddies) > 0:
            title = "Metadata and signal files mismatch"
            msg = "The following signals files were not found in the selected metadata file:"
            msg += f"\n\n{os.linesep.join([os.path.basename(thumb) for thumb in baddies])}\n"
            notify_error(msg, title)
            return False

        return True

    def load_metadata(self):
        """
        Prompt the user to select a previously made metadata file via FileDialog, clear and repopulated self.metadata_list (ListWidget) to display the file path of the metadata file on the main GUI, call self.update_breath_df() if self.breath_df is not empty, and call self.check_metadata_file() if self.signals is not empty.

        Parameters
        --------
        self.workspace_dir: str
            This attribute refers to the directory path of the user-selected output directory.
        QFileDialog: class
            A standard FileDialog allows the user to select multiple signal files from one directory.
        self.metadata_list: QListWidget
            This ListWidget inherited from Ui_Plethysmography class displays the file path of the current metadata file on the main GUI.
        self.breath_df: list
            This attribute is either an empty list or a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        
        Outputs
        --------
        self.metadata_list: QListWidget
            This ListWidget is either cleared and repopulated or just populated with the file path of the recently selected metadata file.
        self.metadata: str
            This attribute is populated with the file path of the recently selected metadata file.
        
        Outcomes
        --------
        self.update_breath_df()
            If self.breath_df is not empty, this method is called to update the list of variables used to populate self.breath_df and show the STAGG settings subGUI to reflect any changes in metadata-derived variables.
        self.check_metadata_file()
            If self.signals is not empty, this method checks whether or not references to the selected signals files are found in the current metadata file.
        """
        while True:
            meta_file = MetadataSettings.open_file(self.workspace_dir)
            # break out of cancel
            if not meta_file:
                return

            # TODO: this should be done in `attempt_load()` ?? Need to push validation back -- is this function really just require_load()?
            # If there are not valid files, try again
            if self.test_signal_metadata_match(self.signal_files, MetadataSettings.attempt_load(meta_file)):
                self.metadata = meta_file
                break

                #if len(self.breath_df) > 0:
                #    self.update_breath_df("metadata")


    def mp_parser(self):
        """
        This method was adapted from a function written by Chris Ward.

        Grab MUIDs and PlyUIDs from signal file names.hey are expected to be named with the ID of the mouse beginning with the letter "M", followed by an underscore, followed by the ID of the plethysmography run beginning with the letters "Ply". 

        Parameters
        --------
        self.signals: list
            This attribute is a list of file paths of the selected signal files intended as BASSPRO input.
        
        Outputs
        --------
        self.mp_parsed: dict
            This attribute is populated with the mouse IDs, plethysmography IDs, and the tuple constructed from both scraped from the file name of each signal file currently selected.
        self.mp_parserrors: list
            This attribute is set as an empty list and is populated with the file path of any files that fail to be scraped.
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
        This method was adapted from a function written by Chris Ward.

        Collect relevant metadata for the mice and their runs as indicated by their MUID and PlyUID in the signal file name as sourced via self.mp_parser().

        Parameters
        --------
        self.signals: list
            This attribute is a list of file paths of the selected signal files intended as BASSPRO input.
        self.metadata_list: QListWidget
            This ListWidget inherited from Ui_Plethysmography class displays the file path of the current metadata file on the main GUI.
        self.workspace_dir: str
            This attribute refers to the path of the user-selected output directory.
        
        Outputs
        --------
        reply: QMessageBox
            This MessageBox informs the user that if not signal files have been selected and prompts the user to correct this.
        self.metadata_warnings: dict
            This attribute is set as an empty dictionary.
        self.metadata_pm_warnings: list
            This attribute is set as an empty list.
        self.missing_plyuids: list
            This attribute is set as an empty list.
        self.metadata_list: QListWidget
            This ListWidget is populated with the file path of the metadata file created from the information accessed in the database.
        self.mousedb: ?
            This attribute refers to the connection to the database accessible via the information provided in the variable dsn.

        Outcomes
        --------
        self.get_signal_files()
            This method is called if the user has not selected signal files and prompts them to do so via FileDialog.
        self.mp_parser()
            This method grabs MUIDs and PlyUIDs from signal file names. They are expected to be named with the ID of the mouse beginning with the letter "M", followed by an underscore, followed by the ID of the plethysmography run beginning with the letters "Ply".
        self.get_study()
            This method scrapes the values from the relevant fields of the database for the metadata based on the IDs gotten via self.mp_parser().
        self.require_workspace_dir()
            This method ensures that the user has selected an output directory and prompt them to do so if they have not.
        self.save_filemaker()
            This method saves the information grabbed from the database as a .csv file, sets self.metadata as the new file path, and populates self.metadata_list (ListWidget) with the new file path on the main GUI.
        self.get_metadata()
            Prompt the user to select a previously made metadata file via FileDialog, clear and repopulated self.metadata_list (ListWidget) to display the file path of the metadata file on the main GUI, call self.update_breath_df() if self.breath_df is not empty, and call self.check_metadata_file() if self.signals is not empty.
        """

        # Wait for user to get signal files
        while self.signal_files_list.count() == 0:
            reply = QMessageBox.information(self, 'Unable to connect to database', 'No signal files selected.\nWould you like to select a signal file directory?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.get_signal_files()
            elif reply == QMessageBox.Cancel:
                break
        
        # TODO: Is this true?
        # Cannot connect to database if no signal files
        if self.signal_files_list.count() == 0:
            return

        self.metadata_warnings={}
        self.metadata_pm_warnings=[]
        self.missing_plyuids=[]
        self.hangar.append("Gauging Filemaker connection...")
        try:
            dsn = 'DRIVER={FileMaker ODBC};Server=128.249.80.130;Port=2399;Database=MICE;UID=Python;PWD='
            self.mousedb = pyodbc.connect(dsn)
            self.mousedb.timeout=1
            self.mp_parser()
            self.get_study()
            if not self.require_workspace_dir():
                return
            self.metadata_list.clear()
            self.save_filemaker()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            reply = QMessageBox.information(self, 'Unable to connect to database', 'You were unable to connect to the database.\nWould you like to select another metadata file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.load_metadata()

    def get_study(self, fixformat=True):
        """
        This method was adapted from a function written by Chris Ward.

        Scrape the values from the relevant fields of the database for the metadata.

        Parameters
        --------
        self.mp_parsed: dict
            This attribute is populated with the mouse IDs, plethysmography IDs, and the tuple constructed from both scraped from the file name of each signal file currently selected.
        self.mp_parserrors: list
            This attribute is set as an empty list and is populated with the file path of any files that fail to be scraped.
        self.mousedb: ?
            This attribute refers to the connection to the database accessible via the information provided in the variable dsn.
        self.hangar: QTextEdit
            This attribute is a QTextEdit inherited from the Ui_Plethysmography class that displays feedback to the user.
        self.metadata_warnings: dict
            This attribute is set as an empty dictionary.
        self.metadata_pm_warnings: list
            This attribute is set as an empty list.
        self.missing_plyuids: list
            This attribute is set as an empty list.

        Outputs
        --------
        self.m_mouse_dict: dict
            This attribute is populated with the fields and values scraped from the Mouse_List view of the Ray Lab's database.
        self.p_mouse_dict: dict
            This attribute is populated with the fields and values scarped from the Plethysmography view of the Ray Lab's database.
        self.mousedb: ?
            The connection is closed.
        self.hangar: QTextEdit
            This attribute is a QTextEdit inherited from the Ui_Plethysmography class that prints a summary of any errors in the process of grabbing metadata from the database.
        self.assemble_df: Dataframe
            This attribute is the dataframe constructed from the concatenated dataframes derived from self.m_mouse_dict and self.p_mouse_dict.
        
        Outcomes
        --------
        self.metadata_checker_filemaker()
            This method scans the information grabbed from the database to note any discrepancies.
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

    def metadata_checker_filemaker(self):
        """
        Populate self.metadata_pm_warnings (list), self.missing_plyuids (list), and self.metadata_warnings (dict) with information on discrepancies found in the metadata accessed from the database.

        Parameters
        --------
        self.gui_config: dict
           This attribute is a nested dictionary loaded from gui_config.json. It contains paths to the BASSPRO and STAGG modules and the local Rscript.exe file, the fields of the database accessed when building a metadata file, and settings labels used to organize the populating of the TableWidgets in the BASSPRO settings subGUIs. See the README file for more detail.
        self.metadata_list: QListWidget
            This ListWidget inherited from Ui_Plethysmography class displays the file path of the current metadata file on the main GUI.
        self.mp_parsed: dict
            This attribute is populated with the mouse IDs, plethysmography IDs, and the tuple constructed from both scraped from the file name of each signal file currently selected.
        self.m_mouse_dict: dict
            This attribute is populated with the fields and values scraped from the Mouse_List view of the Ray Lab's database.
        self.p_mouse_dict: dict
            This attribute is populated with the fields and values scarped from the Plethysmography view of the Ray Lab's database.
        self.metadata_warnings: dict
            This attribute is as an empty dictionary.
        self.metadata_pm_warnings: list
            This attribute is as an empty list.
        self.missing_plyuids: list
            This attribute is as an empty list.
        self.metadata_passlist: list
            This attribute is an empty list.

        Outputs
        --------
        self.essential_fields: dict
            This attribute is a nested dictionary from self.gui_config (dict) containing the names of the fields in the Ray Lab Filemaker database that should be accessed to create a metadata file.
        self.metadata_list: QListWidget
            This ListWidget is populated with an update.
        self.metadata_pm_warnings: list
            This attribute is populated with strings summarizing the instance of discrepancy if any are found.
        self.missing_plyuids: list
            This attribute is populated with the mouse IDs that are in the database but whose PlyUID (plethysmography run ID as indicated by the file name of the signal file) is not in the database.
        self.metadata_warnings: dict
            This attribute is a populated with PlyUID keys and strings as their values warning of a particular field of metadata missing from the metadata for that plethysmography run.
        self.metadata_passlist: list
            This attribute is populated with the IDs of the signals files that had no discrepancies in the collection of their metadata from the database.
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

        Parameters
        --------
        self.workspace_dir: str
            This attribute refers to the path of the user-selected output directory.
        self.metadata_list: QListWidget
            This ListWidget inherited from Ui_Pletysmography class displays the file path of the current metadata file on the main GUI.
        self.assemble_df: Dataframe
            This attribute is the dataframe constructed from the concatenated dataframes derived from self.m_mouse_dict and self.p_mouse_dict.
        
        Outputs
        --------
        self.metadata_list: QListWidget
            This ListWidget is populated with the file path of the metadata file created from the information grabbed from the database for display on the main GUI.
        self.metadata: str
            This attribute is set as the file path of the metadata.csv file that was made from the self.assemble_df dataframe saved in self.workspace_dir.
        reply: QMessageBox
            This MessageBox tells the user if they have a file open in another program that shares the same file path as self.metadata.
        """
        print("save_filemaker()")
        self.metadata_list.addItem("Creating csv file...")
        self.metadata = os.path.join(self.workspace_dir,"metadata.csv")
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
    
        Parameters
        --------
        QFileDialog: class
            A standard FileDialog.
        self.workspace_dir: str
            This attribute refers to the path of the user-selected output directory.
        self.sections_list: QListWidget
            This ListWidget inherited from the Ui_Plethysmography class displays the file path of the current BASSPRO settings files intended as input for BASSPRO or as a source of variables for the populating of self.breath_df and the display of the STAGG settings subGUI.
        self.breath_df: list
            This attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        Thumbass: class
            This class defines a simple dialog that gives the user information.
        
        Outputs
        --------
        self.autosections: str
            This attribute refers to the path to the automated BASSPRO settings file. The file's name must start with either "auto_sections" or "autosections".
        self.mansections: str
            This attribute refers to the file path of the manual BASSPRO settings file selected via FileDialog. The file's name must start with "manual_sections".
        self.basicap: str
            This attribute refers to the file path of the basic BASSPRO settings file selected via FileDialog. The file's name must start with "basic".
        
        Outcomes
        --------
        self.update_breath_df()
            This method updates self.breath_df to reflect any changes to the variable list used to populate Config.variable_table and display the STAGG settings subGUI due to selection of new settings.
        Thumbass.show()
            This method displays the Thumbass dialog.
        """
        filenames, filter = QFileDialog.getOpenFileNames(self, 'Select files', self.workspace_dir)
        # Catch cancel
        if not filenames:
            return

        added_files = []
        for file in filenames:
            if AutoSettings.validate(file):
                self.autosections = file
                added_files.append(file)

            elif ManualSettings.validate(file):
                self.mansections = file
                added_files.append(file)

            elif BasicSettings.validate(file):
                self.basicap = file
                added_files.append(file)

            # If we added files
            if len(added_files):
                #if len(self.breath_df)>0:
                #    self.update_breath_df("settings")
                pass

        if len(added_files):
            msg = "Added files: "
            msg += ", ".join(added_files)
            notify_info(msg)
        else:
            notify_info("No files added")

    def select_stagg_input_files(self):
        """
        Prompt the user to select input files for STAGG. Only .RData files or JSON files are accepted.

        Parameters
        --------
        QFileDialog: class
            A standard FileDialog.
        self.stagg_input_files: list
            This attribute is either an empty list or a list of one of the following: JSON files produced by the most recent run of BASSPRO in the same session; JSON files produced by BASSPRO selected by user with a FileDialog; an .RData file produced by a previous run of STAGG; an .RData file produced by a previous run of STAGG and JSON files produced by BASSPRO.
        self.workspace_dir: str
            This attribute refers to the path of the user-selected output directory.
        self.breath_list: QListWidget
            This ListWidget inherited from the Ui_Plethysmography class displays the file paths of the STAGG input.
        Thumbass: class
            This class defines a simple dialog that gives the user information.
        
        Outputs
        --------
        self.breath_list: QListWidget
            This ListWidget is emptied and repopulated or just populated with the file paths selected by the user via FileDialog.
        self.stagg_input_files: list
            This attribute is either emptied and repopulated or appended with the file paths of any user-selected files that end in ".RData" or ".json".
        reply: QMessageBox
            This MessageBox informs the user that none of the files they've selected are the right file format and prompts the user to resolve this by calling self.select_stagg_input_files() again.
        
        Outcomes
        --------
        Thumbass.show()
            This methods displays the Thumbass dialog with lists the file paths of the files that did not meet criteria (namely wrong file type).
        self.select_stagg_input_files()
            This method is called again if the user selected bad files.
        """
        files = STAGGInputSettings.open_files(self.workspace_dir)
        if files:
            # if we already have a selection, check about overwrite
            if self.breath_list.count():
                if ask_user_yes('Clear STAGG input list?',
                                'Would you like to remove the previously selected STAGG input files?'):
                    self.breath_list.clear()

            for x in files:
                self.breath_list.addItem(x)
    
    def check_bp_reqs(self):
        """
        Ensure that the user has provided metadata, basic BASSPRO settings,
          and either automated or manual BASSPRO settings before launching BASSPRO.

        Parameters
        --------
        self.metadata: str
            This attribute refers to the file path of the metadata file.
        self.autosections: str
            This attribute refers to the file path of the automated BASSPRO settings file.
        self.mansections: str
            This attribute refers to the file path of the manual BASSPRO settings file.
        self.basicap: str
            This attribute refers to the file path of the basic BASSPRO settings file.
        
        Outputs
        --------
        reply: QMessageBox
            This specialized dialog prompts the user to select the files still required by BASSPRO.
        
        Outcomes
        --------
        self.get_metadata()
            This method prompts the user to select a previously made metadata file via FileDialog.
        self.get_autosections()
            This method prompts the user to select a previously made automated or manual or basic BASSPRO settings file via FileDialog.
        """
        if len(self.signal_files) == 0:
            notify_error("Please select signal files")
            return False

        if self.metadata_df is None:
            notify_error("Please select a metadata file")
            return False

        if self.autosections_df is None and self.mansections_df is None:
            notify_error("Please select a sections file")
            return False
        
        if self.basicap_df is None:
            notify_error("Please select a basic settings file")
            return False

        # Make sure we have an output dir
        if not self.require_workspace_dir():
            return False
        
        return True


    def full_run(self):
        """
        Ensure the user has selected an output directory and prompt them to do so if they haven't, check that the required input for BASSPRO has been selected, launch BASSPRO, detect the JSON files produced after BASSPRO has finished and populate self.stagg_input_files with the file paths to those JSON files.

        Outcomes
        --------
        self.require_workspace_dir()
            This method ensures that the user has selected an output directory and prompts them to do so if they have not.
        self.get_bp_reqs()
            This method ensures that the user has provided metadata, basic BASSPRO settings, and either automated or manual BASSPRO settings before launching BASSPRO.
        self.launch_basspro()
            This method copies the required BASSPRO input other than the signal files and the breathcaller_config.json file to the timestamped BASSPRO output folder (self.output_dir_py) and runs self.launch_worker().
        self.auto_get_breath_files()
            Populate self.stagg_input_files with the file paths of the JSON files held in the directory of the most recent BASSPRO run within the same session (the directory file path stored in self.output_dir_py) and populate self.breath_list (ListWidget) with the file paths of those JSON files.
        """

        is_full_run = self.full_run_checkbox.isChecked()

        # check that the required input for BASSPRO has been selected
        if not self.check_bp_reqs():
            return

        # If doing full run
        clear_stagg_input = None
        if is_full_run:
            # check stagg reqs
            if not self.check_stagg_reqs(full_run=True):
                return

            # Check whether we have stagg input already
            if len(self.stagg_input_files):
                clear_stagg_input = ask_user_yes('Clear STAGG input list?', 'Would you like to remove the previously selected STAGG input files?')

        # launch BASSPRO
        self.status_message("\n-- -- Launching BASSPRO -- --")
        basspro_output_folder, shared_queue, workers = self.launch_basspro()
        self.basspro_launch_button.setEnabled(False)

        # TODO: prevent full run if stagg already running
        # Kick off stagg later if doing a full-run!
        if is_full_run:
            # Prevent any changes to stagg setup while waiting
            self.enable_stagg_buttons(False)

            # Set next function to run and monitor the workers
            execute_after = lambda : self.pickup_after_basspro(basspro_output_folder, clear_stagg_input)

        else:
            # Wait to check output after basspro finishes
            execute_after = self.complete_basspro

        # Monitor the basspro processes and execute a function after completion
        self.add_monitor(workers, shared_queue, execute_after, proc_name="BASSPRO")

    def complete_basspro(self):
        # TODO: automatically load in basspro output every time?
        self.basspro_launch_button.setEnabled(True)
        self.output_check()

    def cancel_monitor(self, monitor_id, exec_after_cancel=None):
        self.monitors[monitor_id]['status'] = 'cancelled'
        if exec_after_cancel:
            exec_after_cancel()

    def add_monitor(self, workers, msg_queue, execute_after=None, proc_name=None):
        new_id = generate_unique_id(self.monitors.keys())
        self.monitors[new_id] = {
            'status': 'running',
            'execute_after': execute_after,
            'workers': workers,
            'msg_queue': msg_queue,
            'dialog_window': None,
            'last_heard': datetime.now(),
            'proc_name': proc_name if proc_name else f"Process {new_id}"
        }

        # monitor worker to execute next function
        self.monitor_workers(new_id)
        
        # monitor status messages (faster interval)
        self.print_queue_status(new_id)

    def print_queue_status(self, monitor_id, interval=200):
        # Check if proc is completed or cancelled
        if monitor_id not in self.monitors or self.monitors[monitor_id]['status'] == 'cancelled':
            return

        monitor = self.monitors[monitor_id]

        # TODO: search - "pyqt multiprocessing signals vs queue messages"
        queue = monitor['msg_queue']
        while not queue.empty():
            worker_id, new_msg = queue.get_nowait()
            if new_msg == 'DONE':
                # Remove worker from monitor
                self.monitors[monitor_id]['workers'].pop(worker_id)
                self.hangar.append(f'{worker_id} : {new_msg}')
            else:
                self._reset_last_msg_time(monitor_id)
                self.hangar.append(f'{worker_id} : {new_msg}')

        QTimer.singleShot(interval, lambda : self.print_queue_status(monitor_id, interval=interval))

    def _reset_last_msg_time(self, monitor_id):
        """
        Reset the time we last heard from a monitored process
        Also, unset the dialog window for cancelling since we're getting a heartbeat
        """
        self.monitors[monitor_id]['last_heard'] = datetime.now()
        self.monitors[monitor_id]['dialog_window'] = None

    def monitor_workers(self, monitor_id, interval=1000):
        """
        Use this function to monitor a longrunning process and pick up afterwards
          with some arbitrary function
        Data about each monitoring instance is stored in `self.monitors`
        """
        monitor = self.monitors[monitor_id]

        # TODO: make sure we handle any still running processes
        # Check if this monitor has been cancelled
        if monitor['status'] == 'cancelled':
            self.monitors.pop(monitor_id)
            return

        # If any of our workers are still working
        if len(monitor['workers']) > 0:
            last_heard = monitor['last_heard']

            # Unset dialog window if it was hidden (user made a selection)
            if monitor['dialog_window'] and monitor['dialog_window'].isHidden():
                self.monitors[monitor_id]['dialog_window'] = None

            # TODO: implement BASSPRO cancel, not just STAGG continuation
            # If it's been longer than 1 minute since we've heard from the threads
            if datetime.now() - last_heard > timedelta(minutes=2) and \
                not monitor['dialog_window']:
                msg = f"{monitor['proc_name']} is taking a while, would you like to cancel checking for STAGG autostart?"
                yes_func = lambda : self.cancel_monitor(monitor_id, exec_after_cancel=lambda : self.enable_stagg_buttons(True))
                no_func = lambda : self._reset_last_msg_time(monitor_id)
                msg_box = nonblocking_msg(msg, 'yes', (yes_func, no_func))
                self.monitors[monitor_id]['dialog_window'] = msg_box
            
            # Check again in a second
            # TODO: make this a timer on interval, not singleshot
            QTimer.singleShot(interval, lambda : self.monitor_workers(monitor_id, interval=interval))
            return
        
        execute_after = monitor['execute_after']
        
        # Run next function
        if execute_after:
            self.monitors.pop(monitor_id)
            execute_after()

    def pickup_after_basspro(self, basspro_output_folder, clear_stagg_input):

        # check whether Basspro output is correct, re-enable basspro button
        self.complete_basspro()

        ## RUN STAGG ##
        self.status_message("\nAutopopulating STAGG")

        # detect the JSON files produced after BASSPRO has finished
        self.auto_get_breath_files(basspro_output_folder, clear_files=clear_stagg_input)

        # launch STAGG
        self.status_message("\n-- -- Launching STAGG -- --")
        stagg_output_folder, shared_queue, workers = self.launch_stagg()

        # Prevent any changes to stagg setup while waiting
        self.enable_stagg_buttons(False)

        # Wait to check output after basspro finishes
        execute_after = lambda : self.enable_stagg_buttons(True)

        # Monitor the basspro processes and execute a function after completion
        self.add_monitor(workers, shared_queue, execute_after, proc_name="STAGG")

    def enable_stagg_buttons(self, status:bool):
        # TODO: when stagg continuation is cancelled, basspro is still running
        #   - below will enable basspro button again, but need to make sure we stop basspro process
        self.basspro_launch_button.setEnabled(status)
        self.stagg_settings_button.setEnabled(status)
        self.stagg_launch_button.setEnabled(status)
        self.breath_files_button.setEnabled(status)

    def status_message(self, msg):
        self.hangar.append(msg)

    def launch_stagg(self):
        """
        Assign the file paths to the attributes, ensure that all required STAGG input has been selected and prompt the user to select whatever is missing, and launch STAGG.

        Parameters
        --------
        Config.configs: dict
            This attribute is populated with a nested dictionary in which each item contains a dictionary unique to each settings file - variable_config.csv, graph_config.csv, and other_config.csv. Each dictionary has the following key, value items: "variable", the Plethysmography class attribute that refers to the file path to the settings file; "path", the string file path to the settings file; "frame", the Config class attribute that refers to the dataframe; "df", the dataframe.
        self.stagg_input_files: list
            This attribute is a list of user-selected signal file paths.
        
        Outputs
        --------
        self.variable_config: str
            This attribute is populated with the variable_config path stored in Config.configs (dict).
        self.graph_config: str
            This attribute is populated with the graph_config path stored in Config.configs (dict).
        self.other_config: str
            This attribute is populated with the other_config path stored in Config.configs (dict).
        
        Outcomes
        --------
        self.rthing_to_do()
            Copy STAGG input to timestamped STAGG output folder, determine which STAGG scripts to use based on the presence or absence of an .RData file, and determine if self.input_dir_r needs to be a str path to directory instead of list because the list has more than 200 files, and run self.rthing_to_do_cntd().
        """
        """
        Ensure the STAGG script exists, prompt the user to indicate where the Rscript.exe file is, and run self.launch_worker().

        Parameters
        --------
        self.pipeline_des: str
            self.pipeline_des: str
            This attribute is set as the file path to one of two scripts that launch STAGG. If self.stagg_input_files has a .RData file in it, then self.pipeline_des refers to the file path for Pipeline_env_multi.R. If self.stagg_input_files consists entirely of JSON files, then self.pipeline_des refers to the file path for Pipeline.R.
        self.gui_config: dict
            This attribute is a nested dictionary loaded from gui_config.json. It contains paths to the BASSPRO and STAGG modules and the local Rscript.exe file, the fields of the database accessed when building a metadata file, and settings labels used to organize the populating of the TableWidgets in the BASSPRO settings subGUIs. See the README file for more detail. 
        
        Outputs
        --------
        self.rscript_des: str
            This attribute refers to the file path to the Rscript.exe of the user's device or of R-Portable.
        reply: QMessageBox
            This MessageBox prompts the user to navigate to the Rscript executable file if the file path stored in self.gui_config cannot be found.
        self.gui_config: dict
            This dictionary is updated with the new file path of the Rscript.exe file when appropriate.
        gui_config.json
            The updated self.gui_config is dumped to the gui_config.json file in the GUI scripts folder.
        
        Outcomes
        --------
        self.launch_worker()
            Run parallel processes capped at the number of CPU's selected by the user to devote to BASSPRO or STAGG.
        """
        if not self.check_stagg_reqs():
            return

        # Set pipeline destination
        if any(os.path.basename(b).endswith("RData") for b in self.stagg_input_files):
            pipeline_des = os.path.join(self.papr_dir, "Pipeline_env_multi.R")
        else:
            pipeline_des = os.path.join(self.papr_dir, "Pipeline.R")

        if not Path(pipeline_des).is_file():
            # If Main.pipeline_des (aka the first STAGG script file path) isn't a file,
            #   then the STAGG scripts aren't where they're supposed to be.
            notify_error(title='STAGG scripts not found',
                         msg='BASSPRO-STAGG cannot find the scripts for STAGG. Check the BASSPRO-STAGG folder for missing files or directories.')
            return


        # Set Rscript path
        rscript_des = self.gui_config['Dictionaries']['Paths']['rscript']

        # Get image format
        if self.svg_radioButton.isChecked():
            image_format = ".svg"
        elif self.jpeg_radioButton.isChecked():
            image_format = ".jpeg"
        else:
            # TODO: this should never happen
            raise RuntimeError("No image format checked!")


        ## WRITE FILES ##
        # Create output folder
        stagg_output_dir = os.path.join(self.workspace_dir, 'STAGG_output')

        if not os.path.exists(stagg_output_dir):
            os.mkdir(stagg_output_dir)

        curr_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stagg_run_folder = os.path.join(stagg_output_dir, f'STAGG_output_{curr_timestamp}')
        os.mkdir(stagg_run_folder)

        # Write variable config
        variable_config = os.path.join(stagg_run_folder, f"variable_config_{curr_timestamp}.csv")
        VariableSettings.save_file(self.variable_config_df, variable_config)
        
        # Write graph config
        graph_config = os.path.join(stagg_run_folder, f"graph_config_{curr_timestamp}.csv")
        GraphSettings.save_file(self.graph_config_df, graph_config)
        
        # Write other config
        other_config = os.path.join(stagg_run_folder, f"other_config_{curr_timestamp}.csv")
        OtherSettings.save_file(self.other_config_df, other_config)
            
        # adjust thread limit for the qthreadpool
        self.qthreadpool.setMaxThreadCount(1)
        shared_queue = queue.Queue()
        workers = {}

        # Launch STAGG worker!
        for job in MainGUIworker.get_jobs_r(rscript_des,
                                            pipeline_des,
                                            self.papr_dir,
                                            self.workspace_dir,
                                            self.input_dir_r,
                                            variable_config,
                                            graph_config,
                                            other_config,
                                            stagg_run_folder,
                                            image_format
                                            ):
            worker_id = generate_unique_id(workers.keys())
            # create a Worker
            new_worker = MainGUIworker.Worker(
                job,
                worker_id,
                shared_queue
                )

            # Add the 'QRunnable' worker to the threadpool which will manage how
            # many are started at a time
            self.qthreadpool.start(new_worker)

            # Keep the worker around in a list
            workers[worker_id] = new_worker

        return stagg_run_folder, shared_queue, workers

    def require_workspace_dir(self):
        """
        Ensure the user has selected an output directory and prompt them to do so if they have not.

        Parameters
        --------
        output_folder: str
            This argument is either self.output_dir_py or self.output_dir_r, the timestamped output directories within either BASSPRO_output or STAGG_output respectively within the self.workspace_dir directory. These attributes are either empty strings or a directory path.
        output_folder_parent: str
            This argument is either self.basspro_output_dir or self.r_output_folder, the directory paths to either BASSPRO_output or STAGG_output respectively within the self.workspace_dir directory. These attributes are either empty strings or a directory path.
        text: str
            This argument provides the text needed to customize the FileDialog window title.
        self.workspace_dir: str
            This attribute is either an empty string or refers to the file path of the user-selected output directory.
        QFileDialog: class
            A standard FileDialog allows the user to select a directory.
        
        Outputs
        --------
        self.output_folder: str
            This attribute is set as an empty string and then populated with the appropriate directory path (i.e. the path that will serve as either self.output_dir_py or self.output_dir_r). The corresponding directory is created if it doesn't already exist.
        self.output_folder_parent: str
            This attribute is set as an empty string and then populated with the appropriate directory path (i.e. the path that will serve as either self.basspro_output_dir or self.r_output_folder). The corresponding directory is created if it doesn't already exist.
        """

        # Keep looping until we get an output directory
        while not self.workspace_dir:
            if not ask_user_ok('No Output Folder', 'Please select an output folder.'):
                return False

            # open a dialog that prompts the user to choose the directory
            self.select_workspace_dir()

        return True
    
    def launch_basspro(self):
        """
        Copy the required BASSPRO input other than the signal files and the breathcaller_config.json file to the timestamped BASSPRO output folder (self.output_dir_py) and run self.launch_worker().

        Parameters
        --------
        
        Outcomes
        --------
        self.launch_worker()
            Run parallel processes capped at the number of CPU's selected by the user to devote to BASSPRO or STAGG.
        """

        # Create new folder for run
        basspro_output_dir = os.path.join(self.workspace_dir, 'BASSPRO_output')

        if not os.path.exists(basspro_output_dir):
            os.mkdir(basspro_output_dir)

        curr_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        basspro_run_folder = os.path.join(basspro_output_dir, f'BASSPRO_output_{curr_timestamp}')
        os.mkdir(basspro_run_folder)

        # Write metadata file
        metadata_file = os.path.join(basspro_run_folder, f"metadata_{curr_timestamp}.csv")
        MetadataSettings.save_file(self.metadata_df, metadata_file)

        # Write basspro config file
        #new_filename = os.path.join(basspro_run_folder, f"basspro_config_{os.path.basename(basspro_run_folder).lstrip('py_output')}.txt")
        #shutil.copyfile(f'{Path(__file__).parent}/breathcaller_config.json', new_filename)

        # Write autosections file
        autosections_file = ""
        if self.autosections_df is not None:
            autosections_file = os.path.join(basspro_run_folder, f"auto_sections_{curr_timestamp}.csv")
            AutoSettings.save_file(self.autosections_df, autosections_file)
    
        # Write mansections file
        mansections_file = ""
        if self.mansections_df is not None:
            mansections_file = os.path.join(basspro_run_folder, f"manual_sections_{curr_timestamp}.csv")
            ManualSettings.save_file(self.mansections_df, mansections_file)

        # Write basic settings
        basic_file = os.path.join(basspro_run_folder, f"basics_{curr_timestamp}.csv")
        print(basic_file)
        BasicSettings.save_file(self.basicap_df, basic_file)

        # Write json config to gui_config location
        print(os.getcwd())
        print(os.path.join(CONFIG_DIR, 'gui_config.json'))
        with open(os.path.join(os.getcwd(),CONFIG_DIR, 'gui_config.json'),'w') as gconfig_file:
            json.dump(self.gui_config, gconfig_file)

        # Copy over config file
        #new_filename = os.path.join(basspro_run_folder, f"gui_config_{curr_timestamp}.txt")
        #shutil.copyfile(f'{Path(__file__).parent}/gui_config.json', new_filename)
        
        print('launch_basspro thread id',threading.get_ident())
        print("launch_basspro process id",os.getpid())

        ## Threading Settings ##
        # TODO: remove invalid inputs -- add label to combobox instead of putting description as option
        # adjust thread limit for the qthreadpool
        try:
            # Try to convert combo box text to int
            thread_limit_combo_selection = self.parallel_combo.currentText()
            thread_limit = int(thread_limit_combo_selection)
        except ValueError:
            # ValueError thrown when no option selected
            #   Set to default
            thread_limit = 1
            self.parallel_combo.setCurrentText("1")

        self.qthreadpool.setMaxThreadCount(thread_limit)

        shared_queue = queue.Queue()
        workers = {}

        ## Start Jobs ##
        for job in MainGUIworker.get_jobs_py(signal_files=self.signal_files,
                                             module=self.basspro_path,
                                             output=basspro_run_folder,
                                             metadata=metadata_file,
                                             manual=mansections_file,
                                             auto=autosections_file,
                                             basic=basic_file):

            worker_id = generate_unique_id(workers.keys())

            # create a Worker
            new_worker = MainGUIworker.Worker(
                job,
                worker_id,
                shared_queue,
                )

            # Add the 'QRunnable' worker to the threadpool which will manage how
            # many are started at a time
            self.qthreadpool.start(new_worker)

            # Keep the worker around in a dict
            workers[worker_id] = new_worker

        return basspro_run_folder, shared_queue, workers
    
    def output_check(self):
        """
        Find the signal files that did not produce BASSPRO output.

        Parameters
        --------
        self.signals: list
            This attribute is a list of the file paths of the current signal files selected.
        self.stagg_input_files: list
            This attribute is a list of one of the following:
              - JSON files produced by the most recent run of BASSPRO in the same session;
              - JSON files produced by BASSPRO selected by user with a FileDialog;
              - An .RData file produced by a previous run of STAGG;
              - An .RData file produced by a previous run of STAGG and JSON files produced by BASSPRO.
        self.hangar: QTextEdit
            This TextEdit displays feedback on user activity and either BASSPRO or STAGG processing.
        
        Outputs
        --------
        self.hangar: QTextEdit
            This TextEdit is appended with a list of othe signal files that did not pass BASSPRO and failed to produce JSON files.
        """
        goodies = []
        baddies = []
        if len(self.stagg_input_files) != len(self.signal_files):
            for s in self.signal_files:
                name = os.path.basename(s).split('.')[0]
                for g in self.stagg_input_files:
                    if '_' in name:
                        if os.path.basename(g).split('.')[0] == name:
                            goodies.append(name)
                    else:
                        if os.path.basename(g).split('_')[0] == name:
                            goodies.append(name)
                if name not in goodies:
                    baddies.append(name)

        if len(baddies) > 0:
            self.status_message(f"\nThe following signals files did not pass BASSPRO:\n\n{', '.join([os.path.basename(thumb) for thumb in baddies])}\n")

    def check_stagg_reqs(self, full_run=False):
        """
        Copy STAGG input to timestamped STAGG output folder, determine which STAGG scripts to use based on the presence or absence of an .RData file, and determine if self.input_dir_r needs to be a str path to directory instead of list because the list has more than 200 files, and run self.rthing_to_do_cntd().

        Parameters
        --------
        self.output_folder: str
            This attribute is set as an empty string and then populated with the appropriate directory path (i.e. the path that will serve as either self.output_dir_py or self.output_dir_r). The corresponding directory is created if it doesn't already exist.
        self.variable_config: str
            This attribute refers to the file path of the variable_config.csv file.
        self.graph_config: str
            This attribute refers to the file path of the graph_config.csv file.
        self.other_config: str
            This attribute refers to the file path of the other_config.csv file.
        self.papr_dir: str
            This attribute refers to the directory path of the STAGG scripts folder.
        self.stagg_input_files: list
            This attribute is a list of one of the following: JSON files produced by the most recent run of BASSPRO in the same session; JSON files produced by BASSPRO selected by user with a FileDialog; an .RData file produced by a previous run of STAGG; an .RData file produced by a previous run of STAGG and JSON files produced by BASSPRO.
        
        Outputs
        --------
        self.output_dir_r: str
            This attribute is set as a file path to the timestamped STAGG_output_{time} folder within the STAGG_output directory within the user-selected directory self.workspace_dir. It is not spawned until self.require_workspace_dir() is called when STAGG is launched.
        self.image_format: str
            This attribute is set as either ".svg" or ".jpeg" depending on which RadioButton is checked on the main GUI.
        self.pipeline_des: str
            This attribute is set as the file path to one of two scripts that launch STAGG. If self.stagg_input_files has a .RData file in it, then self.pipeline_des refers to the file path for Pipeline_env_multi.R. If self.stagg_input_files consists entirely of JSON files, then self.pipeline_des refers to the file path for Pipeline.R.
        self.input_dir_r: str
            This attribute is set as the directory path of the first file in self.stagg_input_files if self.stagg_input_files contains the file paths of more than 200 files from the same directory.
        reply: QMessageBox
            This MessageBox informs the user that they have more than 200 file paths in self.stagg_input_files from more than one directory and asks the user to put the file in one directory.

        Outcomes
        --------
        self.rthing_to_do_cntd()
            This method ensures the STAGG script exists, prompts the user to indicate where the Rscript.exe file is, and runs self.launch_worker().
        """
        if self.variable_config_df is None or \
            self.graph_config_df is None or \
            self.other_config_df is None:
            notify_error("Missing STAGG config")
            return False

        # if we cant expect output from basspro, then we need to make sure the files are already there
        if not full_run and len(self.stagg_input_files) == 0:
            notify_error("Missing STAGG input files")
            return False

        # Ensure we have a workspace dir selected
        if not self.require_workspace_dir():
            return False

        rscript_path = self.gui_config['Dictionaries']['Paths']['rscript']
        # If path stored in gui_config.json does not exist or is not an Rscript executable file:
        while not os.path.splitext(os.path.basename(rscript_path))[0] == "Rscript" or \
            not os.path.exists(rscript_path):
            
            # Ask user to choose new Rscript
            if not ask_user_ok('Rscript not found',
                               'Rscript path not defined. Would you like to select the R executable?'):
                return
            else:
                # Keep trying to select valid Rscrip
                while True:
                    rscript_path, filter = QFileDialog.getOpenFileName(self, 'Find Rscript Executable', str(self.workspace_dir), "Rscript*")
                    # Catch cancel
                    if not rscript_path:
                        break

                    if os.path.splitext(os.path.basename(rscript_path))[0] == "Rscript":
                        # Got a good Rscript!
                        self.gui_config['Dictionaries']['Paths']['rscript'] = rscript_path
                        with open(os.path.join(CONFIG_DIR, "gui_config.json"), 'w') as gconfig_file:
                            json.dump(self.gui_config, gconfig_file)
                        break

                    notify_error("Must pick a file named Rscript")

        ##  Handle large input  ##
        # If more than 200 input files
        if len(self.stagg_input_files) > 200:
            # STAGG has troubles importing too many files when provided as a list of file paths,
            #   so in these cases, we want args$JSON to be a directory path instead

            unique_dirs = set([os.path.dirname(y) for y in self.stagg_input_files])

            # If more than 1 dir involved
            if len(unique_dirs) > 1:
                # Need to have a different command line, so instead we'll regulate the user:
                title = "That's a lot of JSON"
                msg = 'The STAGG input provided consists of more than 200 files from multiple directories.'
                msg += '\nPlease condense the files into one directory for STAGG to analyze.'
                notify_info(msg, title)
                return False

            # Use directory path instead
            else:
                self.input_dir_r = os.path.dirname(self.stagg_input_files[0])
                return True
        else:
            # If there aren't a ridiculous number of json files in Main.stagg_input_files,
            #   then we just need to render the list of file paths into an unbracketed string 
            #   so that STAGG can recognize it as a list. STAGG didn't like the brackets.
            self.input_dir_r = ','.join(item for item in self.stagg_input_files)
            return True
    

class STAGGInputSettings(Settings):

    valid_filetypes = ['.json', '.RData']
    file_chooser_message = 'Choose STAGG input files from BASSPRO output'
