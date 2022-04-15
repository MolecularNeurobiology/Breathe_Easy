
import os
from pathlib import Path
from pyclbr import Class
import pandas as pd
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTreeWidgetItem, QFileDialog
from PyQt5 import QtCore
from ui.annot_form import Ui_Annot
from util import Settings, notify_error

class Annot(QMainWindow, Ui_Annot):
    """
    The Annot class inherits widgets and layout of Ui_Annot and defines the metadata customization subGUI.

    Parameters
    --------
    QMainWindow: class
        The Annot class inherits properties and methods from the QMainWindow class.
    Ui_Annot: Class
        The Annot class inherits its widgets and layouts of the Ui_Annot class.
    """
    def __init__(self,Plethysmography: Class):
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
        self.metadata: None
            This attribute will store a pandas dataframe.
        self.column: str
            This attribute is set as an empty string.
        self.new_column: str
            This attribute is set as an empty string.
        self.selected_values: list
            This attribute is set as an empty list.
        self.groups: list
            This attribute is set as an empty list.
        self.changes: list
            This attribute is set as an empty list.
        self.kids: dict
            This attribute is set as an empty dictionary.
        """
        super(Annot, self).__init__()

#region class attributes

        self.setupUi(self)
        self.pleth = Plethysmography
        self.setWindowTitle("BASSPRO Variable Annotation")
        self.isActiveWindow()

        self.metadata = None
        self.column = ""
        self.new_column = ""
        self.selected_values = []
        self.groups = []
        self.changes = []
        self.kids = {}

#endregion

    def show_metadata_file(self):
        """
        Determine the source of the metadata that will be manipulated by the user in the Annot subGUI.
        
        Parameters
        --------
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        self.pleth.metadata: str
            This Plethysmography attribute is either an empty string or a string of the path to the user-selected file that has the metadata.
        self.metadata: Dataframe | None
            This attribute is either a dataframe or is set as None.

        Outputs
        --------
        self.metadata: Dataframe | None
            This attritube is either a dataframe or continues to be None.
        
        Outcomes
        --------
        self.load_metadata_file()
            This method is called if the user has not yet selected a metadata file (self.pleth.metadata is an empty string) or if the selected metadata file is not the correct file format (self.pleth.metadata is a file path) or if the selected metadata file was not found (self.pleth.metadata is a file path that does not exist).
        self.populate_list_columns()
            This method is called after self.metadata is populated with a dataframe. The headers of the dataframe are added to self.variable_list_columns (ListWidget).
        self.close()
            This method closes the Annot subGUI if the user chooses not to provide a metadata file.
        """
        print("annot.show_metadata_file()")
        if not self.pleth.metadata and self.metadata is None:
            reply = QMessageBox.information(self, 'Missing metadata file', 'Please select a metadata file.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.load_metadata_file()
            if reply == QMessageBox.Cancel:
                self.close()
        elif self.pleth.metadata and self.metadata is None:
            if Path(self.pleth.metadata).exists():
                if self.pleth.metadata.endswith('.xlsx'):
                    self.metadata = pd.read_excel(self.pleth.metadata)
                    self.populate_list_columns()
                elif self.pleth.metadata.endswith('.csv'):
                    self.metadata = pd.read_csv(self.pleth.metadata)
                    self.populate_list_columns()
                else:
                    reply = QMessageBox.information(self, 'Incorrect file format', 'Only .csv or .xlsx files are accepted.\nWould you like to select a different file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                    if reply == QMessageBox.Ok:
                        self.load_metadata_file()
            else:
                reply = QMessageBox.information(self, 'File not found', 'The previously selected metadata file was not found.\nWould you like to select a different file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                if reply == QMessageBox.Ok:
                    self.load_metadata_file()
                if reply == QMessageBox.Cancel:
                    self.close()
        else:
            print("existing annot activity")
            
#region populate
    def load_metadata_file(self):
        """
        Clear the widgets, reset some attributes, and spawn a file dialog to get the path to the file that will populate self.metadata with a dataframe.

        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.metadata dataframe. ListWidgetItem is editable.
        self.variable_list_values: QListWidget
            This ListWidget displays the unique values of the self.metadata dataframe column selected by the user in self.variable_list_columns. Not editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.variable_tree: QTreeWidget
            This TreeWidget displays the new groups and all of their contents (all values, not just unique values). Not editable.
        self.groups: list
            This attribute is set as an empty list.
        self.kids: dict
            This attribute is set as an empty dictionary.
        self.metadata: Dataframe | None
            This attribute is either a dataframe or is set as None.
        file: QFileDialog
            This variable stores the path of the file the user selected via the FileDialog.
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        
        Outputs
        --------
        self.variable_list_columns: QListWidget
            This ListWidget is cleared of contents.
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
        self.metadata: Dataframe | None
            This attribute is either a dataframe or continues to be None.
        
        Outcomes
        --------
        self.populate_list_columns()
            This method is called after self.metadata is populated with a dataframe. The headers of the dataframe are added to self.variable_list_columns (ListWidget).
        self.close()
            This method closes the Annot subGUI if the user chooses not to provide a metadata file.
        """
        print("loading metadata file for annot subGUI")
        self.variable_list_columns.clear()
        self.variable_list_values.clear()
        self.variable_tree.clear()
        self.group_list.clear()
        self.kids={}
        self.groups=[]

        # Opens open file dialog
        file, filter = QFileDialog.getOpenFileName(self, 'Select metadata file', str(self.pleth.workspace_dir))

        # If you the file you chose sucks, the GUI won't crap out.
        if os.path.exists(file):
            if Path(file).suffix == ".xlsx":
                self.metadata = pd.read_excel(file)
                self.populate_list_columns()
            elif Path(file).suffix == ".csv":
                self.metadata = pd.read_csv(file)
                self.populate_list_columns()
            else:
                reply = QMessageBox.information(self, 'Incorrect file format', 'Only .csv or .xlsx files are accepted.\nWould you like to select a different file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                if reply == QMessageBox.Ok:
                    self.load_metadata_file()
        else:
            self.close()

    def populate_list_columns(self):
        """
        Clear the widgets, reset some attributes, and populate self.variable_list_columns (ListWidget) with the headers of the dataframe stored in the attribute self.metadata.

        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.metadata dataframe. ListWidgetItem is editable.
        self.variable_list_values: QListWidget
            This ListWidget displays the unique values of the self.metadata dataframe column selected by the user in self.variable_list_columns. Not editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.variable_tree: QTreeWidget
            This TreeWidget displays the new groups and all of their contents (all values, not just unique values). Not editable.
        self.groups: list
            This attribute is set as an empty list.
        self.kids: dict
            This attribute is set as an empty dictionary.
        self.metadata: Dataframe | None
            This attribute is either a dataframe or is set as None.
        
        Outputs
        --------
        self.variable_list_columns: QListWidget
            This ListWidget is cleared of contents and then populated with the headers of the dataframe stored in self.metadata.
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
        self.metadata: Dataframe
            This attribute is a dataframe. 
        """
        print("annot.populate_list_columns()")
        self.variable_list_columns.clear()
        self.variable_list_values.clear()
        self.group_list.clear()
        self.variable_tree.clear()
        self.groups=[]
        self.kids={}
        for x in self.metadata.columns:
            self.variable_list_columns.addItem(x)
    
    def populate_list_values(self):
        """
        Clear some widgets, reset some attributes, and populate self.variable_list_values (ListWidget) with the unique values of the column selected by the user in self.variable_list_columns (ListWidget)of the dataframe stored in the attribute self.metadata.

        Parameters
        --------
        self.column: str
            This attribute is set as an empty string
        self.variable_list_values: QListWidget
            This ListWidget displays the unique values of the self.metadata dataframe column selected by the user in self.variable_list_columns. Not editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.variable_tree: QTreeWidget
            This TreeWidget displays the new groups and all of their contents (all values, not just unique values). Not editable.
        self.groups: list
            This attribute is set as an empty list.
        self.kids: dict
            This attribute is set as an empty dictionary.
        self.metadata: Dataframe
            This attribute is a dataframe.
        
        Outputs
        --------
        self.column: str
            This attribute is the text of the ListWidgetItem in self.variable_list_columns (ListWidget) selected by the user. It is one of the headers of the self.metadata dataframe.
        self.variable_list_values: QListWidget
            This ListWidget is populated with the unique and sorted values of the column in the self.metadata dataframe with a header matching the text stored in the attribute self.column. Not editable.
        self.group_list: QListWidget
            This ListWidget is cleared of contents.
        self.variable_tree: QTreeWidget
            This TreeWidget is cleared of contents.
        self.groups: list
            This attribute is set as an empty list.
        self.kids: dict
            This dictionary is populated with the not-null sorted unique values typed as strings as the keys and typed as is as the values.
        self.metadata: Dataframe
            This attribute is a dataframe. 
        """
        print("annot.populate_list_values()")
        self.variable_list_values.clear()
        self.group_list.clear()
        self.variable_tree.clear()
        self.groups=[]
        self.kids={}
        
        self.column = self.variable_list_columns.currentItem().text()
        for y in sorted(set([m for m in self.metadata[self.column] if not(pd.isnull(m) == True)])):
            self.variable_list_values.addItem(str(y))
            self.kids[str(y)]=y
# endregion

#region actions
    def binning_value(self):
        """Inspect the list of values in the column selected in self.variable_list_columns for non-numeric values and missing values before starting self.binning_value_continued().
        
        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.metadata dataframe. ListWidgetItem is editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.metadata: Dataframe
            This attribute is a dataframe.
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        
        Outputs
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.metadata dataframe. ListWidgetItem is editable.
        self.group_list: QListWidget
            This ListWidget is cleared of contents. If the values of the selected ListWidgetItem's header equivalent in the self.metadata dataframe have non-numeric values, a ListWidgetItem with text stating that is added to this widget.
        
        Outcomes
        --------
        self.binning_value_continued()
            This method actually divides the values of the selected column into bins by value.
        """
        print("annot.binning_value()")
        value_list = self.metadata[self.variable_list_columns.selectedItems()[0].text()]
        if value_list.dtypes == object:
            self.group_list.addItem("Selected variable has non-numeric values.")
        elif pd.isna(value_list).any() == True:
            reply = QMessageBox.question(self, 'Missing values', 'The selected variable has missing values.\n\nWould you like to continue?\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.binning_value_continued()
        else:
            self.binning_value_continued()

    def binning_value_continued(self):
        """
        This method was written with significant contributions from Chris Ward.

        Divide the values displayed in self.variable_list_values (ListWidget) into bins by value. 

        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.metadata dataframe. ListWidgetItem is editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.variable_tree: QTreeWidget
            This TreeWidget displays the new groups and all of their contents (all values, not just unique values). Not editable.
        self.groups: list
            This attribute is set as an empty list.
        self.metadata: Dataframe
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
            This attribute is cleared and then populated with a list of dictionaries (why?). Each dictionary consists of one level with two keys: the "alias" key's value is self.current_group, and the "kids" key's value is self.selected_values.
        self.bin_number: int
            The text of the self.bin_edit (LineEdit) typed as int. This attribute determines the number of bins.
        self.selected_values: list
            This attribute is cleared and then iteratively populated with the values of the active bin.
        self.current_group: str
            This attribute is constructed from the concatenation of "Group" and the number of groups in self.groups (list).
        self.tree_group: QTreeWidgetItem
            This attribute is a first-level child of self.variable_tree (TreeWidget) with self.current_group set as its text. It is iteratively populated by kid (TreeWidgetItem). 
        kid: QTreeWidgetItem
            This variable is a first-level child of self.tree_group (TreeWidgetItem) and thus a second-level child of self.variable_tree (TreeWidget). It iteratively populates its parent self.tree_group (TreeWidgetItem) with values from self.selected_values (list) typed as str. This unhelpfully named variable is distinct from the attribute self.kids (dict). 
        """
        print("annot.binning_value_continued()")
        self.group_list.clear()
        self.variable_tree.clear()
        self.selected_values = []
        self.groups = []
        value_list = self.metadata[self.variable_list_columns.selectedItems()[0].text()]
        value_list = value_list.sort_values()
        self.bin_number = int(self.bin_edit.text())
        diff = value_list.max() - value_list.min()
        cutt_off = diff/self.bin_number
        for x in range(self.bin_number):
            # One is subtracted from the bin number because Python is left inclusive.
            if x == self.bin_number - 1:
                self.selected_values = value_list[(value_list>=(x*cutt_off)+value_list.min())]
            else:
                self.selected_values = value_list[(value_list>=(x*cutt_off)+value_list.min())&(value_list<value_list.min()+cutt_off*(x+1))]

            self.current_group = 'Group {}'.format(len(self.groups)+1)
            self.group_list.addItem(self.current_group)

            self.tree_group = QTreeWidgetItem(self.variable_tree)
            self.tree_group.setExpanded(True)
            self.tree_group.setText(0, self.current_group)

            for y in self.selected_values:
                kid = QTreeWidgetItem(self.tree_group)
                kid.setText(0,str(y))
                self.tree_group.addChild(kid)
            self.groups.append({"alias": self.current_group,"kids":self.selected_values})

    def binning_count(self):
        """Inspect the list of values in the column selected in self.variable_list_columns for non-numeric values and missing values before starting self.binning_count_continued().
        
        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.metadata dataframe. ListWidgetItem is editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.metadata: Dataframe
            This attribute is a dataframe.
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        
        Outputs
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.metadata dataframe. ListWidgetItem is editable.
        self.group_list: QListWidget
            This ListWidget is cleared of contents. If the values of the selected ListWidgetItem's header equivalent in the self.metadata dataframe have non-numeric values, a ListWidgetItem with text stating that is added to this widget.
        
        Outcomes
        --------
        self.binning_count_continued()
            This method actually divides the values of the selected column into bins by count.
        """
        print("annot.binning_count()")
        value_list = self.metadata[self.variable_list_columns.selectedItems()[0].text()]
        if value_list.dtypes == object:
            self.group_list.addItem("Selected variable has non-numeric values.")
        elif pd.isna(value_list).any() == True:
            reply = QMessageBox.question(self, 'Missing values', 'The selected variable has missing values.\n\nWould you like to continue?\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.binning_count_continued()
        else:
            self.binning_count_continued()

    def binning_count_continued(self):
        """
        This method was written with significant contributions from Chris Ward.

        Divide the values displayed in self.variable_list_values (ListWidget) into bins by count. 

        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.metadata dataframe. ListWidgetItem is editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.variable_tree: QTreeWidget
            This TreeWidget displays the new groups and all of their contents (all values, not just unique values). Not editable.
        self.groups: list
            This attribute is set as an empty list.
        self.metadata: Dataframe
            This attribute is a dataframe.
        self.bin_edit: QLineEdit
            This LineEdit is editable by the user. The text is set by default as 4. This number dictates the number of bins.
        self.selected_values: list
            This attribute is set as an empty list.
        
        Outputs
        --------
        self.group_list: QListWidget
            This ListWidget is cleared and then iteratively populated by successive self.current_group values, i.e. Group 1, Group 2, etc. ListWidgetItem is editable so the user can change the names to something less generic than Group 1. 
        self.variable_tree: QTreeWidget
            This TreeWidget provides a nested display of the new groups and all of their contents (all values, not just unique values). It is cleared and then iteratively populated by self.tree_group (TreeWidgetItem). Not editable.
        self.groups: list
            This attribute is cleared and then populated with a list of dictionaries (why?). Each dictionary consists of one level with two keys: the "alias" key's value is self.current_group, and the "kids" key's value is self.selected_values.
        self.bin_number: int
            The text of the self.bin_edit (LineEdit) typed as int. This attribute determines the number of bins.
        self.selected_values: list
            This attribute is iteratively cleared and then populated with the values of the active bin.
        self.current_group: str
            This attribute is constructed from the concatenation of "Group" and the number of groups in self.groups (list).
        self.tree_group: QTreeWidgetItem
            This attribute is a first-level child of self.variable_tree (TreeWidget) with self.current_group set as its text. It is iteratively populated by kid (TreeWidgetItem). 
        kid: QTreeWidgetItem
            This variable is a first-level child of self.tree_group (TreeWidgetItem) and thus a second-level child of self.variable_tree (TreeWidget). It iteratively populates its parent self.tree_group (TreeWidgetItem) with values from self.selected_values (list) typed as str. This unhelpfully named variable is distinct from the attribute self.kids (dict). 
        """
        print("annot.binning_count_continued()")
        self.group_list.clear()
        self.variable_tree.clear()
        self.selected_values = []
        self.groups = []
        value_list = self.metadata[self.variable_list_columns.selectedItems()[0].text()]
        value_list = value_list.sort_values()
        value_list = [v for v in value_list if not(pd.isna(v))]
        self.bin_number = int(self.bin_edit.text())
        diff = len(value_list)
        cutt_off = int(diff/self.bin_number)
        for x in range(self.bin_number):
            self.selected_values = []

            if x == self.bin_number - 1:
                self.selected_values = [v for v in value_list if v>=value_list[x*cutt_off]]
            else:
                self.selected_values = [v for v in value_list if (v>=value_list[x*cutt_off]) and (v<value_list[(x+1)*cutt_off])]
            self.current_group = 'Group {}'.format(len(self.groups)+1)
            self.group_list.addItem(self.current_group)

            self.tree_group = QTreeWidgetItem(self.variable_tree)
            self.tree_group.setExpanded(True)
            self.tree_group.setText(0, self.current_group)
            for y in self.selected_values:
                kid = QTreeWidgetItem(self.tree_group)
                kid.setText(0,str(y))
                self.tree_group.addChild(kid)
            self.groups.append({"alias": self.current_group,"kids":self.selected_values})

    def recode(self):  
        """
        Create a manually-selected bin from multiple values selected in self.variable_list_values (ListWidget). 

        Parameters
        --------
        self.variable_list_values: QListWidget
            This ListWidget displays the unique values of the self.metadata dataframe column selected by the user in self.variable_list_columns. Not editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.variable_tree: QTreeWidget
            This TreeWidget displays the new groups and all of their contents (all values, not just unique values). Not editable.
        self.groups: list
            This attribute is set as an empty list.
        self.selected_values: list
            This attribute is set as an empty list.
        
        Outputs
        --------
        self.group_list: QListWidget
            This ListWidget is cleared and then iteratively populated by successive self.current_group values, i.e. Group 1, Group 2, etc. ListWidgetItem is editable so the user can change the names to something less generic than Group 1. 
        self.variable_tree: QTreeWidget
            This TreeWidget provides a nested display of the new groups and all of their contents (all values, not just unique values). It is cleared and then iteratively populated by self.tree_group (TreeWidgetItem). Not editable.
        self.groups: list
            This attribute is cleared and then populated with a list of dictionaries (why?). Each dictionary consists of one level with two keys: the "alias" key's value is self.current_group, and the "kids" key's value is self.selected_values.
        self.selected_values: list
            This attribute is iteratively cleared and then populated with the values of the active bin.
        self.current_group: str
            This attribute is constructed from the concatenation of "Group" and the number of groups in self.groups (list).
        self.tree_group: QTreeWidgetItem
            This attribute is a first-level child of self.variable_tree (TreeWidget) with self.current_group set as its text. It is iteratively populated by kid (TreeWidgetItem). 
        kid: QTreeWidgetItem
            This variable is a first-level child of self.tree_group (TreeWidgetItem) and thus a second-level child of self.variable_tree (TreeWidget). It iteratively populates its parent self.tree_group (TreeWidgetItem) with values from self.selected_values (list) typed as str. This unhelpfully named variable is distinct from the attribute self.kids (dict). 
        """
        print("annot.recode()") 
        self.selected_values=[]
        for value in list(self.variable_list_values.selectedItems()):
            self.selected_values.append(value.text())

        self.current_group = 'Group {}'.format(len(self.groups)+1)
        self.group_list.addItem(self.current_group)

        self.tree_group = QTreeWidgetItem(self.variable_tree)
        self.tree_group.setExpanded(True)
        self.tree_group.setText(0, self.current_group)
        for x in self.selected_values:
            print(f'manual binning:{type(x)}')
            kid = QTreeWidgetItem(self.tree_group)
            kid.setText(0,x)
            self.tree_group.addChild(kid)
        self.groups.append({"alias": self.current_group,"kids":self.selected_values})
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
        Change the text of the first-level TreeWidgetItem in self.variable_tree that corresponds to the selected ListWidgetItem in self.group_list (ListWidget) that was edited by self.relabel_group().

        Parameters
        --------
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.variable_tree: QTreeWidget
            This TreeWidget displays the groups and all of their contents (all values, not just unique values). Not editable.
        item: QListWidgetItem
            This ListWidgetItem in self.group_list (ListWidget) has been selected by the user.
        self.groups: list
            This attribute is a list of dictionaries. Each dictionary consists of one level with two keys: the "alias" key's value is self.current_group, and the "kids" key's value is self.selected_values.

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
        Change the text of the selected ListWidgetItem in self.variable_list_columns (ListWidget). Currently, there is nothing preventing the user from renaming a column with a header that's already in use, which will cause problems in either BASSPRO or STAGG.

        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.metadata dataframe. ListWidgetItem is editable.
        item: QListWidgetItem
            This ListWidgetItem in self.variable_list_columns (ListWidget) has been selected by the user.

        Outputs
        --------
        self.variable_list_columns: QListWidget
            The text of item (ListWidgetItem) is edited by the user.
        """
        print("annot.relabel_column()")
        index = self.variable_list_columns.currentIndex()
        item = self.variable_list_columns.itemFromIndex(index)
        if index.isValid():
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.variable_list_columns.edit(index)

    def column_label(self):
        """
        Change the text of the header in self.metadata dataframe that corresponds to the selected ListWidgetItem in self.variable_list_columns that was edited by self.relabel_column().

        Parameters
        ------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.metadata dataframe. ListWidgetItem is editable.
        item: QListWidgetItem
            This ListWidgetItem in self.variable_list_columns (ListWidget) has been selected by the user.
        self.metadata: Dataframe
            This attribute is set as a dataframe.

        Outputs
        --------
        self.metadata: Dataframe
            The header corresponding to item (ListWidgetItem) is changed in the dataframe to reflect the user's edit.
        """
        print("annot.column_label()")
        index = self.variable_list_columns.currentIndex()
        item = self.variable_list_columns.itemFromIndex(index)
        self.metadata.rename(columns = {self.column:item.text()}, inplace=True)

    def naming(self):
        """
        Change the name of the new column by appending a suffix "_recode_#" to avoid duplicate column names in the metadata.

        Parameters
        --------
        self.metadata: Dataframe
            This attribute is a dataframe.
        self.column: str
            This attribute is the text of the ListWidgetItem in self.variable_list_columns (ListWidget) selected by the user. It is one of the headers of the self.metadata dataframe.
        
        Outputs
        --------
        self.new_column: str
            This attribute is constructed from the concatenation of str value in self.column and "_recode_#".
        """
        print("annot.naming()")
        c=1
        if any(f"{self.column}_recode" in col for col in self.metadata.columns):
            c+=1
            self.new_column = f"{self.column}_recode_{c}"
        else:
            self.new_column = f"{self.column}_recode_1"

    def add_config(self):
        """
        Create a new column in the self.metadata dataframe from self.groups and update self.variable_list_column to reflect the added column.

        Parameters
        --------
        self.variable_list_columns: QListWidget
            This ListWidget displays the headers of the self.metadata dataframe. ListWidgetItem is editable.
        self.variable_list_values: QListWidget
            This ListWidget displays the unique values of the self.metadata dataframe column selected by the user in self.variable_list_columns. Not editable.
        self.group_list: QListWidget
            This ListWidget displays the new groups and allows the user the change the name of the group. ListWidgetItem is editable.
        self.metadata: Dataframe
            This attribute is set as a dataframe.
        self.groups: list
            This attribute is cleared and then populated with a list of dictionaries (why?). Each dictionary consists of one level with two keys: the "alias" key's value is self.current_group, and the "kids" key's value is self.selected_values.
        self.new_column: str
            This attribute is constructed from the concatenation of str value in self.column and "_recode_#" in self.naming().
        
        Outputs
        --------
        self.megameta: Dataframe
            This attribute is a copy of the self.metadata dataframe. A new column is added to the dataframe based on the contents of self.group (list).
        self.metadata: Dataframe
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
        print("annot.add_config()")
        self.megameta = self.metadata.copy()
        self.naming()
        for group in self.groups:
            for value in group["kids"]:
                self.megameta.loc[self.megameta[self.column].astype(str)==str(value),
                    [self.new_column]]=group["alias"]
        self.variable_list_columns.clear()
        self.variable_list_values.clear()
        self.group_list.clear()
        for x in self.megameta.columns:
            self.variable_list_columns.addItem(x)
        self.metadata=self.megameta.copy()
        self.groups=[]

    def save_config(self):
        """
        Write the self.metadata dataframe to a csv file saved by the user via a standard FileDialog, populate self.pleth.metadata with the corresponding file path, and add the file path as a ListWidgetItem to self.pleth.metadata_list (ListWidget).

        Parameters
        --------
        file: QFileDialog
            This variable stores the path of the file the user selected via the FileDialog.
        self.metadata: Dataframe
            This attribute is set as a dataframe.
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        self.pleth.breath_df: list
            This Plethysmography class attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        
        Outputs
        --------
        self.pleth.metadata: str
            This Plethysmography class attribute stores the path of the csv file that self.metadata dataframe was written to.
        self.pleth.metadata_list: QListWidget
            This ListWidget is populated with the file path in self.pleth.metadata.
        
        Outcomes
        --------
        self.pleth.update_breath_df()
            This Plethysmography class method updates the Plethysmography class attribute self.pleth.breath_df to reflect the changes to the metadata.
        """
        print("annot.save_config()")
        try:
            file, filter = QFileDialog.getSaveFileName(self, 'Save File', '', ".csv(*.csv))")
            self.metadata.to_csv(file, index = False)
            self.pleth.metadata = file
        except PermissionError:
            reply = QMessageBox.information(self, 'File in use', 'One or more of the files you are trying to save is open in another program.', QMessageBox.Ok)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')

        if self.pleth.breath_df != []:
            self.pleth.update_breath_df()

    def cancel_annot(self):
        print("annot.cancel_annot()")
        self.metadata = None

class MetadataSettings(Settings):

    valid_filetypes = ['.csv', '.xlsx']
    file_chooser_message = 'Select metadata file'
    editor_class = Annot

    @staticmethod
    def _right_filename(filepath):
        file_basename = os.path.basename(filepath) 
        return file_basename.startswith("metadata")

    def attempt_load(metadata_file):
        # Check file types
        if metadata_file.endswith(".csv"):
            return pd.read_csv(metadata_file)
        elif metadata_file.endswith(".xlsx"):
            return pd.read_excel(metadata_file)
        else:
            return None
        