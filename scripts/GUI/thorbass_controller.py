
from typing import Callable
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from ui.thorbass import Ui_Thorbass

class Thorbass(QDialog, Ui_Thorbass):
    """
    This class defines a specialized dialog that prompts the user to provide the necessary input for the function they are trying to use. It's instantiated by Manual.manual_merge() or Plethysmography.show_variable_config().

    Parameters
    --------
    QDialog: class
        The Thorbass class inherits properties and methods from the QDialog class.
    Ui_Thorbass: class
        The Thorbass class inherits widgets and layouts from the Ui_Thorbass class.
    """
    def __init__(self,Plethysmography):
        """"
        Instantiate the Thorbass class.

        Parameters
        --------
        Ui_Thorbass: class
            Thorbass inherits widgets and layouts of Ui_Thorbass.
        Plethysmography: class
            Thorbass inherits Plethysmography's methods, attributes, and widgets.
        
        Outputs
        --------
        self.pleth: class
            Shorthand for the Plethysmography class.
        """
        super(Thorbass, self).__init__()
        self.pleth = Plethysmography
        self.setupUi(self)
        self.setWindowTitle("Nailed it.")
        self.setAttribute(Qt.WA_DeleteOnClose)
    
    def message_received(self, title: str, words: str, new: Callable, opens: Callable):
        """
        Set the Dialog's window title as the text of "title", set the text of Label as the text of "words", assign the clicked signal and slot defined by "new" to Thorbass.new_button, and assign the clicked signal and slot defined by "opens" to Thorbass.open_button.

        Parameters
        --------
        title: str
            This argument is a string intended to be the Dialog's window title.
        words: str
            This argument is a string intended to be set as Thorbass.label's text.
        new: Callable
            This argument is a callable to either Manual.new_manual_file() or Plethysmography.new_variable_config().
        opens: Callable
            This argument is a callable to either Manual.open_manual_file() or Plethysmography.get_variable_config().


        Outputs
        --------
        Thorbass.label: QLabel
            The label displays the text provided as the argument "words" of Thorbass.message_received().
        Thorbass.new_button: QPushButton
            This PushButton is assigned the clicked signal and the slot defined by "new".
        Thorbass.open_button: QPushButton
            This PushButton is assigned the clicked signal and the slot defined by "opens".
        """
        print("thorbass.message_received()")
        self.setWindowTitle(title)
        self.label.setText(words)
        self.new_button.clicked.connect(new)
        self.open_button.clicked.connect(opens)