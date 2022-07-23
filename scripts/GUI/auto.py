
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QDialog, QInputDialog
from util.tools import avert_name_collision
from util import Settings
from util.ui.dialogs import notify_info
from util.ui.tools import populate_table
from ui.auto_form import Ui_Auto

from tools.convert_timestamps_to_autosections import convert_timestamps_to_autosections

class Auto(QDialog, Ui_Auto):
    """
    The Auto class defines the the properties, attributes, and methods used by the automated BASSPRO settings subGUI.

    Parameters
    --------
    QWidget: class
        The Basic class inherits properties and methods from the QWidget class. 
    Ui_Auto: class
        The Auto class inherits widgets and layouts defined in the Ui_Auto class.
    """
    def __init__(self, defaults, auto_labels, ref_definitions, signal_files, data=None, output_dir=""):
        """
        Instantiate the Auto class.

        Parameters
        --------
        Plethysmography.bc_config: dict
            This Plethysmography class attribute is a nested dictionary loaded from basspro_config.json. It contains the default settings of multiple experimental setups for basic, automated, and manual BASSPRO settings and  the most recently saved settings for automated and basic BASSPRO settings. See the README file for more detail.
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
        self.ref_buttons: dict
            This dictionary relates the self.help_{setting} ToolButtons with the appropriate self.{tab}_reference TextBrowser.
        self.help_{setting}: QToolButton
            These buttons are assigned clicked signals and slotted for self.reference_event().
        self.auto_setting_combo: QComboBox
            A comboBox that is populated with the experimental setups for which the GUI has default automated BASSPRO settings. These experimental setups are sourced from the keys of the "default" dictionary nested in the "Auto Settings" dictionary from Plethysmography.bc_config.
        
        Outcomes
        --------
        self.choose_dict()
            This method populates the automated BASSPRO settings subGUI widgets with default values derived from Plethysmography.bc_config (basspro_config.json).
        """
        super(Auto, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Automated sections file creation")
        self.isMaximized()

        sections_reference = [
            self.help_key,
            self.help_cal_seg,
            self.help_auto_ind_include, 
            self.help_auto_ind_injection,
            self.help_startpoint,
            self.help_midpoint,
            self.help_endpoint
            ]

        cal_reference = [
            self.help_auto_ind_cal,
            self.help_auto_ind_gas_cal,
            self.help_cal_co2,
            self.help_cal_o2
            ]

        thresh_reference = [
            self.help_min_co2,
            self.help_max_co2,
            self.help_min_o2,
            self.help_max_calibrated_TV,
            self.help_maxVEVO2,
            self.help_max_o2,
            self.help_within_start,
            self.help_within_end,
            self.help_after_start,
            self.help_before_end
            ]

        inc_reference = [
            self.help_min_TT,
            self.help_max_TT,
            self.help_max_dvtv,
            self.help_X,
            self.help_max_pX,
            self.help_vol_mov_avg_drift,
            self.help_min_tv,
            self.help_min_bout,
            self.help_include_apnea,
            self.help_include_sigh,
            self.help_include_high_chamber_temp
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
                ref_button.clicked.connect(self.reference_event)

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


    def set_new_header(self, col_idx):
        headers = self.data.columns.values
        old_header = headers[col_idx]
        new_name, ok = QInputDialog.getText(self, "Rename Column", f'Change "{old_header}" to:')
        if ok and new_name != "":
            headers[col_idx] = new_name
            self.data.columns = pd.Index(headers, name='Alias')
            self.update_tabs()

    def untransform_data(self, df):
        """
        Re-transpose data back to original format for
        writing to file
        """
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
        
        # Remove Key column (we will use Aliases)
        # df = df.drop(columns='Key')

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
        return [self.sections_char_table,
                self.sections_spec_table,
                self.cal_table,
                self.gas_thresh_table,
                self.time_thresh_table,
                self.inc_table,
                self.summary_table]

    def timestamps_from_signals(self):
        if not self.signal_files:
            notify_info("Must load signal files to generate auto template")
            return

        df = convert_timestamps_to_autosections(self.signal_files)
        self.load_data(df)
        msg = "Please see documentation for help with"
        msg += "\nsetting values appropriately."
        notify_info(msg)

    def update_template_selection(self):
        """
        This method populates the automated BASSPRO settings
          subGUI widgets with default values derived from 
          Plethysmography.bc_config (basspro_config.json).

        Parameters
        --------
        self.auto_setting_combo: QComboBox
            A comboBox that is populated with the experimental setups for which the GUI has default automated BASSPRO settings. These experimental setups are sourced from the keys of the "default" dictionary nested in the "Auto Settings" dictionary from Plethysmography.bc_config.

        Outputs
        --------
        self.auto_dict: dict
            This attribute stores the nested dictionary in Plethysmography.bc_config that contains the default automated BASSPRO settings of multiple experimental setups.
        self.data: Dataframe
            This attribute stores the dataframe converted from self.auto_dict.

        Outcomes
        --------
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

        self.update_tabs()

    def edit_cell(self, table, row, col):
        """
        Receive callback for editing a table cell
        Update underlying dataframe and propogate to other tables
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
        for table in self.all_tables():
            table.blockSignals(True)

    def signals_on(self):
        for table in self.all_tables():
            table.blockSignals(False)

    def update_tabs(self):
        """
        This method populates the automated BASSPRO settings subGUI widgets with default values of the experimental setup derived from Plethysmography.bc_config (basspro_config.json).
        
        Parameters
        --------
        self.pleth.gui_config: dict
            This attribute is a nested dictionary loaded from gui_config.json. It contains paths to the BASSPRO and STAGG modules and the local Rscript.exe file, the fields of the database accessed when building a metadata file, and settings labels used to organize the populating of the TableWidgets in the BASSPRO settings subGUIs. See the README file for more detail.
        self.data: Dataframe
            This attribute stores the dataframe converted from self.auto_dict.
        self.{division}_table: QTableWidget
            These TableWidgets display the automated BASSPRO settings is in the appropriate TableWidgets over multiple tabs.
        self.summary_table: QTableWidget
            The TableWidget displays the automated BASSPRO settings in one table on the fifth tab.
        
        Outcomes
        --------
        populate_table(frame,table)
            This method populates the self.{division}_table widgets with the appropriate portions of the self.data dataframe based on the relationship of particular rows to particular divisions as defined in the "Settings Names" dictionary within self.pleth.gui_config.
        """
        # Block signals to prevent endless table edit callback loop
        self.signals_off()

        # Populate table of tabs with appropriately sliced dataframes derived from selected settings template
        
        # Populate Section Characterization table
        all_sec_char_items = self.auto_labels['Section Characterization']['Section Identification and Settings'].values()
        sec_char_df = self.data.loc[(self.data.index.isin(all_sec_char_items)),:]
        populate_table(sec_char_df, self.sections_char_table)

        # Populate Section Spec table
        all_sec_spec_items = self.auto_labels['Section Characterization']['Interruptions'].values()
        sec_spec_df = self.data.loc[(self.data.index.isin(all_sec_spec_items)),:]
        populate_table(sec_spec_df, self.sections_spec_table)
        
        # Populate Section Calibration table
        all_cal_items = self.auto_labels['Section Calibration']['Volume and Gas Calibrations'].values()
        cal_df = self.data.loc[(self.data.index.isin(all_cal_items)),:]
        populate_table(cal_df,self.cal_table)

        # Populate Gass Threshold Settings table
        all_gas_thresh_items = self.auto_labels['Threshold Settings']['Gas Thresholds'].values()
        gas_thresh_df = self.data.loc[(self.data.index.isin(all_gas_thresh_items)),:]
        populate_table(gas_thresh_df,self.gas_thresh_table)

        # Populate Time Threshold Settings table
        all_time_thresh_items = self.auto_labels['Threshold Settings']['Time Thresholds'].values()
        time_thresh_df = self.data.loc[(self.data.index.isin(all_time_thresh_items)),:]
        populate_table(time_thresh_df,self.time_thresh_table)

        # Populate Inclusion DF table
        all_inc_items = self.auto_labels['Inclusion Criteria']['Breath Quality Standards'].values()
        inc_df = self.data.loc[(self.data.index.isin(all_inc_items)),:]
        populate_table(inc_df,self.inc_table)

        # Populate summary table with all data
        populate_table(self.data,self.summary_table)

        # Re-enable signals
        self.signals_on()
    
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
        for ref_box, ref_button_dict in self.ref_buttons.items():
            # If this is my ref_box, set the help text
            if str(buttoned) in ref_button_dict:
                ref_box.setPlainText(self.ref_definitions[buttoned.replace("help_","")])

    def save_as(self):
        """
        Write the contents of the self.summary_table TableWidget to .csv file as indicated in the file path self.pleth.auto_sections, call self.pleth.update_breath_df(), and add self.pleth.auto_sections to self.pleth.sections_list (ListWidget) for display in the main GUI. 

        Parameters
        --------
        self.path: str
            This attribute stores the file path selected by the user to which the .csv file of the automated BASSPRO settings wll be saved.
        self.pleth.breath_df: list
            This Plethysmography class attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        self.summary_table: QTableWidget
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
        try:
            if AutoSettings.save_file(data=self.data, output_dir=self.output_dir):
                notify_info("Automated settings saved")

        except PermissionError:
            notify_info(title='File in use',
                        msg='One or more of the files you are trying to save is open in another program.')

    def load_file(self):
        # TODO: streamline this like the other settings
        # Opens open file dialog
        filepath = AutoSettings.open_file(self.output_dir)
        # Catch cancel
        if not filepath:
            return

        data = AutoSettings.attempt_load(filepath)

        if data is not None:
            self.load_data(data)

    def load_data(self, df):
        """
        Prompt the user to indicate the location of a previously made file - either .csv, .xlsx, or .json formatted file - detailing the basic BASSPRO settings of a previous run, populate self.basic_df with a dataframe from that file, call populate_table(), and warn the user if they chose files in formats that are not accepted and ask if they would like to select a different file.

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
        self.summary_table: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        reply: QMessageBox
            This specialized dialog communicates information to the user.

        Outputs
        --------
        self.basic_df: Dataframe
            This attribute stores a dataframe derived from the .csv file indicated by the user-selected file path (Plethysmography.basicap).
        self.summary_table: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        
        Outcomes
        --------
        self.update_tabs()
            This method populates the automated BASSPRO settings subGUI widgets with default values of the experimental setup derived from Plethysmography.bc_config (basspro_config.json).
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
            # for table in self.all_tables():
            #     table.blockSignals(True)
            self.update_template_selection()
            # for table in self.all_tables():
            #     table.blockSignals(False)

        # Otherwise, set to custom and let it automatically update
        else:
            # Set to Custom
            self.auto_setting_combo.setCurrentIndex(self.auto_setting_combo.count()-1)
            # ^this should eventually trigger update_tabs()

    def confirm(self):
        self.data = self.untransform_data(self.data)

        # Add the keys back in
        # self.data['Key'] = self.keys
        self.accept()

class AutoSettings(Settings):

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
        