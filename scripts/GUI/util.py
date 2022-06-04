
from abc import abstractstaticmethod
import os
from pathlib import Path
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QTableWidgetItem, QComboBox, QCheckBox, QLineEdit, QPushButton, QStyle
from checkable_combo_box import CheckableComboBox

# TODO: split into PyQt-specific utils
def update_checkable_combo_values(combo, valid_values, renamed=None, default_value=""):
    combo.blockSignals(True)

    # Store current value
    curr_values = combo.currentData()

    # Clear out and add new items
    combo.clear()
    if default_value is not None:
        combo.addItem(default_value)
    combo.addItems(valid_values)

    # Check if I need to update the name of my selected value
    if renamed:
        old_name, new_name = renamed
        if old_name in curr_values:
            idx = curr_values.index(old_name)
            curr_values[idx] = new_name

    # if curr selection is still indep/cov, keep in box
    still_selected = [val for val in curr_values if val in valid_values]
    combo.loadCustom(still_selected)

    combo.blockSignals(False)

def update_combo_values(combo, valid_values, renamed=None, default_value=""):
    combo.blockSignals(True)

    # Store current value
    curr_value = combo.currentText()

    # Clear out and add new items
    combo.clear()
    if default_value is not None:
        combo.addItem(default_value)
    combo.addItems(valid_values)

    # Check if I need to update the name of my selected value
    if renamed:
        old_name, new_name = renamed
        if curr_value == old_name:
            curr_value = new_name

    # if curr selection is still indep/cov, keep in box
    if curr_value in valid_values:
        combo.setCurrentText(curr_value)

    combo.blockSignals(False)

def read_widget(widget):

    if type(widget) is QTableWidgetItem:
        widget_data = widget.text()

    elif type(widget) is QCheckBox:
        widget_data = int(widget.isChecked())

    elif type(widget) is QComboBox:
        widget_data = widget.currentText()

    elif type(widget) is CheckableComboBox:
        widget_data = widget.currentData()

    else:
        raise RuntimeError(f"Cannot read {type(widget)}!!")

    return widget_data

def write_widget(widget, text):
    widget.blockSignals(True)
    if type(widget) is QComboBox:
        widget.setCurrentText(text)
    elif type(widget) is QLineEdit:
        widget.setText(text)
    else:
        raise RuntimeError(f"Cannot write {type(widget)}!!")
    widget.blockSignals(False)

def notify_error(msg, title="Error"):
    QMessageBox.critical(None, title, msg)

def notify_warning(msg, title="Warning"):
    QMessageBox.warning(None, title, msg)

def notify_info(msg, title="Info"):
    QMessageBox.information(None, title, msg)

def nonblocking_msg(msg, callbacks, title="", msg_type='info'):
    msgBox = QMessageBox()
    msgBox.setText(msg)
    if title:
        msgBox.setWindowTitle(title)
    msgBox.setModal(False)

    if msg_type == 'yes':
        assert len(callbacks) == 2, "Must have 2 callbacks for yes/no message"
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        # Attach callbacks to Yes and No buttons
        buttons = msgBox.buttons()
        for button, callback in zip(buttons, callbacks):
            # Connect Yes button to callback
            button.clicked.connect(callback)

    elif msg_type == 'info':
        assert len(callbacks) == 1, "Must have 1 callback for info message"
        msgBox.setStandardButtons(QMessageBox.Ok)
        
        # Attach callback to Ok button
        buttons = msgBox.buttons()
        buttons[0].clicked.connect(callbacks[0])

    else:
        raise RuntimeError(f"Bad message type: {msg_type}")

    msgBox.show()
    return msgBox
    

def ask_user_yes(title, msg):
    reply = QMessageBox.question(None, title, msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
    return reply == QMessageBox.Yes
    
def ask_user_ok(title, msg):
    reply = QMessageBox.question(None, title, msg, QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
    return reply == QMessageBox.Ok

def choose_save_location(default_filename, file_types="*.csv"):
    """
    Pick a file location for basic settings
    """
    path, filter = QFileDialog.getSaveFileName(None, 'Save file', default_filename, file_types)
    return path

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
        msg = "The selected file is not in the correct format."
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

        # Assume new name
        name_taken = False
        
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

def generate_unique_id(existing_ids):
    new_id = 0
    # Keep incrementing id until we get an id that is not used
    while new_id in existing_ids:
        new_id += 1
    return new_id