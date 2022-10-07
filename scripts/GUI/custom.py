"""
the custom class, used to help customize settings for each
dependent variable for a future STAGG run

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
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QCheckBox
from PyQt5.QtCore import Qt
from checkable_combo_box import CheckableComboBox
from util.ui.tools import read_widget
from ui.custom_config import Ui_Custom

class Custom(QDialog, Ui_Custom):
    """
    Defines the subGUI within the STAGG settings subGUI that allows users
    to customize the settings for each dependent variable.

    Attributes
    ---------
    data (dict): data in the GUI represented as a dictionary
    """
    def __init__(self, custom_data: dict, dependent_vars: List[str]):
        """
        Instantiate the Custom class.

        Parameters
        ---------
        custom_data: initial data with which to populate the GUI
        dependent_vars:
            all the dependent variables are available for settings customization
        """
        super(Custom, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Custom graph settings configuration")
        self.isMaximized()
        
        # Set initial data
        if custom_data is None:
            self.data = None
        else:
            self.data = custom_data.copy()

        self.populate_table(custom_data, dependent_vars)
        self.adjustSize()

    def populate_table(self, custom_data: dict, dependent_vars: List[str]):
        """
        Populate the window with an initial set of data and a list of available variables

        Parameters
        ---------
        custom_data: initial data with which to populate the GUI
        dependent_vars:
            all the dependent variables are available for settings customization
        """
        # Populate tablewidgets with dictionary holding widgets. 
        table = self.custom_table
        table.setRowCount(len(dependent_vars))

        default_vals = {
            'ymin': "",
            'ymax': "",
            'Poincare': 0,
            'Transformation': ""
        }

        for row, var_name in enumerate(dependent_vars):
            vals = custom_data[custom_data.Alias == var_name]
            if len(vals):
                vals = vals.to_dict('records')[0]
            else:
                # No existing data, set to default
                vals = default_vals

            # The first three columns are: the name of the dependent variables
            #   selected, and empty strings for ymin and ymax
            # alias
            alias_item = QTableWidgetItem(var_name)
            alias_item.setFlags(alias_item.flags() ^ Qt.ItemIsEditable)
            table.setItem(row, 0, alias_item)

            # ymin
            table.setItem(row, 1, QTableWidgetItem(str(vals['ymin'])))

            # ymax
            table.setItem(row, 2, QTableWidgetItem(str(vals['ymax'])))

            # Creating the radio buttons that will populate the cells in each row:
            # Poincare
            poincare_checkbox = QCheckBox()
            poincare_checkbox.setChecked(vals['Poincare'] == 1)
            table.setCellWidget(row, 4, poincare_checkbox)

            # Creating the combo boxes that will populate the cells in each row:
            transformation_combo = CheckableComboBox()
            transformation_combo.addItems(["raw","log10","ln","sqrt"])
            transformation_combo.loadCustom(vals['Transformation'])
            transformation_combo.updateText()
            table.setCellWidget(row, 3, transformation_combo)

        table.resizeColumnsToContents()
        table.resizeRowsToContents()

    def confirm(self):
        """
        Confirm user input, collect the user-selections
        into a dictionary, and close the window

        Attributes-Out
        -------------
        data: this attribute is set for the caller's retrieval of confirmed state
        """
        custom_data = {}
        # Loop through each row in the table
        for row_idx in range(self.custom_table.rowCount()):
            row_data = {}

            # Pull data from each widget in this row
            for col_idx in range(self.custom_table.columnCount()):
                col_name = self.custom_table.horizontalHeaderItem(col_idx).text()
                widget = self.custom_table.item(row_idx, col_idx)

                # Any widgets that we put in the cell will be stored as cellWidget
                if widget is None:
                    widget = self.custom_table.cellWidget(row_idx, col_idx)

                row_data[col_name] = read_widget(widget)

            var_alias = row_data['Variable']
            custom_data[var_alias] = row_data

        # Set to self.data for access to outside caller
        self.data = custom_data
        self.accept()
