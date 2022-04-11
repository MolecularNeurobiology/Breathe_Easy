
import os
import json
from pathlib import Path
import pandas as pd
from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QFileDialog, QMessageBox
from PyQt5.QtCore import QObject
from ui.basic_form import Ui_Basic
from PyQt5.QtCore import Qt
from util import choose_save_location, notify_error, notify_info

class Basic(QWidget, Ui_Basic):
    """
    The Basic class defines the the properties, attributes, and methods used by the basic BASSPRO settings subGUI.

    Parameters
    --------
    QWidget: class
        The Basic class inherits properties and methods from the QWidget class. 
    Ui_Basic: class
        The Basic class inherits widgets and layouts defined in the Ui_Basic class.
    """
    def __init__(self, Plethysmography):
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
        self.setup_tabs()
            This method populates the basic BASSPRO settings subGUI widgets with default values derived from Plethysmography.bc_config (breathcaller_config.json).
        """
        super(Basic, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Basic BASSPRO settings")
        self.pleth = Plethysmography
        self.isMaximized()
        self.setup_variables()
        self.setup_tabs()
        
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
        self.basic_dict: dict
            This attribute stores the nested dictionary in Plethysmography.bc_config that contains the default basic BASSPRO settings.
        self.widgy: dict
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
        print("basic.setup_variables()")
        self.basic_dict = self.pleth.bc_config['Dictionaries']['AP']['default']
        self.widgy = {self.basic_reference:[self.help_minTI,self.help_minPIF,self.help_minPEF,self.help_TTwin,self.help_SIGHwin,self.help_minAplTT,self.help_minApsTT],
        self.rig_reference:[self.help_ConvertTemp,self.help_ConvertCO2,self.help_ConvertO2,self.help_Flowrate,self.help_Roto_x,self.help_Roto_y,self.help_chamber_temp_cutoffs,self.help_chamber_temperature_units,self.help_chamber_temperature_default,self.help_chamber_temperature_trim_size,self.help_chamber_temperature_narrow_fix],
        self.crude_reference: [self.help_per500win,self.help_perX,self.help_maxPer500,self.help_maximum_DVTV,self.help_apply_smoothing_filter,self.help_maxTV,self.help_maxVEVO2]}

        self.lineEdits = {self.lineEdit_minimum_TI: "minimum_TI", 
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
        
        self.resets = [self.reset_minimum_TI,
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

        for v in self.widgy.values():
            for vv in v:
                vv.clicked.connect(self.reference_event)
        
        for r in self.resets:
            r.clicked.connect(self.reset_event)
        
        for l in self.lineEdits:
            l.textChanged.connect(self.update_table_event)

    def setup_tabs(self):
        """
        Populate widgets in each tab with appropriate values for the default basic BASSPRO settings stored in self.basic_dict.

        Parameters
        --------
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.
        self.basic_dict: dict
            This attribute stores the nested dictionary in Plethysmography.bc_config that contains the default basic BASSPRO settings.
        Plethysmography.basicap: str
            The path of the user-selected basic BASSPRO settings file.
        self.view_tab: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        
        Outputs
        --------
        self.lineEdit_{setting}: QLineEdit
            The LineEdits' values are iteratively set as the values of the corresponding keys in self.basic_dict.
        self.basic_df: Dataframe
            This attribute stores a dataframe derived either from self.basic_dict or from the .csv file indicated by the user-selected file path (self.basicap).
        
        Outcomes
        --------
        self.populate_table()
            This method populates self.view_tab (TableWidget) with the self.basic_df dataframe.
        """
        print("basic.setup_tabs()")
        # Populate lineEdit widgets with default basic parameter values from breathcaller configuration file:
        for widget in self.lineEdits:
            widget.setText(str(self.basic_dict[self.lineEdits[widget]]))
        if self.pleth.basicap:
            if Path(self.pleth.basicap).exists():
                self.basic_df = pd.read_csv(self.pleth.basicap)
        else:
            self.basic_df = pd.DataFrame.from_dict(self.basic_dict,orient='index').reset_index()
            self.basic_df.columns = ['Parameters','Settings']
            # Populate table of summary tab:
        self.populate_table(self.basic_df,self.view_tab)
    
    def reference_event(self):
        """
        Respond to the signal emitted by the self.help_{setting} ToolButton clicked by the user by calling self.populate_reference(self.sender.objectName()) to populate the appropriate TextBrowser with the definition, description, and default value of corresponding setting.
        """
        sbutton = self.sender()
        self.populate_reference(sbutton.objectName())
    
    def reset_event(self):
        """
        Respond to the signal emitted by the self.reset_{setting} ToolButton clicked by the user by calling self.reset_parameters(self.sender.objectName()) to revert the LineEdit value to the default value in the default basic BASSPRO settings dictionary (self.basic_dict).
        """
        sbutton = self.sender()
        self.reset_parameter(sbutton.objectName())
    
    def update_table_event(self):
        """
        Respond to the signal emitted by the self.lineEdit_{setting} LineEdit edited by the user by calling self.update_table(self.sender.objectName()) to update self.view_tab to reflect changes made to LineEdits in other tabs.
        """
        sbutton = self.sender()
        self.update_table(sbutton.objectName())

    def populate_reference(self,buttoned):
        """
        Populate the appropriate reference TextBrowser with the definition, description, and default values of the appropriate setting as indicated by the suffix of the ToolButton's objectName(), e.g. "help_{setting}" from Plethysmography.rc_config (reference_config.json).
        """
        for k,v in self.widgy.items():
            for vv in v:
                if vv.objectName() == str(buttoned):
                    k.setPlainText(self.pleth.rc_config['References']['Definitions'][buttoned.replace("help_","")])
                    k.setOpenExternalLinks(True)
   
    def populate_table(self,frame,table):
        """
        Populate self.view_tab (TableWidget) with the self.basic_df dataframe.

        Parameters
        --------
        frame: Dataframe
            This variable refers to the self.basic_df dataframe.
        table: QTableWidget
            This variable refers to self.view_tab (TableWidget).

        Outputs
        --------
        self.view_tab: QTableWidget
            The TableWidget is populated by the contents of the self.basic_df dataframe, assigned cellChanged signals slotted to self.update_tabs, and cell dimensions adjusted to accommodate the text.
        """
        print("basic.populate_table()")
        # Populate tablewidgets with views of uploaded csv. Currently editable.
        table.setColumnCount(len(frame.columns))
        table.setRowCount(len(frame))
        for col in range(table.columnCount()):
            for row in range(table.rowCount()):
                table.setItem(row, col, QTableWidgetItem(str(frame.iloc[row,col])))
                table.item(row,0).setFlags(Qt.ItemIsEditable)
        table.setHorizontalHeaderLabels(frame.columns)
        self.view_tab.cellChanged.connect(self.update_tabs)
        self.view_tab.resizeColumnsToContents()
        self.view_tab.resizeRowsToContents()

    def update_table(self, donor: QObject.objectName):
        """
        Update self.view_tab (TableWidget) to reflect changes to LineEdits.

        Parameters
        --------
        donor: QObject.objectName
            This variable is the objectName of the LineEdit that emitted the signal self.update_table_event that called this method. Its suffix is used to identify the appropriate cell in self.view_tab (TableWidget).
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.
        self.view_tab: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.

        Outputs
        --------
        self.view_tab: QTableWidget
            The cell that contains the value of the setting that was updated by the user editing a LineEdit is updated to reflect the edit.
        """
        print("basic.update_table()")
        # The first loop grabs the widget with the text we need because donor is passed to this method as a QObject.objectName(), not the actual object.
        for l in self.lineEdits:
            if donor == l.objectName():
                d = l
        for row in range(self.view_tab.rowCount()):
            if self.view_tab.item(row,0).text() == donor.replace("lineEdit_",""):
                self.view_tab.item(row,1).setText(d.text())
        
    def update_tabs(self):
        """
        Update the LineEdits to reflect changes to self.view_tab (TableWidget).

        Parameters
        --------
        self.view_tab: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.
        
        Outputs
        --------
        self.lineEdit_{settings}: QLineEdit
            The LineEdit whose objectName suffix matches the setting that was edited by the user in self.view_tab (TableWidget) is updated to reflect the edit.
        """
        print("basic.update_tabs()")
        for row in range(self.view_tab.rowCount()):
            for l in self.lineEdits:
                if self.view_tab.item(row,0).text() == l.objectName().replace("lineEdit_",""):
                    l.setText(self.view_tab.item(row,1).text())

    def reset_parameter(self,butts):
        """
        Revert the settings to its corresponding default value in the basic BASSPRO settings stored in the self.basic_dict.

        Parameters
        --------
        self.lineEdits: dict
            This dictionary relates the self.lineEdit_{setting} widgets with the string of the setting name.
        self.basic_df: Dataframe
            This attribute stores a dataframe derived either from self.basic_dict or from the .csv file indicated by the user-selected file path (self.basicap).

        Outputs
        --------
        self.lineEdit_{settings}: QLineEdit
            The LineEdit whose objectName suffix matches the setting that was edited by the user in self.view_tab (TableWidget) is updated to reflect the edit.
        """
        print("basic.reset_parameter()")
        for widget in self.lineEdits:
            if widget.objectName().replace("lineEdit_","") == str(butts).replace("reset_",""):
                widget.setText(str(self.basic_dict[self.lineEdits[widget]]))

    def get_parameter(self):
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
        self.basic_df: Dataframe
            This attribute stores a dataframe made from the "current" dictionary that was updated with the values of the corresponding LineEdits.
        """
        # Read lineEdit widgets
        for k,v in self.lineEdits.items():
            # Update current dictionary
            self.pleth.bc_config['Dictionaries']['AP']['current'].update({v:k.text()})

        # Update the dataframe with new dict values
        self.basic_df = pd.DataFrame.from_dict(self.pleth.bc_config['Dictionaries']['AP']['current'], orient='index').reset_index()
        self.basic_df.columns = ['Parameter','Setting']

    def save_as(self):
        """
        """
        save_path = choose_save_location(default_filename="basics.csv")
        # Cancelled - No path chosen
        if not save_path:
            return
        self.save(save_path)

    def save(self, save_path=None):
        """
        Write self.basic_df dataframe to a .csv file, dump the nested dictionary stored in Plethysmography.bc_config to breathcaller_config.json to save changes made to the "current" dictionary in the basic BASSPRO settings dictionary in Plethysmography.bc_config, and add the file path self.basicap to the ListWidget self.sections_list for display in the main GUI.

        Parameters
        --------
        self.path: str
            This attribute stores the file path automatically generated based on the user-selected output directory.
        Plethysmography.basicap: str
            This Plethysmography class attribute stores the file path of the .csv file that the basic BASSPRO settings are saved to.
        self.basic_df: Dataframe
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
        # Get save path if not passed in
        if not save_path:

            # Try to create path with workspace_dir
            if self.pleth.workspace_dir:
                save_path = os.path.join(self.pleth.workspace_dir, "basics.csv")

            # Try asking user
            else:
                save_path = choose_save_location(default_filename="basics.csv")
                # Cancelled - No path chosen
                if not save_path:
                    return

        if not os.path.exists(os.path.split(save_path)[0]):
            notify_error(f"Bad save path: {save_path}")

        # Update parameters
        self.get_parameter()

        self.pleth.basicap = save_path

        # Saving the dataframes holding the configuration preferences to csvs and assigning them their paths:
        self.basic_df.set_index('Parameter').to_csv(self.pleth.basicap)
    
        with open(f'{Path(__file__).parent}/breathcaller_config.json','w') as bconfig_file:
            json.dump(self.pleth.bc_config,bconfig_file)
        
        notify_info("Basic settings saved")
        self.pleth.hangar.append("BASSPRO basic settings file saved.")

    def load_basic_file(self):
        """
        Prompt the user to indicate the location of a previously made file - either .csv, .xlsx, or .json formatted file - detailing the basic BASSPRO settings of a previous run, populate self.basic_df with a dataframe from that file, call self.populate_table(), and warn the user if they chose files in formats that are not accepted and ask if they would like to select a different file.

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
        self.view_tab: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        reply: QMessageBox
            This specialized dialog communicates information to the user.

        Outputs
        --------
        self.basic_df: Dataframe
            This attribute stores a dataframe derived from the .csv file indicated by the user-selected file path (Plethysmography.basicap).
        self.view_tab: QTableWidget
            The TableWidget displays the dataframe compiling all the basic BASSPRO settings on the fourth tab. Its contents are editable.
        
        Outcomes
        --------
        self.populate_table()
            Populate self.view_tab (TableWidget) with the self.basic_df dataframe.
        self.load_basic_file()
            Prompt the user to indicate the location of a previously made file - either .csv, .xlsx, or .json formatted file - detailing the basic BASSPRO settings of a previous run, populate self.basic_df with a dataframe from that file, call self.populate_table(), and warn the user if they chose files in formats that are not accepted and ask if they would like to select a different file.
        """
        print("basic.load_basic_file()")
        # Opens open file dialog
        yes = 0
        file = QFileDialog.getOpenFileName(self, 'Select breathcaller configuration file to edit basic parameters:', str(self.pleth.mothership))
        if os.path.exists(file[0]):
            try:
                if Path(file[0]).suffix == ".json":
                    with open(file[0]) as config_file:
                        basic_json = json.load(config_file)
                    self.basic_df = pd.DataFrame.from_dict(basic_json['Dictionaries']['AP']['current'],orient='index').reset_index()
                    self.basic_df.columns = ['Parameter','Setting']
                    yes = 1
                elif Path(file[0]).suffix == ".csv":
                    self.basic_df = pd.read_csv(file[0])
                    yes = 1
                elif Path(file[0]).suffix == ".xlsx":
                    self.basic_df = pd.read_excel(file[0])
                    yes = 1
                if yes == 1:
                    self.populate_table(self.basic_df,self.view_tab)
            except Exception as e:
                reply = QMessageBox.information(self, 'Incorrect file format', 'The selected file is not in the correct format. Only .csv, .xlsx, or .JSON files are accepted.\nWould you like to select a different file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                if reply == QMessageBox.Ok:
                    self.load_basic_file()
        