
import json
from PyQt5.QtWidgets import QDialog, QPushButton
from PyQt5.QtCore import Qt
from config import ConfigSettings
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
    def __init__(self, valid_options):
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
        self.setupUi(self)
        self.setWindowTitle("Multiple data sources")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.selected_option = None

        assert len(valid_options) <= 3, "Max 3 options for Thinbass dialog"

        for i, option in enumerate(valid_options):
            new_button = QPushButton(option)
            new_button.clicked.connect(lambda _checked, selection=option : self.make_selection(selection))
            self.horizontalLayout_4.insertWidget(i, new_button)

    def make_selection(self, selection):
        self.selected_option = selection
        self.accept()

    def get_value(self):
        return self.selected_option