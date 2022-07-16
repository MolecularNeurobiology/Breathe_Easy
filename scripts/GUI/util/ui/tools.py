from checkable_combo_box import CheckableComboBox
from PyQt5.QtWidgets import QTableWidgetItem, QComboBox, QCheckBox, QLineEdit

def update_checkable_combo_values(combo, valid_values, renamed=None, default_value=""):
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

def update_combo_values(combo, valid_values, renamed=None, default_value=""):
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

def update_hierarchical_combos(valid_values, combos, default_value, renamed=None, enable_set=True, first_required=False):
    """ Populate a sequence of combo boxes which maintain dependencies on their previous sibling
    Dependencies:
        - Combo box enabled only if previous sibling has a selected value other than the `default_value`
        - Valid values are the previous valid values, less the selected value of the previous sibling
    
    Args:
        valid_values: initial valid values used to populate the first combo box
        combos: list of combo boxes to populate, in order
        default_value: default option used to populate the first index of the combos
        renamed: tuple mapping a renamed value from its old value to its new value
        enable_set: bool determining whether the set of combo boxes should be enabled
                    in case there is an external dependency
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

def read_widget(widget):

    if type(widget) is QTableWidgetItem:
        widget_data = widget.text()

    elif type(widget) is QCheckBox:
        widget_data = int(widget.isChecked())

    elif type(widget) is QComboBox:
        widget_data = widget.currentText()

    elif type(widget) is CheckableComboBox:
        widget_data = widget.currentData()

    else:
        raise RuntimeError(f"Cannot read {type(widget)}!!")

    return widget_data

def write_widget(widget, text):
    widget.blockSignals(True)
    if type(widget) is QComboBox:
        widget.setCurrentText(text)
    elif type(widget) is QLineEdit:
        widget.setText(text)
    else:
        raise RuntimeError(f"Cannot write {type(widget)}!!")
    widget.blockSignals(False)

def populate_table(frame, table):
    """
    This method populates the self.{division}_table widgets with the appropriate portions of the self.data dataframe based on the relationship of particular rows to particular divisions as defined in the "Settings Names" dictionary within self.pleth.gui_config.

    Parameters
    --------
    frame: Dataframe
        This variable refers to the appropriate portion of the self.data dataframe.
    table: QTableWidget
        This variable refers to the appropriate self.{division}_table.

    Outputs
    --------
    self.{division}_table: QTableWidget
        The TableWidget referred to by the argument "table" is populated with the appropriate settings from self.data dataframe as contained in the argument "frame".
    """
    # Populate tablewidgets with views of uploaded csv. Currently editable.
    table.setColumnCount(len(frame.columns))
    table.setRowCount(len(frame))
    for col in range(table.columnCount()):
        for row in range(table.rowCount()):
            table.setItem(row,col,QTableWidgetItem(str(frame.iloc[row,col])))
    table.setHorizontalHeaderLabels(frame.columns)
    table.resizeColumnsToContents()
    table.resizeRowsToContents()