
from ui.ordering_form import Ui_GroupOrdering
from PyQt5.QtWidgets import QDialog

class OrderingWindow(QDialog, Ui_GroupOrdering):
    def __init__(self, window_title, group_name, items):
        super().__init__()
        self.setupUi(self)
        
        # Set title label to show where list of values comes from
        self.title.setText(f"{window_title.upper()} -- {group_name} Items")

        # Callbacks
        self.up_button.clicked.connect(self.item_up)
        self.down_button.clicked.connect(self.item_down)

        self.set_items(items)

    def get_items(self):
        return [self.item_list.item(i).text() for i in range(self.item_list.count())]

    def set_items(self, items):
        self.item_list.clear()
        [self.item_list.addItem(item) for item in items]

    def move(self, idx, new_idx):
        items = self.get_items()

        # Remove item
        selected_item = items.pop(idx)
        
        # Re-insert at given jump from index
        items.insert(new_idx, selected_item)
        
        # Push back to listwidget
        self.set_items(items)
        
    def item_up(self):
        curr_idx = self.item_list.currentRow()
        new_idx = max(0, curr_idx - 1)
        self.move(curr_idx, new_idx)
        self.item_list.setCurrentRow(new_idx)

    def item_down(self):
        curr_idx = self.item_list.currentRow()
        new_idx = min(self.item_list.count()-1, curr_idx + 1)
        self.move(curr_idx, new_idx)
        self.item_list.setCurrentRow(new_idx)