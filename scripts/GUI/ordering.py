
from typing import Any, List
from ui.ordering_form import Ui_GroupOrdering
from PyQt5.QtWidgets import QDialog

class OrderingWindow(QDialog, Ui_GroupOrdering):
    """
    Dialog used to reorder a variable's values
    """
    def __init__(self, window_title: str, variable_name: str, items: List[Any]):
        """
        Initialize dialog and populate the window with the input data

        Args:
            window_title: Title of window
            variable_name: name of variable whose values are displayed
            items: list of values for this variable
        """
        super().__init__()
        self.setupUi(self)
        
        # Set title label to show where list of values comes from
        self.title.setText(f"{window_title.upper()} -- {variable_name} Items")

        # Callbacks
        self.up_button.clicked.connect(self.item_up)
        self.down_button.clicked.connect(self.item_down)

        self.set_items(items)

    def get_items(self):
        """Get the current list ordering of items"""
        return [self.item_list.item(i).text() for i in range(self.item_list.count())]

    def set_items(self, items: List[Any]):
        """Reset the window with the given list of items"""
        self.item_list.clear()
        [self.item_list.addItem(str(item)) for item in items]

    def move(self, idx: int, new_idx: int):
        """Move an item from `idx` to `new_idx`"""
        items = self.get_items()

        # Remove item
        selected_item = items.pop(idx)
        
        # Re-insert at given jump from index
        items.insert(new_idx, selected_item)
        
        # Push back to listwidget
        self.set_items(items)
        
    def item_up(self):
        """Move the current selection up one"""
        curr_idx = self.item_list.currentRow()
        new_idx = max(0, curr_idx - 1)
        self.move(curr_idx, new_idx)
        self.item_list.setCurrentRow(new_idx)

    def item_down(self):
        """Move the current selection down one"""
        curr_idx = self.item_list.currentRow()
        new_idx = min(self.item_list.count()-1, curr_idx + 1)
        self.move(curr_idx, new_idx)
        self.item_list.setCurrentRow(new_idx)
