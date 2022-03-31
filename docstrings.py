# region classes

class AlignDelegate(QStyledItemDelegate):
    """
    This class assigns delegates to Config.variable_table and Config.loop_table TableWidgets and and centers the delegate items.

    Parameters
    --------
    QStyledItemDelegate: class
        The AlignDelegate class inherits properties and methods from the QStyledItemDelegate class.
    """
class Thinbass(QDialog,Ui_Thinbass):
    """
    This class is used when the user has metadata and BASSPRO settings files as well as JSON files - either can be a source for building the variable list that populates the STAGG Settings subGUI. This dialog prompts them to decide which source they'd like to use.

    Parameters
    --------
    QDialog: class
        The Thinbass class inherits properties and methods from the QDialog class.
    Ui_Thinbass: class
        The Thinbass class inherits widgets and layouts from the Ui_Thinbass class.
    """
class Thumbass(QDialog, Ui_Thumbass):
    """
    This class defines a simple dialog that displays information to the user.

    Parameters
    --------
    QDialog: class
        The Thumbass class inherits properties and methods from the QDialog class.
    Ui_Thumbass: class
        The Thumbass class inherits widgets and layouts from the Ui_Thumbass class.
    """
class Thorbass(QDialog, Ui_Thorbass):
    """
    This class defines a specialized dialog that prompts the user to provide the necessary input for the function they are trying to use. It's instantiated by Manual.manual_merge() or Plethysmography.show_variable_config().

    Parameters
    --------
    QDialog: class
        The Thorbass class inherits properties and methods from the QDialog class.
    Ui_Thorbass: class
        The Thorbass class inherits widgets and layouts from the Ui_Thorbass class.
    """
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
class Auto(QWidget, Ui_Auto):
    """
    The Auto class defines the the properties, attributes, and methods used by the automated BASSPRO settings subGUI.

    Parameters
    --------
    QWidget: class
        The Basic class inherits properties and methods from the QWidget class. 
    Ui_Auto: class
        The Auto class inherits widgets and layouts defined in the Ui_Auto class.
    """
class Manual(QWidget, Ui_Manual):
    """
    The Manual class defines the properties, attributes, and methods used by the manual BASSPRO settings subGUI.

    Parameters
    --------
    QWidget: class
        The Manual class inherits properties and methods from the QWidget class.
    Ui_Manual: class
        The Manual class inherits widgets and layouts defined in the Ui_Manual class.
    """
class CheckableComboBox(QComboBox):
    # source: https://gis.stackexchange.com/questions/350148/qcombobox-multiple-selection-pyqt5
    """
    The CheckableComboBox class populates a comboBox with checkable items (checkboxes).
    """
class Custom(QWidget, Ui_Custom):
    """
    The Custom class inherits widgets and layouts of Ui_Custom and defines the subGUI within the STAGG settings subGUI that allows users to customize the settings for each dependent variable.

    Parameters
    --------
    QWidget: class
        The Custom class inherits properties and methods from the QWidget class. 
    Ui_Custom: class
        The Custom class inherits widgets and layouts defined in the Ui_Custom class.
    """
class Config(QWidget, Ui_Config):
    """
    The Config class inherits widgets and layouts of Ui_Config and defines the STAGG settings subGUI that allows users to define the STAGG settings.
    
    Parameters
    --------
    QWidget: class
        The Config class inherits properties and methods from the QWidget class.
    Ui_Config: class
        The Config class inherits widgets and layouts defined in the Ui_Config class.
    """
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
#endregion

