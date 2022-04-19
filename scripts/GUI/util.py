
import os
from pathlib import Path
from PyQt5.QtWidgets import QMessageBox, QFileDialog

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

    @classmethod
    def choose_file(cls, workspace_dir=""):
        while True:
            file, filter = QFileDialog.getOpenFileName(None, cls.file_chooser_msg, workspace_dir)

            # Break if cancelled
            if not file:
                return None

            # If good file, return
            if cls.validate(file):
                return file

            # If bad file display error and try again
            notify_error( 'The selected file is not in the correct format. Only .csv, .xlsx, or .JSON files are accepted.')

    @classmethod
    def edit(cls, *args, **kwargs):
        editor = cls.editor_class(*args, **kwargs)
        if editor.exec():
            # returned gracefully!
            # return settings
            pass
        else:
            # cancelled or closed
            return None

    @classmethod
    def choose_file(cls, workspace_dir):
        while True:
            file, filter = QFileDialog.getOpenFileName(None, cls.file_chooser_message, workspace_dir)

            # Break if cancelled
            if not file:
                return None

            # If good file, return
            if cls.validate(file):
                return file

            # If bad file display error and try again
            notify_error(f'The selected file is not in the correct format. Only {", ".join(cls.valid_filetypes)} files are accepted.')

    def attempt_load(filepath):
        raise NotImplemented

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
