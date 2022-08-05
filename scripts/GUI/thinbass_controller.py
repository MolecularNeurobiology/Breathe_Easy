
from typing import List
from PyQt5.QtWidgets import QDialog, QPushButton
from PyQt5.QtCore import Qt
from ui.thinbass import Ui_Thinbass

class Thinbass(QDialog,Ui_Thinbass):
    """
    General popup window used to provide arbitrary list of user-selectable options

    Attributes
    ---------
    selected_option: attribute set upon user selection
    """
    def __init__(self, valid_options: List[str]):
        """"
        Set valid options and their callbacks for popup dialog

        Parameters
        --------
        valid_options: list of options to set as buttons on dialog window
        """
        super(Thinbass, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Select an option")
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.selected_option = None

        assert len(valid_options) <= 3, "Max 3 options for Thinbass dialog"

        # Set callbacks for all options
        for i, option in enumerate(valid_options):
            new_button = QPushButton(option)
            new_button.clicked.connect(lambda _checked, selection=option : self.make_selection(selection))
            self.horizontalLayout_4.insertWidget(i, new_button)

    def make_selection(self, selection):
        self.selected_option = selection
        self.accept()

    def get_value(self):
        """Used by caller to retrieve the selected option"""
        return self.selected_option