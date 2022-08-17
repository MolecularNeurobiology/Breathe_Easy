"""
The following code defines classes and functions for the main GUI.
Signficant contributions and help from Chris Ward, Savannah Lusk, Andersen Chang, and Russell Ray.
"""

from collections import defaultdict
import os
import traceback
from typing import Dict
from glob import glob
from pathlib import Path
import re
import pyodbc
from datetime import datetime

# data parsing
import json
import pandas as pd

# multithreading
import queue

# pyqt
from PyQt5.QtWidgets import QMainWindow, QFileDialog
from PyQt5.QtCore import QThreadPool, Qt

# Local imports
from thinbass_controller import Thinbass
from util import Settings, generate_unique_id
from util.ui.dialogs import ask_user_ok, ask_user_yes, nonblocking_msg, notify_error, notify_info, notify_warning
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

# Directory containing configuration JSONs
CONFIG_DIR = os.path.join("scripts", "GUI", "config")


#%% Define Classes
class STAGGInputSettings(Settings):
    """Attributes and methods for handling STAGG input files"""
    valid_filetypes = ['.json', '.RData']
    file_chooser_message = 'Choose STAGG input files from BASSPRO output'

class BASSPROInputSettings(Settings):
    """Attributes and methods for handling BASSPRO input files"""
    valid_filetypes = ['.txt']
    file_chooser_message = 'Select signal files'

