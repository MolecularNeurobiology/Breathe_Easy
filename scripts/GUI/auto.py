
import os
from copy import deepcopy
import csv
import pandas as pd
from PyQt5.QtWidgets import QDialog, QMessageBox, QLabel, QVBoxLayout, qApp
from PyQt5.QtCore import Qt
from util import notify_info, Settings, populate_table
from ui.auto_form import Ui_Auto

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
    def __init__(self, defaults, auto_labels, ref_definitions, data=None, workspace_dir=""):
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
            self.help_max_VEVO2,
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
        self.loaded_data = deepcopy(data)
        self.workspace_dir = workspace_dir

        # Populate default template keys
        self.auto_setting_combo.addItems(self.defaults)

        # If we've already selected a file, load it in
        if self.loaded_data is not None:

            # Add custom option
            self.auto_setting_combo.addItem('Custom')

            # Set to current
            self.auto_setting_combo.setCurrentIndex(self.auto_setting_combo.count()-1)

        # Otherwise, set to defaults
        else:
            # First item is instruction text, set to index 1
            self.auto_setting_combo.setCurrentIndex(1)

        ## NOTE: ^^ The update will automatically trigger on index change ^^
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

        for table in self.all_tables():
            table.cellChanged.connect(lambda row, col, t=table : self.edit_cell(t, row, col))

    def all_tables(self):
        return [self.sections_char_table,
                self.sections_spec_table,
                self.cal_table,
                self.gas_thresh_table,
                self.time_thresh_table,
                self.inc_table,
                self.summary_table]

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

        ''' TODO: display loading dialog
        loading_window = QDialog(self) #flags=Qt.FramelessWindowHint)
        loading_window.setModal(True)
        layout = QVBoxLayout()
        label = QLabel("Loading...")
        layout.addWidget(label)
        loading_window.setLayout(layout)
        loading_window.show()
        '''


        # Get the appropriate template based on user's choice of experimental condition
        curr_selection = self.auto_setting_combo.currentText()
        if curr_selection == 'Custom':
            # set curr data to loaded data
            self.data = self.loaded_data
        else:
            auto_dict = self.defaults[curr_selection]
            self.data = pd.DataFrame(auto_dict).reset_index()

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
        
        # Get index_name of setting
        index_name = table.item(row, 0).text()
        
        # Find the df item that matches the index name of the edited cell
        df_match = self.data[self.data.Index == index_name]
        
        # Make sure there is only 1 match!
        if len(df_match) == 1:
            # Get dataframe index of edited item
            df_idx = df_match.index[0]
            
            # Get currently stored data value
            prev_data = df_match.iloc[0, col]
        else:
            raise RuntimeError(f"Multiple matches for index name '{index_name}'")
        
        # If data changed, perform update
        if prev_data != new_data:
            # Set new data
            self.data.iat[df_idx, col] = new_data

            # Block signals to prevent endless table edit callback loop
            self.signals_off()

            # Update all table widgets
            self.update_tabs()
            
            # Re-enable signals
            self.signals_on()

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
        # Populate table of tabs with appropriately sliced dataframes derived from selected settings template

        # Rename column names for much easier pandas usage
        #   Make column named 'index' capitalized to 'Index'
        #   having a column named 'index' collides with the built-in `index` attribute of dataframes
        #   spaces are problematic, but tolerable for now
        self.data.columns = ['Index' if col == 'index' else col for col in self.data.columns]
        
        # Populate Section Characterization table
        sec_char_df = self.data.loc[(self.data.Index.isin(self.auto_labels['Section Characterization']['Section Identification and Settings'].values())),:]
        populate_table(sec_char_df, self.sections_char_table)

        # Populate Section Spec table
        sec_spec_df = self.data.loc[(self.data.Index.isin(self.auto_labels['Section Characterization']['Interruptions'].values())),:]
        populate_table(sec_spec_df, self.sections_spec_table)
        
        # Populate Section Calibration table
        cal_df = self.data.loc[(self.data.Index.isin(self.auto_labels['Section Calibration']['Volume and Gas Calibrations'].values())),:]
        populate_table(cal_df,self.cal_table)

        # Populate Gass Threshold Settings table
        gas_thresh_df = self.data.loc[(self.data.Index.isin(self.auto_labels['Threshold Settings']['Gas Thresholds'].values())),:]
        populate_table(gas_thresh_df,self.gas_thresh_table)

        # Populate Time Threshold Settings table
        time_thresh_df = self.data.loc[(self.data.Index.isin(self.auto_labels['Threshold Settings']['Time Thresholds'].values())),:]
        populate_table(time_thresh_df,self.time_thresh_table)

        # Populate Inclusion DF table
        inc_df = self.data.loc[(self.data.Index.isin(self.auto_labels['Inclusion Criteria']['Breath Quality Standards'].values())),:]
        populate_table(inc_df,self.inc_table)

        # Populate summary table with all data
        populate_table(self.data,self.summary_table)
    
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
            # TODO: set data during run, not just summary table
            if AutoSettings.save_file(data=self.summary_table, workspace_dir=self.workspace_dir):
                notify_info("Automated settings saved")

        except PermissionError:
            QMessageBox.information(self, 'File in use', 'One or more of the files you are trying to save is open in another program.', QMessageBox.Ok)

    def load(self):
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
        # Opens open file dialog
        filepath = AutoSettings.open_file(self.workspace_dir)
        if filepath:
            first_time_loading = self.loaded_data is None
            self.loaded_data = AutoSettings.attempt_load(filepath)

            if self.loaded_data is not None:

                # If we haven't loaded anything yet
                if first_time_loading:
                    # Add custom option
                    self.auto_setting_combo.addItem('Custom')

                # If 'Custom' is already selected, we need to manually call the update function
                if self.auto_setting_combo.currentText() == 'Custom':
                    self.update_template_selection()

                # Otherwise, set to custom and let it automatically update
                else:
                    # Set to Custom
                    self.auto_setting_combo.setCurrentIndex(self.auto_setting_combo.count()-1)
                    # ^this should eventually trigger update_tabs()

class AutoSettings(Settings):

    valid_filetypes = ['.csv']
    file_chooser_message = 'Select auto sections file to edit'
    default_filename = 'autosections.csv'
    editor_class = Auto

    @staticmethod
    def _right_filename(filepath):
        file_basename = os.path.basename(filepath) 
        return "auto" in file_basename and "sections" in file_basename

    def attempt_load(filepath):
        return pd.read_csv(filepath, index_col='Key').transpose().reset_index()

    @staticmethod
    def _save_file(filepath, data):
        # TODO: make this actual data, not widget
        summary_table = data

        # Saving the dataframes holding the configuration preferences to csvs and assigning them their paths:
        with open(filepath, 'w', newline = '') as stream:
            writer = csv.writer(stream)
            header = []

            for row in range(summary_table.rowCount()):
                item = summary_table.item(row,0)
                if item.text() == "nan":
                    header.append("")
                else:
                    header.append(item.text())

            for column in range(summary_table.columnCount()):
                coldata = []

                for row in range(summary_table.rowCount()):
                    item = summary_table.item(row, column)
                    if item.text() == "nan":
                        coldata.append("")
                    else:
                        coldata.append(item.text())
                writer.writerow(coldata)

        # This is ridiculous.
        auto = pd.read_csv(filepath)
        auto['Key'] = auto['Alias']
        auto.to_csv(filepath, index=False)
        