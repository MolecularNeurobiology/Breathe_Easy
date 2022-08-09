
from copy import deepcopy
from pathlib import Path
from typing import Optional

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QTableWidgetItem

from ui.basic_form import Ui_Basic
from util import Settings
from util.ui.dialogs import notify_info
from util.ui.tools import populate_table

class Basic(QDialog, Ui_Basic):
    """
    Properties, attributes, and methods used by the basic BASSPRO settings subGUI.

    Attributes
    ---------
    defaults (dict): default basic settings
    ref_definitions (dict): help text for each auto section variable
    data (pd.DataFrame): current data reflected in the GUI widgets
    output_dir (str): current working directory
    ref_buttons (dict): the help messages for each help button, mapped to the appropriate display box
    lineEdits (dict): lineEdit widgets mapped to their labels
    """
    def __init__(self, defaults: dict, ref_definitions: dict, data: Optional[pd.DataFrame] = None, output_dir: str = ""):
        """
        Instantiate the Basic class.

        Parameters
        ---------
        defaults: default basic settings
        ref_definitions: help text for each auto section variable
        data: initial data given from caller
        output_dir: current working directory
        """
        super(Basic, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Basic BASSPRO settings")
        self.defaults = defaults
        self.ref_definitions = ref_definitions
        self.data = deepcopy(data)
        self.output_dir = output_dir
        self.isMaximized()
        
        # Create self attributes for widget access
        self.setup_variables()

        self.load_data()

        # Update the lineEdits when a cell is changed in the summary table
        self.summary_table.cellChanged.connect(self.update_lineedit)


    def setup_variables(self):
        """
        Organize widgets into dictionaries and assign signals and slots to relevant buttons.
        """
        # Set up help buttons and callbacks
        basic_reference = [self.help_minTI,self.help_minPIF,self.help_minPEF,self.help_TTwin,self.help_SIGHwin,self.help_minAplTT,self.help_minApsTT]
        rig_reference = [self.help_ConvertTemp,self.help_ConvertCO2,self.help_ConvertO2,self.help_Flowrate,self.help_Roto_x,self.help_Roto_y,self.help_chamber_temp_cutoffs,self.help_chamber_temperature_units,self.help_chamber_temperature_default,self.help_chamber_temperature_trim_size,self.help_chamber_temperature_narrow_fix]
        crude_reference = [self.help_per500win,self.help_perX,self.help_maxPer500,self.help_maximum_DVTV,self.help_apply_smoothing_filter,self.help_maxTV,self.help_maxVEVO2]
        output_reference = [self.help_All_Breath_Output,self.help_Aggregate_Output]
        self.ref_buttons = {
            self.basic_reference: {widg.objectName(): widg for widg in basic_reference},
            self.rig_reference: {widg.objectName(): widg for widg in rig_reference},
            self.crude_reference: {widg.objectName(): widg for widg in crude_reference},
            self.output_reference: {widg.objectName(): widg for widg in output_reference}
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
            self.lineEdit_maxVEVO2: "maxVEVO2",
            self.lineEdit_All_Breath_Output: "All_Breath_Output",
            self.lineEdit_Aggregate_Output: "Aggregate_Output"
        }
        
        resets = [
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
            self.reset_maxVEVO2,
            self.reset_All_Breath_Output,
            self.reset_Aggregate_Output
            ]

        # Connect help message signals to help buttons
        for ref_button_dict in self.ref_buttons.values():
            for ref_button in ref_button_dict.values():
                ref_button.clicked.connect(self.show_help)
        
        # Connect reset button callbacks
        for r in resets:
            r.clicked.connect(self.reset_parameter)
        
        # Connect lineEdit callbacks
        for l in self.lineEdits:
            l.textChanged.connect(self.update_table_cell)

    def load_data(self):
        """Populate widgets with current data"""

        # If no data, load defaults
        if self.data is None:
            self.data = pd.DataFrame.from_dict(self.defaults, orient='index').reset_index()
            self.data.columns = ['Parameters', 'Settings']

        # Populate new data into summary table
        self.summary_table.blockSignals(True)
        populate_table(self.data, self.summary_table)
        self.summary_table.blockSignals(False)

        # Update lineEdits to match table
        self.update_all_lineedits()
    
    def show_help(self):
        """Callback to display help text for the caller"""
        sbutton = self.sender()
        button_name = sbutton.objectName()
        for ref_box, ref_button_dict in self.ref_buttons.items():
            if str(button_name) in ref_button_dict:
                ref_text = self.ref_definitions.get(button_name.replace("help_",""), "No Reference Info")
                ref_box.setPlainText(ref_text)
                ref_box.setOpenExternalLinks(True)
    
    def reset_parameter(self):
        """Callback to reset the caller's parameter to default"""
        sbutton = self.sender()
        button_name = sbutton.objectName()
        for widget in self.lineEdits:
            if widget.objectName().replace("lineEdit_","") == str(button_name).replace("reset_",""):
                widget.setText(str(self.defaults[self.lineEdits[widget]]))
    
    def update_table_cell(self):
        """Callback to update the summary table with a changed lineEdit"""

        lineedit = self.sender()

        # Get updated data in lineedit
        updated_data = lineedit.text()

        variable_to_update = lineedit.objectName().replace("lineEdit_","")

        # Prevent endless loop of triggering lineEdit update and back
        self.summary_table.blockSignals(True)

        # Find the corresponding cell to update
        for row in range(self.summary_table.rowCount()):
            sum_table_index_name = self.summary_table.item(row, 0).text()
            if sum_table_index_name == variable_to_update:
                self.summary_table.item(row, 1).setText(updated_data)
        
        # Reenable signals
        self.summary_table.blockSignals(False)


    def update_summary_table(self):
        """Populate the summary table with the current data"""

        # Populate tablewidgets with views of uploaded csv. Currently editable.
        self.summary_table.setColumnCount(len(self.data.columns))
        self.summary_table.setRowCount(len(self.data))

        for col in range(self.summary_table.columnCount()):
            for row in range(self.summary_table.rowCount()):
                self.summary_table.setItem(row, col, QTableWidgetItem(str(self.data.iloc[row, col])))
                self.summary_table.item(row,0).setFlags(Qt.ItemIsEditable)

        self.summary_table.setHorizontalHeaderLabels(self.data.columns)
        self.summary_table.resizeColumnsToContents()
        self.summary_table.resizeRowsToContents()

    def update_lineedit(self, row: int, col: int):
        """
        Update a lineedit to match the associated summary table cell
        
        Parameters
        ---------
        row: row of summary table cell
        column: column of summary table cell
        """
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
        Update all LineEdits to reflect the current data in the summary table.
        """
        # For each row in the summary table
        for row in range(self.summary_table.rowCount()):
            self.update_lineedit(row, None)


    def confirm(self):
        """Confirm user input and close window"""
        # Update dataframe with latest edits
        self.data = self.get_dataframe()
        
        # Close with accepted signal
        self.accept()

    def get_dataframe(self):
        """
        Return DataFrame created from current lineEdit widget values
        """
        # Read lineEdit widgets and create dataframe
        lineedit_data = [(param_name, widg.text()) for widg, param_name in self.lineEdits.items()]
        data = pd.DataFrame(data=lineedit_data, columns=['Parameter', 'Setting'])
        return data

    def save_as(self):
        """Save current data to user-selected file"""
        # Update dataframe from curr widget inputs
        self.data = self.get_dataframe()

        if BasicSettings.save_file(self.data):
            notify_info("Basic settings saved.")

    def load_file(self):
        """Load basic settings from user-selected file"""
        while True:
            # Opens open file dialog
            filepath = BasicSettings.open_file(self.output_dir)

            # Catch cancel
            if not filepath:
                break

            dataframe = BasicSettings.attempt_load(filepath)
            if dataframe is not None:
                self.data = dataframe

                self.load_data()
                break


class BasicSettings(Settings):
    """Attributes and methods for handling Basic settings"""

    valid_filetypes = ['.csv', '.xlsx']
    naming_requirements = ['basic']
    file_chooser_message = 'Select breathcaller configuration file to edit basic parameters'
    default_filename = 'basicap.csv'
    editor_class = Basic

    @staticmethod
    def attempt_load(file):
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
        