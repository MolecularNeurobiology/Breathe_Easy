
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtCore import Qt

class AlignDelegate(QStyledItemDelegate):
    """
    This class assigns delegates to Config.variable_table and Config.loop_table TableWidgets and and centers the delegate items.

    Parameters
    --------
    QStyledItemDelegate: class
        The AlignDelegate class inherits properties and methods from the QStyledItemDelegate class.
    """
    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter
