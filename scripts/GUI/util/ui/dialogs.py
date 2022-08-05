
from typing import Callable, Iterable
from PyQt5.QtWidgets import QMessageBox, QFileDialog

def notify_error(msg: str, title: str = "Error"):
    """Notify user of some error"""
    QMessageBox.critical(None, title, msg)

def notify_warning(msg: str, title: str = "Warning"):
    """Notify user of some warning"""
    QMessageBox.warning(None, title, msg)

def notify_info(msg: str, title: str = "Info"):
    """Notify user of some information"""
    QMessageBox.information(None, title, msg)

def nonblocking_msg(msg: str, callbacks: Iterable[Callable], title: str = "", msg_type: str = 'info'):
    """
    Create and display a popup message that is non-modal and non-blocking
    
    Non-modal: new window does not prevent user from interacting with parent window
    Non-blocking: asynchronous; processing does not wait for close of new window

    Parameters
    ---------
    msg: message to display
    callbacks: functions to assign to each button given
    title: title of message window
    msg_type: which default window setup to use (defines # buttons and labels)

    Returns
    ------
    QMessageBox: the newly constructed message window
    """
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

    # elif msg_type == 'custom':
    else:
        raise RuntimeError(f"Bad message type: {msg_type}")

    msgBox.show()
    return msgBox
    
def ask_user_yes(title: str, msg: str):
    """
    Display popup message with default Yes/No responses
    
    Returns
    ------
    bool: whether the selected response is "Yes"
    """
    reply = QMessageBox.question(None, title, msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
    return reply == QMessageBox.Yes
    
def ask_user_ok(title: str, msg: str):
    """
    Display popup message with default Ok/Cancel responses

    Returns
    ------
    bool: whether the selected response is "Ok"
    """
    reply = QMessageBox.question(None, title, msg, QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
    return reply == QMessageBox.Ok

def choose_save_location(default_filename: str, file_types: str = "*.csv"):
    """
    Pick a file location for saving a file

    Parameters
    ---------
    default_filename: default filename to populate file browser
    file_types: string representing regex filter of file types

    Returns
    ------
    str: selected file path
    """
    path, filter = QFileDialog.getSaveFileName(None, 'Save file', default_filename, file_types)
    return path
