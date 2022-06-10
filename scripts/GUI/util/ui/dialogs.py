
from PyQt5.QtWidgets import QMessageBox, QFileDialog

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
