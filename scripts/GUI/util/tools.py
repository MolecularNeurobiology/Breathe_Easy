
from abc import abstractstaticmethod
import os
from pathlib import Path
from PyQt5.QtWidgets import QFileDialog
from util.ui.dialogs import ask_user_ok, notify_error

class Settings:
    naming_requirements = []

    @classmethod
    def _right_filename(cls, filepath):
        right_filename = all(name_str in os.path.basename(filepath) for name_str in cls.naming_requirements)
        return right_filename

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
    def open_files(cls, workspace_dir=""):
        while True:
            files, filter = QFileDialog.getOpenFileNames(None, cls.file_chooser_message, workspace_dir)

            # Break if cancelled
            if not files:
                return None

            # If good files, return
            if all([cls.validate(file) for file in files]):
                return files

            cls._display_bad_file_error()

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

            cls._display_bad_file_error()
            
    @classmethod
    def _display_bad_file_error(cls):
        # If bad file display error and try again
        filetypes_str = ", ".join(cls.valid_filetypes)
        filenames_str = " and ".join(f"'{name}'" for name in cls.naming_requirements)
        msg  =  "The selected file is not in the correct format."
        msg += f"\nFilename must include: {filenames_str}"
        msg += f"\nValid filetypes: {filetypes_str}"
        notify_error(msg)

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
    @abstractstaticmethod
    def attempt_load(filepath):
        pass

    @classmethod
    def import_file(cls, workspace_dir=""):
        """ Choose file and load """
        file = cls.open_file(workspace_dir=workspace_dir)
        if not file:
            return None
        
        data = cls.attempt_load(file)
        if not data:
            return None

        return data


def avert_name_collision(new_name, existing_names):
    """
    """

    # No issue, send it back
    if new_name not in existing_names:
        return new_name
    
    name_taken = True
    count = 0
    # Keep incrementing count until we get a unique name
    while name_taken:
        # Generate new name with count appended
        modified_name = f"{new_name}_{count+1}"
        
        # Check if any are named the same
        name_taken = modified_name in existing_names
        
        # Increment and try again
        count += 1

    msg = f"The column name {new_name} already exists."
    msg += f"\nWould you like to use {modified_name} instead?"
    reply = ask_user_ok("Duplicate Column Name", msg)

    # Use modified name
    if reply:
        new_name = modified_name

    # Cancel, tell calling function the user cancelled
    else:
        new_name = None

    return new_name

def generate_unique_id(existing_ids):
    new_id = 0
    # Keep incrementing id until we get an id that is not used
    while new_id in existing_ids:
        new_id += 1
    return new_id