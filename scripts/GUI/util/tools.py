
from abc import ABC, abstractstaticmethod
import os
from pathlib import Path
from typing import List, Optional
from PyQt5.QtWidgets import QFileDialog
from util.ui.dialogs import ask_user_ok, notify_error

class Settings(ABC):
    """Abstract class used to implement read, write, and validation for different sets of Settings"""
    naming_requirements = []

    @classmethod
    def _right_filename(cls, filepath):
        """Validate whether the input filepath has the correct naming"""
        right_filename = all(name_str in os.path.basename(filepath) for name_str in cls.naming_requirements)
        return right_filename

    @classmethod
    def validate(cls, filepath):
        """Validate that the given filepath exists and has the right type and name"""
        file_extension = os.path.splitext(filepath)[1]
        right_filetype = file_extension in cls.valid_filetypes
        return cls._right_filename(filepath) and \
               right_filetype and Path(filepath).exists()

    @abstractstaticmethod
    def _save_file(filepath, data):
        """Save data data to a filepath"""
        pass

    @classmethod
    def save_file(cls, data, save_filepath: Optional[str] = None):
        """
        Make sure there's a save filepath, then call subclass's save method
        
        Parameters
        ---------
        data: data to write
        save_filepath: location to save data

        Returns
        ------
        bool: whether save was successful
        """
        if not save_filepath:
            save_filepath, filter = QFileDialog.getSaveFileName(None, 'Save File', cls.default_filename, "*.csv")
            if not save_filepath:
                return False
        # Send a copy of the data in case there are transformations before saving
        cls._save_file(save_filepath, data.copy())
        return True

    @classmethod
    def open_files(cls, output_dir: str = ""):
        """
        Select multiple files and return after validation
        
        Parameters
        ---------
        output_dir: default path for file browser
        
        Returns
        ------
        Optional[list[str]]: selected files
        """
        while True:
            filter = ' '.join(['*' + ext for ext in cls.valid_filetypes])
            files, filter = QFileDialog.getOpenFileNames(None, cls.file_chooser_message, output_dir, filter)

            # Break if cancelled
            if not files:
                return None

            # If good files, return
            if all([cls.validate(file) for file in files]):
                return files

            cls._display_bad_file_error()

    @classmethod
    def open_file(cls, output_dir: str = ""):
        """
        Select single file and return after validation
        
        Parameters
        ---------
        output_dir: default path for file browser
        
        Returns
        ------
        Optional[str]: selected file
        """
        while True:
            filter = ' '.join(['*' + ext for ext in cls.valid_filetypes])
            file, filter = QFileDialog.getOpenFileName(None, cls.file_chooser_message, output_dir, filter)

            # Break if cancelled
            if not file:
                return None

            # If good file, return
            if cls.validate(file):
                return file

            cls._display_bad_file_error()
            
    @classmethod
    def _display_bad_file_error(cls):
        """Notify user of file requirements"""
        # If bad file display error and try again
        filetypes_str = ", ".join(cls.valid_filetypes)
        filenames_str = " and ".join(f"'{name}'" for name in cls.naming_requirements)
        msg  =  "The selected file is not in the correct format."
        msg += f"\nFilename must include: {filenames_str}"
        msg += f"\nValid filetypes: {filetypes_str}"
        notify_error(msg)

    @classmethod
    def edit(cls, *args, **kwargs):
        """
        Open settings editor and return result
        
        Returns
        ------
        Optional[Any]: return value of editor
        """
        editor = cls.editor_class(*args, **kwargs)
        # If editor gui is accepted (Ok)
        if editor.exec():
            return editor.data
        # If rejected (Cancel)
        else:
            return None

    @abstractstaticmethod
    def attempt_load(filepath):
        """Attempt to load file"""
        pass

    @classmethod
    def import_file(cls, output_dir=""):
        """
        Select file and load
        
        Returns
        ------
        Optional[Any]: result of subclass load method
        """
        file = cls.open_file(output_dir=output_dir)
        if not file:
            return None
        
        data = cls.attempt_load(file)
        if not data:
            return None

        return data


def avert_name_collision(new_name: str, existing_names: List[str]):
    """
    Auto-rename of `new_name` if collision in `existing_names`

    Parameters
    ---------
    new_name: intended name to be given
    existing_names: list of all current names

    Returns
    ------
    Optional[str]: unique name
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
    """Generate a unique id given a list of ids"""
    new_id = 0
    # Keep incrementing id until we get an id that is not used
    while new_id in existing_ids:
        new_id += 1
    return new_id
