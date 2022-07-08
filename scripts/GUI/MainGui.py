"""
BASSPRO-STAGG GUI

Signficant contributions and help from Chris Ward, Savannah Lusk, Andersen Chang, and Russell Ray.

version 5 trillion
"""



from collections import defaultdict
import os
import traceback

# general
from glob import glob
from pathlib import Path
import re
import pyodbc
from datetime import datetime

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
from PyQt5.QtCore import QThreadPool, Qt, QTimer

# Local imports
from thinbass_controller import Thinbass
from util import Settings, generate_unique_id
from util.ui.dialogs import ask_user_ok, ask_user_yes, nonblocking_msg, notify_error, notify_info
from auto import AutoSettings
from basic import BasicSettings
from manual import ManualSettings
from AnnotGUI import MetadataSettings
from config import GraphSettings, OtherSettings, VariableSettings, ConfigSettings
from tools.import_cols_vals_thread import ColValImportThread
from tools.constants import BASSPRO_OUTPUT
from thread_manager import ThreadManager
import MainGUIworker
from ui.form import Ui_Plethysmography

# Chris's scripts
from tools.columns_and_values_tools import columns_and_values_from_settings

CONFIG_DIR = os.path.join("scripts","GUI","config")

# TODO: only for development!
AUTOLOAD = 'shaun' in os.getcwd()

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

    DEFAULT_GRAPH_CONFIG_DF = pd.DataFrame(data=[(1, "", ""), (2, "", ""), (3, "", ""), (4, "", "")], columns=['Role', 'Alias', 'Order'])
    DEFAULT_OTHER_CONFIG_DF = pd.DataFrame(columns=["Graph", "Variable", "Xvar", "Pointdodge", "Facet1", "Facet2", "Covariates", "ymin", "ymax", "Inclusion"])

    def __init__(self):
        """
        Instantiate the Plethysmography class and its attributes

        This function extends QMainWindow and the custom
        Ui_Plethysmography class to create the Main GUI window. Below
        are setup methods for PyQt, widget population, initial
        attribute assignments, and callback methods for GUI events
        
        # TODO: move these to BP and STAGG functions

        Parameters
        --------

        """

        super(Plethysmography, self).__init__()

        self.setupUi(self)
        self.setWindowTitle("Plethysmography Analysis Pipeline")
        self.showMaximized()

        # Set working directory to 3 folders up ( . --^ GUI --^ scripts --^ code )
        os.chdir(Path(__file__).parent.parent.parent)

        # Access configuration settings for GUI in gui_config.json
        # - Paths to the BASSPRO and STAGG modules and the local
        #   Rscript.exe file
        # - Fields of the database accessed when building a
        #   metadata file
        # - Settings labels used to organize the populating of the
        #   TableWidgets in the BASSPRO settings subGUIs
        with open(os.path.join(CONFIG_DIR, 'gui_config.json'), 'r') as config_file:
            self.gui_config = json.load(config_file)

        # Access timestamp settings for storing timestamper results in timestamps.json
        # - Populated dictionary with the default timestamps of
        #   multiple experimental setups and an empty dictionary that
        #   will be populated by the timestamps of signal files
        #   selected by the user.
        # TODO: why do we do this?? Never accessed!
        with open(os.path.join(CONFIG_DIR, 'timestamps.json'), 'r') as stamp_file:
            self.stamp = json.load(stamp_file)

        # Access configuration settings for the basspro in breathcaller_config.json
        # - Default settings of multiple experimental setups for
        #   basic, automated, and manual BASSPRO settings
        # - Recently saved settings for automated and basic
        #   BASSPRO settings
        with open(os.path.join(CONFIG_DIR, 'breathcaller_config.json'), 'r') as bconfig_file:
            self.bc_config = json.load(bconfig_file)

        # Access references for the basspro in breathcaller_config.json
        # - Definitions, descriptions, and recommended values
        #   for every basic, manual, and automated BASSPRO setting.
        with open(os.path.join(CONFIG_DIR, 'reference_config.json'), 'r') as rconfig_file:
            self.rc_config = json.load(rconfig_file)

        # General GUI attributes
        self.dialogs = {}  # store nonblocking dialog boxes

        # Threading attributes
        self.qthreadpool = QThreadPool()
        self.qthreadpool.setMaxThreadCount(1)
        self.thread_manager = ThreadManager()
        
        # Use for importing cols/vals from basspro json files
        self.import_thread = None
        self.imported_files = None
        self.col_vals = None


        # TODO: these are just bypassing the gui_config defaults?
        # path to the BASSPRO module script and STAGG scripts directory
        self.basspro_path = os.path.join("scripts", "python_module.py")
        self.papr_dir = os.path.join("scripts", "papr")

        # STAGG Settings
        self.variable_config_df = None
        self.graph_config_df = self.DEFAULT_GRAPH_CONFIG_DF.copy()
        self.other_config_df = self.DEFAULT_OTHER_CONFIG_DF.copy()
        self.breath_df = []  # TODO: unused?
        self.stagg_input_dir_or_files = ""  # path to the STAGG input directory

        # Basspro settings
        self.autosections_df = None
        self.mansections_df = None
        self.metadata_df = None
        self.basicap_df = None

        # Populate default automated experimental setups
        self.necessary_timestamp_box.addItems(list(self.bc_config['Dictionaries']['Auto Settings']['default'].keys()))
        
        # Populate parallel processing with options for number of cores
        self.parallel_combo.addItems([str(num) for num in range(1, os.cpu_count()+1)])

        # CALLBACKS #
        self.meta_layout.delete_button.clicked.connect(self.delete_meta)
        self.auto_layout.delete_button.clicked.connect(self.delete_auto)
        self.manual_layout.delete_button.clicked.connect(self.delete_manual)
        self.basic_layout.delete_button.clicked.connect(self.delete_basic)
        self.stagg_settings_layout.delete_button.clicked.connect(self.delete_stagg_settings)

        # Autoload configuration (dev only)
        if AUTOLOAD:
            self.signal_files_list.addItem("/home/shaun/Projects/Freelancing/BASSPRO_STAGG/data/Test Dataset/Text files/M39622.txt")
            self.metadata = "/home/shaun/Projects/Freelancing/BASSPRO_STAGG/data/Test Dataset/metadata.csv"
            self.output_dir = "/home/shaun/Projects/Freelancing/BASSPRO_STAGG/output"
            self.autosections = "/home/shaun/Projects/Freelancing/BASSPRO_STAGG/data/Test Dataset/BASSPRO Configuration Files/auto_sections.csv"
            self.basicap = "/home/shaun/Projects/Freelancing/BASSPRO_STAGG/data/Test Dataset/BASSPRO Configuration Files/basics.csv"

            # Pick either RData or json
            if False:
                self.breath_list.addItem("/home/shaun/Projects/Freelancing/BASSPRO_STAGG/data/Test Dataset/R Environment/myEnv_20220324_140527.RData")
            else:
                json_glob = "/home/shaun/Projects/Freelancing/BASSPRO_STAGG/data/Test Dataset/JSON files/*"
                for json_path in glob(json_glob):
                    self.breath_list.addItem(json_path)

    ## Getters & Setters ##
    @property
    def output_dir(self):
        """Get output directory path from widget"""
        return self.output_path_display.text()

    @output_dir.setter
    def output_dir(self, new_dir):
        """Set output directory path"""
        self.output_path_display.setText(new_dir)

    @property
    def metadata(self):
        """Get the current metadata filepath"""
        if self.metadata_list.count():
            return self.metadata_list.item(0).text()
        else:
            return None

    @metadata.setter
    def metadata(self, filepath_or_data):
        """Set metadata filepath or data"""
        if type(filepath_or_data) is str:
            filepath = filepath_or_data

            if MetadataSettings.validate(filepath):
                self.metadata_df = MetadataSettings.attempt_load(filepath)
                if self.metadata_df is not None:
                    self.metadata_list.clear()
                    self.metadata_list.addItem(filepath)
        else:
            data = filepath_or_data
            self.metadata_df = data

        if self.metadata_df is None:
            self.meta_layout.delete_button.hide()
            self.metadata_list.clear()
        else:
            self.meta_layout.delete_button.show()

    @property
    def signal_files(self):
        """Get list of signal files from listwidget"""
        return [self.signal_files_list.item(i).text() for i in range(self.signal_files_list.count())]

    @property
    def autosections(self):
        """Get current autosections file from listwidget"""
        return self.get_settings_file_from_list("auto")

    @autosections.setter
    def autosections(self, filepath_or_data):
        """Set autosections filepath or data"""
        if type(filepath_or_data) is str:
            filepath = filepath_or_data

            if AutoSettings.validate(filepath):
                self.autosections_df = AutoSettings.attempt_load(filepath)

                if self.autosections_df is not None:
                    # Remove old autosections
                    for item in self.sections_list.findItems("auto", Qt.MatchContains):
                        self.sections_list.takeItem(self.sections_list.row(item))
                    
                    # Add new one
                    self.sections_list.addItem(filepath)
                    self.necessary_timestamp_box.addItem("Custom")
        else:
            data = filepath_or_data
            self.autosections_df = data

        if self.autosections_df is None:
            self.auto_layout.delete_button.hide()
            if self.necessary_timestamp_box.findText("Custom") != -1:
                self.necessary_timestamp_box.removeItem(self.necessary_timestamp_box.findText("Custom"))
                self.necessary_timestamp_box.setCurrentIndex(0)
            # Remove old autosections
            for item in self.sections_list.findItems("auto", Qt.MatchContains):
                self.sections_list.takeItem(self.sections_list.row(item))
        else:
            self.auto_layout.delete_button.show()
            if self.necessary_timestamp_box.findText("Custom") != -1:
                self.necessary_timestamp_box.removeItem(self.necessary_timestamp_box.findText("Custom"))
            self.necessary_timestamp_box.addItem("Custom")

    @property
    def mansections(self):
        """Get current mansections file from listwidget"""
        return self.get_settings_file_from_list("manual")

    @mansections.setter
    def mansections(self, filepath_or_data):
        """Set mansections filepath or data"""
        if type(filepath_or_data) is str:
            filepath = filepath_or_data

            if ManualSettings.validate(filepath):
                self.mansections_df = ManualSettings.attempt_load(filepath)
                if self.mansections_df is not None:
                    # Remove old mansections
                    for item in self.sections_list.findItems("manual", Qt.MatchContains):
                        self.sections_list.takeItem(self.sections_list.row(item))

                    # Add new one
                    self.sections_list.addItem(filepath)
        else:
            data = filepath_or_data
            self.mansections_df = data

        if self.mansections_df is None:
            self.manual_layout.delete_button.hide()
            # Remove old mansections
            for item in self.sections_list.findItems("manual", Qt.MatchContains):
                self.sections_list.takeItem(self.sections_list.row(item))
        else:
            self.manual_layout.delete_button.show()

    @property
    def config_data(self):
        """Get all STAGG settings data -- variable, graph, other"""
        # Get all config data collectively
        var_df = self.variable_config_df

        # If var configs is None, return None (others always have at least default values)
        if var_df is None:
            return None
        # Otherwise return dict of data
        else:
            graph_df = self.graph_config_df
            other_df = self.other_config_df
            return {'variable': var_df, 'graph': graph_df, 'other': other_df}
    
    @config_data.setter
    def config_data(self, new_data):
        """Set all STAGG settings data -- variable, graph, other"""
        # Set all config data collectively
        if new_data is None:
            self.variable_config_df = None
            self.graph_config_df = self.DEFAULT_GRAPH_CONFIG_DF.copy()
            self.other_config_df = self.DEFAULT_OTHER_CONFIG_DF.copy()
            self.variable_list.clear()
            self.stagg_settings_layout.delete_button.hide()
        else:
            var_df = new_data['variable']
            graph_df = new_data['graph']
            other_df = new_data['other']
            self.variable_config_df = var_df if var_df is None else var_df.copy()
            self.graph_config_df = self.DEFAULT_GRAPH_CONFIG_DF.copy() if graph_df is None else graph_df.copy()
            self.other_config_df = self.DEFAULT_OTHER_CONFIG_DF.copy() if other_df is None else other_df.copy()
            self.stagg_settings_layout.delete_button.show()

    @property
    def basicap(self):
        """Get basic settings file from listwidget"""
        return self.get_settings_file_from_list("basic")

    @basicap.setter
    def basicap(self, filepath_or_data):
        """Set basics settings filepath or data"""
        if type(filepath_or_data) is str:
            filepath = filepath_or_data
            if BasicSettings.validate(filepath):
                self.basicap_df = BasicSettings.attempt_load(filepath)
                if self.basicap_df is not None:
                    # Remove old basic settings
                    for item in self.sections_list.findItems("basics",Qt.MatchContains):
                        self.sections_list.takeItem(self.sections_list.row(item))
                    
                    # Add new one
                    self.sections_list.addItem(filepath)
        else:
            data = filepath_or_data
            self.basicap_df = data

        if self.basicap_df is None:
            self.basic_layout.delete_button.hide()
            # Remove old autosections
            for item in self.sections_list.findItems("basics", Qt.MatchContains):
                self.sections_list.takeItem(self.sections_list.row(item))
        else:
            self.basic_layout.delete_button.show()

    @property
    def stagg_input_files(self):
        """Get STAGG input files from listwidget"""
        return [self.breath_list.item(i).text() for i in range(self.breath_list.count())]
    ##         ##

    def get_settings_file_from_list(self, type):
        """Retrieve a particular STAGG settings file from listwidget"""
        all_settings = [self.sections_list.item(i).text() for i in range(self.sections_list.count())]

        for settings_file in all_settings:

            if (type == 'auto' and AutoSettings.validate(settings_file)) or \
               (type == 'manual' and ManualSettings.validate(settings_file)) or \
               (type == 'basic' and BasicSettings.validate(settings_file)):
                return settings_file
        return None

    def dir_contains_valid_import_files(self, dir):
        """Check if `dir` contains any valid files for importing"""
        files = os.listdir(dir)
        for file in files:
            for checker in [MetadataSettings.validate,
                            AutoSettings.validate,
                            ManualSettings.validate,
                            BasicSettings.validate]:
                if checker(file):
                    return True
        return False


    def timestamp_dict(self):
        """
        Compare the timestamps of the signal files to those of the experimental
        setup selected by the user via self.necessary_timestamp_box. Print
        a status message with the results of the comparison.

        Parameters
        --------
        self.stamp: dict
            This attribute is a nested dictionary loaded from timestamps.json.
            It contains a populated dictionary with the default timestamps of
            multiple experimental setups and an empty dictionary that will be
            populated by the timestamps of signal files selected by the user.
        self.necessary_timestamp_box: QComboBox
            A comboBox that is populated with the experimental setups for which
            the GUI has default automated BASSPRO settings. These experimental
            setups are sourced from the keys of the "default" dictionary nested
            in the "Auto Settings" dictionary loaded from the
            breathcaller_config.json file.
        self.bc_config: dict
            This attribute is a nested dictionary loaded from breathcaller_config.json.
            It contains the default settings of multiple experimental setups for
            basic, automated, and manual BASSPRO settings and  the most recently
            saved settings for automated and basic BASSPRO settings.
            See the README file for more detail.
        
        """
        combo_need = self.necessary_timestamp_box.currentText()

        # Check if user has made any combobox selection
        if combo_need == "Select dataset...":
            notify_info(title='Missing dataset',
                        msg='Please select one of the options from the dropdown menu above.')
            return

        # Check if user has selected signal files
        if len(self.signal_files) == 0:
            notify_info(title='Missing signal files',
                        msg='Please select signal files.')
            return

        # Populate self.stamp with keys based on directories of signal files.
        self.stamp['Dictionaries']['Data'] = {}

        # wut?
        # I'm leaving this weird epoch, condition stuff in here because I don't want to break anything but I don't remember why I did this.
        #   Maybe I thought comparisons for multiple signal file selections would be saved to the same dictionary? T
        epochs = []
        conditions = []
        
        for f in self.signal_files:
            if os.path.basename(Path(f).parent.parent) in epochs:
                continue
            else:
                epochs.append(os.path.basename(Path(f).parent.parent))
                if os.path.basename(Path(f).parent) in conditions:
                    continue
                else:
                    conditions.append(os.path.basename(Path(f).parent))

        stamp_data = self.stamp['Dictionaries']['Data']
        for condition in conditions:
            for epoch in epochs:
                if epoch in stamp_data:
                    if condition in stamp_data[epoch]:
                        continue
                    else:
                        self.stamp['Dictionaries']['Data'][epoch][condition] = {}
                else:
                    self.stamp['Dictionaries']['Data'][epoch] = {}
                    self.stamp['Dictionaries']['Data'][epoch][condition] = {}

        if combo_need == "Custom":
            timestamps_needed = dict(zip(self.autosections_df['Alias'],[[x] for x in self.autosections_df['Alias']]))
            for y in timestamps_needed:
                timestamps_needed[y] = [y]
        else:
            bc = self.bc_config['Dictionaries']['Auto Settings']['default'][combo_need]
            timestamps_needed = bc.fromkeys(bc.keys())
            for b in timestamps_needed:
                timestamps_needed[b] = [b]

        self.status_message("Checking timestamps...")

        # TODO: put in separate thread/process
        tsbyfile = self.grabTimeStamps()
        check = self.checkFileTimeStamps(tsbyfile, timestamps_needed)

        for epoch in epochs:
            for condition in conditions:
                self.stamp['Dictionaries']['Data'][epoch][condition]["tsbyfile"] = tsbyfile
                for notable in check:
                    self.stamp['Dictionaries']['Data'][epoch][condition][notable] = check[notable]  

        try:
            # Dump self.stamp into a JSON saved in the same directory as the first signal file listed in self.signals.
            curr_time_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            dir_of_first_signal = Path(self.signal_files[0]).parent
            dir_of_first_signal_basename = os.path.basename(dir_of_first_signal)
            tpath = os.path.join(dir_of_first_signal, f"timestamp_{dir_of_first_signal_basename}_{curr_time_str}")
            with open(tpath,"w") as f:
                f.write(json.dumps(self.stamp))

        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            notify_error(title=f"{type(e).__name__}: {e}", msg=f"The timestamp file could not be written.")

        # Print summary of timestamps review to the hangar.
        self.status_message("Timestamp output saved.")
        self.status_message("---Timestamp Summary---")
        self.status_message(f"Files with missing timestamps: {', '.join(set([w for m in check['files_missing_a_ts'] for w in check['files_missing_a_ts'][m]]))}")
        self.status_message(f"Files with duplicate timestamps: {', '.join(set([y for d in check['files_with_dup_ts'] for y in check['files_with_dup_ts'][d]]))}")

        if len(set([z for n in check['new_ts'] for z in check['new_ts'][n]])) == len(self.signal_files):
            self.status_message(f"Files with novel timestamps: all signal files")
        else:
            self.status_message(f"Files with novel timestamps: {', '.join(set([z for n in check['new_ts'] for z in check['new_ts'][n]]))}")

        self.nonblocking_msg(f"Full review of timestamps located at:\n{tpath}")


    def grabTimeStamps(self):
        """
        Iterate through user-selected signal files to compare the signal file's timestamps to the timestamps of one of multiple experimental setups.

        (This method was adapted from a function written by Chris Ward.)

        Parameters
        --------
        self.signals: list
            The list of file paths of the user-selected .txt signal files that are analyzed by BASSPRO.
        tsbyfile: dict
            This attribute is set as an empty dictionary.
        
        Outputs
        --------
        tsbyfile: dict
            This attribute stores a nested dictionary containing the timestamps for every signal file, as well as listing the file and the offending timestamp for duplicate timestamps, missing timestamps, and novel timestamps.
        """
        timestamps = []

        # dictionary containing the timestamps for every signal file, as well
        # as listing the file and the offending timestamp for duplicate
        # timestamps, missing timestamps, and novel timestampsstamps
        tsbyfile = {}
        
        for CurFile in self.signal_files:
            tsbyfile[CurFile] = []
            with open(CurFile,'r') as opfi:
                for i, line in enumerate(opfi):
                    if '#' in line:
                        print('{} TS AT LINE: {} - {}'.format(os.path.basename(CurFile), i, line.split('#')[1][2:]))
                        timestamps.append(line.split('#')[1][2:])
                        c = line.split('#')[1][2:].split(' \n')[0]
                        tsbyfile[CurFile].append(f"{c}")

            # TODO: does this do anything?? -- `[1, 2, 3] = [1, 2, 3]` ?
            tsbyfile[CurFile] = [i for i in tsbyfile[CurFile]]

        timestamps=list(set(timestamps))
        timestamps=[i.split(' \n')[0] for i in timestamps]
        timestamps.sort()
        return tsbyfile

    def checkFileTimeStamps(self, tsbyfile, timestamps_needed):
        """
        Iterate through contents of tsbyfile (dict) to compare them to the
        default timestamps of the user-selected experimental set-up and
        populate self.new_check (dict) with offending timestamps and their signals.

        (This method was adapted from a function written by Chris Ward.)

        Parameters
        --------
        tsbyfile: dict
            Timestamps for every signal file, as well as listing the file
            and the offending timestamp for duplicate timestamps,
            missing timestamps, and novel timestamps.
        timestamps_needed: dict
            Experimental setups for which the GUI has default automated BASSPRO
            settings based on the user's selection of experimental setup via
            the self.necessary_timestamp_box comboBox. These experimental setups
            are sourced from the keys of the "default" dictionary nested in the
            "Auto Settings" dictionary loaded from the breathcaller_config.json file.
        
        Outputs
        --------
            dict: goodfiles, filesmissingts, filesextrats, and new_ts.
        """
        new_ts = defaultdict(list)
        filesmissingts = defaultdict(list)
        filesextrats = defaultdict(list)
        goodfiles = []

        for f in tsbyfile:
            error = False

            for k in timestamps_needed: 
                nt_found = 0

                for t in tsbyfile[f]:
                    if t in timestamps_needed[k]:
                        nt_found += 1

                if nt_found == 1:
                    continue

                elif nt_found > 1:
                    error = True
                    filesextrats[k].append(os.path.basename(f))

                else:
                    error = True
                    filesmissingts[k].append(os.path.basename(f))

            for t in tsbyfile[f]:
                ts_found = False

                for k in timestamps_needed:
                    if t in timestamps_needed[k]:
                        ts_found = True

                if not ts_found:
                    error = True
                    new_ts[t].append(os.path.basename(f))

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

        check = {
            'good_files':goodfiles,
            'files_missing_a_ts':filesmissingts,
            'files_with_dup_ts':filesextrats,
            'new_ts':new_ts
        } 
        return check


    def prepare_meta(self):
        """
        Show popup to choose source of metadata, before
        opening the variable annotation window
        """
        if self.metadata_df is None:
            valid_options = ["Select file", "Load from Database"]
            thinb = Thinbass(valid_options=valid_options)
            if not thinb.exec():
                return

            selected_option = thinb.get_value()

            if selected_option == "Select file":
                self.load_metadata()
            elif selected_option == "Load from Database":
                self.connect_database()

        if self.metadata_df is not None:
            self.show_annot()


    def show_annot(self):
        """Show the metadata settings subGUI to edit metadata"""

        # If no metadata files in play
        if self.metadata_df is None:
            notify_info("Please import a metadata file")
            return

        new_metadata = MetadataSettings.edit(self.metadata_df,
                                             self.output_dir)
        if new_metadata is not None:
            self.metadata = new_metadata

            #if self.breath_df != []:
            #    self.update_breath_df("metadata")

    def show_manual(self):
        """Show the manual BASSPRO settings subGUI to edit manual settings"""
        # Populate GUI widgets with experimental condition choices:
        new_settings = ManualSettings.edit(self.bc_config['Dictionaries']['Manual Settings']['default'],
                                           self.mansections_df,
                                           self.output_dir)
        if new_settings is not None:
            self.mansections = new_settings

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
                                         output_dir=self.output_dir)

        if new_settings is not None:
            self.autosections = new_settings

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
                                          self.output_dir)
        if new_settings is not None:
            self.basicap = new_settings
        
        
    def prepare_stagg_settings(self):
        """
        Ensure that there is a source of variables to populate Config.variable_table with,
        then call stagg settings

        Can be sourced from:
          - metadata and (autosections or mansections)
          - self.variable_config_df
          - self.stagg_input_files (jsons)

        NOTE: the need for this "prepare_" function comes from the potentially longrunning import of
              stagg settings from JSON basspro output files
        """

        # Reset button color in case indicating import completion
        self.stagg_settings_button.setStyleSheet("background-color: #eee")

        # If we already have data for all the configs, use this
        if self.variable_config_df is not None:
            input_data = self.config_data
            col_vals = self.col_vals
        
        # Check for import options
        else:

            # Gather input options
            import_options = ["Select files"]
            if self.stagg_input_files:
                import_options.append("BASSPRO output")
            if self.metadata_df is not None and (self.autosections_df is not None or self.mansections_df is not None):
                import_options.append("Settings files")

            # If we only have one option, choose it (load files)
            if len(import_options) == 1:
                selected_option = import_options[0]

            # If more than 1 option, ask user what they want to do
            else:
                thinb = Thinbass(valid_options=import_options)
                if not thinb.exec():
                    return

                selected_option = thinb.get_value()

            if selected_option == "Select files":
                files = ConfigSettings.open_file(output_dir=self.output_dir)
                if not files:
                    return

                input_data = ConfigSettings.attempt_load(files)
                if input_data is None:
                    notify_error("Could not import files")
                    return

                # Add files to widget to indicate they were loaded
                self.variable_list.clear()
                [self.variable_list.addItem(file) for file in files.values()]

                graph_config_df = input_data['graph']
                col_vals = {}
                for record in graph_config_df.to_dict('records'):
                    # TODO: remaining backwards compatible for files without the Order column
                    order_str = record.get('Order', None)
                    if order_str:
                        col_vals[record['Alias']] = order_str.split('@')
                
            elif selected_option == "BASSPRO output":
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
                        'graph': self.graph_config_df,
                        'other': self.other_config_df}

                    col_vals = self.col_vals

                # Run a new import!
                else:

                    # Filter out anything thats not json (RData files)
                    json_files = [f for f in self.stagg_input_files if f.endswith('.json')]

                    # load basspro output files
                    self.import_thread = ColValImportThread(json_files)
                    
                    # Print out any progress messages emitted by thread
                    self.import_thread.progress.connect(self.status_message)
                    
                    # Call finish method on emitting finished signal
                    self.import_thread.finished.connect(self.finish_import)

                    self.status_message("Importing columns and values from json...")

                    # Disable any change in stagg input files
                    self.breath_files_button.setEnabled(False)
                    self.import_thread.start()
                    notify_info("Starting import, try again when import is done")
                    return

            elif selected_option == "Settings files":
                col_vals, input_data = self.get_cols_vals_from_settings()

        # Open settings window
        self.show_stagg_settings(input_data, col_vals)

    def finish_import(self, kill_thread=False):
        """
        Called at the conclusion of reading columns and values from Basspro json output
          OR at the cancellation of existing import process
        """

        # TODO: Make sure there is no overlap of new thread and an old thread waiting to die
        #   -do proper cleanup!
        if self.import_thread:
            if kill_thread:
                self.status_message("Killing thread...")
                # TODO: ensure the thread cleans up properly!
                # Remove finished callback
                self.import_thread.quit()

            else:
                self.status_message("Done!")
                self.stagg_settings_button.setStyleSheet("background-color: #0f0")
                self.col_vals = self.import_thread.output
                self.imported_files = self.stagg_input_files

                # Automatically set result as current data
                variable_names = self.col_vals.keys()
                var_config_df = ConfigSettings.get_default_variable_df(variable_names)

                self.config_data = {
                    'variable': var_config_df,
                    'graph': self.graph_config_df,
                    'other': self.other_config_df}

            self.breath_files_button.setEnabled(True)
            self.import_thread = None

    def show_stagg_settings(self, input_data, col_vals):
        """
        Show stagg settings window to edit variable, graph, and other configuration

        Parameters
        --------
        input_data (Dict, DataFrame):
            data for variable-, graph-, and other- configs
        col_vals (Dict, list):
            column names and their values

        Outcomes
        --------
        On window "Ok", apply changes to current config data
        """
        # Open Config editor GUI
        new_config_data = ConfigSettings.edit(self.rc_config['References']['Definitions'],
                                              input_data,
                                              col_vals,
                                              self.output_dir)
        if new_config_data is not None:
            self.config_data = new_config_data
            self.col_vals = col_vals


    def delete_meta(self):
        self.metadata = None
        notify_info("Metadata removed.")

    def delete_auto(self):
        self.autosections = None
        notify_info("Auto settings removed.")

    def delete_manual(self):
        self.mansections = None
        notify_info("Manual settings removed.")

    def delete_basic(self):
        self.basicap = None
        notify_info("Basic settings removed.")

    def delete_stagg_settings(self):
        self.config_data = None
        notify_info("STAGG settings removed.")



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

    def select_output_dir(self):
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
        if self.output_dir:
            selection_dir = str(Path(self.output_dir).parent.absolute())
        else:
            selection_dir = None

        output_dir = QFileDialog.getExistingDirectory(self, 'Choose output directory', selection_dir, QFileDialog.ShowDirsOnly)
        # Catch cancel
        if not output_dir:
            return

        # Set output dir
        self.output_dir = output_dir
        
        # TODO: remove?? Not functional for user -- maybe put in some testing utils file
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
            This attribute is set as a file path to the timestamped BASSPRO_output_{time} folder within the BASSPRO_output directory within the user-selected directory output_dir. It is not spawned until self.require_output_dir() is called when BASSPRO is launched.

        Returns
        --------
        output_dir_py: str
            Newly created output dir
        """
        basspro_output_dir = os.path.join(self.output_dir, f'{toolname}_output')

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
        self.output_dir: str
            This attribute is set as the file path to the user-selected output directory.
        self.metadata_list: QListWidget
            This ListWidget inherited from the Ui_Plethysmography class displays the file path of the current metadata file intended as input for BASSPRO or as a source of variables for the populating of self.breath_df and the display of the STAGG settings subGUI.
        
        Outputs
        --------
        self.metadata_list: QListWidget
            This ListWidget is populated with the file path of the metadata.csv file detected in the user-selected self.output_dir output directory.
        self.metadata: str
            This attribute is set as the file path to the metadata.csv file detected in the user-selected self.output_dir output directory.
        """
        metadata_path = os.path.join(self.output_dir, 'metadata.csv')
        if MetadataSettings.validate():
            self.metadata = metadata_path
        else:
            print("No metadata file selected.")

    def auto_get_basic(self):
        """
        Detect a basic BASSPRO settings file, set self.basicap as its file path, and populate self.sections_list with the file path for display to the user.

        Parameters
        --------
        self.output_dir: str
            This attribute is set as the file path to the user-selected output directory.
        self.sections_list: QListWidget
            This ListWidget inherited from the Ui_Plethysmography class displays the file path of the current BASSPRO settings files intended as input for BASSPRO or as a source of variables for the populating of self.breath_df and the display of the STAGG settings subGUI.
        
        Outputs
        --------
        self.sections_list: QListWidget
            This ListWidget is populated with the file path of the basic.csv file detected in the user-selected self.output_dir output directory.
        self.basicap: str
            This attribute is set as the file path to the basic.csv file detected in the user-selected self.output_dir output directory.
        """
        basic_path = os.path.join(self.output_dir, 'basics.csv')
        if BasicSettings.validate(basic_path):
            self.basicap = basic_path
        else:
            print("Basic parameters settings file not detected.")

    def auto_get_autosections(self):
        """
        Detect an automated BASSPRO settings file, set self.autosections as its file path, and populate self.sections_list with the file path for display to the user.

        Parameters
        --------
        self.output_dir: str
            This attribute is set as the file path to the user-selected output directory.
        self.sections_list: QListWidget
            This ListWidget inherited from the Ui_Plethysmography class displays the file path of the current BASSPRO settings files intended as input for BASSPRO or as a source of variables for the populating of self.breath_df and the display of the STAGG settings subGUI.
        
        Outputs
        --------
        self.sections_list: QListWidget
            This ListWidget is populated with the file path of the autosections.csv file detected in the user-selected self.output_dir output directory.
        self.autosections: str
            This attribute is set as the file path to the autosections.csv file detected in the user-selected self.output_dir output directory.
        """
        autosections_path = os.path.join(self.output_dir, 'auto_sections.csv')
        if Path(autosections_path).exists():
            self.autosections = autosections_path
        else:
            print("Autosection parameters file not detected.")

    def auto_get_mansections(self):
        """
        Detect a manual BASSPRO settings file, set self.mansections as its file path, and populate self.sections_list with the file path for display to the user.

        Parameters
        --------
        self.output_dir: str
            This attribute is set as the file path to the user-selected output directory.
        self.sections_list: QListWidget
            This ListWidget inherited from the Ui_Plethysmography class displays the file path of the current BASSPRO settings files intended as input for BASSPRO or as a source of variables for the populating of self.breath_df and the display of the STAGG settings subGUI.
        
        Outputs
        --------
        self.sections_list: QListWidget
            This ListWidget is populated with the file path of the manual_sections.csv file detected in the user-selected self.output_dir output directory.
        self.mansections: str
            This attribute is set as the file path to the manual_sections.csv file detected in the user-selected self.output_dir output directory.
        """
        print("auto_get_mansections()")
        mansections_path = os.path.join(self.output_dir, 'manual_sections.csv')
        if ManualSettings.validate(mansections_path):
            self.mansections = mansections_path
        else:
            print("Manual sections parameters file not detected.")

    # def auto_get_stagg_settings(self, basspro_run_folder):
    #     # Load in settings files from basspro run folder
    #     files = glob(os.path.join(basspro_run_folder, "metadata_*.csv"))
    #     if len(files) == 0:
    #         notify_error(f"Cannot find metadata file in folder: {basspro_run_folder}")
    #         return False
    #     elif len(files) > 1:
    #         notify_error(f"Too many metadata files in folder: {basspro_run_folder}")
    #         return False

    #     metadata_file = files[0]
    #     metadata_df = MetadataSettings.attempt_load(metadata_file)
    #     if metadata_df is None:
    #         notify_error(f"Cannot load metadata file: {metadata_file}")
    #         return False

    #     files = glob(os.path.join(basspro_run_folder, "auto_sections_*.csv"))
    #     if len(files) > 1:
    #         notify_error(f"Too many autosections files in folder: {basspro_run_folder}")
    #         return False

    #     if len(files) == 0:
    #         autosections_df = None
    #     else:
    #         autosections_file = files[0]
    #         autosections_df = AutoSettings.attempt_load(autosections_file)
    #         if autosections_df is None:
    #             notify_error(f"Cannot load autosections file: {autosections_file}")
    #             return False

    #     files = glob(os.path.join(basspro_run_folder, "*manual_sections_*.csv"))
    #     if len(files) > 1:
    #         notify_error(f"Too many mansections files in folder: {basspro_run_folder}")
    #         return False

    #     if len(files) == 0:
    #         mansections_df = None
    #     else:
    #         mansections_file = files[0]
    #         mansections_df = ManualSettings.attempt_load(mansections_file)
    #         if mansections_df is None:
    #             notify_error(f"Cannot load mansections file: {mansections_file}")
    #             return False

    #     # Need at least one sections file present
    #     if autosections_df is None and mansections_df is None:
    #         notify_error(f"Cannot find sections file in folder: {basspro_run_folder}")
    #         return

    #     # Import columns and values from settings files
    #     self.col_vals = columns_and_values_from_settings(metadata_df, autosections_df, mansections_df)

    #     # Create default df with imported variables
    #     variable_names = self.col_vals.keys()
    #     var_config_df = ConfigSettings.get_default_variable_df(variable_names)

    #     # graph_df/other_df are None
    #     self.config_data = {
    #         'variable': var_config_df,
    #         'graph': self.graph_config_df,
    #         'other': self.other_config_df}

    #     return True

    def auto_get_breath_files(self, basspro_run_folder, clear_files):
        """
        Populate self.stagg_input_files with the file paths of the JSON files held in the directory of the most recent BASSPRO run within the same session (the directory file path stored in self.output_dir_py) and populate self.breath_list (ListWidget) with the file paths of those JSON files.

        Parameters
        --------
        self.output_dir_py: str
            This attribute is set as a file path to the timestamped BASSPRO_output_{time} folder within the BASSPRO_output directory within the user-selected directory self.output_dir. It is not spawned until self.require_output_dir() is called when BASSPRO is launched.
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
        # This method needs fixing. If they say yes, I want to keep them, then what happens? It looks like self.stagg_input_files populates with the new files regardless of the user's choice.
        if len(self.stagg_input_files) and clear_files:
            self.breath_list.clear()

        # Get all json files in basspro_run_folder
        stagg_input_files = glob(os.path.join(basspro_run_folder, "*.json"))
        for file in stagg_input_files:
            self.breath_list.addItem(file)

    def open_click(self,item):
        """
        Open the double-clicked ListWidgetItem in the default program for the user's device.
        """
        if Path(item.text()).exists():
            os.startfile(item.text())

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
        # Only allowed to select .txt files
        filenames, filter = QFileDialog.getOpenFileNames(self, 'Select signal files', self.output_dir, '*.txt')

        # Catch cancel
        if not filenames:
            return

        # Print message to user if there is a mismatch with metadata
        if self.metadata_df is not None and \
            not self.test_signal_metadata_match(filenames, self.metadata_df):
            notify_error("Signal files mismatch with metadata.")
            # return

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
        self.output_dir: str
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
            meta_file = MetadataSettings.open_file(self.output_dir)
            # break out of cancel
            if not meta_file:
                return

            data = MetadataSettings.attempt_load(meta_file)
            if data is None:
                notify_error("Could not load metadata")
                return

            # TODO: this should be done in `attempt_load()` ?? Need to push validation back -- is this function really just require_load()?
            # If there are not valid files, try again
            if self.test_signal_metadata_match(self.signal_files, data):
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
        mp_parsed: dict
            This attribute is populated with the mouse IDs, plethysmography IDs, and the tuple constructed from both scraped from the file name of each signal file currently selected.
        """
        print("mp_parser()")

        mp_parsed = {
            'MUIDLIST': [],
            'PLYUIDLIST': [],
            'MUID_PLYUID_tuple': []
        }

        muid_plyuid_re=re.compile('M(?P<muid>.+?(?=_|\.txt))(_Ply)?(?P<plyuid>.*).txt')
        for file in self.signal_files:
            try:
                parsed_filename=re.search(muid_plyuid_re,os.path.basename(file))
                if parsed_filename['muid']!='' and parsed_filename['plyuid']!='':
                    mp_parsed['MUIDLIST'].append(int(parsed_filename['muid']))
                    mp_parsed['PLYUIDLIST'].append(int(parsed_filename['plyuid']))
                    mp_parsed['MUID_PLYUID_tuple'].append(
                        (int(parsed_filename['muid']),int(parsed_filename['plyuid']))
                        )
                elif parsed_filename['muid']!='':
                    mp_parsed['MUIDLIST'].append(int(parsed_filename['muid']))
                    mp_parsed['MUID_PLYUID_tuple'].append(
                        (int(parsed_filename['muid']),'')
                        )
                elif parsed_filename['plyuid']!='':
                    mp_parsed['PLYUIDLIST'].append(int(parsed_filename['plyuid']))
                    mp_parsed['MUID_PLYUID_tuple'].append(
                            ('',int(parsed_filename['plyuid']))
                            )

            # TODO: catch a specific error
            except Exception:
                pass

        return mp_parsed

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
        self.output_dir: str
            This attribute refers to the path of the user-selected output directory.
        
        Outputs
        --------
        reply: QMessageBox
            This MessageBox informs the user that if not signal files have been selected and prompts the user to correct this.
        metadata_warnings: dict
            This attribute is set as an empty dictionary.
        metadata_pm_warnings: list
            This attribute is set as an empty list.

        Outcomes
        --------
        self.get_signal_files()
            This method is called if the user has not selected signal files and prompts them to do so via FileDialog.
        self.mp_parser()
            This method grabs MUIDs and PlyUIDs from signal file names. They are expected to be named with the ID of the mouse beginning with the letter "M", followed by an underscore, followed by the ID of the plethysmography run beginning with the letters "Ply".
        self.get_study()
            This method scrapes the values from the relevant fields of the database for the metadata based on the IDs gotten via self.mp_parser().
        self.require_output_dir()
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

        self.status_message("Gauging Filemaker connection...")
        try:

            mp_parsed = self.mp_parser()
            if not self.require_output_dir():
                return

            dsn = 'DRIVER={FileMaker ODBC};Server=128.249.80.130;Port=2399;Database=MICE;UID=Python;PWD='
            mousedb = pyodbc.connect(dsn)
            mousedb.timeout = 1

            # Retrieve metadata from database
            self.metadata = self.get_study(mousedb, mp_parsed)

            mousedb.close()

        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            msg = "You were unable to connect to the database."
            msg += "\nWould you like to select another metadata file?"
            reply = ask_user_yes('Unable to connect to database', msg)
            if reply:
                self.load_metadata()

    def get_study(self, mousedb, mp_parsed, fixformat=True):
        """
        This method was adapted from a function written by Chris Ward.

        Scrape the values from the relevant fields of the database for the metadata.

        Parameters
        --------
        mp_parsed: dict
            This attribute is populated with the mouse IDs, plethysmography IDs, and the tuple constructed from both scraped from the file name of each signal file currently selected.
        mousedb: ?
            This attribute refers to the connection to the database accessible via the information provided in the variable dsn.

        Outputs
        --------
        m_mouse_dict: dict
            This attribute is populated with the fields and values scraped from the Mouse_List view of the Ray Lab's database.
        p_mouse_dict: dict
            This attribute is populated with the fields and values scarped from the Plethysmography view of the Ray Lab's database.
        self.hangar: QTextEdit
            This attribute is a QTextEdit inherited from the Ui_Plethysmography class that prints a summary of any errors in the process of grabbing metadata from the database.
        self.assemble_df: Dataframe
            This attribute is the dataframe constructed from the concatenated dataframes derived from m_mouse_dict and p_mouse_dict.
        
        Outcomes
        --------
        self.metadata_checker_filemaker()
            This method scans the information grabbed from the database to note any discrepancies.
        """
        self.status_message("Building query...")
        try:
            FieldDict = {
                'Plethysmography': [
                    'MUID',
                    'PlyUID',
                    # 'Misc. Variable 1 Value',
                    'Group',
                    'Weight',
                    # 'Experiment_Name',
                    'Researcher',
                    'Experimental_Date',
                    'time started',
                    'Rig',
                    'Start_body_temperature',
                    'Mid_body_temperature',
                    'End_body_temperature',
                    'post30_body_temperature',
                    'Room_Temp',
                    'Bar_Pres',
                    'Rotometer_Flowrate',
                    'Pump Flowrate',
                    'Calibration_Volume',
                    'Experimental_Date',
                    'Calibration_Condition',
                    # 'Experimental_Condition',
                    'Experimental_Treatment',
                    # 'Gas 1',
                    # 'Gas 2',
                    # 'Gas 3',
                    # 'Tank 1',
                    # 'Tank 2',
                    # 'Tank 3',
                    # 'Dose',
                    # 'Habituation',
                    # 'Plethysmography',
                    'PlyUID'
                    # 'Notes',
                    # 'Project Number',
                ],
                'Mouse_List': [
                    'MUID',
                    'Sex',
                    'Genotype',
                    'Comments',
                    'Date of Birth',
                    'Tag Number',
                    'Age_days'
                ]
            }
            
            #assemble fields for SQL query
            m_FieldText='"' + '","'.join(FieldDict['Mouse_List']) + '"'
            p_FieldText='"' + '","'.join(FieldDict['Plethysmography']) + '"'
            
            # filter sql query based on muid and plyuid info if provided
            if mp_parsed['MUIDLIST'] and mp_parsed['PLYUIDLIST']:
                m_cursor = mousedb.execute(
                    """select """ + m_FieldText +
                    """ from "Mouse_List" where "MUID" in (""" +
                    ','.join([str(i) for i in mp_parsed['MUIDLIST']]) +
                    """) """)    

                p_cursor = mousedb.execute(
                    """select """ + p_FieldText +
                    """ from "Plethysmography" where "PLYUID" in (""" +
                    ','.join([str(i) for i in mp_parsed['PLYUIDLIST']]) +
                    """) and "MUID" in (""" +
                    ','.join(["'M{}'".format(int(i)) for i in mp_parsed['MUIDLIST']]) +
                    """) """)

            elif mp_parsed['PLYUIDLIST']:
                m_cursor = mousedb.execute(
                    """select """ + m_FieldText +
                    """ from "Mouse_List" """)    

                p_cursor = mousedb.execute(
                    """select """ + p_FieldText +
                    """ from "Plethysmography" where "PLYUID" in (""" +
                    ','.join([str(i) for i in mp_parsed['PLYUIDLIST']]) +
                    """) """)

            elif mp_parsed['MUIDLIST']:
                m_cursor = mousedb.execute(
                    """select """ + m_FieldText +
                    """ from "Mouse_List" where "MUID" in (""" +
                    ','.join([str(i) for i in mp_parsed['MUIDLIST']]) +
                    """) """)    

                p_cursor = mousedb.execute(
                    """select """ + p_FieldText +
                    """ from "Plethysmography" where "MUID" in (""" +
                    ','.join(["'M{}'".format(int(i)) for i in mp_parsed['MUIDLIST']]) +

                    """) """)
            else:
                m_cursor = mousedb.execute(
                    """select """ + m_FieldText +
                    """ from "Mouse_List" """)    

                p_cursor = mousedb.execute(
                    """select """ + p_FieldText +
                    """ from "Plethysmography" """)
                
            self.status_message("Fetching metadata...")
            m_mouse_list = m_cursor.fetchall()
            p_mouse_list = p_cursor.fetchall()
            m_head_list = [i[0] for i in m_cursor.description]
            p_head_list = [i[0] for i in p_cursor.description]

            p_mouse_dict = {}
            for i in p_mouse_list:
                p_mouse_dict['Ply{}'.format(int(i[p_head_list.index('PlyUID')]))] = dict(zip(p_head_list,i))

            m_mouse_dict = {}
            for i in m_mouse_list:
                m_mouse_dict['M{}'.format(int(i[p_head_list.index('MUID')]))] = dict(zip(m_head_list,i))

            for z in p_mouse_dict:
                if p_mouse_dict[z]['Mid_body_temperature'] == 0.0:
                    p_mouse_dict[z]['Mid_body_temperature'] = None

            metadata_warnings, metadata_pm_warnings = self.metadata_checker_filemaker(mp_parsed, p_mouse_dict, m_mouse_dict)

            # TODO: build the dict like this from the beginning
            plys = {}
            for ply_id, warnings in metadata_warnings.items():
                for warning in warnings:
                    if warning in plys:
                        plys[warning].append(ply_id)
                    else:
                        plys[warning] = [ply_id]

            for warning, ply_ids in plys.items():
                self.status_message(f"{warning}: {', '.join(ply_ids)}")
            for u in set(metadata_pm_warnings):
                self.status_message(u)

            p_df = pd.DataFrame(p_mouse_dict).transpose()
            m_df = pd.DataFrame(m_mouse_dict).transpose()

            if fixformat:
                p_df['PlyUID']='Ply'+p_df['PlyUID'].astype(int).astype(str)
                p_df['Experimental_Date']=pd.to_datetime(p_df['Experimental_Date'], errors='coerce')
                m_df['MUID']='M'+m_df['MUID'].astype(int).astype(str)
                m_df['Date of Birth']=pd.to_datetime(m_df['Date of Birth'], errors='coerce')

            assemble_df = pd.merge(p_df, m_df, how='left', left_on='MUID', right_on='MUID')
            assemble_df['Age'] = (assemble_df['Experimental_Date'] - assemble_df['Date of Birth']).dt.days

            return assemble_df

        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            new_error='unable to assemble metadata'

    def metadata_checker_filemaker(self, mp_parsed, p_mouse_dict, m_mouse_dict):
        """
        Populate metadata_pm_warnings (list), and metadata_warnings (dict) with information on discrepancies found in the metadata accessed from the database.

        Parameters
        --------
        self.gui_config: dict
           This attribute is a nested dictionary loaded from gui_config.json. It contains paths to the BASSPRO and STAGG modules and the local Rscript.exe file, the fields of the database accessed when building a metadata file, and settings labels used to organize the populating of the TableWidgets in the BASSPRO settings subGUIs. See the README file for more detail.
        self.metadata_list: QListWidget
            This ListWidget inherited from Ui_Plethysmography class displays the file path of the current metadata file on the main GUI.
        mp_parsed: dict
            This attribute is populated with the mouse IDs, plethysmography IDs, and the tuple constructed from both scraped from the file name of each signal file currently selected.
        m_mouse_dict: dict
            This attribute is populated with the fields and values scraped from the Mouse_List view of the Ray Lab's database.
        p_mouse_dict: dict
            This attribute is populated with the fields and values scarped from the Plethysmography view of the Ray Lab's database.

        Outputs
        --------
        self.essential_fields: dict
            This attribute is a nested dictionary from self.gui_config (dict) containing the names of the fields in the Ray Lab Filemaker database that should be accessed to create a metadata file.
        self.metadata_list: QListWidget
            This ListWidget is populated with an update.
        metadata_pm_warnings: list
            This attribute is populated with strings summarizing the instance of discrepancy if any are found.
        metadata_warnings: dict
            This attribute is a populated with PlyUID keys and strings as their values warning of a particular field of metadata missing from the metadata for that plethysmography run.
        """
        print("metadata_checker_filemaker()")
        self.essential_fields = self.gui_config['Dictionaries']['metadata']['essential_fields']
        self.status_message("Checking metadata...")

        metadata_warnings = {}
        metadata_pm_warnings = {}

        # For the MUID and PlyUID pair taken from the signal files provided by the user:
        for m,p in mp_parsed["MUID_PLYUID_tuple"]:

            # Check if the PlyUID is in the metadata:
            if f"Ply{p}" not in p_mouse_dict:

                # If the PlyUID isn't in the metadata, check if its associated MUID is:
                # (We check for the MUID in the m_mouse_dict because its populated regardless of the status of 
                # a MUID's associated PlyUID)
                if f"M{m}" not in m_mouse_dict:
                    metadata_pm_warnings.append(f"Neither Ply{p} nor M{m} were found in metadata.")
                # If the PlyUID isn't in the metadata, but its associated MUID is:
                else:
                    if p != "":
                        metadata_pm_warnings.append(f"Ply{p} of M{m} not found in metadata.")

                    mice = [p_mouse_dict[d]['MUID'] for d in p_mouse_dict]
                    for c in mice:
                        if mice.count(c)>1:
                            metadata_pm_warnings.append(f"More than one PlyUID was found for the following metadata: {', '.join(c for c in set(mice) if mice.count(c)>1)}")
            else:
                # Check if the MUID of the signal file matches that found in the metadata:
                if p_mouse_dict[f"Ply{p}"]["MUID"] != f"M{m}":
                    # If there is no MUID associated with the PlyUID in the metadata:
                    if p_mouse_dict[f"Ply{p}"]["MUID"] == "":
                        # Check if the provided MUID is even in the metadata:
                        if f"M{m}" not in m_mouse_dict:
                            metadata_warnings[f"Ply{p}"] = [f"M{m} of Ply{p} not found in metadata."]
                        else:
                            metadata_warnings[f"Ply{p}"] = [f"M{m} of Ply{p} found in Mouse_List, but no MUID was found in Plethysmography."]
                    else:
                        db_meta = p_mouse_dict[f"Ply{p}"]["MUID"]     
                        metadata_warnings[f"Ply{p}"] = [f"Unexpected MUID: M{m} provided by file, {db_meta} found in metadata."]

                else:
                    for fm in self.essential_fields["mouse"]:
                        if fm not in m_mouse_dict[f"M{m}"]:
                            if f"Ply{p}" in metadata_warnings:
                                metadata_warnings[f"Ply{p}"].append(f"Missing metadata for {fm}")
                            else:
                                metadata_warnings[f"Ply{p}"] = [f"Missing metadata for {fm}"]
                        elif m_mouse_dict[f"M{m}"][fm] == None:
                            if f"Ply{p}" in metadata_warnings:
                                metadata_warnings[f"Ply{p}"].append(f"Empty metadata for {fm}")
                            else:
                                metadata_warnings[f"Ply{p}"] = [f"Empty metadata for {fm}"]

                    for fp in self.essential_fields["pleth"]:
                        if fp not in p_mouse_dict[f"Ply{p}"]:
                            if f"Ply{p}" in metadata_warnings:
                                metadata_warnings[f"Ply{p}"].append(f"Missing metadata for {fp}")
                            else:
                                metadata_warnings[f"Ply{p}"] = [f"Missing metadata for {fp}"]
                        elif p_mouse_dict[f"Ply{p}"][fp] == None:
                            if f"Ply{p}" in metadata_warnings:
                                metadata_warnings[f"Ply{p}"].append(f"Empty metadata for {fp}")
                            else:
                                metadata_warnings[f"Ply{p}"] = [f"Empty metadata for {fp}"]

            return metadata_warnings, metadata_pm_warnings
      
    def get_autosections(self):
        """
        Prompt the user to select a previously made automated BASSPRO settings file.
    
        Parameters
        --------
        QFileDialog: class
            A standard FileDialog.
        self.output_dir: str
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
        filenames, filter = QFileDialog.getOpenFileNames(self, 'Select files', self.output_dir)
        # Catch cancel
        if not filenames:
            return

        skipped_files = []
        for file in filenames:
            if AutoSettings.validate(file):
                self.autosections = file

            elif ManualSettings.validate(file):
                self.mansections = file

            elif BasicSettings.validate(file):
                self.basicap = file

            else:
                skipped_files.append(file)

        # Notify user if invalid files were picked
        if len(skipped_files):
            msg = "Could not load files: "
            msg += ", ".join(skipped_files)
            notify_info(msg)

    def select_stagg_input_files(self):
        """
        Prompt the user to select input files for STAGG. Only .RData files or JSON files are accepted.

        Parameters
        --------
        QFileDialog: class
            A standard FileDialog.
        self.stagg_input_files: list
            This attribute is either an empty list or a list of one of the following: JSON files produced by the most recent run of BASSPRO in the same session; JSON files produced by BASSPRO selected by user with a FileDialog; an .RData file produced by a previous run of STAGG; an .RData file produced by a previous run of STAGG and JSON files produced by BASSPRO.
        self.output_dir: str
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
        files = STAGGInputSettings.open_files(self.output_dir)
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
        if not self.require_output_dir():
            return False
        
        return True

    def get_cols_vals_from_settings(self):

        # Import columns and values from settings files
        col_vals = columns_and_values_from_settings(self.metadata_df, self.autosections_df, self.mansections_df)

        # For any column guaranteed to output from BASSPRO
        #   -if its not included yet, add the column name with an empty list
        for col in BASSPRO_OUTPUT:
            if col not in col_vals:
                col_vals[col] = []

        # Create default df with imported variables
        variable_names = col_vals.keys()
        var_config_df = ConfigSettings.get_default_variable_df(variable_names)

        config_data = {
            'variable': var_config_df.copy(),
            'graph': self.graph_config_df.copy(),
            'other': self.other_config_df.copy()}

        return col_vals, config_data


    def basspro_run(self):
        """
        Check BASSPRO requirements, then launch BASSPRO and track asynchronously

        If the "full_run" box is selected, will automatically attempt to run STAGG
        after BASSPRO completion
        """

        is_full_run = self.full_run_checkbox.isChecked()

        # check that the required input for BASSPRO has been selected
        if not self.check_bp_reqs():
            return

        # If doing full run, check stagg reqs
        if is_full_run and not self.check_stagg_reqs(full_run=True):
                return

        # Prep stagg settings ahead of time using current BP settings
        #   -delay actually setting them in case BP fails
        if self.config_data is None:
            col_vals, config_data = self.get_cols_vals_from_settings()
        else:
            col_vals, config_data = self.col_vals, self.config_data

        # Check whether we have stagg input already
        #   new output will automatically populate
        clear_stagg_input = False
        if len(self.stagg_input_files):
            clear_stagg_input = ask_user_yes('Clear STAGG input list?',
                                             'Would you like to remove the previously selected STAGG input files?')

        # launch BASSPRO
        self.status_message("\n-- -- Launching BASSPRO -- --")
        basspro_run_folder, shared_queue, workers = self.launch_basspro()
        self.basspro_launch_button.setEnabled(False)

        # TODO: prevent full run if stagg already running
        # Kick off stagg later if doing a full-run!
        if is_full_run:
            # Prevent any changes to stagg setup while waiting
            self.enable_stagg_buttons(False)

            # Set next function to run and monitor the workers
            execute_after = lambda : self.pickup_after_basspro(basspro_run_folder, clear_stagg_input, config_data, col_vals)
            
            # Set function in case cancel is selected
            cancel_func = lambda : self.basspro_launch_button.setEnabled(True) or self.enable_stagg_buttons(True)

        else:

            # Wait to check output after basspro finishes
            execute_after = lambda : self.complete_basspro(basspro_run_folder, clear_stagg_input, config_data, col_vals)

            # Set function in case cancel is selected
            cancel_func = lambda : self.basspro_launch_button.setEnabled(True)

        # Monitor the basspro processes and execute a function after completion
        self.thread_manager.add_monitor(workers,
                                        shared_queue,
                                        execute_after=execute_after,
                                        exec_after_cancel=cancel_func,
                                        print_funcs=[self.status_message],
                                        proc_name="BASSPRO")


    def complete_basspro(self, basspro_run_folder, clear_stagg_input, config_data, col_vals):
        # Re-enable basspro button
        self.basspro_launch_button.setEnabled(True)

        # autoload output JSON files
        self.status_message("\nAutopopulating STAGG")
        self.auto_get_breath_files(basspro_run_folder, clear_files=clear_stagg_input)
        
        # Set STAGG Settings
        self.config_data = config_data
        self.col_vals = col_vals
        
        # Check the output and give message to user
        self.output_check()

        # Indicate completion to the user
        title = "BASSPRO finished"
        msg = f"Output can be found at: {basspro_run_folder}."
        self.nonblocking_msg(msg, title)

    def complete_stagg(self, stagg_output_folder):
        self.stagg_launch_button.setEnabled(True)

        # Indicate completion to the user
        title = "STAGG finished"
        msg = f"Output can be found at: {stagg_output_folder}."
        self.nonblocking_msg(msg, title)

    def nonblocking_msg(self, msg, title=""):
        """
        Create new nonblocking dialog message.
        Store in self identified with unique key.
        Provide callback to remove on "Ok".
        """
        dialog_id = generate_unique_id(self.dialogs.keys())
        ok_callback = lambda : self.dialogs.pop(dialog_id)  # remove dialog
        self.dialogs[dialog_id] = nonblocking_msg(msg, [ok_callback], title=title, msg_type='info')

    def stagg_run(self):
        if not self.check_stagg_reqs():
            return

        # Set pipeline destination
        if any(os.path.basename(b).endswith("RData") for b in self.stagg_input_files):
            pipeline_des = os.path.join(self.papr_dir, "Pipeline_env.R")
        else:
            pipeline_des = os.path.join(self.papr_dir, "Pipeline.R")

        if not Path(pipeline_des).is_file():
            # If Main.pipeline_des (aka the first STAGG script file path) isn't a file,
            #   then the STAGG scripts aren't where they're supposed to be.
            notify_error(title='STAGG scripts not found',
                         msg='BASSPRO-STAGG cannot find the scripts for STAGG. Check the BASSPRO-STAGG folder for missing files or directories.')
            return

        self.status_message("\n-- -- Launching STAGG -- --")
        stagg_output_folder, shared_queue, workers = self.launch_stagg(pipeline_des)

        # Prevent another run while running STAGG
        self.stagg_launch_button.setEnabled(False)

        # Wait to check output after basspro finishes
        execute_after = lambda : self.complete_stagg(stagg_output_folder)
        cancel_func = lambda : self.stagg_launch_button.setEnabled(True)

        # Monitor the basspro processes and execute a function after completion
        self.thread_manager.add_monitor(workers,
                                        shared_queue,
                                        execute_after=execute_after,
                                        exec_after_cancel=cancel_func,
                                        print_funcs=[self.status_message],
                                        proc_name="STAGG")
        

    def pickup_after_basspro(self, basspro_run_folder, clear_stagg_input, config_data, col_vals):

        self.enable_stagg_buttons(True)

        # check whether Basspro output is correct, re-enable basspro button
        self.complete_basspro(basspro_run_folder, clear_stagg_input, config_data, col_vals)

        ## RUN STAGG ##
        # launch STAGG
        self.stagg_run()

    def enable_stagg_buttons(self, status:bool):
        self.stagg_settings_button.setEnabled(status)
        self.stagg_settings_layout.delete_button.setEnabled(status)
        self.breath_files_button.setEnabled(status)
        self.stagg_launch_button.setEnabled(status)

    def status_message(self, msg):
        self.hangar.append(msg)

    def launch_stagg(self, pipeline_des):
        """
        Launch STAGG as asynchronous processes

        Parameters
        --------
        pipeline_des: str
            filepath to one of two scripts that launch STAGG
              - Pipeline_env_multi.R
              - Pipeline.R
        """

        # Get image format
        if self.svg_radioButton.isChecked():
            image_format = ".svg"
        elif self.jpeg_radioButton.isChecked():
            image_format = ".jpeg"


        ## WRITE FILES ##
        # Create output folder
        stagg_output_dir = os.path.join(self.output_dir, 'STAGG_output')

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

        rscript_des = os.path.abspath(self.gui_config['Dictionaries']['Paths']['rscript'])

        # Launch STAGG worker!
        for job in MainGUIworker.get_jobs_r(rscript=rscript_des,
                                            pipeline=pipeline_des,
                                            papr_dir=self.papr_dir,
                                            output_dir=self.output_dir,
                                            stagg_input_dir_or_files=self.stagg_input_dir_or_files,
                                            variable_config=variable_config,
                                            graph_config=graph_config,
                                            other_config=other_config,
                                            output_dir_r=stagg_run_folder,
                                            image_format=image_format
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

    def require_output_dir(self):
        """
        Ensure the user has selected an output directory and prompt them to do so if they have not.

        Parameters
        --------
        output_folder: str
            This argument is either self.output_dir_py or self.output_dir_r, the timestamped output directories within either BASSPRO_output or STAGG_output respectively within the self.output_dir directory. These attributes are either empty strings or a directory path.
        output_folder_parent: str
            This argument is either self.basspro_output_dir or self.r_output_folder, the directory paths to either BASSPRO_output or STAGG_output respectively within the self.output_dir directory. These attributes are either empty strings or a directory path.
        text: str
            This argument provides the text needed to customize the FileDialog window title.
        self.output_dir: str
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
        while not self.output_dir:
            if not ask_user_ok('No Output Folder', 'Please select an output folder.'):
                return False

            # open a dialog that prompts the user to choose the directory
            self.select_output_dir()

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
        basspro_output_dir = os.path.join(self.output_dir, 'BASSPRO_output')

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
        BasicSettings.save_file(self.basicap_df, basic_file)

        # Write json config to gui_config location
        with open(os.path.join(CONFIG_DIR, 'gui_config.json'), 'w') as gconfig_file:
            json.dump(self.gui_config, gconfig_file)

        # Copy over config file
        #new_filename = os.path.join(basspro_run_folder, f"gui_config_{curr_timestamp}.txt")
        #shutil.copyfile(f'{Path(__file__).parent}/gui_config.json', new_filename)
        
        print('launch_basspro thread id',threading.get_ident())
        print("launch_basspro process id",os.getpid())

        ## Threading Settings ##
        # Adjust thread limit for the qthreadpool
        thread_limit = int(self.parallel_combo.currentText())
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

        # Compare just the MUID numbers
        # TXT can be MXXX.txt or MXXX_PlyYYY.txt
        signal_basenames = set([os.path.basename(f).split('.')[0].split('_')[0] for f in self.signal_files])
        # JSONs can be MXXX_PlyYYY.json
        json_basenames = set([os.path.basename(f).split('.')[0].split('_')[0] for f in self.stagg_input_files])

        # TODO: should only match on portion that is actually written MXXX or MXXX_PlyYYY
        baddies = signal_basenames.difference(json_basenames)

        if len(baddies) > 0:
            baddies_list_str = ', '.join(baddies)
            msg  = "\nThe following signals files did not pass BASSPRO:"
            msg += f"\n{baddies_list_str}"
            self.status_message(msg)

    def check_stagg_reqs(self, full_run=False):
        """
        Copy STAGG input to timestamped STAGG output folder, determine which STAGG scripts to use based on the presence or absence of an .RData file, and determine if self.stagg_input_dir_or_files needs to be a str path to directory instead of list because the list has more than 200 files, and run self.rthing_to_do_cntd().

        Parameters
        --------
        full_run: bool
        """
        if not full_run and (
            self.variable_config_df is None or \
            self.graph_config_df is None or \
            self.other_config_df is None):
            notify_error("Missing STAGG config")
            return False

        # if we cant expect output from basspro, then we need to make sure the files are already there
        if not full_run and len(self.stagg_input_files) == 0:
            notify_error("Missing STAGG input files")
            return False

        # Ensure we have a workspace dir selected
        if not self.require_output_dir():
            return False


        # Set Rscript path
        rscript_path = os.path.abspath(self.gui_config['Dictionaries']['Paths']['rscript'])
        # If path stored in gui_config.json does not exist or is not an Rscript executable file:
        while not os.path.splitext(os.path.basename(rscript_path))[0] == "Rscript" or \
            not os.path.exists(rscript_path):
            
            # Ask user to choose new Rscript
            if not ask_user_ok('Rscript not found',
                               'Rscript path not defined. Would you like to select the R executable?'):
                return False

            # Keep trying to select valid Rscrip
            while True:
                rscript_path, filter = QFileDialog.getOpenFileName(self, 'Find Rscript Executable', str(self.output_dir), "Rscript*")
                # Catch cancel
                if not rscript_path:
                    return False

                if os.path.splitext(os.path.basename(rscript_path))[0] == "Rscript":
                    # Got a good Rscript!
                    self.gui_config['Dictionaries']['Paths']['rscript'] = rscript_path
                    # TODO: this should not overwrite defaults
                    with open(os.path.join(CONFIG_DIR, "gui_config.json"), 'w') as gconfig_file:
                        json.dump(self.gui_config, gconfig_file)
                    break

                notify_error("Must pick a file named Rscript")

        ##  Handle large input  ##
        unique_dirs = set([os.path.dirname(y) for y in self.stagg_input_files])
        # If more than 200 input files
            
            # STAGG has troubles importing too many files when provided as a list of file paths,
            #   so in these cases, we want args$JSON to be a directory path instead

        # If more than 1 dir involved
        if len(unique_dirs) > 1:

            if len(self.stagg_input_files) > 200:
            # Need to have a different command line, so instead we'll regulate the user:
                title = "That's a lot of JSON"
                msg = 'The STAGG input provided consists of more than 200 files from multiple directories.'
                msg += '\nPlease condense the files into one directory for STAGG to analyze.'
                notify_info(msg, title)
                return False

            else:
            # If there aren't a ridiculous number of json files in Main.stagg_input_files,
            #   then we just need to render the list of file paths into an unbracketed string 
            #   so that STAGG can recognize it as a list. STAGG didn't like the brackets.
                self.stagg_input_dir_or_files = ','.join(item for item in self.stagg_input_files)
                return True

        # Use directory path instead
        else:
            self.stagg_input_dir_or_files = os.path.dirname(self.stagg_input_files[0])
            return True

class STAGGInputSettings(Settings):

    valid_filetypes = ['.json', '.RData']
    file_chooser_message = 'Choose STAGG input files from BASSPRO output'