class Plethysmography(QMainWindow, Ui_Plethysmography):
    """
    The Plethysmography class extends Ui_Plethysmography and defines the main GUI.

    Attributes
    ---------
    DEFAULT_GRAPH_CONFIG_DF (DataFrame): default data for graph config
    DEFAULT_OTHER_CONFIG_DF (DataFrame): default data for other config
    gui_config (str): path to default gui config
    stamp (dict): timestamp settings
    bc_config (dict): default basspro settings
    rc_config (dict): help text config settings
    dialogs (Dict): attribute used to store nonblocking dialog windows
    qthreadpool (QThreadPool): used to allocate processes across CPU cores
    thread_manager (ThreadManager): used to monitor running threads
    import_thread (Thread): used on import of STAGG Settings from BP output
    imported_files (list[str]):
        list of STAGG input paths previously used to import STAGG Settings
    col_vals (Dict[str, list]):
        all values for each column in STAGG Settings
    basspro_path (str): path to BASSPRO python script
    papr_dir (str): path to STAGG scripts directory
    config_data (Dict[str, DataFrame]):
        'variable', 'graph', and 'other' data for STAGG Settings
    autosections_df (DataFrame): autosections data
    mansections_df (DataFrame): mansections data
    metadata_df (DataFrame): metadata settings data
    basicap_df (DataFrame): basic settings data
    """

    DEFAULT_GRAPH_CONFIG_DF = pd.DataFrame(data=[(1, "", ""), (2, "", ""), (3, "", ""), (4, "", "")], columns=['Role', 'Alias', 'Order'])
    DEFAULT_OTHER_CONFIG_DF = pd.DataFrame(columns=["Graph", "Variable", "Xvar", "Pointdodge", "Facet1", "Facet2", "Covariates", "ymin", "ymax", "Inclusion"])

    def __init__(self):
        """Instantiate the Plethysmography class and its attributes"""

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
        # TODO: this is never accessed, except for a file write
        with open(os.path.join(CONFIG_DIR, 'timestamps.json'), 'r') as stamp_file:
            self.stamp = json.load(stamp_file)

        # Access configuration settings for basspro in breathcaller_config.json
        # - Default settings of multiple experimental setups for
        #   basic, automated, and manual BASSPRO settings
        # - Recently saved settings for automated and basic
        #   BASSPRO settings
        with open(os.path.join(CONFIG_DIR, 'breathcaller_config.json'), 'r') as bconfig_file:
            self.bc_config = json.load(bconfig_file)

        # Access references for basspro in reference_config.json
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


        # TODO: deconflict with paths stored in gui config defaults
        # path to the BASSPRO module script and STAGG scripts directory
        self.basspro_path = os.path.join("scripts", "python_module.py")
        self.papr_dir = os.path.join("scripts", "papr")

        # STAGG Settings
        self.config_data = None  # {var=None, graph/other=defaults}

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
        # adding callbacks for delete buttons
        self.meta_layout.delete_button.clicked.connect(self.delete_meta)
        self.auto_layout.delete_button.clicked.connect(self.delete_auto)
        self.manual_layout.delete_button.clicked.connect(self.delete_manual)
        self.basic_layout.delete_button.clicked.connect(self.delete_basic)
        self.stagg_settings_layout.delete_button.clicked.connect(self.delete_stagg_settings)

    #######################
    ## Getters & Setters ##
    #######################
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

        # Preparing to clean up the timestamp options below
        custom_timestamp_idx = self.necessary_timestamp_box.findText("Custom") 

        if self.autosections_df is None:
            self.auto_layout.delete_button.hide()
            if custom_timestamp_idx != -1:
                if self.necessary_timestamp_box.currentIndex() == custom_timestamp_idx:
                    # Set back to default
                    self.necessary_timestamp_box.setCurrentIndex(0)
                self.necessary_timestamp_box.removeItem(custom_timestamp_idx)

            # Remove old autosections
            for item in self.sections_list.findItems("auto", Qt.MatchContains):
                self.sections_list.takeItem(self.sections_list.row(item))
        else:
            self.auto_layout.delete_button.show()
            if custom_timestamp_idx == -1:
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
        """Get collective STAGG settings data -- variable, graph, other"""
        var_df = self.variable_config_df

        # If var configs is None, return None (others will always have at least default values)
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
            print("none")
            self.variable_config_df = None
            self.graph_config_df = self.DEFAULT_GRAPH_CONFIG_DF.copy()
            self.other_config_df = self.DEFAULT_OTHER_CONFIG_DF.copy()
            self.variable_list.clear()
            self.stagg_settings_layout.delete_button.hide()
        else:
            print("not non")
            var_df = new_data['variable']
            graph_df = new_data['graph']
            other_df = new_data['other']
            self.variable_config_df = var_df if var_df is None else var_df.copy()
            # Set defaults if None is given
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
                    for item in self.sections_list.findItems("basics", Qt.MatchContains):
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

    def get_settings_file_from_list(self, ftype):
        """Retrieve a particular STAGG settings file from listwidget"""
        all_settings = [self.sections_list.item(i).text() for i in range(self.sections_list.count())]

        for settings_file in all_settings:

            if (ftype == 'auto' and AutoSettings.validate(settings_file)) or \
               (ftype == 'manual' and ManualSettings.validate(settings_file)) or \
               (ftype == 'basic' and BasicSettings.validate(settings_file)):
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

    #####################
    ## Delete Settings ##
    #####################
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

    ###############
    ## Utilities ##
    ###############
    def open_click(self, item):
        """Open the double-clicked ListWidgetItem in the default program."""
        if Path(item.text()).exists():
            os.startfile(item.text())

    def nonblocking_msg(self, msg: str, title: str = ""):
        """
        Create new nonblocking dialog message.

        Parameters
        ---------
        msg: message to display
        title: title of dialog window
        
        Attributes-In
        ------------
        self.dialogs: stores the new nonblocking dialog
        """
        dialog_id = generate_unique_id(self.dialogs.keys())
        ok_callback = lambda : self.dialogs.pop(dialog_id)  # remove dialog
        self.dialogs[dialog_id] = nonblocking_msg(msg, [ok_callback], title=title, msg_type='info')

    def status_message(self, msg):
        """Write message to status window"""
        self.hangar.append(msg)

    #######################
    ## Launching subGUIs ##
    #######################
    def edit_metadata(self):
        """
        Show the metadata settings subGUI to edit metadata

        On initialization, show popup to choose source of metadata.
        If subGUI edits confirmed, store selections
        """
        filepath = None
        if self.metadata_df is not None:
            input_data = self.metadata_df

        else:
            options = ["Select file", "Load from Database"]
            thinb = Thinbass(valid_options=options)
            if not thinb.exec():
                return

            selected_option = thinb.get_value()

            if selected_option == "Select file":
                resp = self.load_metadata()
            elif selected_option == "Load from Database":
                resp = self.connect_database()

            if resp is None:
                return

            input_data, filepath = resp


        new_metadata = MetadataSettings.edit(input_data,
                                             self.output_dir)
        if new_metadata is not None:
            self.metadata = new_metadata

            # If we did get information from filesystem, add file to listwidget
            if filepath:
                self.metadata_list.clear()
                self.metadata_list.addItem(filepath)

    def edit_manual(self):
        """
        Show the manual BASSPRO settings subGUI to edit manual settings.
        
        If subGUI edits confirmed, store selections
        """
        # Populate GUI widgets with experimental condition choices:
        new_settings = ManualSettings.edit(self.bc_config['Dictionaries']['Manual Settings']['default'],
                                           self.mansections_df,
                                           self.output_dir)
        if new_settings is not None:
            self.mansections = new_settings

    def edit_auto(self):
        """
        Show the automated BASSPRO settings subGUI to edit auto settings.
        
        If subGUI edits confirmed, store selections
        """
        new_settings = AutoSettings.edit(self.bc_config['Dictionaries']['Auto Settings']['default'],
                                         self.gui_config['Dictionaries']['Settings Types']['Auto Settings'],
                                         self.rc_config['References']['Definitions'],
                                         self.signal_files,
                                         data=self.autosections_df,
                                         output_dir=self.output_dir)

        if new_settings is not None:
            self.autosections = new_settings

    def edit_basic(self):
        """
        Show the basic BASSPRO settings subGUI to edit basic settings.
        
        If subGUI edits confirmed, store selections
        """
        new_settings = BasicSettings.edit(self.bc_config['Dictionaries']['AP']['default'],
                                          self.rc_config['References']['Definitions'],
                                          self.basicap_df,
                                          self.output_dir)
        if new_settings is not None:
            self.basicap = new_settings
        
        
    def finish_import(self, kill_thread=False):
        """
        Called at the conclusion of reading columns and values from Basspro json output
          OR at the cancellation of existing import process

        Parameters
        ---------
        kill_thread (bool): whether to finish by killing the running thread or not

        Attribute-In
        -----------
        self.import_thread: the running import thread
        self.col_vals: results of import
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

    def edit_stagg_settings(self):
        """
        Show the STAGG Settings subGUI for editing.

        On initialization, prompt the user to select an import source.
        Settings can be sourced from:
          - metadata and (autosections or mansections)
          - self.variable_config_df
          - self.stagg_input_files (jsons)

        If subGUI edits confirmed, store selections

        NOTE: this method may initiate a potentially longrunning import of
              stagg settings from JSON basspro output files

        Attribute-In
        -----------
        self.import_thread: the thread used to import settings asynchronously
        self.col_vals: results of settings import
        """

        # Reset button color in case indicating import completion
        self.stagg_settings_button.setStyleSheet("background-color: #eee")

        # Use later to check if data was loaded from filesystem
        # TODO: will be obsolete when we stop holding filepaths
        files = None

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

                # Retrieve col vals from graph config dataframe
                col_vals = GraphSettings.get_col_vals(input_data['graph'])
                
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

        # Open Config editor GUI
        stagg_settings_data = ConfigSettings.edit(self.rc_config['References']['Definitions'],
                                              input_data,
                                              col_vals,
                                              self.output_dir)
        if stagg_settings_data is not None:
            new_config_data, col_vals = stagg_settings_data
            self.config_data = new_config_data
            self.col_vals = col_vals

            # If we did get information from filesystem, add files to listwidget
            if files:
                self.variable_list.clear()
                [self.variable_list.addItem(file) for file in files.values()]

    ##############################
    ## File/Directory Selection ##
    ##############################
    def select_output_dir(self):
        """Allow user to select an output folder, used for both BASSPRO and STAGG"""

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

    def require_output_dir(self):
        """
        Ensure the user has selected an output directory

        Returns
        ------
        bool: whether the user has selected an output directory
        """

        # Keep looping until we get an output directory
        while not self.output_dir:
            if not ask_user_ok('No Output Folder', 'Please select an output folder.'):
                return False

            # open a dialog that prompts the user to choose the directory
            self.select_output_dir()

        return True
        
    def select_signal_files(self):
        """
        Allow user selection of .txt signal files

        User may choose signal files from multiple directories by calling this
        method multiple times.
        """
        # Only allowed to select .txt files
        files = BASSPROInputSettings.open_files(self.output_dir)
        # Catch cancel
        if not files:
            return

        # Print message to user if there is a mismatch with metadata
        if self.metadata_df is not None and \
            not self.test_signal_metadata_match(files, self.metadata_df):
            notify_error("Signal files mismatch with metadata.")

        # Overwrite existing files?
        if self.signal_files_list.count() > 0:
            reply = ask_user_yes(title='Clear signal files list?',
                                 msg='Would you like to remove the previously selected signal files?')
            if reply:
                self.signal_files_list.clear()

        # Add signal files
        [self.signal_files_list.addItem(file) for file in files]
      
    def load_basspro_settings(self):
        """
        Prompt user to select BASSPRO Settings files

        The following can be selected at once:
            * Auto sections
            * Manual sections
            * Basic settings
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
            notify_warning(msg)

    def select_stagg_input_files(self):
        """
        Prompt user to select STAGG input files

        Only .RData files or JSON files are accepted.
        """
        files = STAGGInputSettings.open_files(self.output_dir)
        # Catch cancel
        if not files:
            return

        # if we already have a selection, check about overwrite
        if self.breath_list.count():
            if ask_user_yes('Clear STAGG input list?',
                            'Would you like to remove the previously selected STAGG input files?'):
                self.breath_list.clear()

        for x in files:
            self.breath_list.addItem(x)

    ######################
    ## Metadata Loading ##
    ######################
    @staticmethod
    def test_signal_metadata_match(signal_files: list, meta_df: pd.DataFrame):
        """
        Ensure that the selected metadata file does contain metadata for the signal files selected.

        Parameters
        ---------
        signal_files: file paths of .txt signal files that are analyzed by BASSPRO.
        meta_df: metadata information
        
        Returns
        ------
        bool: whether the signals and metadata are matched
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
            title = "Metadata and signal files mismatch."
            msg = "The following signals files were not found in the selected metadata file:"
            msg += f"\n\n{os.linesep.join([os.path.basename(thumb) for thumb in baddies])}\n"
            notify_error(msg, title)
            # TODO: clean up the Trues here
            return True

        return True

    def load_metadata(self):
        """
        Load metadata from user-selected file
        
        File will be checked for compatibility with signal files
        """
        while True:
            meta_file = MetadataSettings.open_file(self.output_dir)
            # break out of cancel
            if not meta_file:
                return None

            data = MetadataSettings.attempt_load(meta_file)
            if data is None:
                notify_error("Could not load metadata")
                return None

            # TODO: push this to `attempt_load()`
            #   Could we use this as require_load()?
            # If there are not valid files, try again
            if self.test_signal_metadata_match(self.signal_files, data):
                return data, meta_file

    def mp_parser(self):
        """
        Grab MUIDs and PlyUIDs from signal file names.

        Signal files are expected to be named with the ID of the mouse
        beginning with the letter "M", followed by an underscore,
        followed by the ID of the plethysmography run beginning
        with the letters "Ply". 
            ex. "M<mouse_id>_Ply<pleth_id>"
        """

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
        Connect to Ray Lab database and retrieve metadata
        
        Attributes-In
        ------------
        self.signal_files: checked to make sure user has signal files selected
        """

        # Wait for user to get signal files
        while len(self.signal_files) == 0:
            reply = ask_user_ok(
                "Unable to connect to database",
                "No signal files selected.\nWould you like to select a signal file directory?")
            if reply:
                self.select_signal_files()
            else:
                return None
        
        self.status_message("Gauging Filemaker connection...")
        try:

            mp_parsed = self.mp_parser()
            if not self.require_output_dir():
                return None

            # TODO: Make this a constant or class attribute -- move to a DatabaseManager class?
            dsn = 'DRIVER={FileMaker ODBC};Server=128.249.80.130;Port=2399;Database=MICE;UID=Python;PWD='
            mousedb = pyodbc.connect(dsn)
            mousedb.timeout = 1

            # Retrieve metadata from database
            metadata_df = self.get_study(mousedb, mp_parsed)

            mousedb.close()

            # TODO: when no longer handling files, simplify this logic and use of load_metadata()
            return metadata_df, None  # `files` is None

        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            msg = "You were unable to connect to the database."
            msg += "\nWould you like to select an existing metadata file?"
            reply = ask_user_yes('Unable to connect to database', msg)
            if reply:
                return self.load_metadata()

    def get_study(self, mousedb: pyodbc.Connection, mp_parsed: dict, fixformat: bool = True):
        """
        Scrape relevant metadata fields from data from a given database connection

        Parameters
        ---------
        mousedb: database connection object
        mp_parsed:
            mouse IDs, plethysmography IDs, and the tuple constructed from both
            scraped from the file name of each signal file currently selected.
        fixformat: whether to rectify format of returned data

        Returns
        ------
        pd.DataFrame: concatenated dataframes derived from m_mouse_dict and p_mouse_dict.
        """
        self.status_message("Building query...")
        try:
            FieldDict = {
                'Plethysmography': [
                    'MUID',
                    'PlyUID',
                    'Misc. Variable 1 Value',
                    'Group',
                    'Weight',
                    'Experiment_Name',
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
                    'Gas 2',
                    'PlyUID'
                ],
                'Mouse_List': [
                    'MUID',
                    'Sex',
                    'Genotype',
                    'Date of Birth',
                    'Tag Number',
                    'Age_days'
                ]
            }
            
            # assemble fields for SQL query
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

            # fields and values scraped from the Plethysmography view
            p_mouse_dict = {}
            for i in p_mouse_list:
                p_mouse_dict['Ply{}'.format(int(i[p_head_list.index('PlyUID')]))] = dict(zip(p_head_list,i))

            # fields and values scraped from the Mouse_List view
            m_mouse_dict = {}
            for i in m_mouse_list:
                m_mouse_dict['M{}'.format(int(i[p_head_list.index('MUID')]))] = dict(zip(m_head_list,i))

            # Set invalid temperature to None
            for z in p_mouse_dict:
                if p_mouse_dict[z]['Mid_body_temperature'] == 0.0:
                    p_mouse_dict[z]['Mid_body_temperature'] = None

            metadata_warnings, metadata_pm_warnings = self.metadata_checker_filemaker(mp_parsed, p_mouse_dict, m_mouse_dict)

            # TODO: we're just converting format here.
            #   build it like this when it's first created
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

    def metadata_checker_filemaker(self, mp_parsed: dict, p_mouse_dict: dict, m_mouse_dict: dict):
        """
        Populate metadata_pm_warnings (list), and metadata_warnings (dict) with information on discrepancies found in the metadata accessed from the database.

        Parameters
        ---------
        mp_parsed:
            mouse IDs, plethysmography IDs, and the tuple constructed from both
            scraped from the file name of each signal file currently selected.
        p_mouse_dict: dict
            fields and values scraped from the Plethysmography database view
        m_mouse_dict: dict
            fields and values scraped from the Mouse_List database view

        Returns
        ------
        tuple[dict[str, list], list]:
            [0]: list of warnings for each PlyUID keys
            [1]: strings summarizing instances of discrepancy
        """
        print("metadata_checker_filemaker()")
        essential_fields = self.gui_config['Dictionaries']['metadata']['essential_fields']
        self.status_message("Checking metadata...")

        metadata_warnings = {}
        metadata_pm_warnings = []

        # For the MUID and PlyUID pair taken from the signal files provided by the user:
        for m, p in mp_parsed["MUID_PLYUID_tuple"]:

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
                    for fm in essential_fields["mouse"]:
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

                    for fp in essential_fields["pleth"]:
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

    #################
    ## Run BASSPRO ##
    #################
    def basspro_run(self):
        """
        Check BASSPRO requirements, then launch BASSPRO and track asynchronously.

        If the "full_run" box is selected, will automatically attempt to run STAGG
        after BASSPRO completion.
        """

        # check that the required input for BASSPRO has been selected
        if not self.check_bp_reqs():
            return

        # If doing full run, check stagg reqs
        is_full_run = self.full_run_checkbox.isChecked()
        if is_full_run and not self.check_stagg_reqs(wait_for_basspro=True):
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
            cancel_msg = "would you like to cancel checking for STAGG autostart?"

        else:
            # Wait to check output after basspro finishes
            execute_after = lambda : self.complete_basspro(basspro_run_folder, clear_stagg_input, config_data, col_vals)

            # Set function in case cancel is selected
            cancel_func = lambda : self.basspro_launch_button.setEnabled(True)
            cancel_msg = None

        # Monitor the basspro processes and execute a function after completion
        self.thread_manager.add_monitor(workers,
                                        shared_queue,
                                        execute_after=execute_after,
                                        exec_after_cancel=cancel_func,
                                        print_funcs=[self.status_message],
                                        proc_name="BASSPRO",
                                        cancel_msg=cancel_msg,
                                        )
    
    def launch_basspro(self):
        """Kick off a BASSPRO run as a collection of asynchronous processes."""

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
        """Check for signal files that did not produce BASSPRO output."""

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

    def complete_basspro(self,basspro_run_folder: str, clear_stagg_input: bool,
                         config_data: Dict[str, pd.DataFrame], col_vals: Dict[str, list]):
        """
        Follow-up processing after BASSPRO run
        
        Parameters
        ---------
        basspro_run_folder: path to folder containing BASSPRO output
        clear_stagg_input: flag whether to clear existing STAGG input
        config_data: stagg settings
        col_vals: all input column names and their values
        """
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

    def auto_get_breath_files(self, basspro_run_folder: str, clear_files: bool):
        """
        Parameters
        --------
        basspro_run_folder: path to basspro run output
        clear_files: flag indicating whether to clear existing breath files
        """

        if len(self.stagg_input_files) and clear_files:
            self.breath_list.clear()

        # Get all json files in basspro_run_folder
        stagg_input_files = glob(os.path.join(basspro_run_folder, "*.json"))
        for file in stagg_input_files:
            self.breath_list.addItem(file)

    def check_bp_reqs(self):
        """
        Check requirements for running BASSPRO
        
        Returns
        ------
        bool: whether all requirements are met
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
        """
        Import columns and values from current BASSPRO settings files.
        
        The output will be used to populate the STAGG settings.

        Returns
        ------
        tuple[dict[str, list], dict[str, pd.DataFrame]]:
            [0]: list of values for every column name
            [1]: dataframe for each of "variable", "graph", and "other" configs
        """

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

    def pickup_after_basspro(self, basspro_run_folder, clear_stagg_input, config_data, col_vals):
        """
        Full-run processing to transition from BASSPRO to STAGG
        
        Parameters
        ---------
        basspro_run_folder: path to folder containing BASSPRO output
        clear_stagg_input: flag whether to clear existing STAGG input
        config_data: stagg settings
        col_vals: all input column names and their values
        """

        # Let the user edit STAGG again
        self.enable_stagg_buttons(True)

        # check whether Basspro output is correct, re-enable basspro button
        self.complete_basspro(basspro_run_folder, clear_stagg_input, config_data, col_vals)

        # launch STAGG
        self.stagg_run()

    ###############
    ## Run STAGG ##
    ###############
    def stagg_run(self):
        """Check requirements, create output folder, and run STAGG"""
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

    def launch_stagg(self, pipeline_des: str):
        """
        Launch STAGG as asynchronous processes

        Parameters
        --------
        pipeline_des:
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

        # write STAGG input filepaths to file, and give that file to STAGG to read in
        filepaths_file = os.path.join(stagg_run_folder, "input_files.txt")
        with open(filepaths_file, 'w+') as f:
            f.write('\n'.join(self.stagg_input_files))

        # Launch STAGG worker!
        for job in MainGUIworker.get_jobs_r(rscript=rscript_des,
                                            pipeline=pipeline_des,
                                            papr_dir=self.papr_dir,
                                            output_dir=self.output_dir,
                                            inputpaths_file=filepaths_file,
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
        
    def complete_stagg(self, stagg_output_folder: str):
        """
        Follow-up processing after STAGG run
        
        Parameters
        ---------
        stagg_output_folder: path to folder containing STAGG output
        """

        self.stagg_launch_button.setEnabled(True)

        # Indicate completion to the user
        title = "STAGG finished"
        msg = f"Output can be found at: {stagg_output_folder}."
        self.nonblocking_msg(msg, title)

    def check_stagg_reqs(self, wait_for_basspro: bool = False):
        """Check requirements to run STAGG

        Parameters
        --------
        wait_for_basspro: flag indicating whether to expect BASSPRO to produce necessary input

        Returns
        ------
        bool: whether all requirements are met
        """

        # Ensure we have a workspace dir selected
        if not self.require_output_dir():
            return False

        # If full run, this will all be handled after basspro runs
        if not wait_for_basspro:
            if self.variable_config_df is None or \
                    self.graph_config_df is None or \
                    self.other_config_df is None:
                notify_error("Missing STAGG config")
                return False

            if len(self.stagg_input_files) == 0:
                notify_error("Missing STAGG input files")
                return False

        # Prevent multiple STAGG processes
        if self.thread_manager.is_process_named('STAGG'):
            notify_error("A STAGG process is already running")
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
                    # TODO: should this overwrite defaults?
                    with open(os.path.join(CONFIG_DIR, "gui_config.json"), 'w') as gconfig_file:
                        json.dump(self.gui_config, gconfig_file)
                    break

                notify_error("Must pick a file named Rscript.")

        return True

    def enable_stagg_buttons(self, enabled: bool):
        """Enable/Disable collection of STAGG buttons"""
        self.stagg_settings_button.setEnabled(enabled)
        self.stagg_settings_layout.delete_button.setEnabled(enabled)
        self.breath_files_button.setEnabled(enabled)
        self.stagg_launch_button.setEnabled(enabled)

    #######################
    ## Timestamp Methods ##
    #######################
    def timestamp_dict(self):
        """
        Check timestamp data and print to file

        Compare the timestamps of the signal files to those of the experimental
        setup selected by the user. Results are printed in the status window.

        Attributes-In
        ------------
        self.stamp: default timestamp data; populated with timestamp
                    comparison data below and written to a file
        self.bc_config: config used to pull default experimental setup
        self.signal_files: used to check if we have signal files selected
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

        # TODO: clean up epoch stuff
        # Are comparisons for multiple signal file selections saved to the same dictionary?
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
        else:
            bc = self.bc_config['Dictionaries']['Auto Settings']['default'][combo_need]
            timestamps_needed = bc.fromkeys(bc.keys())

        for ts in timestamps_needed:
            timestamps_needed[ts] = [ts]

        self.status_message("Checking timestamps...")

        # TODO: put in separate thread/process
        tsbyfile = self.grabTimeStamps()
        check = self.checkFileTimeStamps(tsbyfile, timestamps_needed)

        # Store timestamp comparison data
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
        Read timestamps from signal files

        Attributes-In
        ------------
        self.signals_files: this function iterates over all signal files
        
        Returns
        ------
        dict: timestamps for every signal file, indexed by filename
        """
        tsbyfile = {}
        for CurFile in self.signal_files:
            tsbyfile[CurFile] = []
            with open(CurFile,'r') as opfi:
                for i, line in enumerate(opfi):
                    if '#' in line:
                        # found timestamp!
                        print('{} TS AT LINE: {} - {}'.format(os.path.basename(CurFile), i, line.split('#')[1][2:]))
                        c = line.split('#')[1][2:].split(' \n')[0]
                        tsbyfile[CurFile].append(f"{c}")

            # TODO: may be obsolete -- `[1, 2, 3] = [1, 2, 3]` ?
            tsbyfile[CurFile] = [i for i in tsbyfile[CurFile]]
        return tsbyfile

    def checkFileTimeStamps(self, tsbyfile, timestamps_needed):
        """
        Compare list of timestamps to a set of required timestamps

        Missing, duplicate, and novel timestamps are returned to the caller

        Parameters
        ---------
        tsbyfile (dict):
            timestamps for every signal file, indexed by filename
        timestamps_needed (dict):
            Required timestamps to compare against
        
        Returns
        ------
        dict: goodfiles, filesmissingts, filesextrats, and new_ts.
        """
        new_ts = defaultdict(list)
        filesmissingts = defaultdict(list)
        filesextrats = defaultdict(list)
        goodfiles = []

        # Go through all signal files
        for f in tsbyfile:
            error = False

            for k in timestamps_needed: 
                nt_found = 0

                for t in tsbyfile[f]:
                    if t in timestamps_needed[k]:
                        nt_found += 1

                if nt_found == 1:
                    continue

                # Too many timestamps!
                elif nt_found > 1:
                    error = True
                    filesextrats[k].append(os.path.basename(f))

                # Missing timestamp!
                else:
                    error = True
                    filesmissingts[k].append(os.path.basename(f))

            for t in tsbyfile[f]:
                ts_found = False

                for k in timestamps_needed:
                    if t in timestamps_needed[k]:
                        ts_found = True

                # Novel timestamp!
                if not ts_found:
                    error = True
                    new_ts[t].append(os.path.basename(f))

            if not error:
                goodfiles.append(os.path.basename(f))

        # Reduce error message grouping if all files included
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

        # Compile return information
        check = {
            'good_files': goodfiles,
            'files_missing_a_ts': filesmissingts,
            'files_with_dup_ts': filesextrats,
            'new_ts': new_ts
        } 
        return check

