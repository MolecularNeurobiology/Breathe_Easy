
"""
***
built as part of the Russell Ray Lab Breathing And Physiology Analysis Pipeline
***
Breathe Easy - an automated waveform analysis pipeline
Copyright (C) 2022  
Savannah Lusk, Andersen Chang, 
Avery Twitchell-Heyne, Shaun Fattig, 
Christopher Scott Ward, Russell Ray.
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
***

"""
from typing import List
from PyQt5.QtWidgets import QDialog, QPushButton
from PyQt5.QtCore import Qt
from ui.thinbass import Ui_Thinbass

class Thinbass(QDialog, Ui_Thinbass):
    """
    General popup window used to provide arbitrary list of user-selectable options

    Attributes
    ---------
    selected_option: attribute set upon user selection
    """
    def __init__(self, valid_options: List[str], msg: str = "Please choose one of the following sources:", title: str = "Select an option"):
        """"
        Set valid options and their callbacks for popup dialog

        Parameters
        ---------
        valid_options: list of options to set as buttons on dialog window
        msg: window message to display
        title: window title
        """
        super(Thinbass, self).__init__()
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(title)

        # Break up any long messages into multiple lines
        max_line_len = 50
        if len(msg) > max_line_len:
            msg = [msg]
            # Break the string into separate lines
            while len(msg[-1]) > max_line_len:
                breakup_str = msg[-1]
                break_idx = max_line_len
                # Search for a space to split on
                while breakup_str[break_idx] != " " and break_idx > 0:
                    break_idx -= 1
                # If no spaces to break at, then quit
                if break_idx == 0:
                    break
                msg[-1] = breakup_str[:break_idx]
                msg.append(breakup_str[break_idx + 1:])
            msg = '\n'.join(msg)
        self.label_2.setText(msg)

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
