
from typing import Iterable
from PyQt5.QtWidgets import QComboBox, QStyledItemDelegate, qApp
from PyQt5.QtGui import QPalette, QFontMetrics, QStandardItem
from PyQt5.QtCore import QEvent, Qt

# Subclass Delegate to increase item height
class Delegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        return size

class CheckableComboBox(QComboBox):
    # source: https://gis.stackexchange.com/questions/350148/qcombobox-multiple-selection-pyqt5
    """
    The CheckableComboBox class populates a comboBox with checkable items (checkboxes).

    Attributes
    ---------
    model: the underlying data of the widget
    lineEdit: the main primary output line of the combobox that
              remains when dropdown closes
    """

    def __init__(self, *args, **kwargs):
        """Initialize instance and set data and display configuration"""
        super().__init__(*args, **kwargs)

        # Make the combo editable to set a custom text, but readonly
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        # Make the lineedit the same color as QPushButton
        palette = qApp.palette()
        palette.setBrush(QPalette.Base, palette.button())
        self.lineEdit().setPalette(palette)

        # Use custom delegate
        self.setItemDelegate(Delegate())

        # Update the text when an item is toggled
        self.model().dataChanged.connect(self.updateData)

        # Hide and show popup when clicking the line edit
        self.lineEdit().installEventFilter(self)
        self.closeOnLineEditClick = False

        # Prevent popup from closing when clicking on an item
        self.view().viewport().installEventFilter(self)

    def resizeEvent(self, event):
        # Recompute text to elide as needed
        self.updateText()
        super().resizeEvent(event)

    def updateData(self, new_index):
        """Update underlying data to reflect a new selection"""
        new_item = new_index.data()

        model = self.model()
        checked_items = [model.item(i).text() for i in range(model.rowCount()) if model.item(i).checkState() == Qt.Checked]

        # If none is selected, clear everything
        if new_item == "None":
            self.check_items(["None"])
        elif new_item == "Custom":
            self.check_items(["Custom"])
        # If something other than custom is selected, unselect custom
        elif "Custom" in checked_items and len(checked_items) > 1:
            # TODO: Can we just re-use check_items() here? doing the same thing?
            self.uncheck_custom()

    def check_items(self, items: Iterable[str]):
        """Check the items in a given list"""

        model = self.model()
        all_options = [model.item(i).text() for i in range(model.rowCount())]

        # If we pick custom, let that be the only thing we pick
        if "Custom" in items:
            items = ["Custom"]
            # Make sure it's an option in the list
            if "Custom" not in all_options:
                self.addItem("Custom")
                all_options.append("Custom")
        elif "None" in items:
            items = []

        # Prevent any callbacks used for user selection on modifying model
        model.blockSignals(True)

        # Each index in model
        for i, text in enumerate(all_options):
            # If this one selected, check it
            if text in items:
                model.item(i).setCheckState(Qt.Checked)

            # Otherwise, uncheck it
            else:
                model.item(i).setCheckState(Qt.Unchecked)

        model.blockSignals(False)

    def eventFilter(self, object, event):
        """Customize the response if various mouse events"""
        # If clicking lineedit, toggle popup
        if object == self.lineEdit():
            if event.type() == QEvent.MouseButtonRelease:
                if self.closeOnLineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return False

        # If clicking an item in the viewport
        elif object == self.view().viewport():

            # If mouse released, toggle the check of the item under cursor
            if event.type() == QEvent.MouseButtonRelease:

                index = self.view().indexAt(event.pos())
                item = self.model().item(index.row())

                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                return True
        return False

    def showPopup(self):
        super().showPopup()
        # When the popup is displayed, a click on the lineedit should close it
        self.closeOnLineEditClick = True
        
        # Display nothing while selecting in the popup
        # Will update on close
        self.lineEdit().clear()

    def hidePopup(self):
        super().hidePopup()
        # Used to prevent immediate reopening when clicking on the lineEdit
        self.startTimer(100)

        # Refresh the display text when closing
        self.updateText()

    def timerEvent(self, event):
        # After timeout, kill timer, and reenable click on line edit
        self.killTimer(event.timerId())
        self.closeOnLineEditClick = False

    def updateText(self):
        """Update text of primary viewport (lineEdit)"""
        items = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                items.append(self.model().item(i).text())

        # join all items with commas
        text = ", ".join(items)

        # Compute elided text (with "...")
        metrics = QFontMetrics(self.lineEdit().font())
        elidedText = metrics.elidedText(text, Qt.ElideRight, self.lineEdit().width())
        old_text = self.lineEdit().text()
        self.lineEdit().setText(elidedText)

        if old_text != elidedText:
            self.currentIndexChanged.emit(1)

    def uncheck_custom(self):
        model = self.model()
        all_text = [model.item(i).text() for i in range(model.rowCount())]
        if "Custom" in all_text:
            custom_idx = all_text.index("Custom")
            self.model().blockSignals(True)
            model.item(custom_idx).setCheckState(Qt.Unchecked)
            self.model().blockSignals(False)

    def remove_custom(self):
        """Remove the custom option from the combobox"""
        model = self.model()
        all_text = [model.item(i).text() for i in range(model.rowCount())]
        if "Custom" in all_text:
            custom_idx = all_text.index("Custom")
            self.removeItem(custom_idx)

    def loadCustom(self, items):
        """Check all the items given"""
        self.remove_custom()
        self.check_items(items)
        self.updateText()

    def addItem(self, text: str, data=None):
        """
        Add a new item to the combo
        
        Parameters
        ---------
        text: label of new item
        data: 
        """
        item = QStandardItem()
        item.setText(text)
        if data is None:
            item.setData(text)
        else:
            item.setData(data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, items: Iterable[str], datalist=None):
        """
        Add multiple items to the combo

        Parameters
        ---------
        items: all items to be added
        datalist:
        """
        for i, text in enumerate(items):
            if datalist is None:
                data = None
            else:
                data = datalist[i]
            self.addItem(text, data)

    def currentData(self):
        """Return a list of the currently checked items"""
        # Return the list of selected items data
        res = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                res.append(self.model().item(i).data())
        return res
