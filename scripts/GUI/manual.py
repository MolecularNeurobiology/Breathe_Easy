
import os
from copy import deepcopy
import pandas as pd
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox, QTableWidgetItem
from thorbass_controller import Thorbass
from util import Settings 
from util.ui.dialogs import notify_error, notify_info
from ui.manual_form import Ui_Manual

# YOu need to make the columns reflect the headers of the dataframes
class Manual(QDialog, Ui_Manual):
    """
    The Manual class defines the properties, attributes, and methods used by the manual BASSPRO settings subGUI.

    Parameters
    --------
    QWidget: class
        The Manual class inherits properties and methods from the QWidget class.
    Ui_Manual: class
        The Manual class inherits widgets and layouts defined in the Ui_Manual class.
    """
    def __init__(self, defaults, data=None, workspace_dir=""):
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
        self.isMaximized()
        self.defaults = defaults
        self.data = deepcopy(data)
        self.workspace_dir = workspace_dir

        self.preset_menu.addItems(list(self.defaults.keys()))

        self.datapad = None
        self.preset = None
        self.manual_df = None
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
        files, filter = QFileDialog.getOpenFileNames(self, 'Select Labchart datapad export file')
        # Catch cancel
        if not files:
            return

        dfs=[]
        try:
            for f in files:
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
            dc['start_time'] = pd.to_timedelta(dc['start'],errors='coerce')
            dc['start'] = dc['start_time'].dt.total_seconds()
            dc['stop_time'] = pd.to_timedelta(dc['stop'],errors='coerce')
            dc['stop'] = dc['stop_time'].dt.total_seconds()

            self.datapad = dc
            self.populate_table(self.datapad, self.datapad_view)

        # TODO: catch a specific error
        except Exception as e:
            notify_error(title=f"{type(e).__name__}: {e}", msg="Please ensure that the datapad is formatted as indicated in the documentation.")

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
        self.preset = pd.DataFrame.from_dict(self.defaults[self.preset_menu.currentText()].values())
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
        try:
            self.manual_df = self.datapad.merge(self.preset,'outer',left_on=self.datapad['segment'],right_on=self.preset['Alias'])
            self.manual_df = self.manual_df.iloc[:,1:]
            self.data = self.manual_df
            self.populate_table(self.manual_df,self.manual_view)
        except Exception as e:
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

    def export(self):
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
        if ManualSettings.save_file(self.data, workspace_dir=self.workspace_dir):
            notify_info("Manual sections file saved")
    
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
        file = ManualSettings.open_file(self.workspace_dir)
        if file:

            data = ManualSettings.attempt_load(file)
            self.datapad = data.loc[:, [x for x in self.vals]]
            self.preset = data.loc[:, [x for x in data.columns if x not in self.datapad.columns]].drop_duplicates()
            self.data = data

            self.populate_table(self.data, self.manual_view)
            self.populate_table(self.datapad, self.datapad_view)
            self.populate_table(self.preset, self.settings_view)

class ManualSettings(Settings):

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
