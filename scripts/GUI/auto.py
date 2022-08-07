
from typing import List, Optional
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QDialog, QInputDialog, QTableWidget
from util.tools import avert_name_collision
from util import Settings
from util.ui.dialogs import notify_info, notify_warning
from util.ui.tools import populate_table
from ui.auto_form import Ui_Auto

from tools.convert_timestamps_to_autosections import convert_timestamps_to_autosections

class Auto(QDialog, Ui_Auto):
    """
    Properties, attributes, and methods used by the automated BASSPRO settings subGUI.

    Attributes
    ---------
    ref_buttons (dict): the help messages for each help button, mapped to the appropriate display box
    defaults (dict): default values for a set of template selections
    auto_labels (dict): names of auto section variables, split into named groupings
    ref_definitions (dict): help text for each auto section variable
    signal_files (List[str]): list of signal file paths
    output_dir (str): current working directory
    loaded_data (Optional[pd.DataFrame]): current custom data loaded by user (as opposed to default sets)
    data (pd.DataFrame): current data reflected in the GUI widgets
    """
    def __init__(self, defaults: dict, auto_labels: dict, ref_definitions: dict,
                 signal_files: List[str], data: Optional[pd.DataFrame] = None, output_dir: str = ""):
        """
        Instantiate the Auto class.

        Parameters
        ---------
        defaults: default values for a set of template selections
        auto_labels: names of auto section variables, split into named groupings
        ref_definitions: help text for each auto section variable
        signal_files: list of signal file paths
        data: initial data given from caller
        output_dir: current working directory
        
        """
        super(Auto, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Automated sections file creation")
        self.isMaximized()

        sections_reference = [
            self.help_key,
            self.help_alias,
            self.help_cal_seg,
            self.help_auto_ind_injection, 
            self.help_auto_ind_include,
            self.help_min_co2,
            self.help_max_co2,
            self.help_min_o2,
            self.help_max_o2,
            self.help_within_start,
            self.help_within_end,
            self.help_after_start,
            self.help_before_end
            ]

        cal_reference = [
            self.help_auto_ind_cal,
            self.help_auto_ind_gas_cal,
            self.help_cal_co2,
            self.help_cal_o2
            ]

        thresh_reference = [
            self.help_include_apnea,
            self.help_include_sigh,
            self.help_startpoint,
            self.help_midpoint,
            self.help_endpoint,
            self.help_include_high_chamber_temp
            ]

        inc_reference = [
            self.help_min_VO2,
            self.help_min_VCO2,
            self.help_min_tv,
            self.help_max_calibrated_TV,
            self.help_max_VEVO2,
            self.help_min_TT,
            self.help_max_TT,
            self.help_max_dvtv,
            self.help_X,
            self.help_max_pX,
            self.help_vol_mov_avg_drift,            
            self.help_min_bout
            ]

        # Store ref buttons with their reference box
        self.ref_buttons = {
            self.sections_reference: {widg.objectName(): widg for widg in sections_reference},
            self.cal_reference: {widg.objectName(): widg for widg in cal_reference},
            self.thresh_reference: {widg.objectName(): widg for widg in thresh_reference},
            self.inc_reference: {widg.objectName(): widg for widg in inc_reference}
            }

        # Setup help button callbacks
        for ref_button_dict in self.ref_buttons.values():
            for ref_button in ref_button_dict.values():
                ref_button.clicked.connect(self.show_help)

        self.defaults = defaults
        self.auto_labels = auto_labels
        self.ref_definitions = ref_definitions
        self.signal_files = signal_files
        self.output_dir = output_dir
        self.loaded_data = None

        # Populate default template keys
        self.auto_setting_combo.addItems(self.defaults)

        # If we've got data to load
        if data is not None:
            self.load_data(data.copy())

        # set to defaults
        else:
            # First item is instruction text, set to index 1
            self.auto_setting_combo.setCurrentIndex(1)

        ## NOTE: ^^ The update will automatically trigger on index change ^^
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

        # Set callback for any table item edits
        for table in self.all_tables():
            table.cellChanged.connect(lambda row, col, t=table : self.edit_cell(t, row, col))

        for table in self.all_tables():
            table.horizontalHeader().sectionDoubleClicked.connect(self.set_new_header)


    def set_new_header(self, col_idx: int):
        """
        Display dialog to set table header

        Parameters
        ---------
        col_idx: index of column header to set
        """
        headers = self.data.columns.values
        old_header = headers[col_idx]
        new_name, ok = QInputDialog.getText(self, "Rename Column", f'Change "{old_header}" to:')
        if ok and new_name != "":
            # Update data with new name
            headers[col_idx] = new_name
            self.data.columns = pd.Index(headers, name='Alias')
            # Update GUI with new name
            self.update_tabs()

    def untransform_data(self, df):
        """Re-transpose data to format for writing to file"""
        col_count = self.summary_table.columnCount()
        headers = [self.summary_table.horizontalHeaderItem(i).text() for i in range(col_count)]
        variable_column_name = headers[0]
        df = df.drop(columns=variable_column_name)
        df = df.transpose()
        df = df.reset_index()
        return df

    @staticmethod
    def transform_loaded_data(df):
        """Transform data into format for loading widgets"""

        df = df.fillna("")

        # Set df index (these will become the columns)
        df = df.set_index('Alias')

        # Swap rows and columns
        df = df.T
        
        # The original df columns are now the index,
        #   but we want them actually included as a new column in the transposed df
        # Copy index as 'Variable' column
        df.insert(0, 'Variable', df.index)

        return df

    def all_tables(self):
        """Retrieve list of all tables in window"""
        return [self.sections_char_table,
                self.sections_spec_table,
                self.sections_veras_table,
                self.sections_time_table,
                self.cal_table,
                self.inc_table,
                self.sections_art_table,
                self.gas_thresh_table,
                self.time_thresh_table,
                self.summary_table]

    def timestamps_from_signals(self):
        """Import autosections from signal file timestamps"""
        if not self.signal_files:
            notify_info("Must load signal files to generate auto template")
            return

        df = convert_timestamps_to_autosections(self.signal_files)
        self.load_data(df)
        msg = ("When using comments from your recordings, the settings"
               " for different gas exposures may not be appropriate for"
               " your experiment. Please refer to our table of default"
               " automated settings in the references folder of the GitHub"
               " repository and confirm values before proceeding.")
        notify_warning(msg, title="Comment Import Warning")

    def update_template_selection(self):
        """
        Update GUI widgets to reflect template selection
        """

        # Get the appropriate template based on user's choice of experimental condition
        curr_selection = self.auto_setting_combo.currentText()
        if curr_selection == 'Custom':
            # set curr data to loaded data
            self.data = self.loaded_data
        else:
            auto_dict = self.defaults[curr_selection]
            df = pd.DataFrame(auto_dict)

            # Set key row as columns
            df.loc['Key'] = df.columns

            # Set aliases as columns
            df.columns = df.loc['Alias']
            # Remove alias row
            df = df.drop(index='Alias')

            # Set the index as a new Variable column
            df.insert(0, 'Variable', df.index)

            self.data = df

        # Propagate update to tabs
        self.update_tabs()

    def edit_cell(self, table: QTableWidget, row: int, col: int):
        """
        Receive callback for editing a table cell
        Update underlying dataframe and propogate to other tables

        Parameters
        ---------
        table: widget that is being edited
        row: row number of cell being edited
        col: column number of cell being edited
        """

        # Get edited cell
        cell = table.item(row, col)

        # Get new data
        new_data = cell.text()
        
        # Get the value currently stored in the df
        prev_data = self.data.iloc[row, col]
        
        # If data changed, perform update
        if prev_data != new_data:

            # Check for duplicates in Variable column
            if col == 0:
                # Get all the current names, excluding the edited item
                curr_names = self.data['Variable'].values
                curr_names = np.delete(curr_names, row)

                new_data = avert_name_collision(new_data, curr_names)
                # If user cancelled, set to previous name
                if not new_data:
                    new_data = prev_data

            # Set new data
            self.data.iloc[row, col] = new_data

            # Update all table widgets
            self.update_tabs()

    def signals_off(self):
        """
        Disable signals for all tables
        
        This prevents editing callbacks from firing
        when performing server-side edits to widgets
        """
        for table in self.all_tables():
            table.blockSignals(True)

    def signals_on(self):
        """Enable signals for all tables"""
        for table in self.all_tables():
            table.blockSignals(False)

    def update_tabs(self):
        """
        Update tab widgets to reflect latest `data` attribute
        """
        # Block signals to prevent endless table edit callback loop
        self.signals_off()

        ################
        ## Populate table of tabs with appropriately sliced
        ## dataframes derived from selected settings template
        
        # Populate Section Characterization table
        all_sec_char_items = self.auto_labels['Section Settings']['Section Naming'].values()
        sec_char_df = self.data.loc[(self.data.index.isin(all_sec_char_items)),:]
        populate_table(sec_char_df, self.sections_char_table)

        # Populate Section Spec table
        all_sec_spec_items = self.auto_labels['Section Settings']['Experiment Settings'].values()
        sec_spec_df = self.data.loc[(self.data.index.isin(all_sec_spec_items)),:]
        populate_table(sec_spec_df, self.sections_spec_table)

        # Populate Section Verification table
        all_sec_veras_items = self.auto_labels['Section Settings']['Section Verification'].values()
        sec_veras_df = self.data.loc[(self.data.index.isin(all_sec_veras_items)),:]
        populate_table(sec_veras_df, self.sections_veras_table)

        # Populate Section Timing table
        all_sec_time_items = self.auto_labels['Section Settings']['Section Timing'].values()
        sec_time_df = self.data.loc[(self.data.index.isin(all_sec_time_items)),:]
        populate_table(sec_time_df, self.sections_time_table)
        
        # Populate Calibration Settings table
        all_cal_items = self.auto_labels['Calibration Settings']['Volume and Gas Calibrations'].values()
        cal_df = self.data.loc[(self.data.index.isin(all_cal_items)),:]
        populate_table(cal_df, self.cal_table)

        # Populate Inclusion DF table
        all_inc_items = self.auto_labels['Breath Inclusion Criteria']['Limits'].values()
        inc_df = self.data.loc[(self.data.index.isin(all_inc_items)),:]
        populate_table(inc_df, self.inc_table)

        # Populate Artifact Exclusion table
        all_sec_art_items = self.auto_labels['Breath Inclusion Criteria']['Artifact Exclusion'].values()
        sec_art_df = self.data.loc[(self.data.index.isin(all_sec_art_items)),:]
        populate_table(sec_art_df, self.sections_art_table)

        # Populate Gass Threshold Settings table
        all_gas_thresh_items = self.auto_labels['Additional Settings']['Featured Breathing'].values()
        gas_thresh_df = self.data.loc[(self.data.index.isin(all_gas_thresh_items)),:]
        populate_table(gas_thresh_df, self.gas_thresh_table)

        # Populate Time Threshold Settings table
        all_time_thresh_items = self.auto_labels['Additional Settings']['Temperature Settings'].values()
        time_thresh_df = self.data.loc[(self.data.index.isin(all_time_thresh_items)),:]
        populate_table(time_thresh_df, self.time_thresh_table)

        # Populate summary table with all data
        populate_table(self.data, self.summary_table)

        # Re-enable signals
        self.signals_on()
    
    def show_help(self):
        """Callback to display help text for the caller"""
        sbutton = self.sender()
        button_name = sbutton.objectName()
        for ref_box, ref_button_dict in self.ref_buttons.items():
            # If this is my ref_box, set the help text
            if str(button_name) in ref_button_dict:
                ref_box.setPlainText(self.ref_definitions[button_name.replace("help_","")])

    def save_as(self):
        """
        Save current data to user-selected file
        
        Display error if file in use and cannot be written
        """
        try:
            if AutoSettings.save_file(data=self.data, output_dir=self.output_dir):
                notify_info("Automated settings saved")

        except PermissionError:
            notify_info(title='File in use',
                        msg='One or more of the files you are trying to save is open in another program.')

    def load_file(self):
        """Load auto settings from user-selected file"""
        # TODO: streamline this like the other settings
        # Opens open file dialog
        filepath = AutoSettings.open_file(self.output_dir)
        # Catch cancel
        if not filepath:
            return

        data = AutoSettings.attempt_load(filepath)

        if data is not None:
            self.load_data(data)

    def load_data(self, df: pd.DataFrame):
        """
        Load a given DataFrame into the GUI widgets

        Parameters
        --------
        df: data to be loaded
        """

        first_time_loading = self.loaded_data is None
        # If we haven't loaded anything yet
        if first_time_loading:
            # Add custom option
            self.auto_setting_combo.addItem('Custom')

        # self.loaded_keys = df['Key'].values
        self.loaded_data = self.transform_loaded_data(df)

        # If 'Custom' is already selected, we need to manually call the update function
        if self.auto_setting_combo.currentText() == 'Custom':
            self.update_template_selection()

        # Otherwise, set to custom and let it automatically update
        else:
            # Set to Custom
            self.auto_setting_combo.setCurrentIndex(self.auto_setting_combo.count()-1)
            # ^this should eventually trigger update_tabs()

    def confirm(self):
        """
        Confirm user input and close window

        Current dataframe will be reformatted for external use
        """
        self.data = self.untransform_data(self.data)

        # Add the keys back in
        # self.data['Key'] = self.keys
        self.accept()

class AutoSettings(Settings):
    """Attributes and methods for handling Auto sections"""

    valid_filetypes = ['.csv']
    naming_requirements = ['auto', 'sections']
    file_chooser_message = 'Select auto sections file to edit'
    default_filename = 'autosections.csv'
    editor_class = Auto

    @classmethod
    def attempt_load(cls, filepath):
        df = pd.read_csv(filepath)
        return df

    @staticmethod
    def _save_file(filepath, df):
        df.to_csv(filepath, index=False)
        