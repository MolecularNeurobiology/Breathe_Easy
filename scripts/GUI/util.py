
from PyQt5.QtWidgets import QMessageBox, QFileDialog

def notify_error(msg, title="Error"):
    QMessageBox.critical(None, title, msg)

def notify_info(msg, title="Info"):
    QMessageBox.information(None, title, msg)

def choose_save_location(default_filename, file_types="*.csv"):
    """
    Pick a file location for basic settings
    """
    path, filter = QFileDialog.getSaveFileName(None, 'Save file', default_filename, file_types)
    return path
