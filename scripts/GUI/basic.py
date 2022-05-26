
import os
from copy import deepcopy
import json
from pathlib import Path
import pandas as pd
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QFileDialog, QMessageBox
from PyQt5.QtCore import QObject
from ui.basic_form import Ui_Basic
from PyQt5.QtCore import Qt
from util import notify_info, Settings, populate_table

class Basic(QDialog, Ui_Basic):
    """
    The Basic class defines the the properties, attributes, and methods used by the basic BASSPRO settings subGUI.

    Parameters
    --------
    QWidget: class
        The Basic class inherits properties and methods from the QWidget class. 
    Ui_Basic: class
        The Basic class inherits widgets and layouts defined in the Ui_Basic class.
    """
    def __init__(self, defaults, ref_definitions, data=None, workspace_dir=""):
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
        self.load_data()
            This method populates the basic BASSPRO settings subGUI widgets with default values derived from Plethysmography.bc_config (breathcaller_config.json).
        """
        super(Basic, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Basic BASSPRO settings")
        self.defaults = defaults
        self.ref_definitions = ref_definitions
        self.data = deepcopy(data)
        self.workspace_dir = workspace_dir
        self.isMaximized()
        
        # Create self attributes for widget access
        self.setup_variables()

        self.load_data()

        # Update the lineEdits when a cell is changed in the summary table
        self.summary_table.cellChanged.connect(self.update_lineedit)


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
        self.defaults: dict
            This attribute stores the nested dictionary in Plethysmography.bc_config that contains the default basic BASSPRO settings.
        self.ref_buttons: dict
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
        basic_reference = [self.help_minTI,self.help_minPIF,self.help_minPEF,self.help_TTwin,self.help_SIGHwin,self.help_minAplTT,self.help_minApsTT]
        rig_reference = [self.help_ConvertTemp,self.help_ConvertCO2,self.help_ConvertO2,self.help_Flowrate,self.help_Roto_x,self.help_Roto_y,self.help_chamber_temp_cutoffs,self.help_chamber_temperature_units,self.help_chamber_temperature_default,self.help_chamber_temperature_trim_size,self.help_chamber_temperature_narrow_fix]
        crude_reference = [self.help_per500win,self.help_perX,self.help_maxPer500,self.help_maximum_DVTV,self.help_apply_smoothing_filter,self.help_maxTV,self.help_maxVEVO2]
        self.ref_buttons = {
            self.basic_reference: {widg.objectName(): widg for widg in basic_reference},
            self.rig_reference: {widg.objectName(): widg for widg in rig_reference},
            self.crude_reference: {widg.objectName(): widg for widg in crude_reference}
            }

        self.lineEdits = {
            self.lineEdit_minimum_TI: "minimum_TI", 
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
        
        self.resets = [
            self.reset_minimum_TI,
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

        for ref_button_dict in self.ref_buttons.values():
            for ref_button in ref_button_dict.values():
                ref_button.clicked.connect(self.reference_event)
        
        for r in self.resets:
            r.clicked.connect(self.reset_event)
        
        for l in self.lineEdits:
            l.textChanged.connect(self.update_table_event)

    def load_data(self):
        """
        Populate widgets in each tab with appropriate values for the default basic BASSPRO settings stored in self.defaults.

        Parameters
        --------
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.
        self.defaults: dict
            This attribute stores the nested dictionary in Plethysmography.bc_config that contains the default basic BASSPRO settings.
        Plethysmography.basicap: str
            The path of the user-selected basic BASSPRO settings file.
        self.summary_table: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        
        Outputs
        --------
        self.lineEdit_{setting}: QLineEdit
            The LineEdits' values are iteratively set as the values of the corresponding keys in self.defaults.
        self.data: Dataframe
            This attribute stores a dataframe derived either from self.defaults or from the .csv file indicated by the user-selected file path (self.basicap).
        
        Outcomes
        --------
        self.update_summary_table()
            This method populates self.summary_table (TableWidget) with the self.data dataframe.
        """

        # If no data, load defaults
        if self.data is None:
            self.data = pd.DataFrame.from_dict(self.defaults, orient='index').reset_index()
            self.data.columns = ['Parameters', 'Settings']

        # Populate new data into summary table
        self.summary_table.blockSignals(True)
        populate_table(self.data, self.summary_table)
        self.summary_table.blockSignals(False)

        ## Populate lineEdit widgets with default basic parameter values from breathcaller configuration file:
        #for widget in self.lineEdits:
        #    widget.setText(str(self.defaults[self.lineEdits[widget]]))

        # Update lineEdits to match table:
        self.update_all_lineedits()
    
    def reference_event(self):
        """
        Respond to the signal emitted by the self.help_{setting} ToolButton clicked by the user by calling self.display_help(self.sender.objectName()) to populate the appropriate TextBrowser with the definition, description, and default value of corresponding setting.
        """
        sbutton = self.sender()
        self.display_help(sbutton.objectName())
    
    def reset_event(self):
        """
        Respond to the signal emitted by the self.reset_{setting} ToolButton clicked by the user by calling self.reset_parameters(self.sender.objectName()) to revert the LineEdit value to the default value in the default basic BASSPRO settings dictionary (self.defaults).
        """
        sbutton = self.sender()
        self.reset_parameter(sbutton.objectName())
    
    def update_table_event(self):
        """
        Respond to the signal emitted by the self.lineEdit_{setting} LineEdit edited by the user by calling self.update_summary_cell(self.sender.objectName()) to update self.summary_table to reflect changes made to LineEdits in other tabs.
        """
        sbutton = self.sender()
        self.update_summary_cell(sbutton.objectName())

    def display_help(self, buttoned):
        """
        Populate the appropriate reference TextBrowser with the definition, description, and default values of the appropriate setting as indicated by the suffix of the ToolButton's objectName(), e.g. "help_{setting}" from Plethysmography.rc_config (reference_config.json).
        """
        for ref_box, ref_button_dict in self.ref_buttons.items():
            if str(buttoned) in ref_button_dict:
                ref_box.setPlainText(self.ref_definitions[buttoned.replace("help_","")])
                ref_box.setOpenExternalLinks(True)
   
    def update_summary_table(self):
        """
        Populate self.summary_table (TableWidget) with the self.data dataframe.

        Parameters
        --------
        frame: Dataframe
            This variable refers to the self.data dataframe.
        table: QTableWidget
            This variable refers to self.summary_table (TableWidget).

        Outputs
        --------
        self.summary_table: QTableWidget
            The TableWidget is populated by the contents of the self.data dataframe, assigned cellChanged signals slotted to self.update_all_lineedits, and cell dimensions adjusted to accommodate the text.
        """
        frame = self.data

        # Populate tablewidgets with views of uploaded csv. Currently editable.
        self.summary_table.setColumnCount(len(frame.columns))
        self.summary_table.setRowCount(len(frame))

        for col in range(self.summary_table.columnCount()):
            for row in range(self.summary_table.rowCount()):
                self.summary_table.setItem(row, col, QTableWidgetItem(str(frame.iloc[row, col])))
                self.summary_table.item(row,0).setFlags(Qt.ItemIsEditable)

        self.summary_table.setHorizontalHeaderLabels(frame.columns)
        self.summary_table.resizeColumnsToContents()
        self.summary_table.resizeRowsToContents()

    def update_summary_cell(self, donor: QObject.objectName):
        """
        Update self.summary_table (TableWidget) to reflect changes to LineEdits.

        Parameters
        --------
        donor: QObject.objectName
            This variable is the objectName of the LineEdit that emitted the signal self.update_table_event that called this method. Its suffix is used to identify the appropriate cell in self.summary_table (TableWidget).
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.
        self.summary_table: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.

        Outputs
        --------
        self.summary_table: QTableWidget
            The cell that contains the value of the setting that was updated by the user editing a LineEdit is updated to reflect the edit.
        """
        # Prevent endless loop of triggering lineEdit update and back
        self.summary_table.blockSignals(True)

        variable_to_update = donor.replace("lineEdit_","")

        # Get name of updated widget
        for l in self.lineEdits:
            if donor == l.objectName():
                updated_data = l.text()

        # Find the corresponding cell
        for row in range(self.summary_table.rowCount()):
            sum_table_index_name = self.summary_table.item(row, 0).text()
            if sum_table_index_name == variable_to_update:
                self.summary_table.item(row,1).setText(updated_data)
        
        # Reenable signals
        self.summary_table.blockSignals(False)

    def update_lineedit(self, row, col):
        # Get the index name of that row's parameter
        sum_table_index_name = self.summary_table.item(row, 0).text()

        # Check each lineEdit
        for l in self.lineEdits:
            variable_to_update = l.objectName().replace("lineEdit_", "")
            
            # If this is the corresponding lineEdit for the table row
            if sum_table_index_name == variable_to_update:

                # Prevent endless loop of triggering summary table update and back again
                l.blockSignals(True)

                # Update lineEdit data
                l.setText(self.summary_table.item(row,1).text())

                # Reenable signals
                l.blockSignals(False)
        
    def update_all_lineedits(self):
        """
        Update the LineEdits to reflect changes to self.summary_table (TableWidget).

        Parameters
        --------
        self.summary_table: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.
        
        Outputs
        --------
        self.lineEdit_{settings}: QLineEdit
            The LineEdit whose objectName suffix matches the setting that was edited by the user in self.summary_table (TableWidget) is updated to reflect the edit.
        """

        # For each row in the summary table
        for row in range(self.summary_table.rowCount()):
            self.update_lineedit(row, None)


    def reset_parameter(self,butts):
        """
        Revert the settings to its corresponding default value in the basic BASSPRO settings stored in the self.defaults.

        Parameters
        --------
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.
        self.data: Dataframe
            This attribute stores a dataframe derived either from self.defaults or from the .csv file indicated by the user-selected file path (self.basicap).

        Outputs
        --------
        self.lineEdit_{settings}: QLineEdit
            The LineEdit whose objectName suffix matches the setting that was edited by the user in self.summary_table (TableWidget) is updated to reflect the edit.
        """
        print("basic.reset_parameter()")
        for widget in self.lineEdits:
            if widget.objectName().replace("lineEdit_","") == str(butts).replace("reset_",""):
                widget.setText(str(self.defaults[self.lineEdits[widget]]))

    def confirm(self):
        # Update dataframe with latest edits
        self.data = self.get_dataframe()
        
        # Close with accepted signal
        self.accept()

    def get_dataframe(self):
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
        self.data: Dataframe
            This attribute stores a dataframe made from the "current" dictionary that was updated with the values of the corresponding LineEdits.
        """
        # Read lineEdit widgets and create dataframe
        lineedit_data = [(param_name, widg.text()) for widg, param_name in self.lineEdits.items()]
        data = pd.DataFrame(data=lineedit_data, columns=['Parameter', 'Setting'])
        return data

    def save_as(self):
        """
        Write self.data dataframe to a .csv file, dump the nested dictionary stored in Plethysmography.bc_config to breathcaller_config.json to save changes made to the "current" dictionary in the basic BASSPRO settings dictionary in Plethysmography.bc_config, and add the file path self.basicap to the ListWidget self.sections_list for display in the main GUI.

        Parameters
        --------
        self.path: str
            This attribute stores the file path automatically generated based on the user-selected output directory.
        Plethysmography.basicap: str
            This Plethysmography class attribute stores the file path of the .csv file that the basic BASSPRO settings are saved to.
        self.data: Dataframe
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
        # Update dataframe from curr widget inputs
        self.data = self.get_dataframe()

        if BasicSettings.save_file(self.data, workspace_dir=self.workspace_dir):
            notify_info("Basic settings saved")

    def load_file(self):
        """
        Prompt the user to indicate the location of a previously made file - either .csv, .xlsx, or .json formatted file - detailing the basic BASSPRO settings of a previous run, populate self.data with a dataframe from that file, call self.update_summary_table(), and warn the user if they chose files in formats that are not accepted and ask if they would like to select a different file.

        Parameters
        --------
        file: QFileDialog
            This variable stores the path of the file the user selected via the FileDialog.
        yes: int
            This variable is used to indicate whether or not self.data was successfully populated with a dataframe from the user-selected file.
        Plethysmography.workspace_dir: str
            The path to the user-selected directory for all output.
        self.data: Dataframe
            This attribute stores a dataframe derived from the .csv file indicated by the user-selected file path (Plethysmography.basicap).
        self.summary_table: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        reply: QMessageBox
            This specialized dialog communicates information to the user.

        Outputs
        --------
        self.data: Dataframe
            This attribute stores a dataframe derived from the .csv file indicated by the user-selected file path (Plethysmography.basicap).
        self.summary_table: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        
        Outcomes
        --------
        self.update_summary_table()
            Populate self.summary_table (TableWidget) with the self.data dataframe.
        self.load_basic_file()
            Prompt the user to indicate the location of a previously made file - either .csv, .xlsx, or .json formatted file - detailing the basic BASSPRO settings of a previous run, populate self.data with a dataframe from that file, call self.update_summary_table(), and warn the user if they chose files in formats that are not accepted and ask if they would like to select a different file.
        """
        while True:
            # Opens open file dialog
            filepath = BasicSettings.open_file(self.workspace_dir)

            # Catch cancel
            if not filepath:
                break

            dataframe = BasicSettings.attempt_load(filepath)
            if dataframe is not None:
                self.data = dataframe

                self.load_data()
                break
            
            # If no dataframe, loop again and try to open a different file



class BasicSettings(Settings):

    valid_filetypes = ['.csv', '.xlsx']
    naming_requirements = ['basic']
    file_chooser_message = 'Select breathcaller configuration file to edit basic parameters'
    default_filename = 'basicap.csv'
    editor_class = Basic

    @staticmethod
    def attempt_load(file):
        # TODO: do we want to keep the json format?
        #if Path(file).suffix == ".json":
        #    with open(file) as config_file:
        #        basic_json = json.load(config_file)
        #    data = pd.DataFrame.from_dict(basic_json['Dictionaries']['AP']['current'],orient='index').reset_index()
        #    data.columns = ['Parameter','Setting']
        if Path(file).suffix == ".csv":
            data = pd.read_csv(file)
        elif Path(file).suffix == ".xlsx":
            data = pd.read_excel(file)
        else:
            return None
        return data

    def _save_file(filepath, data):
        # Save basic settings csv
        data.set_index('Parameter').to_csv(filepath)
        