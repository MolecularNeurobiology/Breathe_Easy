"""
This script outlines the class for the metadata subGUI, which allows
users to modify names and group of variables.
"""

from typing import Any, List, Union
import csv

import pandas as pd
from PyQt5.QtWidgets import QDialog, QTreeWidgetItem, QListWidgetItem
from PyQt5 import QtCore

from ui.annot_form import Ui_Annot
from util import Settings, avert_name_collision
from util.ui.dialogs import ask_user_ok, notify_error, notify_info

class Annot(QDialog, Ui_Annot):
    """
    Properties, attributes, and methods used by the BASSPRO metadata subGUI.

    Attributes
    ---------
    data (pd.DataFrame): current data mirrored in the GUI widgets
    output_dir (str): current working directory
    """
    def __init__(self, data: pd.DataFrame = None, output_dir: str = ""):
        """
        Instantiate the Annot class.
        
        Parameters
        ---------
        data: initial input data for populating the GUI
        output_dir: current working directory
        """
        super(Annot, self).__init__()

        self.setupUi(self)
        self.setWindowTitle("BASSPRO Variable Annotation")
        self.isActiveWindow()

        self.data = data.copy()
        self.output_dir = output_dir
        self.populate_list_columns()

    @property
    def groups(self):
        """
        Retrieve the current group names and children values
        from the GUI widgets.
        
        Returns
        ------
        list[dict[str, Any]]]:
            each group, identified by its alias string and list of values
        """
        groups = []
        root = self.variable_tree.invisibleRootItem()
        num_groups = root.childCount()
        for group_idx in range(num_groups):
            group_item = root.child(group_idx)
            alias = group_item.text(0) # text at first (0) column
            kids = []
            for val_idx in range(group_item.childCount()):
                subitem = group_item.child(val_idx)
                kids.append(subitem.text(0))
            groups.append({
                'alias': alias,
                'kids': kids
            })
        return groups

    def populate_list_columns(self):
        """Clear the entire window and fill the variable list"""
        # Clear all the widgets
        self.variable_list_columns.clear()
        self.variable_list_values.clear()
        self.group_list.clear()
        self.variable_tree.clear()

        # Add all column names
        for col_name in self.data.columns:
            item = QListWidgetItem(col_name)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self.variable_list_columns.addItem(item)

    def populate_list_values(self):
        """Clear the selection and update the values list"""
        # Clear everything but column names
        self.variable_list_values.clear()
        self.group_list.clear()
        self.variable_tree.clear()
        
        # Get currently selected column
        curr_column = self.variable_list_columns.currentItem().text()
        
        # Populate values in this column
        #   skip null values
        for y in sorted(set([m for m in self.data[curr_column] if not pd.isnull(m)])):
            self.variable_list_values.addItem(str(y))

    def binning_validation(self, value_list: List[Any]):
        """
        Inspect a list of values for non-numeric and missing values.

        Returns
        ------
        bool: whether the values are valid for binning
        """
        # Catch any non-numeric types
        if value_list.dtypes == object:
            print(value_list.dtypes)
            self.group_list.addItem("Selected variable has non-numeric values.")
            return False

        # Catch any null values
        elif pd.isna(value_list).any():
            # Ask user if they want to continue
            reply = ask_user_ok('Missing values', 'The selected variable has missing values.\n\nWould you like to continue?\n')
            if not reply:
                return False

        return True

    def binning_value(self):
        """
        Divide the values for the currently selected column into bins by value.
        """
        curr_selected_column = self.variable_list_columns.currentItem().text()
        value_list = self.data[curr_selected_column]

        # Check that values are valid
        if not self.binning_validation(value_list):
            return

        # Clear widgets
        self.group_list.clear()
        self.variable_tree.clear()

        value_list = value_list.sort_values()

        # Get bin number
        bin_number = int(self.bin_edit.text())

        diff = value_list.max() - value_list.min()
        cutt_off = diff/bin_number

        for x in range(bin_number):
            # One is subtracted from the bin number because Python is left inclusive.
            if x == (bin_number - 1):
                selected_values = value_list[
                    (value_list >= (x*cutt_off) + value_list.min())]

            else:
                selected_values = value_list[
                    (value_list >= (x*cutt_off) + value_list.min()) & \
                    (value_list < value_list.min() + (cutt_off * (x+1)))]

            self.add_new_group(selected_values)

    def binning_count(self):
        """
        Divide the values for the currently selected column into bins by count.
        """
        curr_selected_column = self.variable_list_columns.currentItem().text()
        value_list = self.data[curr_selected_column]

        # Check that values are valid
        if not self.binning_validation(value_list):
            return

        # Clear widgets
        self.group_list.clear()
        self.variable_tree.clear()

        value_list = value_list.sort_values()
        value_list = [v for v in value_list if not(pd.isna(v))]

        bin_number = int(self.bin_edit.text())
        diff = len(value_list)
        cutt_off = int(diff/bin_number)
        for x in range(bin_number):
            if x == (bin_number - 1):
                selected_values = [v for v in value_list if v>=value_list[x*cutt_off]]
            else:
                selected_values = [v for v in value_list if (v>=value_list[x*cutt_off]) and (v<value_list[(x+1)*cutt_off])]

            self.add_new_group(selected_values)

    def add_new_group(self, selected_values: List[Union[str, int]]):
        """
        Add new group based on input values
        
        Parameters
        ---------
        selected_values: values to include in the new group
        """
        # Add new group in listwidget
        group_name = 'Group {}'.format(len(self.groups)+1)
        item = QListWidgetItem(group_name)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.group_list.addItem(item)

        # Create new group in TreeWidget
        tree_group = QTreeWidgetItem(self.variable_tree)
        tree_group.setExpanded(True)
        tree_group.setText(0, group_name)
        for val in selected_values:
            new_item = QTreeWidgetItem()
            new_item.setText(0, str(val))
            tree_group.addChild(new_item)

    def manual_bin(self):  
        """Collect the selected items into a bin manually."""
        selected_values = []
        for item in self.variable_list_values.selectedItems():
            selected_values.append(item.text())

        self.add_new_group(selected_values)

        # Remove the binned items from the options
        for selected_value in self.variable_list_values.selectedItems():
            self.variable_list_values.takeItem(self.variable_list_values.row(selected_value))

    def tree_label(self):
        """
        Callback to update group name in TreeWidget after a
        change in the ListWidget
        """
        # Get item that we're talking about
        renamed_item = self.group_list.currentItem()
        index = self.group_list.currentIndex()
        
        # Find the tree item that matches this index
        root = self.variable_tree.invisibleRootItem()
        tree_item = root.child(index.row())

        # Set the new text
        tree_item.setText(0, renamed_item.text())

    def column_label(self):
        """
        Callback to check user rename of column for duplication and
        provide alternative option in popup message.
        """
        # Get current item
        index = self.variable_list_columns.currentRow()
        old_name = self.data.columns[index]
        curr_item = self.variable_list_columns.currentItem()
        new_name = curr_item.text()

        # If there is a name change
        if old_name != new_name:

            # Prevent duplicate names
            new_name = avert_name_collision(new_name, self.data.columns)

            # User cancelled, set back to old name
            if new_name is None:
                new_name = old_name

            # Set text in widget, may be the user-entered name,
            #   a mangled name, or the old name
            self.variable_list_columns.blockSignals(True)
            curr_item.setText(new_name)
            self.variable_list_columns.blockSignals(False)

            # Update new name in data
            # TODO: don't mess with dataframe until saving or retrieving after accept; will clean up above logic too ^^
            self.data.rename(columns = {old_name: new_name}, inplace=True, errors='raise')

    def add_column(self):
        """Add the current groupings as new column and reset the window."""
        # Create copy of metadata
        metadata_temp = self.data.copy()
        
        curr_item = self.variable_list_columns.currentItem()
        if not curr_item:
            return

        # Get currently selected column
        curr_column = curr_item.text()

        # Find unique column name
        new_column = avert_name_collision(curr_column + "_recode", self.data.columns)
        # User rejected rename suggestion
        if new_column is None:
            return 
        
        # Add new groups to metadata
        for group in self.groups:
            for value in group["kids"]:
                metadata_temp.loc[
                    metadata_temp[curr_column].astype(str)==str(value),
                    [new_column]] = group["alias"]
        
        # Clean up list widgets
        self.variable_list_columns.clear()
        self.variable_list_values.clear()
        self.group_list.clear()
        
        # Update new column list
        for col_name in metadata_temp.columns:
            item = QListWidgetItem(col_name)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self.variable_list_columns.addItem(item)
        
        # Copy new data back to metadata
        self.data = metadata_temp.copy()

    def save_as(self):
        """Save current data to user-selected file"""
        try:
            if MetadataSettings.save_file(data=self.data):
                # Tell the user it's a success
                notify_info("Metadata file saved.")

        except PermissionError:
            notify_error('One or more of the files you are trying to save is open in another program.', title="File in use")

    def load_file(self):
        """Load metadata from user-selected file"""
        file = MetadataSettings.open_file()
        if not file:
            return
        
        # Attempt a load, will return None if fails
        metadata = MetadataSettings.attempt_load(file)
        if metadata is not None:
            self.data = metadata
            self.populate_list_columns()

class MetadataSettings(Settings):
    """Attributes and methods for handling Metadata files"""

    valid_filetypes = ['.csv', '.xlsx']
    naming_requirements = ['metadata']
    file_chooser_message = 'Select metadata file'
    default_filename = 'metadata.csv'
    editor_class = Annot

    @staticmethod
    def attempt_load(metadata_file):
        # Check file types
        if metadata_file.endswith(".csv"):
            return pd.read_csv(metadata_file)
        elif metadata_file.endswith(".xlsx"):
            return pd.read_excel(metadata_file)
        else:
            return None

    @staticmethod
    def _save_file(filepath, metadata_df):
        # Save to csv
        # Need quoting flag to make sure lists of items are saved correctly
        metadata_df.to_csv(filepath, index=False, quoting=csv.QUOTE_NONNUMERIC)
        