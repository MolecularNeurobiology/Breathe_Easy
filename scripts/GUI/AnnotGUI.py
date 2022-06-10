
import os
from pathlib import Path
from pyclbr import Class
import csv
import pandas as pd
from PyQt5.QtWidgets import QDialog, QMessageBox, QTreeWidgetItem
from PyQt5 import QtCore
from ui.annot_form import Ui_Annot
from util import Settings, avert_name_collision
from util.ui.dialogs import ask_user_ok, notify_error, notify_info

class Annot(QDialog, Ui_Annot):
    """
    The Annot class inherits widgets and layout of Ui_Annot and defines the metadata customization subGUI.

    Parameters
    --------
    QMainWindow: class
        The Annot class inherits properties and methods from the QMainWindow class.
    Ui_Annot: Class
        The Annot class inherits its widgets and layouts of the Ui_Annot class.
    """
    def __init__(self, data=None, workspace_dir=""):
        """
        Instantiate the Annot class.
        
        Parameters
        --------
        Plethysmography: Class
            The Annot class inherits Plethysmography's methods, attributes, and widgets.

        Outputs
        --------
        self.pleth: Class
            Shorthand for Plethsmography class.
        self.data: None
            This attribute will store a pandas dataframe.
        self.column: str
            This attribute is set as an empty string.
        selected_values: list
            This attribute is set as an empty list.
        self.groups: list
            This attribute is set as an empty list.
        self.changes: list
            This attribute is set as an empty list.
        self.kids: dict
            This attribute is set as an empty dictionary.
        """
        super(Annot, self).__init__()

        self.setupUi(self)
        self.setWindowTitle("BASSPRO Variable Annotation")
        self.isActiveWindow()

        self.data = data.copy()
        self.populate_list_columns()

        # Initialize attributes
        self.workspace_dir = workspace_dir

        self.groups = []
        self.changes = []
        self.kids = {}