#region Methods
"""
The Plethysmography class inherits widgets and layouts of Ui_Plethysmography and defines the main GUI.

    Parameters
    --------
    QMainWindow: class
        The Plethysmography class inherits properties and methods from the QMainWindow class.
    Ui_Plethysmography: class
        The Plethysmography class inherits widgets and layouts defined in the Ui_Plethysmography class.
    """
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
        self.signals: list
            The list of file paths of the user-selected .txt signal files that are analyzed by BASSPRO. Required input for BASSPRO.
        self.mothership: str
            The path to the user-selected directory for all output. Required input for BASSPRO and STAGG.
        self.stagg_list: list
            The list of one of the following: JSON files produced by the most recent run of BASSPRO in the same session; JSON files produced by BASSPRO selected by user with a FileDialog; an .RData file produced by a previous run of STAGG; an .RData file produced by a previous run of STAGG and JSON files produced by BASSPRO.
        self.output_dir_r: str
            The path to the STAGG output directory. Required input for STAGG.
        self.input_dir_r: str
            The path to the STAGG input directory. Derived from os.path.dirname() of the JSON  output files from BASSPRO. Required input for STAGG.
        self.variable_config: str
            The path to thef variable_config.csv file. Required input for STAGG.
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
        sef.py_output_folder: str
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
            """
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
        
        Ensure the user-selected metadata is the correct file format, contains metadata for the signal files that were selected, and is named correctly. This method depends on the presence of a column named MUID and a column named PlyUID in the metadata and depends on the file being named as either MUID or MUID_PlyUID.
        """
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
    def show_variable_config(self):
        # Shouldn't I be using self.get_bp_reqs() in here?
        """
        Ensure that there is a source of variables to populate Config.variable_table with and run test_configuration() to ensure that those sources are viable, run self.variable_configuration() to populate Config.variable_table (TableWidget), and either show the STAGG settings subGUI or show a Thorbass dialog to guide the user through providing the required input if there is no input.

        Parameters
        --------
        self.buttonDict_variable: dict
            This attribute is a nested dictionary used to populate and save the text and RadioButton states of Config.variable_table (TableWidget) in the Config subGUI.
        Config.configs: dict
            This attribute is populated with a nested dictionary in which each item contains a dictionary unique to each settings file - variable_config.csv, graph_config.csv, and other_config.csv. Each dictionary has the following key, value items: "variable", the Plethysmography class attribute that refers to the file path to the settings file; "path", the string file path to the settings file; "frame", the Config class attribute that refers to the dataframe; "df", the dataframe.
        self.stagg_list: list
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
        """
def setup_table_config(self):
        """
        Assign delegates to self.variable_table and self.loop_table, set self.pleth.buttonDict_variable as an empty dictionary, repopulate it with text and widgets based on items listed in self.pleth.breath_df (list), assign the RadioButton widgets of each row to a ButtonGroup, populate self.variable_table (TableWidget) with the contents of self.pleth.buttonDict_variable, assign toggled signals slotted for self.add_combos() to the RadioButtons in self.pleth.buttonDict_variable that correspond to those in the "Independent" and "Covariate" columns of the TableWidget, and adjust the size of the cells of self.variable_table.

        Parameters
        --------
        AlignDelegate: class
            This class assigns delegates to Config.variable_table and Config.loop_table TableWidgets and and centers the delegate items.
        self.variable_table: QTableWidget
            This TableWidget is defined in the Config class, displayed in the STAGG settings subGUI, and populated with rows based on the list of variables (Plethysmography.breath_df).
        self.loop_table: QTableWidget
            This TableWidget is populated with the settings for additional models either via widgets or loading previously made other_config.csv with previous STAGG run's settings for additional models.
        self.pleth.breath_df: list
            This Plethysmography class attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        self.pleth.buttonDict_variable: dict
            This Plethysmography class attribute is a nested dictionary used to populate and save the text and RadioButton states of Config.variable_table (TableWidget) in the Config subGUI.
        
        Outputs
        --------
        self.variable_table: QTableWidget
            This TableWidget is populated with text and widgets stored in self.pleth.buttonDict_variable (dict).
        self.loop_table: QTableWidget
            This TableWidget is populated with one row. (why?)
        self.pleth.buttonDict_variable: dict
            This Plethysmography class attribute is set as an empty dictionary and repopulated with text and widgets based on items in the list self.pleth.breath_df.
        """
    def show_loops(self,table,r):
        """
        Set self.pleth.loop_menu as an empty dictionary, iteratively populate self.pleth.loop_menu with QLineEdits, QComboBoxes, and CheckableComboBox, populate the ComboBoxes with items from self.deps, populate self.loop_table with the contents of self.pleth.loop_menu, and adjust the cell sizes of self.loop_table.

        Parameters
        --------
        self.pleth.loop_menu: dict
            This Plethysmography class attribute is a nested dictionary used to populate and save the text, CheckBox, ComboBox, and CheckableComboBox states of Config.loop_table (TableWidget) in the Config subGUI.
        self.role_list: list
            This attribute is a list of strings that are the headers of the self.loop_table.
        self.deps:
            This attribute is a Series of the variables, specifically the "Alias" column of dataframe self.clades derived from self.variable_table.
        table: QTableWidget
            This argument refers to self.loop_table TableWidget - previously there was another loop table, so that's why we have the "table" argument instead of just used the attribute to refer to the widget.
        r: int
            This argument passes the number of rows self.loop_table should have.
        
        Outputs
        --------
        self.pleth.loop_menu: dict
            This Plethysmography class attribute is set as an empty dictionary and repopulated with widgets with a row count of "r". 
        self.loop_table: QTableWidget
            This TableWidget is populated with the contents of self.pleth.loop_menu.
        """    

def mothership_dir(self):
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
        self.mothership: str
            This attribute is set as the file path to the user-selected output directory.
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