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