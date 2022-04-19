
import json
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from ui.thinbass import Ui_Thinbass

class Thinbass(QDialog,Ui_Thinbass):
    """
    This class is used when the user has metadata and BASSPRO settings files as well as JSON files
        - either can be a source for building the variable list that populates the STAGG Settings subGUI.
      This dialog prompts them to decide which source they'd like to use.

    Parameters
    --------
    QDialog: class
        The Thinbass class inherits properties and methods from the QDialog class.
    Ui_Thinbass: class
        The Thinbass class inherits widgets and layouts from the Ui_Thinbass class.
    """
    def __init__(self,Plethysmography):
        """"
        Instantiate the Thinbass class in the method Plethysmography.show_variable_config().

        Parameters
        --------
        Ui_Thinbass: class
            Thinbass inherits widgets and layouts of Ui_Thinbass.
        Plethysmography: class
            Thinbass inherits Plethysmography's methods, properties, and widgets, including the Config class.
        """
        super(Thinbass, self).__init__()
        self.pleth = Plethysmography
        self.setupUi(self)
        self.setWindowTitle("Variables list sources")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.variables_source = None

    def get_value(self):
        return self.variables_source
    
    def settings(self):
        """
        Populate Config.variable_table and the comboBoxes in Config.loop_table
          with the list of variables (Plethysmography.breath_df) compiled from
          BASSPRO settings and metadata and show the STAGG settings subGUI.

        Parameters
        --------
        self.pleth.Config.variable_table: QTableWidget
            This TableWidget is defined in the Config class, displayed in the STAGG settings subGUI, and populated with rows based on the list of variables (Plethysmography.breath_df). 

        Outputs
        --------
        self.pleth.n: int
            This integer is incremented when variables are given duplicate names and appended to the existing variable's name so that the edited variable retains the user's edits.
        self.pleth.Config.variable_table: QTableWidget
            cellChanged signals are assigned to the TableWidgets cells for two slots: Plethysmography.Config.no_duplicates() and Plethysmography.Config.update_loop().
        
        Outcomes
        --------
        self.pleth.test_configuration()
            This Plethysmography method ensures that the file paths that populate the attributes required to show the STAGG settings subGUI exist and their contents are accessible, and provide feedback to the user on what is missing if anything.
        self.pleth.variable_configuration()
            This Plethysmography method populates self.buttonDict_variable with widgets and text and populates Config.variable_table with the contents of self.buttonDict_variable.
        self.pleth.Config.show()
            This Plethysmography method displays the STAGG settings subGUI.
        """
        self.variables_source = "settings"
        self.accept()

    def output(self):
        # This method was written before we developed the means to accept
        #   .RData files as STAGG input. We need to add functionality that
        #   checks to make sure that Plethysmography.stagg_list[0] is actually
        #   a JSON file and not an .RData file and nexts until it finds one.
        """
        Populate Config.variable_table and the comboBoxes in Config.loop_table
          with the list of variables (Plethysmography.breath_df) compiled from
          BASSPRO output JSON file and show the STAGG settings subGUI.

        Parameters
        --------
        self.pleth: class
            Thinbass inherits Plethysmography's methods, attributes, and widgets.
        self.pleth.Config: class
            Thinbass inherits Config methods, attributes, and widget via its Plethysmography inheritance. Config defines the STAGG settings subGUI.
        self.pleth.Config.variable_table: QTableWidget
            This TableWidget is defined in the Config class, displayed in the STAGG settings subGUI, and populated with rows based on the list of variables (Plethysmography.breath_df). 

        Outputs
        --------
        self.pleth.breath_df: list
            This Plethysmography class attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file. Thinbass.output() populates Plethysmography.breath_df using the third option.
        self.pleth.stagg_list: list
            The list of one of the following: JSON files produced by the most recent run of BASSPRO in the same session; JSON files produced by BASSPRO selected by user with a FileDialog; an .RData file produced by a previous run of STAGG and JSON files produced by BASSPRO.
        self.pleth.n: int
            This integer is incremented when variables are given duplicate names and appended to the existing variable's name so that the edited variable retains the user's edits.
        self.pleth.Config.variable_table: QTableWidget
            cellChanged signals are assigned to the TableWidgets cells for two slots: Plethysmography.Config.no_duplicates() and Plethysmography.Config.update_loop().
        
        Outcomes
        --------
        self.pleth.variable_configuration()
            This Plethysmography method populates self.buttonDict_variable with widgets and text and populates Config.variable_table with the contents of self.buttonDict_variable.
        self.pleth.Config.show()
            This Plethysmography method displays the STAGG settings subGUI.
        """
        self.variables_source = "output"
        self.accept()