
import os
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
import numpy as np
from PyQt5.QtWidgets import QDialog, QSpacerItem, QSizePolicy, QButtonGroup, QTableWidgetItem, QRadioButton, QLineEdit, QComboBox, QFileDialog
from PyQt5.QtCore import Qt

from checkable_combo_box import CheckableComboBox
from align_delegate import AlignDelegate
from custom import Custom
from util.tools import Settings, avert_name_collision
from util.ui.dialogs import notify_error, notify_info
from util.ui.tools import update_hierarchical_combos, write_widget, update_combo_values, update_checkable_combo_values
from ui.config_form import Ui_Config
from ordering import OrderingWindow


class Config(QDialog, Ui_Config):
    """
    Properties, attributes, and methods used by the STAGG settings subGUI.
    
    Attributes
    ---------
    ref_definitions (Dict[str, str]): the help text for each help button
    data (Dict[str, pd.DataFrame]): ('variable', 'graph', and 'other') data for populating the window
    col_vals (Dict[str, List[str]]): values for each column variable in the data
    output_dir (str): path to output directory
    custom_data (dict): custom graphing selections
    variable_names (List[str]): all the current variable names; used to keep the old name around when a user renames
    aliases (List[str]): all the current alias names; used to keep the old name around when a user renames
    """
    def __init__(self, ref_definitions: Dict[str, str], data: Dict[str, pd.DataFrame], col_vals: Dict[str, List[str]], output_dir: str = ""):
        """
        Instantiate the Config class.

        Parameters 
        --------
        ref_definitions: the help text for each help button
        data: ('variable', 'graph', and 'other') data for populating the window
        col_vals: values for each column variable in the data
        output_dir: path to output directory
        """
        super(Config, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("STAGG Variable Configuration")
        self.graphic.setStyleSheet("border-image:url(scripts/GUI/resources/graphic.png)")
        self.isMaximized()

        ## CUSTOM SETUP ##
        # Add custom combo box
        self.setup_transform_combo()

        # Create self attributes containing widget collections and
        #   connect callbacks
        self.setup_variables_config()
        ##   ##   ##   ##   ##

        # GET INPUTS #
        self.output_dir = output_dir
        self.ref_definitions = ref_definitions
        self.col_vals = col_vals
        self.custom_data = None

        self.load_variable_config(data['variable'])

        # Do this after populating variable table
        self.graph_config_df = data['graph'].copy() if data['graph'] is not None else None
        self.other_config_df = data['other'].copy() if data['other'] is not None else None

        self.update_loop()
        self.cascade_variable_table_update()

        # Setup cell changed callbacks
        self.variable_table.cellChanged.connect(self.change_alias)

    def remove_loop(self):
        """Remove the selected row from the loop table"""
        curr_row = self.loop_table.currentRow()
        self.loop_table.removeRow(curr_row)

    def show_help(self):
        """Callback to show help text associated with event sender"""
        sbutton = self.sender()
        buttoned = sbutton.objectName()
        reference_text = self.ref_definitions[buttoned.replace("help_","")]
        self.config_reference.setPlainText(reference_text)

    def change_alias(self):
        """
        Callback to check user rename of Alias for duplication and
        provide alternative option in popup message.

        Changes are cascaded to:
            -custom data
            -graph config
            -loop table
        """
        
        # Get the current item
        curr_row = self.variable_table.currentRow()
        curr_item = self.variable_table.currentItem()
        num_variables = self.variable_table.rowCount()

        # Get old name and new name
        old_name = self.aliases[curr_row]
        new_name = curr_item.text()

        # Get all var names, skipping curr row
        existing_vars = [self.variable_table.item(row, 1).text() for row in range(num_variables) if row != curr_row]
        
        # Get unique name
        new_name = avert_name_collision(new_name, existing_vars)
        if not new_name:
            new_name = old_name
        
        # Set text
        curr_item.setText(new_name)
        self.aliases[curr_row] = new_name

        # Cascade changes to:
        #   -Custom data
        self.update_custom_data(old_name, new_name)
        #   -Graph config
        self.update_graph_config(renamed=(old_name, new_name))
        #   -Loop table
        self.update_loop(renamed=(old_name, new_name))
    
    def update_loop(self,
                    __idx: int = None,
                    renamed: Optional[Tuple[str]] = None):
        """
        Update the loop table with data in other widgets
        
        Parameters
        ---------
        __idx: Selected index of combo box change that (optionally) initiated update
        renamed: Tuple specifying the (old_name, new_name) of a renamed alias
        """
        # Update widgets
        for row_num in range(self.loop_table.rowCount()):

            response_var_combo = self.loop_table.cellWidget(row_num, 1)
            resp_var_default_value = None
            valid_values = np.array(self.aliases)
            # Update value based on valid values and any renamed variables
            update_combo_values(response_var_combo, valid_values, renamed=renamed, default_value=resp_var_default_value)

            # Check if the combo is still on the default value, or if a selection has been made
            curr_resp_var = response_var_combo.currentText()

            # Remove the response var selection from the options available to the rest
            valid_values = valid_values[valid_values != curr_resp_var]

            # Get the covariate values
            covariate_combo = self.loop_table.cellWidget(row_num, 6)
            covariate_values = covariate_combo.currentData()
            
            # Get the rest of the valid values
            valid_values_no_covariate = valid_values[~np.isin(valid_values, covariate_values)]

            # All of these are dependent on the previous
            combos_to_update = [self.loop_table.cellWidget(row_num, col_num) for col_num in range(2, 6)]
            default_value = ""
            update_hierarchical_combos(valid_values_no_covariate, combos_to_update, default_value, renamed=renamed, first_required=True)

            # Extract current status for use in populating covariate combo box
            combo_set_vals = [combo.currentText() for combo in combos_to_update]
            curr_xvar = combo_set_vals[0]
            xvar_selected = (curr_xvar != default_value)

            # do special update for covariate
            covariate_combo.setEnabled(xvar_selected)
            valid_values_no_combo_set = [val for val in self.aliases if val not in combo_set_vals]
            update_checkable_combo_values(covariate_combo, sorted(valid_values_no_combo_set, key=str.lower), renamed, default_value="")

    def setup_transform_combo(self):
        """
        Add CheckableComboBox widget to display data transformation options.
        """
        spacerItem64 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_25.addItem(spacerItem64)
        self.transform_combo = CheckableComboBox()
        self.transform_combo.addItems(["raw","log10","ln","sqrt","None"])
        self.verticalLayout_25.addWidget(self.transform_combo)
        spacerItem65 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_25.addItem(spacerItem65)

    @property
    def loop_table_headers(self):
        """Retrieve list of all header names in the loop table"""
        headers = []
        for i in range(self.loop_table.columnCount()):
            headers.append(self.loop_table.horizontalHeaderItem(i).text())
        return headers

    def setup_variables_config(self): 
        """
        General window setup
        
        Set widget callbacks
        Establish widget groupings for easier reference later
        Add CheckableComboBox to layout
        """
        self.additional_dict = {
            "Feature": self.feature_combo,
            "Poincare": self.Poincare_combo,
            "Spectral": self.Spectral_combo,
            "Transformation": self.transform_combo}

        self.graph_config_combos = {
            "Xvar": self.Xvar_combo,
            "Pointdodge": self.Pointdodge_combo,
            "Facet1": self.Facet1_combo,
            "Facet2": self.Facet2_combo}

        for combo in self.graph_config_combos.values():
            combo.currentIndexChanged.connect(self.update_graph_config)

        help_buttons = [self.help_xvar,
                        self.help_pointdodge,
                        self.help_facet1,
                        self.help_facet2,
                        self.help_feature,
                        self.help_poincare,
                        self.help_spectral,
                        self.help_transformation]

        for button in help_buttons:
            button.clicked.connect(self.show_help)
    

    def populate_variable_table(self, variable_table_df: pd.DataFrame):
        """
        Populate variable table with a given set of data

        Parameters
        ---------
        variable_table_df: dataframe to load

        Attributes-Out
        -------------
        variable_names: assigned to 'Column' column in input data
        aliases: assigned to 'Alias' column in input data
        """
        # I've forgotten what this was specifically about, but I remember it had something to do with spacing or centering text or something.
        delegate = AlignDelegate(self.variable_table)
        delegate_loop = AlignDelegate(self.loop_table)
        self.variable_table.setItemDelegate(delegate)
        self.loop_table.setItemDelegate(delegate_loop)

        # Setting the number of rows in each table upon opening the window:
        self.variable_table.setRowCount(len(variable_table_df))

        self.variable_names = variable_table_df['Column'].tolist()
        self.aliases = variable_table_df['Alias'].tolist()

        self.variable_table.blockSignals(True)
        
        # Grabbing every item in variable_names and making a row for each: 
        for row, record in enumerate(variable_table_df.to_dict('records')):
            var_name = record['Column']
            alias_name = record['Alias']

            # The first two columns are the text of the variable name. Alias should be text editable.
            orig_widget = QTableWidgetItem(var_name)
            orig_widget.setFlags(orig_widget.flags() & ~Qt.ItemIsEditable)  # read-only!
            self.variable_table.setItem(row, 0, orig_widget)
            
            alias_widget = QTableWidgetItem(alias_name)
            self.variable_table.setItem(row, 1, alias_widget)

            button_group = QButtonGroup(self)
            # NOTE: cannot set callback on buttongroup clicked because doing a group set operation wont trigger callback
            #button_group.idClicked.connect(self.cascade_variable_table_update)
            for i, label in enumerate(["Independent", "Dependent", "Covariate", "Ignore"]):
                new_radio_button = QRadioButton(label)
                if label != "Ignore":
                    new_radio_button.setChecked(record[label])
                new_radio_button.toggled.connect(self.cascade_variable_table_update)
                button_group.addButton(new_radio_button, id=i)
                self.variable_table.setCellWidget(row, 2 + i, new_radio_button)

        self.variable_table.resizeColumnsToContents()
        self.variable_table.resizeRowsToContents()

        self.variable_table.blockSignals(False)

    def cascade_variable_table_update(self):
        """Push variable table update to graph config and loop table"""
        self.update_graph_config()
        self.update_loop()

    def update_custom_data(self, old_name: str, new_name: str):
        """Update custom data to reflect a renamed variable
        
        Parameters
        ---------
        old_name: previous name of the variable
        new_name: new name of the variable
        """
        if self.custom_data is None:
            return

        # Update variable name with new alias
        for var_name in self.custom_data:
            if var_name == old_name:
                val = self.custom_data.pop(var_name)
                self.custom_data[new_name] = val
                break

    def get_variable_table_df(self):
        """
        Return a DataFrame built from the data in the variable table

        Attributes-In
        ------------
        custom_data: used to fill 'Custom' fields of the dataframe

        Returns
        --------
        pd.DataFrame: variable config data
        """
        # Create base dataframe
        variable_table_df = pd.DataFrame(
            columns=["Column",
                     "Alias",
                     "Independent",
                     "Dependent",
                     "Covariate",
                     "ymin",
                     "ymax",
                     "Poincare",
                     "Spectral",
                     "Transformation"])

        origin = []
        alias = []
        independent = []
        dependent = []
        covariate = []

        # populate lists with user selections from all buttons
        for row in range(self.variable_table.rowCount()):
            var_name = self.variable_table.item(row, 0).text()
            origin.append(var_name)

            alias_name = self.variable_table.item(row, 1).text()
            alias.append(alias_name)

            # Radio buttons
            indep = self.variable_table.cellWidget(row, 2).isChecked()
            independent.append(int(indep))
            dep = self.variable_table.cellWidget(row, 3).isChecked()
            dependent.append(int(dep))
            covar = self.variable_table.cellWidget(row, 4).isChecked()
            covariate.append(int(covar))

        # Update dataframe with user selections
        variable_table_df["Column"] = origin
        variable_table_df["Alias"] = alias
        variable_table_df["Independent"] = independent
        variable_table_df["Dependent"] = dependent
        variable_table_df["Covariate"] = covariate

        if self.Poincare_combo.currentText() == "All":
            # Assign only dependent variables
            deps = variable_table_df.loc[(variable_table_df["Dependent"] == 1)]["Alias"].values
            variable_table_df.loc[variable_table_df['Alias'].isin(deps), 'Poincare'] = 1
        elif self.Poincare_combo.currentText() == "None":
            variable_table_df["Poincare"] = 0
        elif self.Poincare_combo.currentText() == "Custom" and self.custom_data:
            custom_data_list = [[val['Poincare plot']] for val in self.custom_data.values()]
            variable_table_df.loc[variable_table_df.Alias.isin(self.custom_data.keys()), ["Poincare"]] = custom_data_list

        if self.Spectral_combo.currentText() == "All":
            # Assign only dependent variables
            deps = variable_table_df.loc[(variable_table_df["Dependent"] == 1)]["Alias"].values
            variable_table_df.loc[variable_table_df['Alias'].isin(deps), 'Spectral'] = 1
        elif self.Spectral_combo.currentText() == "None":
            variable_table_df["Spectral"] = 0
        elif self.Spectral_combo.currentText() == "Custom" and self.custom_data:
            custom_data_list = [[val['Spectral graph']] for val in self.custom_data.values()]
            variable_table_df.loc[variable_table_df.Alias.isin(self.custom_data.keys()), ["Spectral"]] = custom_data_list

        # Fill anything else missing with 0s
        variable_table_df[["Poincare", "Spectral"]] = variable_table_df[["Poincare","Spectral"]].fillna(0)
        
        # na for ymin/ymax should be filled with blank, since 0 is a valid response
        variable_table_df["ymin"] = variable_table_df["ymin"].fillna("")
        variable_table_df["ymax"] = variable_table_df["ymax"].fillna("")

        transform_data = self.transform_combo.currentData()
        # If we have custom selections, fill it in
        if 'Custom' in transform_data and self.custom_data:
            custom_data_list = [[val['Transformation']] for val in self.custom_data.values()]
            variable_table_df.loc[variable_table_df.Alias.isin(self.custom_data.keys()), ["Transformation"]] = custom_data_list
        # Otherwise, fill in for group
        else:
            all_checked = [item for item in ['raw', 'log10', 'ln', 'sqrt'] if item in transform_data]
            # Must assign each row independently b/c pandas doesnt like lists
            for idx in np.array(dependent).nonzero()[0]:
                variable_table_df.at[idx, "Transformation"] = all_checked

        # Default to null string ""
        variable_table_df["Transformation"] = variable_table_df["Transformation"].fillna("")

        # Make this much cleaner, decide on a data structure!
        # fill with custom data
        if self.custom_data:
            custom_data_list = [
                [val['Y axis minimum'],
                 val['Y axis maximum'],
                 ] for val in self.custom_data.values()]
            variable_table_df.loc[
                variable_table_df.Alias.isin(self.custom_data.keys()),
                ["ymin", "ymax"]] = custom_data_list

        return variable_table_df

    def get_all_dep_variables(self):
        """Return list of all dependent variables"""
        var_table_df = self.get_variable_table_df()
        dependent_vars = var_table_df.loc[(var_table_df["Dependent"] == 1)]["Alias"]
        return dependent_vars

    def edit_custom(self):
        """Show the custom settings subGUI to edit custom data."""

        deps = self.get_all_dep_variables()

        # Require at least 1 dependent variable assignment
        if deps.empty:
            notify_info(title='Choose variables', msg='Please select response variables to be modeled.')
            return

        # Get this from widgets
        variable_df = self.get_variable_table_df()

        # Open Custom window
        custom_window = Custom(variable_df, deps)
        reply = custom_window.exec()

        if reply:
            # Apply results back to widgets
            # self.custom_data = custom_window.data
            self.load_custom(custom_window.data)

    def load_custom(self, custom_data: dict): 
        """
        Load custom settings into the graph settings widgets and store as self.custom_data
        
        Parameters
        ---------
        custom_data: data to load

        Attributes-Out
        -------------
        custom_data: assigned to input data
        """

        custom_values = custom_data.values()

        # distribute updates to combo boxes
        for var_key, combo_box in {"Poincare plot": self.Poincare_combo, "Spectral graph": self.Spectral_combo}.items():

            all_options = [combo_box.itemText(i) for i in range(combo_box.count())]
            if "Custom" in all_options:
                combo_box.removeItem(all_options.index("Custom"))

            # check size (`all` returns True on empty list)
            if len(custom_values) and all([data_row[var_key] == 1 for data_row in custom_values]):
                combo_box.setCurrentText("All")

            elif any([data_row[var_key] == 1 for data_row in custom_values]):
                combo_box.addItem("Custom")
                combo_box.setCurrentText("Custom")

            else:
                combo_box.setCurrentText("None")
            
        # Check if we can group them without customization
        all_selections = [tuple(data_row['Transformation']) for data_row in custom_values]
        unique_selections = set(all_selections)
        
        # None are selected
        if len(all_selections) == 0:
            self.transform_combo.loadCustom(["None"])

        # If the set has only one value, the selections are all the same
        elif len(unique_selections) == 1:
            selected_options = list(unique_selections)[0]
            self.transform_combo.loadCustom(selected_options)

        # Otherwise we have a custom setup!
        else:
            self.transform_combo.loadCustom(["Custom"])

        self.custom_data = custom_data


    def update_graph_config(self, __idx: Optional[bool] = None, renamed: Optional[Iterable[str]] = None):
        """
        Update the graph config widgets to match the independent and
        covariate variables in the variable table.
    
        Parameters
        ---------
        __idx: index of changed row (for callbacks)
        renamed: tuple of (old, new) name of a renamed variable
        """

        combos = self.graph_config_combos.values()
        default_value = "Select variable:"
        valid_values = self.get_independent_covariate_vars()

        update_hierarchical_combos(valid_values, combos, default_value, renamed=renamed)

    def get_independent_covariate_vars(self, df=None):
        """Return list of all independent and covariate variables."""
        # Default to variable table
        if df is None:
            df = self.get_variable_table_df()
        return df.loc[(df["Independent"] == 1) | (df['Covariate'] == 1)]['Alias'].values

    @property
    def graph_config_df(self):
        """
        Return a DataFrame built from the data in the graph settings widgets

        Returns
        --------
        pd.DataFrame: graph config data
        """
        data = []
        for idx, combo_box in enumerate(self.graph_config_combos.values()):
            role = idx + 1  # (Role)?
            alias = combo_box.currentText()
            if alias == "Select variable:":
                alias = ""
                selected_values = []
            else:
                var_df = self.get_variable_table_df()
                selected_var = var_df[var_df['Alias'] == alias].iloc[0]['Column']
                selected_values = self.col_vals.get(selected_var, [])
            data.append((role, alias, selected_values))

        graph_config_df = pd.DataFrame(data=data,
                                       columns=['Role', 'Alias', 'Order'])
        return graph_config_df

    @graph_config_df.setter
    def graph_config_df(self, new_data: Optional[pd.DataFrame]):
        """Load the given data into the graph config widgets"""
        if new_data is None:
            #self.reset_config()
            pass
        else:
            # Populate widgets
            self.load_graph_config(new_data)

    def get_loop_widget_rows(self):
        """
        Yield the values of each row in the loop table

        Yields
        -----
        List[Union[str, int]]: the values of a loop table row
        """
        headers = self.loop_table_headers
        for row in range(self.loop_table.rowCount()):
            loop_row = [
                self.loop_table.cellWidget(row, headers.index("Graph name")).text(),
                self.loop_table.cellWidget(row, headers.index("Response variable")).currentText(),
                self.loop_table.cellWidget(row, headers.index("Xvar")).currentText(),
                self.loop_table.cellWidget(row, headers.index("Pointdodge")).currentText(),
                self.loop_table.cellWidget(row, headers.index("Facet1")).currentText(),
                self.loop_table.cellWidget(row, headers.index("Facet2")).currentText(),
                self.loop_table.cellWidget(row, headers.index("Covariates")).currentData(),
                self.loop_table.cellWidget(row, headers.index("Y axis minimum")).text(),
                self.loop_table.cellWidget(row, headers.index("Y axis maximum")).text(),
                int(self.loop_table.cellWidget(row, headers.index("Filter breaths?")).currentText() == "Yes")
            ]

            yield loop_row

    @property
    def other_config_df(self):
        """
        Return a DataFrame built from the data in the other settings widgets

        Returns
        --------
        pd.DataFrame: other_config data
        """
        other_config_widget_data = self.get_loop_widget_rows()
        other_config_df = pd.DataFrame(other_config_widget_data,
                                       columns=["Graph",
                                                "Variable",
                                                "Xvar",
                                                "Pointdodge",
                                                "Facet1",
                                                "Facet2",
                                                "Covariates",
                                                "ymin",
                                                "ymax",
                                                "Inclusion"])

        # Add plots for Apneas and/or Sighs
        if self.feature_combo.currentText() != "None":
            loop_table_rows = self.loop_table.rowCount()
            if self.feature_combo.currentText() == "All":
                other_config_df.at[loop_table_rows, "Graph"] = "Apneas"
                other_config_df.at[loop_table_rows+1, "Graph"] = "Sighs"
            else:
                other_config_df.at[loop_table_rows-1, "Graph"] = self.feature_combo.currentText()
        
        # Correcting some issue with filling nas on Apnea/Sighs stuff
        other_config_df['Inclusion'] = other_config_df['Inclusion'].fillna(0).astype(int)

        return other_config_df

    @other_config_df.setter
    def other_config_df(self, new_data):
        """Load the given data into the other config widgets"""
        if new_data is None:
            # TODO: this does weird things with widget placement...
            #self.reset_config()
            pass
        else:
            # Populate widgets
            self.load_other_config(new_data)

    def save_as(self):
        """Save current data to user-selected file"""
        # Ask user to pick a dir
        save_dir = QFileDialog.getExistingDirectory(self, 'Choose directory for STAGG configuration files', self.output_dir)

        # Catch cancel
        if not save_dir:
            return

        # Save each config file using its associated Settings class
        for config_name, (config_df, settings_class) in self.configs.items():

            path = os.path.join(save_dir, f"{config_name}.csv")
            settings_class.save_file(config_df, path)

        notify_info("All settings files have been saved.")

    @property
    def configs(self):
        """
        Return Dict of each config data with their associated Settings class
            -'variable_config'
            -'graph_config'
            -'other_config'
        """
        return {
            'variable_config': (self.get_variable_table_df(), VariableSettings),
            'graph_config': (self.graph_config_df, GraphSettings),
            'other_config': (self.other_config_df, OtherSettings)}

    def confirm(self):
        """Confirm user input and close window"""
        # set data to be retrieved by caller
        self.data = {
            'variable': self.get_variable_table_df(),
            'graph': self.graph_config_df,
            'other': self.other_config_df}
        self.accept()

    def add_loop(self):
        """Add row to loop_table"""

        loop_row = self.loop_table.rowCount()
        self.loop_table.insertRow(loop_row)

        self.loop_table.setCellWidget(loop_row, 0, QLineEdit())

        # Response Var, Xvar, Pointdodge, Facet1, Facet2
        for idx in range(1, 6):
            new_combo_box = QComboBox()
            new_combo_box.currentIndexChanged.connect(self.update_loop)
            self.loop_table.setCellWidget(loop_row, idx, new_combo_box)

        covariates_checkable_combo = CheckableComboBox()
        covariates_checkable_combo.currentIndexChanged.connect(self.update_loop)
        self.loop_table.setCellWidget(loop_row, 6, covariates_checkable_combo)

        self.loop_table.setCellWidget(loop_row, 7, QLineEdit())
        self.loop_table.setCellWidget(loop_row, 8, QLineEdit())

        inclusion_combo_box = QComboBox()
        inclusion_combo_box.addItems(["No", "Yes"])
        inclusion_combo_box.currentIndexChanged.connect(self.update_loop)
        self.loop_table.setCellWidget(loop_row, 9, inclusion_combo_box)

        self.update_loop()

    def reset_config(self):
        """
        Reset all user-selections in the widgets
        """
        # Use default var_df to populate table
        variable_table_df = ConfigSettings.get_default_variable_df(self.variable_names)
        self.populate_variable_table(variable_table_df)

        # Reset graph config combos
        for combo_box in self.graph_config_combos.values():
            combo_box.blockSignals(True)
            combo_box.clear()
            combo_box.addItem("Select variable:")
            combo_box.blockSignals(False)

        # Reset the additional info widgets
        for combo in self.additional_dict.values():
            combo.blockSignals(True)
            if type(combo) is CheckableComboBox:
                combo.loadCustom(["None"])
            else:
                combo.setCurrentText("None")
            combo.blockSignals(False)

        # Remove all loop table rows
        self.clear_loops()

    def clear_loops(self):
        """Remove all loop table rows"""
        for _ in range(self.loop_table.rowCount()):
            # CheckableComboBox keeps emitting signal as it dies...
            # Blocking signals to prevent errors
            self.loop_table.cellWidget(0, 6).blockSignals(True)
            self.loop_table.removeRow(0)

    def load_configs(self, __checked, files=None):
        """
        Load all the configs from user-selected file
            > "variable_config"
            > "graph_config"
            > "other_config"
        """

        # if no paths passed in, let user pick
        if not files:
            files = ConfigSettings.open_file()
            if not files:
                return

            data = ConfigSettings.attempt_load(files)
            if data is None:
                return

            self.load_variable_config(data['variable'])
            self.load_graph_config(data['graph'])
            self.load_other_config(data['other'])

    def load_variable_config(self, df: pd.DataFrame):
        """Load some data into the variable config widgets."""

        df = df.copy()

        # Load into table
        self.populate_variable_table(df)

        # Load custom data
        all_custom = df[df["Dependent"] == 1].fillna("")
        custom_data = {}
        for record in all_custom.to_dict('records'):
            new_custom = {
                'Variable': record['Alias'],
                'Y axis minimum': record['ymin'],
                'Y axis maximum': record['ymax'],
                'Transformation': record['Transformation'],
                'Poincare plot': record['Poincare'],
                'Spectral graph': record['Spectral']}
            custom_data[record['Alias']] = new_custom

        self.load_custom(custom_data)


    def order_items(self, combo_name: str):
        """
        Show window for user reordering of variable values

        Parameters
        ---------
        combo_name: string key identifying which combo to work with

        Attributes-In
        ------------
        col_vals: get list of current values

        Attributes-Out
        -------------
        col_vals: stores new order of values
        """
        combo = self.graph_config_combos[combo_name]
        alias_name = combo.currentText()

        # TODO: find a way to do this more systematically?
        # Skip anything set to default
        if alias_name == "Select variable:":
            return

        # Notify user if values are not available
        if alias_name not in self.col_vals:
            msg  = "No values available to order."
            msg += "\n\nTry loading STAGG Settings from:"
            msg += "\n  -Previous BASSPRO Settings"
            msg += "\n  -Previous BASSPRO Output"
            notify_info(msg)
            return

        items = self.col_vals[alias_name]

        # Check if value list is empty
        if len(items) == 0:
            notify_info("There are no values for this variable")
            return

        order_window = OrderingWindow(combo_name, alias_name, items)
        reply = order_window.exec()
        if reply:
            # set new items
            self.col_vals[alias_name] = order_window.get_items()

    def load_graph_config(self, df):
        """Load the given data into the graph config widgets"""

        gdf = df.copy()

        # Get only Independent/Covariate aliases
        # Try getting from variable_table first
        indep_covariate_vars = self.get_independent_covariate_vars()
        
        for idx, combo in enumerate(self.graph_config_combos.values()):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Select variable:")
            if len(indep_covariate_vars):
                combo.addItems(indep_covariate_vars)

                # Set each box to the value stored for it's Role
                combo_role = idx + 1
                curr_selection = gdf.loc[(gdf['Role'] == combo_role) & pd.notna(gdf['Alias'])]
                if len(curr_selection):
                    combo.setCurrentText(curr_selection["Alias"].values[0])
            combo.blockSignals(False)

    def load_other_config(self, df):
        """Load the given data into the other config widgets"""

        odf = df.copy()
        odf = odf.fillna("")

        # Reset feature comboBox
        self.feature_combo.setCurrentText("None")
        if "Apneas" in set(odf["Graph"]):
            self.feature_combo.setCurrentText("Apneas")

        if "Sighs" in set(odf["Graph"]):
            self.feature_combo.setCurrentText("Sighs") 

        if ("Apneas" and "Sighs") in set(odf["Graph"]):
            self.feature_combo.setCurrentText("All")

        # Remove all Apneas and Sighs items to leave just loop items
        odf.drop(odf.loc[(odf["Graph"]=="Apneas") | (odf["Graph"]=="Sighs")].index, inplace = True)

        # Skip loop processing if df is empty
        if len(odf) == 0:
            return

        odf['Inclusion'] = odf['Inclusion'].astype(int)

        # Clear loop table
        self.clear_loops()

        # TODO: is there a faster/cleaner way to iterate?
        # Populate each row of loop_table
        for row_num in odf.index:
            self.add_loop()
            for table_idx, header in enumerate(self.loop_table_headers):
                if header == "Covariates":
                    covariates = odf.at[row_num, 'Covariates']
                    if covariates:
                        covariate_combo = self.loop_table.cellWidget(row_num, table_idx)
                        covariate_combo.loadCustom(covariates)
                        covariate_combo.updateText()
                    continue

                if header == "Filter breaths?":
                    new_text = "Yes" if odf.at[row_num, "Inclusion"] else "No"
                elif header == "Graph name":
                    new_text = str(odf.at[row_num, "Graph"])
                elif header == "Response variable":
                    new_text = str(odf.at[row_num, "Variable"])
                elif header == "Y axis minimum":
                    new_text = str(odf.at[row_num, "ymin"])
                elif header == "Y axis maximum":
                    new_text = str(odf.at[row_num, "ymax"])
                else:
                    new_text = str(odf.at[row_num, header])

                write_widget(self.loop_table.cellWidget(row_num, table_idx), new_text)


    def checkable_ind(self):
        """Set selected variables as "Independent"."""
        independent_col_idx = 2
        self.check_all(independent_col_idx)

    def checkable_dep(self):
        """Set selected variables as "Dependent"."""
        dependent_col_idx = 3
        self.check_all(dependent_col_idx)
        
    def checkable_cov(self):
        """Set selected variables as "Covariate"."""
        covariate_col_index = 4
        self.check_all(covariate_col_index)

    def checkable_ign(self):
        """Set selected variables as "Ignore"."""
        ignore_col_index = 5
        self.check_all(ignore_col_index)

    def check_all(self, checked_idx: int):
        """
        Assign the selected variables to the group identified by the `checked_idx`.

        Parameters
        ---------
        checked_idx: index of the radio button to check
        """
        for selected_rows in self.variable_table.selectedRanges():
            first_row = selected_rows.topRow()
            last_row = selected_rows.bottomRow()
            for row in range(first_row, last_row+1):
                cell_widget = self.variable_table.cellWidget(row, checked_idx)
                cell_widget.setChecked(True)


# TODO: this is kinda gross -- split these out!
class ConfigSettings(Settings):
    """Attributes and methods for handling Config settings files"""

    valid_filetypes = ['.csv', '.xlsx']
    file_chooser_message = 'Select variable config files to edit'
    editor_class = Config

    # Overwrite superclass method
    def attempt_load(filepaths):
        variable_data = VariableSettings.attempt_load(filepaths['variable'])
        if variable_data is None:
            return None

        graph_data = GraphSettings.attempt_load(filepaths['graph'])
        if graph_data is None:
            return None

        other_data = OtherSettings.attempt_load(filepaths['other'])
        if other_data is None:
            return None

        return {'variable': variable_data, 'graph': graph_data, 'other': other_data}

    # Overwriting parent method for list of files
    @staticmethod
    def validate_list(files):
        right_size = len(files) == 3
        valid_files = []
        files_represented = set()
        for file in files:
            if 'variable' in file:
                valid_files.append(VariableSettings.validate(file))
                files_represented.add('variable')
            elif 'graph' in file:
                valid_files.append(GraphSettings.validate(file))
                files_represented.add('graph')
            elif 'other' in file:
                valid_files.append(OtherSettings.validate(file))
                files_represented.add('other')
        all_files_covered = len(files_represented) == 3
        return right_size and all(valid_files) and all_files_covered


    # Overwriting parent method for list of files
    @classmethod
    def open_file(cls, output_dir=""):
        while True:
            files, filter = QFileDialog.getOpenFileNames(None, cls.file_chooser_message, output_dir)

            # Break if cancelled
            if not files:
                return None

            # If good file, return
            if cls.validate_list(files):
                return_data = {}
                for file in files:
                    if 'variable' in file:
                        return_data['variable'] = file
                    elif 'graph' in file:
                        return_data['graph'] = file
                    elif 'other' in file:
                        return_data['other'] = file
                    
                return return_data

            # If bad file display error and try again
            error_msg = "The selection is invalid. Please choose 3 files:"
            error_msg+= "\n  - variable config"
            error_msg+= "\n  - graph config"
            error_msg+= "\n  - other config"
            notify_error(error_msg)

    @staticmethod
    def get_default_variable_df(variable_names):
        default_values = [0, 0, 0, 0, 0, 0, 0, []]
        default_data = [[var_name, var_name] + default_values for var_name in variable_names]
        variable_table_df = pd.DataFrame(
            default_data,
            columns=["Column",
                     "Alias",
                     "Independent",
                     "Dependent",
                     "Covariate",
                     "ymin",
                     "ymax",
                     "Poincare",
                     "Spectral",
                     "Transformation"])
        return variable_table_df



class VariableSettings(ConfigSettings):

    naming_requirements = ['variable', 'config']
    default_filename = 'variable_config.csv'

    def attempt_load(filepath):
        if filepath.endswith(".xlsx"):
            df = pd.read_excel(filepath)

        elif filepath.endswith(".csv"):
            df = pd.read_csv(filepath)

        df['Transformation'] = df['Transformation'].fillna("")

        new_transforms = []
        # Clean transform values and create list
        for i, record in df.iterrows():
            if record['Transformation']:
                # Replace all 'non' with 'raw'
                transform = [t.replace("non","raw") for t in record['Transformation'].split('@')]
                # Replace all 'log' with 'ln', unless the text is 'log10'
                transform = [t.replace("log","ln") if t != "log10" else t for t in transform ]
                new_transforms.append(transform)
            else:
                new_transforms.append([])

        df['Transformation'] = new_transforms

        return df

    @staticmethod
    def _save_file(filepath, df):
        # Rename transform labels
        populated_trans = df[df["Transformation"] != ""]
        for i, record in populated_trans.iterrows():
            trans = record['Transformation']
            trans = [t.replace("raw", "non") for t in trans]
            trans = [t.replace("ln", "log") for t in trans]
            df.at[i, 'Transformation'] = '@'.join(trans)
        df.to_csv(filepath, index=False)

class GraphSettings(ConfigSettings):

    naming_requirements = ['graph', 'config']
    default_filename = 'graph_config.csv'

    def attempt_load(filepath):
        gdf = pd.read_csv(filepath, index_col=False)
        return gdf

    def _save_file(filepath, df):
        # Transform each Order vals list into '@'-separated string
        for i, record in df.iterrows():
            vals = record['Order']
            # TODO: can we guarantee a data type for all input variables?
            df.at[i, 'Order'] = '@'.join([str(v) for v in vals])
        df.to_csv(filepath, index=False)


class OtherSettings(ConfigSettings):

    naming_requirements = ['other', 'config']
    default_filename = 'other_config.csv'

    def attempt_load(filepath):
        odf = pd.read_csv(filepath, index_col=False, keep_default_na=False)
        odf['Covariates'] = odf['Covariates'].str.split('@')
        return odf

    @staticmethod
    def _save_file(filepath, df):
        # If there are covariates, join them into a string with sep='@'

        df = df.fillna("")

        # Rename transform labels
        df['Covariates'] = df['Covariates'].str.join('@')

        df.to_csv(filepath, index=False)