#region populate
    def load_metadata_file(self):
        """
        - Reset some attributes
        - And spawn a file dialog to get the path to the file that will populate self.data with a dataframe.

        Parameters
        --------
        self.data: Dataframe | None
            This attribute is either a dataframe or is set as None.
        file: QFileDialog
            This variable stores the path of the file the user selected via the FileDialog.
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        
        Outputs
        --------
        self.data: Dataframe | None
            This attribute is either a dataframe or continues to be None.
        
        Outcomes
        --------
        self.populate_list_columns()
            This method is called after self.data is populated with a dataframe. The headers of the dataframe are added to self.variable_list_columns (ListWidget).
        self.close()
            This method closes the Annot subGUI if the user chooses not to provide a metadata file.
        """
        file = MetadataSettings.open_file()
        if not file:
            return
        
        # TODO: make this throw a better error?
        # Attempt a load, will return None if fails
        metadata = MetadataSettings.attempt_load(file)
        if metadata is not None:
            self.data = metadata
            self.populate_list_columns()
        else:
            notify_error("Error loading metadata. Check your file extension")

    def populate_list_columns(self):
        """
        - Clear the widgets
        - reset some attributes
        - and populate self.variable_list_columns (ListWidget) with the headers of the dataframe stored in the attribute self.data.

        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.data dataframe. ListWidgetItem is editable.
        self.variable_list_values: QListWidget
            This ListWidget displays the unique values of the self.data dataframe column selected by the user in self.variable_list_columns. Not editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.variable_tree: QTreeWidget
            This TreeWidget displays the new groups and all of their contents (all values, not just unique values). Not editable.
        self.groups: list
            This attribute is set as an empty list.
        self.kids: dict
            This attribute is set as an empty dictionary.
        self.data: Dataframe | None
            This attribute is either a dataframe or is set as None.
        
        Outputs
        --------
        self.variable_list_columns: QListWidget
            This ListWidget is cleared of contents and then populated with the headers of the dataframe stored in self.data.
        self.variable_list_values: QListWidget
            This ListWidget is cleared of contents.
        self.group_list: QListWidget
            This ListWidget is cleared of contents.
        self.variable_tree: QTreeWidget
            This TreeWidget is cleared of contents.
        self.groups: list
            This attribute is set as an empty list.
        self.kids: dict
            This attribute is set as an empty dictionary.
        self.data: Dataframe
            This attribute is a dataframe. 
        """
        # Clear all the widgets
        self.variable_list_columns.clear()
        self.variable_list_values.clear()
        self.group_list.clear()
        self.variable_tree.clear()
        self.groups=[]
        self.kids={}

        # Add all column names
        for col in self.data.columns:
            self.variable_list_columns.addItem(col)
    
    def populate_list_values(self):
        """
        - Clear some widgets
        - reset some attributes
        - and populate self.variable_list_values (ListWidget) with the unique values of the column selected by the user in self.variable_list_columns (ListWidget)of the dataframe stored in the attribute self.data.

        Parameters
        --------
        self.variable_list_values: QListWidget
            This ListWidget displays the unique values of the self.data dataframe column selected by the user in self.variable_list_columns. Not editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.variable_tree: QTreeWidget
            This TreeWidget displays the new groups and all of their contents (all values, not just unique values). Not editable.
        self.groups: list
            This attribute is set as an empty list.
        self.kids: dict
            This attribute is set as an empty dictionary.
        self.data: Dataframe
            This attribute is a dataframe.
        
        Outputs
        --------
        self.variable_list_values: QListWidget
            This ListWidget is populated with the unique and sorted values of the column in the self.data dataframe with a header matching the text stored in the attribute self.column. Not editable.
        self.group_list: QListWidget
            This ListWidget is cleared of contents.
        self.variable_tree: QTreeWidget
            This TreeWidget is cleared of contents.
        self.groups: list
            This attribute is set as an empty list.
        self.kids: dict
            This dictionary is populated with the not-null sorted unique values typed as strings as the keys and typed as is as the values.
        self.data: Dataframe
            This attribute is a dataframe. 
        """
        # Clear everything but column names
        self.variable_list_values.clear()
        self.group_list.clear()
        self.variable_tree.clear()
        self.groups=[]
        self.kids={}
        
        # Get currently selected column
        curr_column = self.variable_list_columns.currentItem().text()
        
        # TODO: this breaks when there are new columns
        # Populate values in this column
        #   skip null values
        for y in sorted(set([m for m in self.data[curr_column] if not pd.isnull(m)])):
            self.variable_list_values.addItem(str(y))
            self.kids[str(y)] = y

    def binning_validation(self):
        """Inspect the list of values in the column selected in self.variable_list_columns
        for non-numeric values and missing values before starting self.binning_value_continued().
        
        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.data dataframe. ListWidgetItem is editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.data: Dataframe
            This attribute is a dataframe.
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        
        Outputs
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.data dataframe. ListWidgetItem is editable.
        self.group_list: QListWidget
            This ListWidget is cleared of contents. If the values of the selected ListWidgetItem's header equivalent in the self.data dataframe have non-numeric values, a ListWidgetItem with text stating that is added to this widget.
        
        Outcomes
        --------
        self.binning_value_continued()
            This method actually divides the values of the selected column into bins by value.
        """

        curr_selected_column = self.variable_list_columns.currentItem().text()

        # Get all values for column
        value_list = self.data[curr_selected_column]

        # Catch any non-numeric types
        if value_list.dtypes == object:
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
        This method was written with significant contributions from Chris Ward.

        Divide the values displayed in self.variable_list_values (ListWidget) into bins by value. 

        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.data dataframe. ListWidgetItem is editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.variable_tree: QTreeWidget
            This TreeWidget displays the new groups and all of their contents (all values, not just unique values). Not editable.
        self.groups: list
            This attribute is set as an empty list.
        self.data: Dataframe
            This attribute is a dataframe.
        self.bin_edit: QLineEdit
            This LineEdit is editable by the user. The text is set by default as 4. This number dictates the number of bins.
        
        Outputs
        --------
        self.group_list: QListWidget
            This ListWidget is cleared and then iteratively populated by successive self.current_group values, i.e. Group 1, Group 2, etc. ListWidgetItem is editable so the user can change the names to something less generic than Group 1. 
        self.variable_tree: QTreeWidget
            This TreeWidget provides a nested display of the new groups and all of their contents (all values, not just unique values). It is cleared and then iteratively populated by self.tree_group (TreeWidgetItem). Not editable.
        self.groups: list
            This attribute is cleared and then populated with a list of dictionaries (why?). Each dictionary consists of one level with two keys: the "alias" key's value is self.current_group, and the "kids" key's value is selected_values.
        self.bin_number: int
            The text of the self.bin_edit (LineEdit) typed as int. This attribute determines the number of bins.
        selected_values: list
            This attribute is cleared and then iteratively populated with the values of the active bin.
        self.current_group: str
            This attribute is constructed from the concatenation of "Group" and the number of groups in self.groups (list).
        self.tree_group: QTreeWidgetItem
            This attribute is a first-level child of self.variable_tree (TreeWidget) with self.current_group set as its text. It is iteratively populated by kid (TreeWidgetItem). 
        kid: QTreeWidgetItem
            This variable is a first-level child of self.tree_group (TreeWidgetItem) and thus a second-level child of self.variable_tree (TreeWidget). It iteratively populates its parent self.tree_group (TreeWidgetItem) with values from selected_values (list) typed as str. This unhelpfully named variable is distinct from the attribute self.kids (dict). 
        """
        # Check that values are valid
        if not self.binning_validation():
            return

        # Clear widgets
        self.group_list.clear()
        self.variable_tree.clear()

        self.groups = []

        curr_selected_column = self.variable_list_columns.currentItem().text()
        value_list = self.data[curr_selected_column]
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

            current_group = 'Group {}'.format(len(self.groups)+1)
            self.group_list.addItem(current_group)

            # Create new TreeWidgetItem
            self.tree_group = QTreeWidgetItem(self.variable_tree)
            self.tree_group.setExpanded(True)
            self.tree_group.setText(0, current_group)

            for y in selected_values:
                kid = QTreeWidgetItem(self.tree_group)
                kid.setText(0,str(y))
                self.tree_group.addChild(kid)

            self.groups.append({"alias": current_group,
                                "kids": selected_values})

    def binning_count(self):
        """
        This method was written with significant contributions from Chris Ward.

        Divide the values displayed in self.variable_list_values (ListWidget) into bins by count. 

        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.data dataframe. ListWidgetItem is editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.variable_tree: QTreeWidget
            This TreeWidget displays the new groups and all of their contents (all values, not just unique values). Not editable.
        self.groups: list
            This attribute is set as an empty list.
        self.data: Dataframe
            This attribute is a dataframe.
        self.bin_edit: QLineEdit
            This LineEdit is editable by the user. The text is set by default as 4. This number dictates the number of bins.
        selected_values: list
            This attribute is set as an empty list.
        
        Outputs
        --------
        self.group_list: QListWidget
            This ListWidget is cleared and then iteratively populated by successive self.current_group values, i.e. Group 1, Group 2, etc. ListWidgetItem is editable so the user can change the names to something less generic than Group 1. 
        self.variable_tree: QTreeWidget
            This TreeWidget provides a nested display of the new groups and all of their contents (all values, not just unique values). It is cleared and then iteratively populated by self.tree_group (TreeWidgetItem). Not editable.
        self.groups: list
            This attribute is cleared and then populated with a list of dictionaries (why?). Each dictionary consists of one level with two keys: the "alias" key's value is self.current_group, and the "kids" key's value is selected_values.
        self.bin_number: int
            The text of the self.bin_edit (LineEdit) typed as int. This attribute determines the number of bins.
        selected_values: list
            This attribute is iteratively cleared and then populated with the values of the active bin.
        self.current_group: str
            This attribute is constructed from the concatenation of "Group" and the number of groups in self.groups (list).
        self.tree_group: QTreeWidgetItem
            This attribute is a first-level child of self.variable_tree (TreeWidget) with self.current_group set as its text. It is iteratively populated by kid (TreeWidgetItem). 
        kid: QTreeWidgetItem
            This variable is a first-level child of self.tree_group (TreeWidgetItem) and thus a second-level child of self.variable_tree (TreeWidget). It iteratively populates its parent self.tree_group (TreeWidgetItem) with values from selected_values (list) typed as str. This unhelpfully named variable is distinct from the attribute self.kids (dict). 
        """
        # Check that values are valid
        if not self.binning_validation():
            return

        # Clear widgets
        self.group_list.clear()
        self.variable_tree.clear()

        self.groups = []

        curr_selected_column = self.variable_list_columns.currentItem().text()
        value_list = self.data[curr_selected_column]
        value_list = value_list.sort_values()
        value_list = [v for v in value_list if not(pd.isna(v))]

        bin_number = int(self.bin_edit.text())
        diff = len(value_list)
        cutt_off = int(diff/bin_number)
        for x in range(bin_number):
            selected_values = []

            if x == (bin_number - 1):
                selected_values = [v for v in value_list if v>=value_list[x*cutt_off]]
            else:
                selected_values = [v for v in value_list if (v>=value_list[x*cutt_off]) and (v<value_list[(x+1)*cutt_off])]
            current_group = 'Group {}'.format(len(self.groups)+1)
            self.group_list.addItem(current_group)

            self.tree_group = QTreeWidgetItem(self.variable_tree)
            self.tree_group.setExpanded(True)
            self.tree_group.setText(0, current_group)
            for y in selected_values:
                kid = QTreeWidgetItem(self.tree_group)
                kid.setText(0,str(y))
                self.tree_group.addChild(kid)
            self.groups.append({"alias": current_group,
                                "kids": selected_values})

    def recode(self):  
        """
        Create a manually-selected bin from multiple values selected in self.variable_list_values (ListWidget). 

        Parameters
        --------
        self.variable_list_values: QListWidget
            This ListWidget displays the unique values of the self.data dataframe column selected by the user in self.variable_list_columns. Not editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.variable_tree: QTreeWidget
            This TreeWidget displays the new groups and all of their contents (all values, not just unique values). Not editable.
        self.groups: list
            This attribute is set as an empty list.
        selected_values: list
            This attribute is set as an empty list.
        
        Outputs
        --------
        self.group_list: QListWidget
            This ListWidget is cleared and then iteratively populated by successive self.current_group values, i.e. Group 1, Group 2, etc. ListWidgetItem is editable so the user can change the names to something less generic than Group 1. 
        self.variable_tree: QTreeWidget
            This TreeWidget provides a nested display of the new groups and all of their contents (all values, not just unique values). It is cleared and then iteratively populated by self.tree_group (TreeWidgetItem). Not editable.
        self.groups: list
            This attribute is cleared and then populated with a list of dictionaries (why?). Each dictionary consists of one level with two keys: the "alias" key's value is self.current_group, and the "kids" key's value is selected_values.
        selected_values: list
            This attribute is iteratively cleared and then populated with the values of the active bin.
        self.current_group: str
            This attribute is constructed from the concatenation of "Group" and the number of groups in self.groups (list).
        self.tree_group: QTreeWidgetItem
            This attribute is a first-level child of self.variable_tree (TreeWidget) with self.current_group set as its text. It is iteratively populated by kid (TreeWidgetItem). 
        kid: QTreeWidgetItem
            This variable is a first-level child of self.tree_group (TreeWidgetItem) and thus a second-level child of self.variable_tree (TreeWidget). It iteratively populates its parent self.tree_group (TreeWidgetItem) with values from selected_values (list) typed as str. This unhelpfully named variable is distinct from the attribute self.kids (dict). 
        """
        selected_values=[]
        for value in list(self.variable_list_values.selectedItems()):
            selected_values.append(value.text())

        current_group = 'Group {}'.format(len(self.groups)+1)
        self.group_list.addItem(current_group)

        self.tree_group = QTreeWidgetItem(self.variable_tree)
        self.tree_group.setExpanded(True)
        self.tree_group.setText(0, current_group)

        for x in selected_values:
            print(f'manual binning:{type(x)}')
            kid = QTreeWidgetItem(self.tree_group)
            kid.setText(0,x)
            self.tree_group.addChild(kid)

        self.groups.append({"alias": current_group,"kids":selected_values})
        for selected_value in self.variable_list_values.selectedItems():
            self.variable_list_values.takeItem(self.variable_list_values.row(selected_value))

    def relabel_group(self):
        """
        Change the text of the selected ListWidgetItem in self.group_list (ListWidget).

        Parameters
        --------
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        item: QListWidgetItem
            This ListWidgetItem in self.group_list (ListWidget) has been selected by the user.
        
        Outputs
        --------
        self.group_list: QListWidget
            The text of item (ListWidgetItem) is edited by the user.
        """
        print("annot.relabel_group()")
        index = self.group_list.currentIndex()
        if index.isValid():
            item = self.group_list.itemFromIndex(index)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.group_list.edit(index)

    def tree_label(self):
        """
        Change the text of the first-level TreeWidgetItem in self.variable_tree
          that corresponds to the selected ListWidgetItem in self.group_list (ListWidget)
          that was edited by self.relabel_group().

        Parameters
        --------
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.variable_tree: QTreeWidget
            This TreeWidget displays the groups and all of their contents (all values, not just unique values). Not editable.
        item: QListWidgetItem
            This ListWidgetItem in self.group_list (ListWidget) has been selected by the user.
        self.groups: list
            This attribute is a list of dictionaries. Each dictionary consists of one level with two keys: the "alias" key's value is self.current_group, and the "kids" key's value is selected_values.

        Outputs
        --------
        self.variable_tree: QListWidget
            This TreeWidget provides a nested display of the relabeled groups and all of their contents (all values, not just unique values). It is cleared and then iteratively repopulated by self.tree_group (TreeWidgetItem). Not editable.
        self.groups: list
            The value of the "alias" key of the dictionary that is the item in this list with the same index as the selected ListWidgetItem in self.groups (ListWidget) is changed to the edited text of the selected ListWidgetItem. The corresponding "kid" key's value is left unchanged.
        self.tree_group: QTreeWidgetItem
            This attribute is a first-level child of self.variable_tree (TreeWidget) with its text set as the value of the "alias" key of the updated dictionary in self.groups (list). It is iteratively repopulated by kid (TreeWidgetItem).
        kid: QTreeWidgetItem
            This variable is a first-level child of self.tree_group (TreeWidgetItem) and thus a second-level child of self.variable_tree (TreeWidget). It populates its parent self.tree_group (TreeWidgetItem) with values from the "kids" key's list of values from the active dictionary when iterating through self.groups (list). This unhelpfully named variable is distinct from the attribute self.kids (dict). 
        """
        print("annot.tree_label()")
        self.variable_tree.clear()
        index = self.group_list.currentIndex()
        item = self.group_list.itemFromIndex(index)
        self.groups[index.row()]["alias"] = item.text()

        for group in self.groups:
            self.tree_group = QTreeWidgetItem(self.variable_tree)
            self.tree_group.setText(0, group["alias"])
            for k in group["kids"]:
                kid = QTreeWidgetItem(self.tree_group)
                self.tree_group.addChild(kid)
                kid.setText(0,str(k))
            self.tree_group.setExpanded(True)
    
    def relabel_column(self):
        """
        Change the text of the selected ListWidgetItem in self.variable_list_columns (ListWidget).
          Currently, there is nothing preventing the user from renaming a column
          with a header that's already in use, which will cause problems in either BASSPRO or STAGG.

        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.data dataframe. ListWidgetItem is editable.
        item: QListWidgetItem
            This ListWidgetItem in self.variable_list_columns (ListWidget) has been selected by the user.

        Outputs
        --------
        self.variable_list_columns: QListWidget
            The text of item (ListWidgetItem) is edited by the user.
        """
        index = self.variable_list_columns.currentIndex()
        item = self.variable_list_columns.currentItem()
        if index.isValid():
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.variable_list_columns.edit(index)

    def column_label(self):
        """
        Change the text of the header in self.data dataframe that
          corresponds to the selected ListWidgetItem in self.variable_list_columns
          that was edited by self.relabel_column().

        Parameters
        ------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.data dataframe. ListWidgetItem is editable.
        item: QListWidgetItem
            This ListWidgetItem in self.variable_list_columns (ListWidget) has been selected by the user.
        self.data: Dataframe
            This attribute is set as a dataframe.

        Outputs
        --------
        self.data: Dataframe
            The header corresponding to item (ListWidgetItem) is changed in the dataframe to reflect the user's edit.
        """
        # Get current item
        index = self.variable_list_columns.currentRow()
        old_name = self.data.columns[index]
        curr_item = self.variable_list_columns.currentItem()
        new_name = curr_item.text()

        # If there is a name change
        if old_name != new_name:

            # Prevent duplicate names
            if new_name in self.data.columns:
                new_name = avert_name_collision(new_name, self.data.columns)
                if new_name is None:
                    new_name = old_name

        # If there is *still* a name change
        if old_name != new_name:
            # Prevent this function from firing again on set command
            self.variable_list_columns.blockSignals(True)

            # Set text in widget
            curr_item.setText(new_name)

            self.variable_list_columns.blockSignals(False)

            # TODO: don't mess with dataframe until saving or retrieving after accept; will clean up above logic too ^^
            # Rename column old_name to new_name
            self.data.rename(columns = {old_name: new_name}, inplace=True, errors='raise')

    def add_column(self):
        """
        Create a new column in the self.data dataframe from self.groups
          and update self.variable_list_column to reflect the added column.

        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.data dataframe. ListWidgetItem is editable.
        self.variable_list_values: QListWidget
            This ListWidget displays the unique values of the self.data dataframe column selected by the user in self.variable_list_columns. Not editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.data: Dataframe
            This attribute is set as a dataframe.
        self.groups: list
            This attribute is cleared and then populated with a list of dictionaries (why?). Each dictionary consists of one level with two keys: the "alias" key's value is self.current_group, and the "kids" key's value is selected_values.
        
        Outputs
        --------
        self.data: Dataframe
            This attribute is a copy of self.megameta after the new column is added.
        self.variable_list_columns: QListWidget
            This ListWidget is cleared of contents and then populated with the headers of the dataframe stored in self.megameta.
        self.variable_list_values: QListWidget
            This ListWidget is cleared of contents.
        self.group_list: QListWidget
            This ListWidget is cleared of contents.
        self.groups: list
            This attribute is set as an empty list.
        """
        # Create copy of metadata
        metadata_temp = self.data.copy()
        
        curr_item = self.variable_list_columns.currentItem()
        if not curr_item:
            return

        # Get currently selected column
        curr_column = curr_item.text()

        # Find unique column name
        new_column = avert_name_collision(curr_column + "_recode", self.data.columns)
        
        # Add new group to metadata
        for group in self.groups:
            for value in group["kids"]:
                row_idx = metadata_temp.loc[metadata_temp[curr_column].astype(str)==str(value)].index[0]
                metadata_temp.at[row_idx, new_column] = group["alias"]
        
        # Clean up list widgets
        self.variable_list_columns.clear()
        self.variable_list_values.clear()
        self.group_list.clear()
        
        # Update new column list
        for x in metadata_temp.columns:
            self.variable_list_columns.addItem(x)
        
        # Copy new data back to metadata
        self.data=metadata_temp.copy()
        self.groups=[]

    def save_as(self):
        """
        Write the self.data dataframe to a csv file saved by the user via a standard FileDialog, populate self.pleth.metadata with the corresponding file path, and add the file path as a ListWidgetItem to self.pleth.metadata_list (ListWidget).

        Parameters
        --------
        file: QFileDialog
            This variable stores the path of the file the user selected via the FileDialog.
        self.data: Dataframe
            This attribute is set as a dataframe.
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        self.pleth.breath_df: list
            This Plethysmography class attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        
        Outputs
        --------
        self.pleth.metadata: str
            This Plethysmography class attribute stores the path of the csv file that self.data dataframe was written to.
        self.pleth.metadata_list: QListWidget
            This ListWidget is populated with the file path in self.pleth.metadata.
        
        Outcomes
        --------
        self.pleth.update_breath_df()
            This Plethysmography class method updates the Plethysmography class attribute self.pleth.breath_df to reflect the changes to the metadata.
        """
        try:
            if MetadataSettings.save_file(data=self.data, workspace_dir=self.workspace_dir):
                # Tell the user it's a success
                notify_info("Metadata file saved")

        except PermissionError:
            notify_error('One or more of the files you are trying to save is open in another program.', title="File in use")

class MetadataSettings(Settings):

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
        