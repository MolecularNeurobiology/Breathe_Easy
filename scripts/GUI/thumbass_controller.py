
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from ui.thumbass import Ui_Thumbass

class Thumbass(QDialog, Ui_Thumbass):
    """
    This class defines a simple dialog that displays information to the user.

    Parameters
    --------
    QDialog: class
        The Thumbass class inherits properties and methods from the QDialog class.
    Ui_Thumbass: class
        The Thumbass class inherits widgets and layouts from the Ui_Thumbass class.
    """
    def __init__(self,Plethysmography):
        """
        Instantiate the Thumbass class.

        Parameters
        --------
        Plethysmography: class
            Thumbass inherits Plethysmography's methods, attributes, and widgets.
        Ui_Thumbass: class
            Thumbass inherits widgets and layouts from the Ui_Thumbass class 
    
        Outputs
        --------
        Thumbass: QDialog
            The Dialog displays the output of Thumbass.message_received() and its window title is the text of the "title" argument of Thumbass.message_received().
        Thumbass.label: QLabel
            The label displays the text provided as the argument "words" of Thumbass.message_received().
        """
        super(Thumbass, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Nailed it.")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.label.setOpenExternalLinks(True)
    
    def message_received(self,title,words):
        """
        Set the Dialog's window title as the text of "title", set the text of Label as the text of "words".

        Parameters
        --------
        title: str
            This argument is a string intended to be the Dialog's window title.
        words: str
            This argument is a string intended to be set as Thumbass.label's text.

        Outputs
        --------
        Thumbass.label: QLabel
            The label displays the text provided as the argument "words" of Thumbass.message_received().
        """
        self.setWindowTitle(title)
        self.label.setText(words)