
from abc import abstractstaticmethod
import os
from pathlib import Path
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QTableWidgetItem

def notify_error(msg, title="Error"):
    QMessageBox.critical(None, title, msg)

def notify_warning(msg, title="Warning"):
    QMessageBox.warning(None, title, msg)

def notify_info(msg, title="Info"):
    QMessageBox.information(None, title, msg)
    
def ask_user(title, msg):
    reply = QMessageBox.question(None, title, msg, QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
    return reply

def choose_save_location(default_filename, file_types="*.csv"):
    """
    Pick a file location for basic settings
    """
    path, filter = QFileDialog.getSaveFileName(None, 'Save file', default_filename, file_types)
    return path

class Settings:

    @staticmethod
    def _right_filename(filepath):
        """
        Overwrite in derived class if necessary
        """
        return True

    @classmethod
    def validate(cls, filepath):
        file_extension = os.path.splitext(filepath)[1]
        right_filetype = file_extension in cls.valid_filetypes
        return cls._right_filename(filepath) and \
               right_filetype and Path(filepath).exists()

    @abstractstaticmethod
    def _save_file(filename, data):
        pass

    @classmethod
    def save_file(cls, data, save_filepath=None, workspace_dir=""):
        if not save_filepath:
            save_filepath, filter = QFileDialog.getSaveFileName(None, 'Save File', cls.default_filename, "*.csv")
            if not save_filepath:
                return False
        cls._save_file(save_filepath, data)
        return True

    @classmethod
    def open_file(cls, workspace_dir=""):
        while True:
            file, filter = QFileDialog.getOpenFileName(None, cls.file_chooser_message, workspace_dir)

            # Break if cancelled
            if not file:
                return None

            # If good file, return
            if cls.validate(file):
                return file

            # If bad file display error and try again
            filetypes_str = ", ".join([ft for ft in cls.valid_filetypes])
            notify_error(f"The selected file is not in the correct format. Only {filetypes_str} files are accepted.")

    @classmethod
    def edit(cls, *args, **kwargs):
        editor = cls.editor_class(*args, **kwargs)
        # If editor gui is accepted (Ok)
        if editor.exec():
            return editor.data
        # If rejected (Cancel)
        else:
            return None

    @staticmethod
    def attempt_load(filepath):
        raise NotImplemented

    @classmethod
    def require_load(cls, workspace_dir=""):
        while True:
            file = cls.open_file(workspace_dir=workspace_dir)
            if file and cls.validate(file):
                data = cls.attempt_load(file)
                return data

            if not ask_user("File is required", "You must choose a file to proceed"):
                return None


def avert_name_collision(column_name, columns):
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
    """

    # No issue, send it back
    if column_name not in columns:
        return column_name
    
    name_taken = True
    count = 0
    # Keep incrementing count until we get a unique name
    while name_taken:
        # Generate new name with count appended
        new_column_name = f"{column_name}_{count+1}"

        # Assume new name
        name_taken = False
        
        # Check if any are named the same
        for col in columns:
            if col == new_column_name:
                name_taken = True
        
        # Increment and try again
        count += 1

    return new_column_name

def populate_table(frame, table):
    """
    This method populates the self.{division}_table widgets with the appropriate portions of the self.data dataframe based on the relationship of particular rows to particular divisions as defined in the "Settings Names" dictionary within self.pleth.gui_config.

    Parameters
    --------
    frame: Dataframe
        This variable refers to the appropriate portion of the self.data dataframe.
    table: QTableWidget
        This variable refers to the appropriate self.{division}_table.

    Outputs
    --------
    self.{division}_table: QTableWidget
        The TableWidget referred to by the argument "table" is populated with the appropriate settings from self.data dataframe as contained in the argument "frame".
    """
    # Populate tablewidgets with views of uploaded csv. Currently editable.
    table.setColumnCount(len(frame.columns))
    table.setRowCount(len(frame))
    for col in range(table.columnCount()):
        for row in range(table.rowCount()):
            table.setItem(row,col,QTableWidgetItem(str(frame.iloc[row,col])))
    table.setHorizontalHeaderLabels(frame.columns)
    table.resizeColumnsToContents()
    table.resizeRowsToContents()