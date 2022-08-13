from typing import Iterable, Optional, Union
import pandas as pd
from checkable_combo_box import CheckableComboBox
from PyQt5.QtWidgets import QTableWidgetItem, QComboBox, QCheckBox, QLineEdit, QTableWidget
from PyQt5.QtCore import Qt

def update_checkable_combo_values(combo: QComboBox, valid_values: Iterable[str],
                                  renamed: Optional[Iterable[str]] = None, default_value: str = ""):
    """
    Update the options and selections in a checkable combo box
    
    Account for renames and no-longer-valid values

    Parameters
    ---------
    combo: combo box to update
    valid_values: list of all possible valid options
    renamed: tuple of (old, new) renamed item
    default_value: default combo box option
    """
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

def update_combo_values(combo: QComboBox, valid_values: Iterable[str],
                        renamed: Optional[Iterable[str]] = None,
                        default_value: str = ""):
    """
    Update the values and selection in a ComboBox
    
    Account for renames and no-longer-valid values

    Parameters
    ---------
    combo: combo box to update
    valid_values: list of all possible valid options
    renamed: tuple of (old, new) renamed item
    default_value: default combo box option
    """
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

    # if curr selection is still valid, keep in box
    if curr_value in valid_values:
        combo.setCurrentText(curr_value)

    combo.blockSignals(False)

def update_hierarchical_combos(valid_values: Iterable[str], combos: Iterable[QComboBox], default_value: str,
                               renamed: Optional[Iterable[str]] = None, enable_set: bool = True,
                               first_required: bool = False):
    """
    Populate a sequence of combo boxes which maintain dependencies on their previous sibling
    
    Parameters
    ---------
    valid_values: initial valid values used to populate the first combo box
    combos: combo boxes to populate, in order
    default_value: default option used to populate the first index of the combos
    renamed: tuple of (old, new) renamed item
    enable_set: whether the set of combo boxes should be enabled
                in case there is an external dependency
    first_required: whether the first should be given a default placeholder value
                    or only the list of valid values

    Dependencies:
        - Combo box enabled only if previous sibling has a selected value other than the `default_value`
        - Valid values are the previous valid values, minus the selected value of the previous sibling
    """
    prev_selected = enable_set
    for i, combo in enumerate(combos):
        enabled = prev_selected
        combo.setEnabled(enabled)

        # Set all disabled boxes to default val
        # NOTE: Continue on to make sure that values are populated.
        #   This becomes important when setting the text of the
        #   combo from loaded data requires that the value is
        #   available in the list already
        if not enabled:
            combo.blockSignals(True)
            combo.setCurrentText(default_value)
            combo.blockSignals(False)

        # If this one is required, dont provide a default
        _default_value = None if (first_required and i==0) else default_value

        # Update value based on valid values and any renamed variables
        update_combo_values(combo, valid_values, renamed=renamed, default_value=_default_value)

        # Check if the curr_value was set back to default
        curr_value = combo.currentText()
        prev_selected = (curr_value != default_value)

        # remove this value from the options for the next boxes
        valid_values = valid_values[valid_values != curr_value]

def read_widget(widget: Union[QTableWidget, QCheckBox, QComboBox, CheckableComboBox]):
    """Return the value of the given widget"""

    if type(widget) is QTableWidgetItem:
        widget_data = widget.text()

    # TODO: Should this return bool?
    elif type(widget) is QCheckBox:
        widget_data = int(widget.isChecked())

    elif type(widget) is QComboBox:
        widget_data = widget.currentText()

    elif type(widget) is CheckableComboBox:
        widget_data = widget.currentData()

    else:
        raise RuntimeError(f"Cannot read {type(widget)}!!")

    return widget_data

def write_widget(widget: Union[QComboBox, QLineEdit], text: str):
    """Set the text of a widget"""
    widget.blockSignals(True)
    if type(widget) is QComboBox:
        widget.setCurrentText(text)
    elif type(widget) is QLineEdit:
        widget.setText(text)
    else:
        raise RuntimeError(f"Cannot write {type(widget)}!!")
    widget.blockSignals(False)

def populate_table(df: pd.DataFrame, table: QTableWidget, disable_edit: Iterable = []):
    """
    Populate a given TableWidget with the data in a given DataFrame.
    
    Parameters
    ---------
    df: given data
    table: table widget to populate
    disable_edit: all columns to be disabled
    """
    # Set table size
    table.setColumnCount(len(df.columns))
    table.setRowCount(len(df))

    # Set table data
    for col in range(table.columnCount()):
        for row in range(table.rowCount()):
            new_item = QTableWidgetItem(str(df.iloc[row, col]))
            if col in disable_edit:
                new_item.setFlags(new_item.flags() & ~Qt.ItemIsEditable)  # read-only!
            table.setItem(row, col, new_item)

    # Set headers
    table.setHorizontalHeaderLabels(df.columns)

    table.resizeColumnsToContents()
    table.resizeRowsToContents()