
import os
from copy import deepcopy
from typing import Optional

import pandas as pd
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

from thinbass_controller import Thinbass
from util import Settings 
from util.ui.dialogs import ask_user_ok, notify_error, notify_info
from util.ui.tools import populate_table
from ui.manual_form import Ui_Manual

class Manual(QDialog, Ui_Manual):
    """
    Properties, attributes, and methods used by the manual BASSPRO settings subGUI.

    Attributes
    ---------
    defaults (dict): default basic settings
    data (pd.DataFrame): result of merged datapad and preset,
                         reflected in the GUI widgets
    manual_df: same as data
    output_dir (str): current working directory
    vals (List[str]): mandatory datapad columns
    datapad (pd.DataFrame): datapad info
    preset (pd.DataFrame): default info
    """
    def __init__(self, defaults: dict, data: Optional[pd.DataFrame] = None, output_dir: str = ""):
        """
        Instantiates the Manual class and all attributes
        
        Parameters
        --------
        defaults: default manual sections
        data: initial data given from caller
        output_dir: current working directory
        """

        super(Manual, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Manual sections file creation")
        self.showFullScreen()

        self.defaults = defaults
        # TODO: replace manual_df with this!
        self.data = deepcopy(data)
        self.output_dir = output_dir

        self.preset_menu.addItems(list(self.defaults.keys()))

        self.vals = ['animal id','PLYUID','start','stop','duration','mFrequency_Hz','mPeriod_s','mHeight_V','mO2_V','mCO2_V','mTchamber_V','segment']
        
        if data is None:
            self.datapad = None
            self.preset = None
            self.manual_df = None
        else:
            self.load_data(data)

    def get_datapad(self):
        """Choose Labchart file and load into GUI"""
        files, filter = QFileDialog.getOpenFileNames(self, 'Select Labchart datapad export file')
        # Catch cancel
        if not files:
            return

        dfs = []
        try:
            for f in files:
                path_basename = os.path.basename(f)
                if f.endswith('.csv'):
                    df = pd.read_csv(f, header=[2])
                    mp = path_basename.rsplit(".csv")[0]
                elif f.endswith('.txt'):
                    df = pd.read_csv(f, sep="\t", header=[2])
                    mp = path_basename.rsplit(".txt")[0]
                elif f.endswith('.xlsx'):
                    df = pd.read_excel(f, header=[0])
                    mp = path_basename.rsplit(".xlsx")[0]

                if "_" in mp:
                    df['animal id'] = mp.rsplit("_")[0]
                    df['PLYUID'] = mp.rsplit("_")[1]
                else:
                    df['animal id'] = mp
                    df['PLYUID'] = ""

                dfs.append(df)

            dc = pd.concat(dfs, ignore_index=True)
            dc.insert(0,'PLYUID', dc.pop('PLYUID'))
            dc.insert(0,'animal id', dc.pop('animal id'))

            keys = dc.columns
            mand = {}
            for key,val in zip(keys, self.vals):
                mand.update({key: val})

            dc = dc.rename(columns = mand)
            dc['start_time'] = pd.to_timedelta(dc['start'], errors='coerce')
            dc['start'] = dc['start_time'].dt.total_seconds()
            dc['stop_time'] = pd.to_timedelta(dc['stop'], errors='coerce')
            dc['stop'] = dc['stop_time'].dt.total_seconds()

            self.datapad = dc
            populate_table(self.datapad, self.datapad_view)

        # TODO: catch a specific error
        except Exception as e:
            notify_error(title=f"{type(e).__name__}: {e}", msg="Please ensure that the datapad is formatted as indicated in the documentation.")

    def get_preset(self):
        """
        Get default settings for user-selected experimental setup
        
        Attributes-Out
        -------------
        preset: store the default values
        """
        current_menu_selection = self.preset_menu.currentText()
        self.preset = pd.DataFrame.from_dict(self.defaults[current_menu_selection].values())
        populate_table(self.preset, self.settings_view)    
    
    def manual_merge(self):
        """
        Merge the datapad and defaults and update GUI with result
        
        Attributes-Out
        -------------
        manual_df: stores the result of the merge
        data: stores the same thing as manual_df
        """
        try:
            self.manual_df = self.datapad.merge(self.preset, 'outer',
                                                left_on=self.datapad['segment'],
                                                right_on=self.preset['Alias'])
            self.manual_df = self.manual_df.iloc[:,1:]
            self.data = self.manual_df
            populate_table(self.manual_df, self.manual_view)
        except Exception as e:
            if self.datapad is None and self.preset is not None:
                reply = ask_user_ok(title='Missing datapad file',
                                    msg=('You need to select a LabChart datapad exported'
                                        ' as a text file. Would you like to select a file?'))
                if reply:
                    self.get_datapad()
            elif self.preset is None and self.datapad is not None:
                notify_info(title='Missing sections settings',
                            msg='Please select one of the options from the dropdown menu above.')
            elif self.datapad is None and self.preset is None:
                msg = ('There is nothing to merge.'
                       ' Would you like to open an existing manual'
                       ' sections settings file or create a new one?')
                thinb = Thinbass(valid_options=["New File", "Load File"], msg=msg)
                if not thinb.exec():
                    return

                selected_option = thinb.get_value()
                if selected_option == "New File":
                    self.new_manual_file()
                else:
                    self.load_file()
         
    def new_manual_file(self):
        """
        Guide user through selecting LabChart Datapad view exported .txt files and/or an experimental setup from the drop-down menu. 
        """
        if self.datapad is None:
            reply = QMessageBox.information(self, 'Missing datapad file', 'You need to select a LabChart datapad exported as a text file. Would you like to select a file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
            if reply == QMessageBox.Yes:
                self.get_datapad()
        if self.preset is None:
            reply = QMessageBox.information(self, 'Missing sections settings', 'Please select one of the options from the dropdown menu above.', QMessageBox.Ok)

    def export(self):
        """Save current data to user-selected file"""
        if ManualSettings.save_file(self.data):
            notify_info("Manual sections file saved")
    
    def load_file(self):
        """Load manual settings from user-selected file."""
        file = ManualSettings.open_file(self.output_dir)
        if file:
            data = ManualSettings.attempt_load(file)
            self.load_data(data)
            
    def load_data(self, data: pd.DataFrame):
        """
        Load a given DataFrame into the GUI

        Attributes-Out
        -------------
        manual_df: stores the loaded data
        datapad: produced by slicing the loaded data to include only the columns with headers found in self.vals
        preset: produced by slicing the loaded data to include the columns not included in the datapad
        """
        # TODO: Why are we doing this split when self.data already contains all this?
        self.datapad = data.loc[:, [x for x in self.vals]]
        self.preset = data.loc[:, [x for x in data.columns if x not in self.datapad.columns]].drop_duplicates()
        self.data = data

        populate_table(self.data, self.manual_view)
        populate_table(self.datapad, self.datapad_view)
        populate_table(self.preset, self.settings_view)

class ManualSettings(Settings):
    """Attributes and methods for handling Manual settings"""

    valid_filetypes = ['.csv']
    naming_requirements = ['man', 'sections']
    file_chooser_message = 'Select manual sections file to edit'
    default_filename = 'mansections.csv'
    editor_class = Manual

    @staticmethod
    def _save_file(filepath, data):
        # Saving the dataframes holding the configuration preferences to csvs and assigning them their paths:
        data.to_csv(filepath, index=False)

    def attempt_load(filepath):
        data = pd.read_csv(filepath)
        return data
