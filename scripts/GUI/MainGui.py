"""
BASSPRO-STAGG GUI

Signficant contributions and help from Chris Ward, Savannah Lusk, Andersen Chang, and Russell Ray.

version 5 trillion
"""

import csv
import queue
import traceback
from pathlib import Path
import datetime
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

from PyQt5.QtWidgets import QMainWindow, QMessageBox, QButtonGroup, QTableWidgetItem, QRadioButton, QLineEdit, QComboBox, QFileDialog
from PyQt5.QtCore import QThreadPool, pyqtSlot, Qt

from thumbass_controller import Thumbass
from thinbass_controller import Thinbass
from thorbass_controller import Thorbass
from align_delegate import AlignDelegate
from basic import Basic
from auto import Auto
from manual import Manual
from checkable_combo_box import CheckableComboBox
from config import Config
from util import notify_error

from ui.form import Ui_Plethysmography

# TODO: only for development!
AUTOLOAD = False

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

    ## Getters & Setters ##
    @property
    def workspace_dir(self):
        return self.output_path_display.text()

    @property
    def metadata(self):
        if self.metadata_list.count():
            return self.metadata_list.item(0).text()
        else:
            return None

    @property
    def signal_files(self):
        return [self.signal_files_list.item(i).text() for i in range(self.signal_files_list.count())]

    @property
    def metadata_file(self):
        if self.metadata_list.count() > 1:
            # TODO: error- too many files
            raise RuntimeError("too many metadata files!")
        elif self.metadata_list.count() == 1:
            return self.metadata_list.item(0).text()
        else:
            return None

    @property
    def autosections(self):
        return self.get_settings_file_from_list("auto")

    @autosections.setter
    def autosections(self, file):
        # TODO: put validation in here??
        # Remove old autosections
        for item in self.sections_list.findItems("auto", Qt.MatchContains):
            self.sections_list.takeItem(self.sections_list.row(item))
        
        # Add new one
        self.sections_list.addItem(file)

    @property
    def mansections(self):
        return self.get_settings_file_from_list("manual")

    @property
    def basicap(self):
        return self.get_settings_file_from_list("basic")

    @basicap.setter
    def basicap(self, file):
        # Remove old basic settings
        for item in self.sections_list.findItems("basics",Qt.MatchContains):
            self.sections_list.takeItem(self.sections_list.row(item))
        
        # Add new one
        self.sections_list.addItem(file)

    @property
    def stagg_input_files(self):
        return [self.breath_list.item(i).text() for i in range(self.breath_list.count())]
    ##         ##


    ## Validation Methods ##
    def valid_metadata(self, file):
        return os.path.basename(file).startswith("metadata") and os.path.splitext(file)[1] == '.csv'

    def valid_autosections(self, file):
        return os.path.basename(file).startswith("auto_sections") or os.path.basename(file).startswith("autosections")

    def valid_mansections(self, file):
        return os.path.basename(file).startswith("manual_sections")

    def valid_basicap(self, file):
        return os.path.basename(file).startswith("basics")
    ##         ##


    def get_settings_file_from_list(self, type):
        all_settings = [self.sections_list.item(i).text() for i in range(self.sections_list.count())]

        for settings_file in all_settings:

            if (type == 'auto' and self.valid_autosections(settings_file)) or \
               (type == 'manual' and self.valid_mansections(settings_file)) or \
               (type == 'basic' and self.valid_basicap(settings_file)):
                return settings_file
        return None

    def dir_contains_valid_import_files(self, dir):
        """
        Check if `dir` contains any valid files for importing
        """
        files = os.listdir(dir)
        for file in files:
            for checker in [self.valid_metadata,
                            self.valid_autosections,
                            self.valid_mansections,
                            self.valid_basicap]:
                if checker(file):
                    return True
        return False

    def delete_setting_file(self):
        a = self.sections_list.currentItem()
        if a:
            self.hangar.append(f"Deleted settings: {a.text()}")
            self.sections_list.takeItem(self.sections_list.row(a))
            del a

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
        self.stagg_settings_window()
            This method instantiates the Config class.
        self.m()
            This method instantiates the Manual class.
        self.auto_settings_window()
            This method instantiates the Auto class.
        self.b()
            This method instantiates the Basic class.
        self.g()
            This method instantiates the Annot class.
        """
        super(Plethysmography, self).__init__()

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
        self.showMaximized()

        # Load variables with paths for BASSPro and StaGG stored in gui_config dictionary:
        self.gui_config['Dictionaries']['Paths'].update({'breathcaller':str(Path(f'{Path(__file__).parent.parent}/python_module.py'))})
        print(self.gui_config['Dictionaries']['Paths']['breathcaller'])
        self.gui_config['Dictionaries']['Paths'].update({'papr':str(Path(f'{Path(__file__).parent.parent}/papr'))})
        print(self.gui_config['Dictionaries']['Paths']['papr'])


        self.breathcaller_path = self.gui_config['Dictionaries']['Paths']['breathcaller']
        self.input_dir_r=""
        self.output_dir_r=""
        self.papr_dir = self.gui_config['Dictionaries']['Paths']['papr']
        self.r_output_folder=""
        self.variable_config=""
        self.graph_config=""
        self.other_config=""
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
        self.rscript_des = ""
        self.pipeline_des = ""
        self.loop_menu = {}

        # Initiating subGUIs
        self.stagg_settings_window = Config(self)
        self.m = Manual(self)
        self.auto_settings_window = Auto(self)
        self.b = Basic(self)
        self.g = AnnotGUI.Annot(self)

        self.stagg_settings_window.graphic.setStyleSheet("border-image:url(:resources/graphic.png)")

         # Populate GUI widgets with experimental condition choices: 
        self.necessary_timestamp_box.addItems([x for x in self.bc_config['Dictionaries']['Auto Settings']['default'].keys()])
        self.parallel_combo.addItems([str(num) for num in list(range(1,os.cpu_count()+1))])

        # Populate GUI widgets with experimental condition choices:
        self.m.preset_menu.addItems([x for x in self.bc_config['Dictionaries']['Manual Settings']['default'].keys()])
        self.auto_settings_window.auto_setting_combo.addItems([x for x in self.bc_config['Dictionaries']['Auto Settings']['default'].keys()])
        

        # Analysis parameters
        os.chdir(os.path.join(Path(__file__).parent.parent.parent))


        # Autoload configuration
        if AUTOLOAD:
            self.signal_files_list.addItem("/home/shaun/Projects/Freelancing/BASSPRO_STAGG/BASSPRO-STAGG/data/Test Dataset/Text files/M39622.txt")
            self.metadata_list.addItem("/home/shaun/Projects/Freelancing/BASSPRO_STAGG/BASSPRO-STAGG/data/Test Dataset/metadata.csv")
            self.output_path_display.setText("/home/shaun/Projects/Freelancing/BASSPRO_STAGG")
            self.sections_list.addItem("/home/shaun/Projects/Freelancing/BASSPRO_STAGG/BASSPRO-STAGG/data/Test Dataset/BASSPRO Configuration Files/auto_sections.csv")
            self.sections_list.addItem("/home/shaun/Projects/Freelancing/BASSPRO_STAGG/BASSPRO-STAGG/data/Test Dataset/BASSPRO Configuration Files/basics.csv")
        
        
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
                tpath = os.path.join(Path(self.signal_files[0]).parent,f"timestamp_{os.path.basename(Path(self.signal_files[0]).parent)}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                with open(tpath,"w") as tspath:
                    tspath.write(json.dumps(self.stamp))
                    tspath.close()
            except Exception as e:
                print(f'{type(e).__name__}: {e}')
                print(traceback.format_exc())
                # Why is this a Thumbass instead of QMessageBox?
                self.thumb = Thumbass(self)
                self.thumb.show()
                self.thumb.message_received(f"{type(e).__name__}: {e}",f"The timestamp file could not be written.")

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
            if error==0:
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

#endregion

#region show subGUIs
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
        self.g.show()
        self.g.show_metadata_file()

    def show_manual(self):
        """
        Show the manual BASSPRO settings subGUI defined in the Manual class.

        Outcomes
        --------
        Manual.show()
            This method displays the manual BASSPRO settings subGUI.
        """
        self.m.show()

    def show_auto(self):
        """
        Show the automated BASSPRO settings subGUI defined in the Auto class.

        Outcomes
        --------
        Auto.show()
            This method displays the automated BASSPRO settings subGUI.
        """
        self.auto_settings_window.show()

    def show_basic(self):
        """
        Show the basic BASSPRO settings subGUI defined in the Basic class.

        Outcomes
        --------
        Basic.show()
            This method displays the basic BASSPRO settings subGUI.
        """
        self.b.show()
        
#endregion
#region Variable configuration
    def check_metadata_file(self, metadata_file):
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

        self.hangar.append(f"Checking {metadata_file}")

        if metadata_file.endswith(".csv"):
            meta = pd.read_csv(metadata_file)
        elif metadata_file.endswith(".xlsx"):
            meta = pd.read_excel(metadata_file)
        else:
            notify_error("Bad metadata file format")
            return False

        baddies = []
        for s in self.signal_files:
            name = os.path.basename(s).split('.')[0]
            if '_' in name:
                mouse_uid, ply_uid = name.split('_')
                if len(meta.loc[(meta['MUID'] == mouse_uid)])==0:
                    baddies.append(s)
                elif len(meta.loc[(meta['PlyUID'] == ply_uid)])==0:
                    baddies.append(s)
            elif len(meta.loc[(meta['MUID'] == name)])==0:
                baddies.append(s)

        if len(baddies) > 0:
            self.thumb = Thumbass(self)
            self.thumb.show()
            self.thumb.message_received("Metadata and signal files mismatch",f"The following signals files were not found in the selected metadata file:\n\n{os.linesep.join([os.path.basename(thumb) for thumb in baddies])}\n\n")
            return False

        return True

    def get_bp_reqs(self):
        """
        Ensure that the user has provided metadata, basic BASSPRO settings, and either automated or manual BASSPRO settings before launching BASSPRO.

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
        reply = QMessageBox.Ok
        cancelling = False
        while not self.metadata or not (self.autosections or self.mansections) or not self.basicap:
            # TODO: move these loops inside the load function?
            while not self.metadata:
                reply = QMessageBox.information(self, 'Missing metadata', 'Please select a metadata file.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    self.load_metadata()
                elif reply == QMessageBox.Cancel:
                    cancelling = True
                    break

            if cancelling:
                break

            while not (self.autosections or self.mansections):
                reply = QMessageBox.information(self, 'Missing BASSPRO automated/manual settings', 'Please select BASSPRO automated or manual settings files.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    self.get_autosections()
                elif reply == QMessageBox.Cancel:
                    cancelling = True
                    break

            if cancelling:
                break

            while not self.basicap:
                reply = QMessageBox.information(self, 'Missing BASSPRO basic settings', 'Please select BASSPRO basic settings files.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    self.get_autosections()
                elif reply == QMessageBox.Cancel:
                    cancelling = True
                    break

            if cancelling:
                break


        return self.metadata and (self.autosections or self.mansections) and self.basicap

    def new_variable_config(self):
        """
        Run self.get_bp_reqs() and self.test_configuration() to ensure that BASSPRO has the required input, run self.variable_configuration() to populate Config.variable_table (TableWidget), and show the STAGG settings subGUI.

        Parameters
        --------
        Config.variable_table: QTableWidget
            This TableWidget is defined in the Config class, displayed in the STAGG settings subGUI, and populated with rows based on the list of variables (self.breath_df).
        
        Outputs
        --------
        self.n: int
            This integer is incremented when variables are given duplicate names and appended to the existing variable's name so that the edited variable retains the user's edits.
        Config.variable_table: QTableWidget
            cellChanged signals are assigned to the TableWidgets cells for two slots: Config.no_duplicates() and Config.update_loop().
        
        Outcomes
        --------
        self.get_bp_reqs()
            This method ensures that the user has provided metadata, basic BASSPRO settings, and either automated or manual BASSPRO settings before launching BASSPRO.
        self.test_configuration()
            This method ensures that the file paths that populate the attributes required to show the STAGG settings subGUI exist and their contents are accessible, and provides feedback to the user on what is missing if anything.
        self.variable_configuration()
            This method populates self.buttonDict_variable with widgets and text and populates Config.variable_table with the contents of self.buttonDict_variable.
        Config.no_duplicates()
            This method automatically renames the variable in the "Alias" column of Config.variable_table (TableWidget) to avoid duplicate variable names.
        Config.update_loop()
            This method updates the contents of Config.clades_other_dict with the contents of self.loop_menu and then update the contents of Config.loop_table with the newly updated contents of Config.clades_other_dict.
        Config.show()
            This method displays the STAGG settings subGUI.
        """
        self.get_bp_reqs()
        self.test_configuration()
        try:
            self.variable_configuration()
            self.n = 0
            self.stagg_settings_window.variable_table.cellChanged.connect(self.stagg_settings_window.no_duplicates)
            self.stagg_settings_window.variable_table.cellChanged.connect(self.stagg_settings_window.update_loop)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
        try:
            self.stagg_settings_window.show()
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc()) 
        
    def stagg_settings_config(self):
        # Shouldn't I be using self.get_bp_reqs() in here?
        """
        Ensure that there is a source of variables to populate Config.variable_table with and run test_configuration() to ensure that those sources are viable, run self.variable_configuration() to populate Config.variable_table (TableWidget), and either show the STAGG settings subGUI or show a Thorbass dialog to guide the user through providing the required input if there is no input.

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
        self.n: int
            This integer is incremented when variables are given duplicate names and appended to the existing variable's name so that the edited variable retains the user's edits.
        Config.variable_table: QTableWidget
            cellChanged signals are assigned to the TableWidgets cells for two slots: Config.no_duplicates() and Config.update_loop().]

        Outcomes
        --------
        self.test_configuration()
            This method ensures that the file paths that populate the attributes required to show the STAGG settings subGUI exist and their contents are accessible, and provides feedback to the user on what is missing if anything.
        Config.check_load_variable_config()
            This method checks the user-selected STAGG settings files to ensure they exist and they are the correct file format and they begin with either "variable_config", "graph_config", or "other_config", triggering a MessageBox or dialog to inform the user if any do not and loading the file as a dataframe if they do.
        self.variable_configuration()
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
            Run self.get_bp_reqs() and self.test_configuration() to ensure that BASSPRO has the required input, run self.variable_configuration() to populate Config.variable_table (TableWidget), and show the STAGG settings subGUI.
        self.get_variable_config()
            Call Config.check_load_variable_config("yes").
        """
        # Ensure that there is a source of variables to populate Config.variable_table with
        if self.buttonDict_variable == {}:
            if self.stagg_settings_window.configs["variable_config"]["path"] != "":
                self.stagg_settings_window.check_load_variable_config("no")

                # show the STAGG settings subGUI
                self.stagg_settings_window.show()
            elif self.stagg_input_files != [] and any(a.endswith(".json") for a in self.stagg_input_files):
                    if self.metadata and (self.autosections or self.mansections):
                        self.thinb = Thinbass(self)
                        self.thinb.show()
                    else:
                        # run test_configuration() to ensure that those sources are viable
                        self.test_configuration()

                        # run self.variable_configuration() to populate Config.variable_table (TableWidget)
                        self.variable_configuration()
                        self.n = 0
                        self.stagg_settings_window.variable_table.cellChanged.connect(self.stagg_settings_window.no_duplicates)
                        self.stagg_settings_window.variable_table.cellChanged.connect(self.stagg_settings_window.update_loop)

                        # show the STAGG settings subGUI
                        self.stagg_settings_window.show()
            elif self.metadata and (self.autosections or self.mansections):
                # run test_configuration() to ensure that those sources are viable
                self.test_configuration()

                # run self.variable_configuration() to populate Config.variable_table (TableWidget)
                self.variable_configuration()
                self.n = 0
                self.stagg_settings_window.variable_table.cellChanged.connect(self.stagg_settings_window.no_duplicates)
                self.stagg_settings_window.variable_table.cellChanged.connect(self.stagg_settings_window.update_loop)

                # show the STAGG settings subGUI
                self.stagg_settings_window.show()

            # Guide the user through providing the required input if there is no input.
            else:
                self.thorb = Thorbass(self)
                self.thorb.show()
                self.thorb.message_received('Missing source files', f"One or more of the files used to build the variable list has not been selected.\nWould you like to open an existing set of variable configuration files or create a new one?",self.new_variable_config,self.get_variable_config)
        else:
            self.stagg_settings_window.show()
            
    def update_breath_df(self,updated_file):
        """
        Ask the user if they want to update the self.breath_df list to include the latest updates to the metadata and/or the automated or manual BASSPRO settings and if so, reset and repopulate the STAGG settings subGUI widgets, namely Config.variable_table.

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
        self.breathcaller_path: str
            The path to the BASSPRO module script.
        self.buttonDict_variable: dict
            This attribute is either an empty dictionary or a nested dictionary used to populate and save the text and RadioButton states of Config.variable_table (TableWidget) in the Config subGUI.
        Config.vdf: dict
            This Config attribute is either an empty dictionary or a nested dictionary populated with only those settings from variable_config file that are not null or 0.
        Config.variable_table: QTableWidget
            This TableWidget is defined in the Config class, displayed in the STAGG settings subGUI, and populated with rows based on the list of variables (self.breath_df).
        
        Outputs
        --------
        self.old_bdf: list
            This attribute is a copy of self.breath_df before it is emptied.
        self.breath_df: list
            This attribute is emptied, repopulated with variables from the BASSPRO module script, the metadata, and the BASSPRO settings, and compared to self.old_bdf.
        reply: QMessageBox
            If there is a difference between self.old_bdf and self.breath_df, then this MessageBox asks the user if they would like to update the list of variables presented in the STAGG settings subGUI and warned that unsaved changes may be lost.
        self.missing_meta: list
            This attribute is a list of file paths for files that could not be accessed.
        self.buttonDict_variable: dict
            The relevant items of this nested dictionary are updated based on corresponding values in Config.vdf (dict).
        self.n: int
            This integer is incremented when variables are given duplicate names and appended to the existing variable's name so that the edited variable retains the user's edits.
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
        self.old_bdf = self.breath_df
        self.breath_df = []
        missing_meta = []
        for p in [self.metadata, self.autosections, self.mansections]:
            if not self.try_open(p):
                missing_meta.append(p)

        try:
            with open(self.breathcaller_path) as bc:
                soup = bs(bc, 'html.parser')
            for child in soup.breathcaller_outputs.stripped_strings:
                self.breath_df.append(child)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print(traceback.format_exc())
            missing_meta.append(self.breathcaller_path)

        if set(self.breath_df) != set(self.old_bdf):
            non_match_old = set(self.old_bdf) - set(self.breath_df)
            non_match_new = set(self.breath_df) - set(self.old_bdf)
            non_match = list(non_match_old) + list(non_match_new)
            if len(non_match)>0:
                reply = QMessageBox.question(self, f'New {updated_file} selected', 'Would you like to update the variable list in STAGG configuration settings?\n\nUnsaved changes may be lost.\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.stagg_settings_window.setup_table_config()
                    try:
                        for a in self.stagg_settings_window.vdf:
                            self.buttonDict_variable[a]['Alias'].setText(self.stagg_settings_window.vdf[a]['Alias'])
                            for k in ["Independent","Dependent","Covariate"]:
                                if self.stagg_settings_window.vdf[a][k] == '1':
                                    try:
                                        self.buttonDict_variable[a][k].setChecked(True)
                                    except:
                                        pass
                        self.n = 0
                        self.variable_table.cellChanged.connect(self.no_duplicates)
                        self.variable_table.cellChanged.connect(self.update_loop)
                        self.stagg_settings_window.load_custom_config()
                        self.stagg_settings_window.load_graph_config()
                    except Exception as e:
                        print(f'{type(e).__name__}: {e}')
                        print(traceback.format_exc())
                        pass
                else:
                    self.breath_df = self.old_bdf

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

    def test_configuration(self):
        """
        Ensure that the file paths that populate the attributes required to show the STAGG settings subGUI exist and their contents are accessible, and provide feedback to the user on what is missing if anything.

        Parameters
        --------
        self.missing_meta: list
            This attribute is either an empty list or a list of file paths for files that could not be accessed.
        self.metadata: str
            This attribute refers to the file path of the metadata file.
        self.autosections: str
            This attribute refers to the file path of the automated BASSPRO settings file.
        self.mansections: str
            This attribute refers to the file path of the manual BASSPRO settings file.
        self.breathcaller_path: str
            The path to the BASSPRO module script.
        self.breath_df: list
            This attribute is either an empty list or populated with a list of variables derived from the metadata, BASSPRO settings, or STAGG settings.
        self.missing_meta: list
            This attribute is either an empty list or a list of file paths for files that could not be accessed.
        self.metadata_list: QListWidget
            This QListWidget inherited from the Ui_Plethysmography class displays the file path of the selected metadata file on the main GUI.
        
        Outputs
        --------
        self.missing_meta: list
            This attribute is emptied and repopulated with file paths for files that could not be accessed.
        self.breath_df: list
            This attribute is repopulated with variables from the BASSPRO module script, the metadata, and the BASSPRO settings.
        reply: QMessageBox
            If there are any file paths in self.missing_meta, then this MessageBox informs the user that one or more of the sources for building the variable list required to open the STAGG settings subGUI was not found, and prompts the user to select the needed files.
        
        Outcomes
        --------
        self.try_open(path)
            This method ensures that the file passed and its contents are accessible.
        self.get_metadata()
            This method prompts the user to select a previously made metadata file via FileDialog.
        self.get_autosections()
            This method prompts the user to select a previously made automated or manual or basic BASSPRO settings file via FileDialog.
        """

        # Ensure that the file paths that populate the attributes required to show the 
        #   STAGG settings subGUI exist and their contents are accessible
        missing_meta = []
        for p in [self.metadata, self.autosections, self.mansections]:
            if p and not self.try_open(p):
                missing_meta.append(p)

        try:
            with open(self.breathcaller_path) as bc:
                soup = bs(bc, 'html.parser')
            for child in soup.breathcaller_outputs.stripped_strings:
                self.breath_df.append(child)
        except Exception as e:
            missing_meta.append(self.breathcaller_path)

        #  provide feedback to the user on what is missing if anything.
        if len(missing_meta) > 0:
            reply = QMessageBox.information(self, 'Missing source files', f"One or more of the files used to build the variable list was not found:\n{os.linesep.join([m for m in missing_meta])}\nWould you like to select a different file?", QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                for m in missing_meta:
                    # wut? Why would m ever by self.workspace_dir?? I'm changing it to self.metadata.
                    if m == self.metadata:
                        reply = QMessageBox.information(self, 'Missing metadata', 'Please select a metadata file.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                        if reply == QMessageBox.Ok:
                            self.load_metadata()
                        if reply == QMessageBox.Cancel:
                            self.metadata_list.clear()
                    if m == self.autosections or m == self.mansections:
                        reply = QMessageBox.information(self, 'Missing BASSPRO settings', 'Please select BASSPRO settings files.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                        if reply == QMessageBox.Ok:
                            self.get_autosections()
                    if m == self.breathcaller_path:
                        reply = QMessageBox.information(self, "How is this program even running?", f"The program cannot find the following file: \n{self.breathcaller_path}\nPlease reinstall BASSPRO-STAGG.", QMessageBox.Ok)

    def variable_configuration(self):
        """
        Assign delegates to Config.variable_table and Config.loop_table, populate self.buttonDict_variable with widgets and text based on items listed in self.breath_df (list), assign the RadioButton widgets of each row to a ButtonGroup, populate Config.variable_table (TableWidget) with the contents of self.buttonDict_variable, assign toggled signals slotted for Config.cadd_combos() to the RadioButtons in self.buttonDict_variable that correspond to those in the "Independent" and "Covariate" columns of the TableWidget, adjust the size of the cells of Config.variable_table, set self.loop_menu as an empty dictionary, and call self.show_loops().

        Parameters
        --------
        AlignDelegate: class
            This class assigns delegates to Config.variable_table and Config.loop_table TableWidgets and and centers the delegate items.
        Config.variable_table: QTableWidget
            This TableWidget is defined in the Config class, displayed in the STAGG settings subGUI, and populated with rows based on the list of variables (self.breath_df).
        Config.loop_table: QTableWidget
            This Config class TableWidget is populated with the settings for additional models either via widgets or loading previously made other_config.csv with previous STAGG run's settings for additional models.
        self.breath_df: list
            This attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        self.buttonDict_variable: dict
            This attribute is a nested dictionary used to populate and save the text and RadioButton states of Config.variable_table (TableWidget) in the Config subGUI.
        
        Outputs
        --------
        Config.variable_table: QTableWidget
            This TableWidget is populated with text and widgets stored in self.buttonDict_variable (dict) and assigned toggled signals slotted for Config.add_combos().
        Config.loop_table: QTableWidget
            This TableWidget is passed as an argument to self.show_loops().
        self.buttonDict_variable: dict
            This attribute is populated with text and widgets based on items in the list self.breath_df.
        self.loop_menu: dict
            This attribute is set as an empty dictionary.
        
        Outcomes
        --------
        self.show_loops()
            The method iteratively populates self.loop_menu with QLineEdits, QComboBoxes, and CheckableComboBox, populates the ComboBoxes with items from self.breath_df, populates Config.loop_table with the contents of self.loop_menu, and adjusts the cell sizes of Config.loop_table.
        """
        print("self.variable_configuration() has started")

        # I've forgotten what this was specifically about, but I remember it had something to do with spacing or centering text or something.
        delegate = AlignDelegate(self.stagg_settings_window.variable_table)
        delegate_loop = AlignDelegate(self.stagg_settings_window.loop_table)
        self.stagg_settings_window.variable_table.setItemDelegate(delegate)
        self.stagg_settings_window.loop_table.setItemDelegate(delegate_loop)

        # Setting the number of rows in each table upon opening the window:
        self.stagg_settings_window.variable_table.setRowCount(len(self.breath_df))
        self.stagg_settings_window.loop_table.setRowCount(1)
        
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
            self.stagg_settings_window.variable_table.setItem(row,0,self.buttonDict_variable[item]["orig"])
            self.stagg_settings_window.variable_table.setItem(row,1,self.buttonDict_variable[item]["Alias"])

            self.stagg_settings_window.variable_table.setCellWidget(row,2,self.buttonDict_variable[item]["Independent"])
            self.stagg_settings_window.variable_table.setCellWidget(row,3,self.buttonDict_variable[item]["Dependent"])
            self.stagg_settings_window.variable_table.setCellWidget(row,4,self.buttonDict_variable[item]["Covariate"])
            self.stagg_settings_window.variable_table.setCellWidget(row,5,self.buttonDict_variable[item]["Ignore"])

            row += 1

        self.stagg_settings_window.n = 0
        for item_1 in self.breath_df:
            self.buttonDict_variable[item_1]["Independent"].toggled.connect(self.stagg_settings_window.add_combos)
            self.buttonDict_variable[item_1]["Covariate"].toggled.connect(self.stagg_settings_window.add_combos)
        self.stagg_settings_window.variable_table.resizeColumnsToContents()
        self.stagg_settings_window.variable_table.resizeRowsToContents()
        self.loop_menu = {}
        self.show_loops(self.stagg_settings_window.loop_table,1)
        print("self.variable_configuration() has finished")

    def show_loops(self,table,r):
        # This method is almost redundant. Config.show_loops() is almost the same, but populates comboBoxes based on a list of Aliases scraped from the tableWidget Config.variable_table instead of the list of Aliases derived from self.breath_df, which is in turn derived from either the dataframe from Main.variable_config.to_csv() or Main.input_dir_r[0].to_dict() (JSON file) or the compilation of variables from Main.metadata, Main.autosections or Main.mansections, and Main.basic. Config.show_loops() also establishes an empty Main.loop_menu within Config.show_loops instead of before it's called.
        """
        Iteratively populate self.loop_menu with QLineEdits, QComboBoxes, and CheckableComboBox, populate the ComboBoxes with items from self.breath_df, populate Config.loop_table with the contents of self.loop_menu, and adjust the cell sizes of Config.loop_table.

         
        Parameters
        --------
        self.loop_menu: dict
            This attribute is a nested dictionary used to populate and save the text, CheckBox, ComboBox, and CheckableComboBox states of Config.loop_table (TableWidget) in the Config subGUI.
        self.breath_df: list
            This attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        table: QTableWidget
            This argument refers to self.loop_table TableWidget - previously there was another loop table, so that's why we have the "table" argument instead of just used the attribute to refer to the widget.
        r: int
            This argument passes the number of rows self.loop_table should have.
        
        Outputs
        --------
        self.loop_menu: dict
            This attribute is set as an empty dictionary and repopulated with widgets with a row count of "r". 
        Config.loop_table: QTableWidget
            This Config class TableWidget is populated with the contents of self.loop_menu.
        """
        print("pleth.show_loops()")
        for row in range(r):
            self.loop_menu.update({table:{row:{}}})
            # Creating the widgets within the above dictionary that will populate the cells of each row:
            self.loop_menu[table][row]["Graph"] = QLineEdit()
            self.loop_menu[table][row]["Y axis minimum"] = QLineEdit()
            self.loop_menu[table][row]["Y axis maximum"] = QLineEdit()
            for role in self.stagg_settings_window.role_list[1:6]:
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
        self.auto_get_output_dir_r()
            Check whether or not a STAGG_output directory exists in the user-selected directory and make it if it does not exist, and make a timestamped STAGG output folder for the current session's next run of STAGG.
        self.auto_get_basic()
            Detect a basic BASSPRO settings file, set self.basicap as its file path, and populate self.sections_list with the file path for display to the user.
        self.update_breath_df()
            This method updates self.breath_df to reflect any changes to the variable list used to populate Config.variable_table if the user chooses to replace previously selected input with input detected in the selected output directory.
        """
        if self.workspace_dir:
            selection_dir = str(Path(self.workspace_dir).parent.absolute())
        else:
            selection_dir = None

        output_dir = QFileDialog.getExistingDirectory(self, 'Choose output directory', selection_dir, QFileDialog.ShowDirsOnly)
        if os.path.exists(output_dir):

            # Set output dir
            self.output_path_display.setText(output_dir)
            
            if self.dir_contains_valid_import_files(output_dir):

                # If any data exists already
                if self.breath_df or self.metadata or self.autosections or self.basicap or self.mansections:

                    reply = QMessageBox.question(self, f'Input detected', 'The selected directory has recognizable input.\n\nWould you like to overwrite your current input selection?\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    if reply == QMessageBox.Yes:
                        self.auto_get_autosections()
                        self.auto_get_mansections()
                        self.auto_load_metadata()
                        self.auto_get_output_dir_r()
                        self.auto_get_basic()
                    
                # If we have no data yet
                else:
                    self.auto_get_autosections()
                    self.auto_get_mansections()
                    self.auto_load_metadata()
                    self.auto_get_output_dir_r()
                    self.auto_get_basic()
                    if len(self.breath_df)>0:
                        self.update_breath_df("settings")
        
    def create_basspro_output_folder(self):
        """
        Check whether or not a BASSPRO_output directory exists in the user-selected directory and make it if it does not exist, and make a timestamped BASSPRO output folder for the current session's next run of BASSPRO.

        Parameters
        --------
        
        Outputs
        --------
        self.basspro_output_dir: str
            This attribute is set as a file path to the BASSPRO_output directory in the user-selected directory output_dir and the directory itself is spawned if it does not exist.
        self.output_dir_py: str
            This attribute is set as a file path to the timestamped BASSPRO_output_{time} folder within the BASSPRO_output directory within the user-selected directory output_dir. It is not spawned until self.dir_checker() is called when BASSPRO is launched.

        Returns
        --------
        output_dir_py: str
            Newly created output dir
        """
        basspro_output_dir = os.path.join(self.workspace_dir, 'BASSPRO_output')

        if not Path(basspro_output_dir).exists():
            Path(basspro_output_dir).mkdir()

        curr_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir_py = os.path.join(basspro_output_dir, 'BASSPRO_output_' + curr_timestamp)
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
        if Path(metadata_path).exists():

            # TODO: put this check where it needs to go
            if not self.check_metadata_file(metadata_path):
                return

            # We assign the path detected via output_dir to the Plethysmography class attribute that will be an argument for the breathcaller command line.
            for item in self.metadata_list.findItems("metadata",Qt.MatchContains):
                # and we remove them from the widget.
                self.metadata_list.takeItem(self.metadata_list.row(item))

            self.metadata = metadata_path
            self.metadata_list.addItem(self.metadata)
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
        print("auto_get_basic()")
        basic_path=os.path.join(self.workspace_dir, 'basics.csv')
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
        mansections_path=os.path.join(self.workspace_dir, 'manual_sections.csv')
        if Path(mansections_path).exists():
            for item in self.sections_list.findItems("man",Qt.MatchContains):
                # and we remove them from the widget.
                self.sections_list.takeItem(self.sections_list.row(item))
            if self.mansections == "":
            # We assign the path detected via output_dir to the Plethysmography class attribute that will be an argument for the breathcaller command line.
                self.mansections=mansections_path
                self.sections_list.addItem(self.mansections)
            else:
                self.mansections=mansections_path
                self.sections_list.addItem(self.mansections)
        else:
            print("Manual sections parameters file not detected.")

    def get_variable_config(self):
        """
        Call Config.check_load_variable_config("yes").

        Outcomes
        --------
        Config.check_load_variable_config()
            This method checks the user-selected files to ensure they exist and they are the correct file format and they begin with either "variable_config", "graph_config", or "other_config", triggering a MessageBox or dialog to inform the user if any do not and loading the file as a dataframe if they do.
        """
        print("self.get_variable_config()")
        self.stagg_settings_window.check_load_variable_config("yes")

    def auto_get_breath_files(self, basspro_output_dir):
        """
        Populate self.stagg_input_files with the file paths of the JSON files held in the directory of the most recent BASSPRO run within the same session (the directory file path stored in self.output_dir_py) and populate self.breath_list (ListWidget) with the file paths of those JSON files.

        Parameters
        --------
        self.output_dir_py: str
            This attribute is set as a file path to the timestamped BASSPRO_output_{time} folder within the BASSPRO_output directory within the user-selected directory self.workspace_dir. It is not spawned until self.dir_checker() is called when BASSPRO is launched.
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
        if self.stagg_input_files != []:
            reply = QMessageBox.information(self, 'Clear STAGG input list?', 'Would you like to keep the previously selected STAGG input files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                self.breath_list.clear()

        stagg_input_files = [os.path.join(basspro_output_dir, file) for file in os.listdir(basspro_output_dir) if file.endswith(".json")==True]
        for x in stagg_input_files:
            self.breath_list.addItem(x)
           
    def auto_get_output_dir_r(self):
        """
        Check whether or not a STAGG_output directory exists in the user-selected directory and make it if it does not exist, and make a timestamped STAGG output folder for the current session's next run of STAGG.

        Parameters
        --------
        self.workspace_dir: str
            This attribute is set as the file path to the user-selected output directory.
        
        Outputs
        --------
        self.r_output_folder: str
            This attribute is set as a file path to the STAGG_output directory in the user-selected directory self.workspace_dir and the directory itself is spawned if it does not exist.
        self.output_dir_r: str
            This attribute is set as a file path to the timestamped STAGG_output_{time} folder within the STAGG_output directory within the user-selected directory self.workspace_dir. It is not spawned until self.dir_checker() is called when STAGG is launched.
        """
        print("auto_get_output_dir_r()")
        self.r_output_folder=os.path.join(self.workspace_dir,'STAGG_output')
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
        filenames, filter = QFileDialog.getOpenFileNames(self, 'Select signal files')

        # len(filenames) == 0 when dialog is cancelled
        if filenames:

            # Overwrite existing files?
            if self.signal_files_list.count() > 0:
                reply = QMessageBox.information(self, 'Clear signal files list?', 'Would you like to keep the previously selected signal files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    self.signal_files_list.clear()

            self.hangar.append("Signal files selected.")

            # Pull out anything that's not a text file
            bad_file_formats = []
            for file in filenames:
                if file.endswith(".txt"):
                    self.signal_files_list.addItem(file)
                else:
                    bad_file_formats.append(file)

            if bad_file_formats:
                notify_error(f"One or more of the files selected are not text formatted:\n\n{os.linesep.join([os.path.basename(thumb) for thumb in bad_file_formats])}\n\nThey will not be included.")

            if self.metadata_list.count():
                self.check_metadata_file(self.metadata_file)

    def load_metadata(self):
        # There are no checks for quality of file selected in this method. Are they somewhere else?
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
        # Keep selecting metadata until good data or cancel
        while True:
            # TODO: are we picking one file or multiple? -- may apply to multiple spots
            filename, filter = QFileDialog.getOpenFileName(self, 'Select metadata file', self.workspace_dir)

            # if files were selected (not cancelled)
            if filename:

                # check files and return only valid ones

                # If there are valid files, keep going
                if self.check_metadata_file(filename):
                    break
            
            # User cancelled
            else:
                return

        self.metadata_list.clear()
        self.metadata_list.addItem(filename)
        
        if len(self.breath_df) > 0:
            self.update_breath_df("metadata")


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
        self.dir_checker()
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
            self.dir_checker()
            self.metadata_list.clear()
            if os.path.exists(self.workspace_dir):
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
        if not filenames:
            if not self.autosections and not self.basicap and not self.mansections:
                print("No BASSPRO settings files selected.")
        else:
            new_files_added = False
            for file in filenames:
                if file.endswith('.csv'):
                    if os.path.basename(file).startswith("auto_sections") | os.path.basename(file).startswith("autosections"):
                        self.autosections = file
                        new_files_added = True

                    elif os.path.basename(file).startswith("manual_sections"):
                        new_files_added = True
                        for item in self.sections_list.findItems("manual_sections",Qt.MatchContains):
                            self.sections_list.takeItem(self.sections_list.row(item))
                        self.sections_list.addItem(file)

                    elif os.path.basename(file).startswith("basics"):
                        new_files_added = True
                        self.basicap = file

                    # If we added files
                    if new_files_added:
                        if len(self.breath_df)>0:
                            self.update_breath_df("settings")
                else:
                    self.thumb = Thumbass(self)
                    self.thumb.show()
                    self.thumb.message_received("Incorrect file format","The settings files for BASSPRO must be in csv format. \nPlease convert your settings files or choose another file.")

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
        cancelled = False
        # Keep trying to select good files until user cancels
        while not cancelled:
            filenames, filter = QFileDialog.getOpenFileNames(self, 'Choose STAGG input files from BASSPRO output', self.workspace_dir)

            # No files chosen, cancelled dialog
            if not filenames:
                break

            # If all files are right type
            if all(file.endswith(".json") or file.endswith(".RData") for file in filenames):
                # if we already have a selection, check about overwrite
                if self.breath_list.count():
                    reply = QMessageBox.information(self, 'Clear STAGG input list?', 'Would you like to keep the previously selected STAGG input files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply == QMessageBox.No:
                        self.breath_list.clear()
                for x in filenames:
                    self.breath_list.addItem(x)

            # If any of the files are right type
            elif any(file_1.endswith(".json") or file_1.endswith(".RData") for file_1 in filenames):
                baddies = []
                good_files = []
                
                # Choose only the good files
                for file_2 in filenames:
                    if file_2.endswith(".json") or file_2.endswith(".RData"):
                        good_files.append(file_2)
                    else:
                        baddies.append(file_2)

                # Add files to widget
                for x in good_files:
                    self.breath_list.addItem(x)

                # Notify user of files not included
                if len(baddies) > 0:
                    self.thumb = Thumbass(self)
                    self.thumb.show()
                    self.thumb.message_received("Incorrect file format",f"One or more of the files selected are neither JSON nor RData files:\n\n{os.linesep.join([os.path.basename(thumb) for thumb in baddies])}\n\nThey will not be included.")        

            # If none of the files are right type
            else:
                reply = QMessageBox.information(self, 'Incorrect file format', 'The selected file(s) are not formatted correctly.\nWould you like to select different files?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.No:
                    cancelled = True
    
    def full_run(self):
        """
        Ensure the user has selected an output directory and prompt them to do so if they haven't, check that the required input for BASSPRO has been selected, launch BASSPRO, detect the JSON files produced after BASSPRO has finished and populate self.stagg_input_files with the file paths to those JSON files.

        Outcomes
        --------
        self.dir_checker()
            This method ensures that the user has selected an output directory and prompts them to do so if they have not.
        self.get_bp_reqs()
            This method ensures that the user has provided metadata, basic BASSPRO settings, and either automated or manual BASSPRO settings before launching BASSPRO.
        self.launch_basspro()
            This method copies the required BASSPRO input other than the signal files and the breathcaller_config.json file to the timestamped BASSPRO output folder (self.output_dir_py) and runs self.launch_worker().
        self.auto_get_breath_files()
            Populate self.stagg_input_files with the file paths of the JSON files held in the directory of the most recent BASSPRO run within the same session (the directory file path stored in self.output_dir_py) and populate self.breath_list (ListWidget) with the file paths of those JSON files.
        self.output_check()
            This method compares the input and output of BASSPRO and reports the names of the signal files that did not pass BASSPRO and failed to produce JSON files to the hangar for display on the main GUI.
        """

        # Make sure we have an output dir
        if not self.dir_checker():
            notify_error("Need output folder")
            return

        
        # check that the required input for BASSPRO has been selected
        if not self.get_bp_reqs():
            notify_error("Need settings files")
            return

        # launch BASSPRO
        self.status_message("Launching BASSPRO")
        basspro_output_folder = self.launch_basspro()

        ## RUN STAGG ##
        self.status_message("Autopopulating STAGG")
        self.autopopulate_stagg_after_basspro(basspro_output_folder)

        # TODO: auto start of STAGG
        #self.status_message("Launching STAGG")
        #self.launch_stagg()

    def status_message(self, msg):
        self.hangar.append(msg)

    def autopopulate_stagg_after_basspro(self, basspro_output_folder):
        # detect the JSON files produced after BASSPRO has finished
        self.auto_get_breath_files(basspro_output_folder)

        # populate stagg_input_files with the file paths to those JSON files.
        self.output_check()

    def stagg_run(self):
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
        # Assign the file paths to the attributes
        self.variable_config = self.stagg_settings_window.configs["variable_config"]["path"]
        self.graph_config = self.stagg_settings_window.configs["graph_config"]["path"]
        self.other_config = self.stagg_settings_window.configs["other_config"]["path"]

        # ensure that all required STAGG input has been selected
        if any([self.stagg_settings_window.configs[key]['path'] == "" for key in self.stagg_settings_window.configs]):
            if self.stagg_input_files == []:
                notify_error("No STAGG input files")
            else:
                # and prompt the user to select whatever is missing
                QMessageBox.question(self, 'Missing STAGG settings', f"One or more STAGG settings files are missing.", QMessageBox.Ok, QMessageBox.Ok)
        else:
            # launch stagg
            self.rthing_to_do()

    def dir_checker(self, a=None, b=None, text=None):
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

        ''' Folder Structure
        - Input files
            - input_<datetime>
                -file1.csv
                -file2.csv
                -signal_files
                    signal1.txt
                    signal2.txt
        - Output files
            - my_run_<datetime>
                - basspro_output
                    - json
                    - summary files
                - stagg_output
        '''

        if a or b or text:
            raise NotImplementedError(f"Need to implement dir checker for {text}")

        '''
        # If no output dir or invalid output dir
        if self.workspace_dir == "" or not os.path.exists(self.workspace_dir):
            # open a dialog that prompts the user to choose the directory:
            self.select_output_dir()
        '''

        # If no output dir or invalid output dir
        while self.workspace_dir == "" or not os.path.exists(self.workspace_dir):
            # open a dialog that prompts the user to choose the directory:
            reply = QMessageBox.information(self, 'No Output Folder', 'Please select an output folder.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.select_output_dir()
            elif reply == QMessageBox.Cancel:
                return False

        # TODO: what other folders do we need to check?

        # Checking to see if we have anything other than just configs in the directory
        '''
        if any(Path(self.output_folder).iterdir()) == True:
            if all("config" in file for file in os.listdir(self.output_folder)):
                print("just configs")
            else:
                reply = QMessageBox.question(self, f'Confirm {text} output directory', 'The current output directory has files in it that may be overwritten.\n\nWould you like to create a new output folder?\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    output_folder_parent = os.path.dirname(output_folder)
                    self.output_folder = os.path.join(output_folder_parent, f'{text}_output_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
                    os.makedirs(self.output_folder)
        '''
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
        
        # TODO: simplify/combine these copy operations
        #for file in [self.autosections, self.mansections, self.basicap]

        # Create new folder for run
        basspro_output_folder = self.create_basspro_output_folder()

        # Copying over metadata file
        new_filename = os.path.join(basspro_output_folder, f"metadata_{os.path.basename(basspro_output_folder).lstrip('py_output')}.csv")
        shutil.copyfile(self.metadata, new_filename)

        # Copying over breathcaller config file
        new_filename = os.path.join(basspro_output_folder, f"breathcaller_config_{os.path.basename(basspro_output_folder).lstrip('py_output')}.txt")
        shutil.copyfile(f'{Path(__file__).parent}/breathcaller_config.json', new_filename)

        # Copy over autosections file
        if self.autosections:
            new_filename = os.path.join(basspro_output_folder, f"auto_sections_{os.path.basename(basspro_output_folder).lstrip('BASSPRO_output')}.csv")
            shutil.copyfile(self.autosections, new_filename)
    
        # Copy over mansections file
        if self.mansections:
            new_filename = os.path.join(basspro_output_folder, f"manual_sections_{os.path.basename(basspro_output_folder).lstrip('BASSPRO_output')}.csv")
            shutil.copyfile(self.mansections, new_filename)

        # Copy over basic settings file
        if self.basicap:
            new_filename = os.path.join(basspro_output_folder, f"basics_{os.path.basename(basspro_output_folder).lstrip('py_output')}.csv")
            shutil.copyfile(self.basicap, new_filename)

        # Write json config to gui_config location
        with open(f'{Path(__file__).parent}/gui_config.json','w') as gconfig_file:
            json.dump(self.gui_config,gconfig_file)

        # Copy over config file
        new_filename = os.path.join(basspro_output_folder, f"gui_config_{os.path.basename(basspro_output_folder).lstrip('BASSPRO_output')}.txt")
        shutil.copyfile(f'{Path(__file__).parent}/gui_config.json', new_filename)
        
        print('launch_basspro thread id',threading.get_ident())
        print("launch_basspro process id",os.getpid())

        # Start the BASSPRO module
        self.launch_worker("basspro", basspro_output_folder)

        # TODO: isn't this already happening in full_run() ??
        # Check the BASSPRO output to see which signal files successfully produced JSON files
        self.output_check()

        return basspro_output_folder
    
    def launch_worker(self, task, output_dir):
        """
        Run parallel processes capped at the number of CPU's selected by the user to devote to BASSPRO or STAGG.
        """
        print('launch_worker thread id',threading.get_ident())
        print("launch_worker process id",os.getpid())
        if task == "basspro":
            for job in MainGUIworker.get_jobs_py(signal_files=self.signal_files,
                                                 module=self.breathcaller_path,
                                                 output=output_dir,
                                                 metadata=self.metadata,
                                                 manual=self.mansections,
                                                 auto=self.autosections,
                                                 basic=self.basicap):
                # create a Worker
                self.workers[self.counter] = MainGUIworker.Worker(
                    job,
                    self.counter,
                    self.q,
                    self
                    )

                self.workers[self.counter].progress.connect(self.B_run)
                self.workers[self.counter].finished.connect(self.B_Done)

                # TODO: remove invalid inputs -- add label to combobox instead of putting description as option
                # adjust thread limit for the qthreadpool
                try:
                    # Try to convert combo box text
                    thread_limit_combo_selection = self.parallel_combo.currentText()
                    thread_limit = int(thread_limit_combo_selection)
                except ValueError:
                    thread_limit = 1

                self.qthreadpool.setMaxThreadCount(thread_limit)

                # Add the 'QRunnable' worker to the threadpool which will manage how
                # many are started at a time
                self.qthreadpool.start(self.workers[self.counter])

                # advance the counter - used to test launching multiple threads
                self.counter+=1

        elif task == "r":
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
        if len(self.stagg_input_files) != len(self.signal_files):
            goodies = []
            baddies = []
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
            self.hangar.append(f"\nThe following signals files did not pass BASSPRO:\n\n{', '.join([os.path.basename(thumb) for thumb in baddies])}\n")

    def rthing_to_do(self):
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
            This attribute is set as a file path to the timestamped STAGG_output_{time} folder within the STAGG_output directory within the user-selected directory self.workspace_dir. It is not spawned until self.dir_checker() is called when STAGG is launched.
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
            if any(os.path.basename(b).endswith("RData") for b in self.stagg_input_files):
                self.pipeline_des = os.path.join(self.papr_dir, "Pipeline_env_multi.R")
            else:
                self.pipeline_des = os.path.join(self.papr_dir, "Pipeline.R")
            if len(self.stagg_input_files)>200:
                # If there are more than 200 files in Main.stagg_input_files, STAGG has troubles importing all of them when provided as a list of file paths, so in these cases, we would want args$JSON to be a directory path instead:
                if len(set([os.path.dirname(y) for y in self.stagg_input_files]))>1:
                    # If there are more than 200 files in Main.stagg_input_files and they come from more than one directory, we would need to have a different command line, so instead we'll regulate the user:
                    reply = QMessageBox.information(self, "That's a lot of JSON", 'The STAGG input provided consists of more than 200 files from multiple directories.\nPlease condense the files into one directory for STAGG to analyze.', QMessageBox.Ok, QMessageBox.Ok)
                else:
                    # If there are more than 200 files in Main.stagg_input_files but they all come from the same directory, then args$JSON (Main.input_dir_r on our end) needs to be a directory path instead.
                    self.input_dir_r = os.path.dirname(self.stagg_input_files[0])
                    self.rthing_to_do_cntd()
            else:
                # If there aren't a ridiculous number of json files in Main.stagg_input_files, then we just need to render the list of file paths into an unbracketed string so that STAGG can recognize it as a list. STAGG didn't like the brackets.
                self.input_dir_r = ','.join(item for item in self.stagg_input_files)
                self.rthing_to_do_cntd()
    
    def rthing_to_do_cntd(self):
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
                        pre_des = QFileDialog.getOpenFileName(self, 'Find Rscript.exe', str(self.workspace_dir))
                        if os.path.basename(pre_des[0]) == "Rscript.exe":
                            self.rscript_des = pre_des[0]
                            self.gui_config['Dictionaries']['Paths']['rscript'] = pre_des[0]
                            with open(f'{Path(__file__).parent}/gui_config.json','w') as gconfig_file:
                                json.dump(self.gui_config,gconfig_file)
            else:
                reply = QMessageBox.information(self, 'Rscript not found', 'Rscript.exe path not defined. Would you like to select the R executable?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                if reply == QMessageBox.Ok:
                    pre_des = QFileDialog.getOpenFileName(self, 'Find Rscript.exe', str(self.workspace_dir))
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
