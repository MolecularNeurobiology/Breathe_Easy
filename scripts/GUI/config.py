
import os
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import QDialog, QSpacerItem, QSizePolicy, QButtonGroup, QTableWidgetItem, QRadioButton, QLineEdit, QComboBox, QFileDialog
from PyQt5.QtCore import QObject, Qt
from checkable_combo_box import CheckableComboBox
from align_delegate import AlignDelegate
from custom import Custom
from util import Settings, avert_name_collision, notify_error, notify_info, write_widget, update_combo_values, update_checkable_combo_values
from ui.config_form import Ui_Config
from ordering import OrderingWindow

''' TODO
    Trying to find a common way to define the widgets
    Need to put in UI file and just maintain a "LOOP" as a UI element

loop_widget_config = [
    {'column_name': 'Graph Name',  # 0
        'df_index_name': 'Graph name',
        'read_func': lambda widg: widg.text(),
        'widget_class': QLineEdit,
        'valid_values_values': lambda : self.variable_names},
    {'column_name': 'Variable',  # 1
        'df_index_name': 'Variable',
        'read_func': lambda widg: widg.currentText(),
        'widget_class': self.new_other_settings_combo_box,
        'valid_values_func': self.get_independent_covariate_vars},
    {'column_name': 'Xvar',  # 2
        'df_index_name': 'Xvar',
        'read_func': lambda widg: widg.currentText(),
        'widget_class': self.new_other_settings_combo_box,
        'valid_values_func': self.get_independent_covariate_vars},
    {'column_name': 'Pointdodge',  # 3
        'df_index_name': 'Pointdodge',
        'read_func': lambda widg: widg.currentText(),
        'widget_class': self.new_other_settings_combo_box,
        'valid_values_func': self.get_independent_covariate_vars},
    {'column_name': 'Facet1',  # 4
        'df_index_name': 'Facet1',
        'read_func': lambda widg: widg.currentText(),
        'widget_class': self.new_other_settings_combo_box,
        'valid_values_func': self.get_independent_covariate_vars},
    {'column_name': 'Facet2',  # 5
        'df_index_name': 'Facet2',
        'read_func': lambda widg: widg.currentText(),
        'widget_class': self.new_other_settings_combo_box,
        'valid_values_func': self.get_independent_covariate_vars},
    {'column_name': 'Covariates',  # 6
        'df_index_name': 'Covariates',
        'read_func': lambda widg: '@'.join(widg.current_data()),
        'widget_class': self.new_covariates_checkable_combo,
        'valid_values_func': lambda : self.variable_names},
    {'column_name': 'Y axis minimum',  # 7
        'df_index_name': 'Y axis minimum',
        'read_func': lambda widg: widg.text(),
        'widget_class': QLineEdit,
        'valid_values': None},
    {'column_name': 'Y axis maximum',  # 8
        'df_index_name': 'Y axis maximum',
        'read_func': lambda widg: widg.text(),
        'widget_class': QLineEdit,
        'valid_values': None},
    {'column_name': 'Inclusion',  # 9
        'df_index_name': 'Inclusion',
        'read_func': lambda widg: widg.currentText() == "Yes",
        'widget_class': self.new_inclusion_combo_box,
        'valid_values': lambda : ["Yes", "No"]},
]
'''

class Config(QDialog, Ui_Config):
    """
    The Config class inherits widgets and layouts of Ui_Config and defines the STAGG settings subGUI that allows users to define the STAGG settings.
    
    Parameters
    --------
    QWidget: class
        The Config class inherits properties and methods from the QWidget class.
    Ui_Config: class
        The Config class inherits widgets and layouts defined in the Ui_Config class.
    """
    def __init__(self, ref_definitions, data, col_vals, workspace_dir=""):
        """
        Instantiate the Config class.

        Parameters 
        --------

        Outputs
        --------
        self.dependent_vars: list
            This attribute is set as an empty list.
        
        Outcomes
        --------
        self.setup_variables_config()
            Add the CheckableComboBox to the STAGG settings subGUI layout, establish attributes, and assign clicked signals and self.reference_event slots to each self.help_{setting} ToolButton.
        """
        super(Config, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("STAGG Variable Configuration")
        self.graphic.setStyleSheet("border-image:url(:resources/graphic.png)")
        self.isMaximized()

        ## CUSTOM SETUP ##
        # Add custom combo box
        self.setup_transform_combo()

        # Create self attributes containing widget collections and
        #   connect callbacks
        self.setup_variables_config()
        ##   ##   ##   ##   ##

        # GET INPUTS #
        self.workspace_dir = workspace_dir
        self.ref_definitions = ref_definitions
        self.col_vals = col_vals
        self.custom_data = None

        ''' TODO: do we need to require loading configs?
        if data is None:
            data = ConfigSettings.require_load(workspace_dir)
            if data is None:
                self.reject()   
        '''

        variable_config_df = data['variable']
        self.populate_variable_table(variable_config_df)

        # Do this after populating variable table
        self.graph_config_df = data['graph'].copy() if data['graph'] else None
        self.other_config_df = data['other'].copy() if data['other'] else None

        self.update_loop()
        self.cascade_variable_table_update()

        # Setup cell changed callbacks
        self.variable_table.cellChanged.connect(self.change_alias)

    def minus_loop(self):
        """
        Remove the selected row from self.loop_table and its corresponding data from self.loop_widgets (dict).

        Parameters
        --------
        self.loop_table: QTableWidget
            This TableWidget displays the settings for additional models either via widgets or loading previously made other_config.csv with previous STAGG run's settings for additional models.
        self.loop_widgets: dict
            The nested dictionary used to populate and save the text, CheckBox, ComboBox, and CheckableComboBox states of Config.loop_table (TableWidget) in the Config subGUI.
        
        Outputs
        --------
        self.loop_table: QTableWidget
            The user-selected row is removed from this TableWidget.
        self.loop_widgets: dict
            The item in this nested dictionary that corresponds to the removed row is popped from the dictionary.

        """
        curr_row = self.loop_table.currentRow()
        self.loop_table.removeRow(curr_row)
        
    def reference_event(self):
        """
        Respond to the signal emitted by the self.help_{setting} ToolButton clicked by the user by calling self.populate_reference(self.sender.objectName()) to populate the self.config_reference TextBrowser with the definition, description, and default value of corresponding setting.
        """
        sbutton = self.sender()
        self.populate_reference(sbutton.objectName())

    def populate_reference(self, buttoned: QObject.objectName):
        """
        Populate self.config_reference (TextBrowser) with the definition, description, and default values of the appropriate setting as indicated by the suffix of the ToolButton's objectName(), e.g. "help_{setting}" from Plethysmography.rc_config (reference_config.json).

        Parameters
        --------
        buttoned: QObject.objectName
            This variable is the objectName of the ToolButton that emitted the signal self.reference_event that called this method. Its suffix is used to identify the appropriate cell in self.view_tab (TableWidget).
        Plethysmography.rc_config: dict
            This attribute is a shallow dictionary loaded from reference_config.json. It contains definitions, descriptions, and recommended values for every basic, manual, and automated BASSPRO setting.

        Outputs
        --------
        self.config_reference: QTableWidget
            This TableWidget displays the definition, description, and default value of the user-selected setting.
        """
        reference_text = self.ref_definitions[buttoned.replace("help_","")]
        self.config_reference.setPlainText(reference_text)

    def change_alias(self):
        """
        Automatically rename the variable in the "Alias" column of self.variable_table (TableWidget) to avoid duplicate variable names.

        Parameters
        --------
        self.variable_table: QTableWidget
            This TableWidget displays the text and widgets needed to allow the user to indicate the type of a selected variable.
        """
        
        # TODO: why is this called endlessly on close??

        curr_col = self.variable_table.currentColumn()

        # TODO: prevent editing any other column
        if curr_col != 1:
            raise RuntimeError("Can only edit Alias column! TODO: Add functionality to prevent col 0 changes")

        ## PREVENT DUPLICATES ##
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
            # TODO: need to keep around the last text this was changed to
            #  rather than going back to default
            new_name = old_name
        
        # Set text
        curr_item.setText(new_name)
        self.aliases[curr_row] = new_name

        # Cascade changes to
        self.update_custom_data(old_name, new_name)

        #   Graph config
        self.update_graph_config(renamed=(old_name, new_name))

        #   Loop table
        self.update_loop(renamed=(old_name, new_name))
    
    def update_loop(self, __checked=None, renamed=None):
        """
        Update the contents of self.clades_other_dict with the contents of self.loop_widgets and then update the contents of self.loop_table with the newly updated contents of self.clades_other_dict.
        
        Parameters
        --------
        self.variable_table_df: Dataframe
            This attribute is a dataframe that contains the states of the self.variable_table widgets for each variable.
        self.loop_table: QTableWidget
            This TableWidget displays the settings for additional models either via widgets or loading previously made other_config.csv with previous STAGG run's settings for additional models.
        self.loop_widgets: dict
            The nested dictionary used to populate and save the text, CheckBox, ComboBox, and CheckableComboBox states of Config.loop_table (TableWidget) in the Config subGUI.
        self.clades_other_dict: dict
            This dictionary is populated and updated with the current states of the widgets stored in self.loop_widgets.
        
        Outputs
        --------
        self.dependent_vars: Series
            This attribute is a Series of the variables, specifically the "Alias" column of dataframe self.variable_table_df derived from self.variable_table.
        self.loop_table: QTableWidget
            This TableWidget is populated with the settings for additional models either via widgets or loading previously made other_config.csv with previous STAGG run's settings for additional models.
        self.clades_other_dict: dict
            This dictionary is populated and updated with the current states of the widgets stored in self.loop_widgets.
        
        Outcomes
        --------
        """
        '''
        # Update dict
        for row_num in range(self.loop_table.rowCount()):
            loop_row = {
                "Graph": self.loop_widgets[self.loop_table][row_num]["Graph"].text(),
                "Variable": self.loop_widgets[self.loop_table][row_num]["Variable"].currentText(),
                "Xvar": self.loop_widgets[self.loop_table][row_num]["Xvar"].currentText(),
                "Pointdodge": self.loop_widgets[self.loop_table][row_num]["Pointdodge"].currentText(),
                "Facet1": self.loop_widgets[self.loop_table][row_num]["Facet1"].currentText(),
                "Facet2": self.loop_widgets[self.loop_table][row_num]["Facet2"].currentText(),
                "Covariates": '@'.join(self.loop_widgets[self.loop_table][row_num]["Covariates"].currentData()),
                "Inclusion": self.loop_widgets[self.loop_table][row_num]["Inclusion"].currentText(),
                "Y axis minimum": self.loop_widgets[self.loop_table][row_num]["Y axis minimum"].text(),
                "Y axis maximum": self.loop_widgets[self.loop_table][row_num]["Y axis maximum"].text()
            }

            self.clades_other_dict[row_num] = loop_row
        '''

        # Update widgets
        for row_num in range(self.loop_table.rowCount()):

            response_var_combo = self.loop_table.cellWidget(row_num, 1)
            resp_var_default_value = None
            valid_values = self.aliases
            # Update value based on valid values and any renamed variables
            update_combo_values(response_var_combo, valid_values, renamed=renamed, default_value=resp_var_default_value)

            # Check if the combo is still on the default value, or if a selection has been made
            curr_resp_var = response_var_combo.currentText()

            # Remove the response var selection from the options available to the rest
            valid_values = valid_values[valid_values != curr_resp_var]

            covariate_combo = self.loop_table.cellWidget(row_num, 6)
            covariate_values = covariate_combo.currentData()
            valid_values_no_covariate = valid_values[~np.isin(valid_values, covariate_values)]

            # All of these are dependent on the previous and use the same indep/covar variables
            combos_to_update = [self.loop_table.cellWidget(row_num, col_num) for col_num in range(2, 6)]
            default_value = ""
            self.update_hierarchical_combos(valid_values_no_covariate, combos_to_update, default_value, renamed=renamed, first_required=True)

            # Extract current status for use in populating covariate combo box
            combo_set_vals = [combo.currentText() for combo in combos_to_update]
            curr_xvar = combo_set_vals[0]
            xvar_selected = (curr_xvar != default_value)

            # do special update for covariate
            covariate_combo.setEnabled(xvar_selected)
            valid_values_no_combo_set = [val for val in self.aliases if val not in combo_set_vals]
            update_checkable_combo_values(covariate_combo, sorted(valid_values_no_combo_set, key=str.lower), renamed, default_value="")

            '''
                new_text = read_widget(self.loop_table.cellWidget(row_num, header_idx))
                # TODO: catching weird condition skipping the "Covariates" slot
                header_idx = header_idx+1 if header_idx >= 6 else header_idx
                write_widget(self.loop_table.cellWidget(row_num, header_idx), new_text)
                '''

            '''
            # If Covariates is filled
            covariates = self.loop_widgets[row_num]["Covariates"].currentData()
            if covariates != "":
                self.loop_widgets[row_num]['Covariates'].loadCustom(covariates)
                self.loop_widgets[row_num]['Covariates'].updateText()
            '''

    def setup_transform_combo(self):
        """
        Add widget from custom class CheckableComboBox to STAGG settings subGUI layout to serve as drop-down menu for data transformation options.
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
        headers = []
        for i in range(self.loop_table.columnCount()):
            headers.append(self.loop_table.horizontalHeaderItem(i).text())
        return headers

    def setup_variables_config(self): 
        """
        Add the CheckableComboBox to the STAGG settings subGUI layout
        Establish attributes
        Assign clicked signals and self.reference_event slots to each self.help_{setting} ToolButton.

        Parameters
        --------
        self.variable_table_df: Dataframe
            This attribute is a dataframe that containts the states of the self.variable_table widgets for each variable.
        self.graph_config_df: Dataframe
            This attribute is a dataframe that containts the states of the many comboBoxes that define graph roles for selected variables.
        self.other_config_df: Dataframe
            This attribute is a dataframe that containts the states of the self.loop_table widgets for each variable as well as the states for self.feature_combo comboBox..
        self.feature_combo: QCombobBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to produce plots of respiratory features such as sighs and apneas.
        self.Poincare_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to produce Poincare plots for all or none of the selected dependent variables.
        self.Spectral_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to produce Spectral plots for all or none of the selected dependent variables.
        self.transform_combo: CheckableComboBox
            This CheckableComboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to run STAGG on different model transformations.
        self.Xvar_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose which independent or covariate variable should determine the x axis of figures of the main model.
        self.Pointdodge_combbo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose which independent or covariate variable should determine the groups of symbol of figures of the main model.
        self.Facet1_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose which independent or covariate variable should determine the splitting of the x axis if at all.
        self.Facet2_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose which independent or covariate variable should determine the splitting of the y axis if at all.
        self.config_reference: QTextBrowser
            This TableWidget displays the definition, description, and default value of the user-selected setting.
        self.help_{setting}: QToolButton
            These buttons are assigned clicked signals and slotted for self.reference_event().
        self.variable_config: str
            This Plethysmography class attribute is the file path to one of the STAGG settings files.
        self.graph_config: str
            This Plethysmography class attribute is the file path to one of the STAGG settings files.
        self.other_config: str
            This Plethysmography class attribute is the file path to one of the STAGG settings files.

        Outputs
        --------
        self.additional_dict: dict
            This dictionary relates certain header strings to their corresponding comboBoxes.
        self.graph_config_combos: dict
            A nested dictionary that relates the graph settings comboBoxes to their headers.
        self.custom_dict: dict
            This attribue is set as an empty dictionary.
        self.custom_port: dict
            This attribute is set as an empty dictionary.
        self.clades_other_dict: dict
            This dictionary is populated and updated with the current states of the widgets stored in self.loop_widgets.
        self.variable_table_df: Dataframe | list
            This attribute is set as an empty list.
        self.graph_config_df: Dataframe | list
            This attribute is set as an empty list.
        self.other_config_df: Dataframe | list
            This attribute is set as an empty list.
        self.configs: dict
            This attribute is populated with a nested dictionary in which each item contains a dictionary unique to each settings file - variable_config.csv, graph_config.csv, and other_config.csv. Each dictionary has the following key, value items: "variable", the Plethysmography class attribute that refers to the file path to the settings file; "path", the string file path to the settings file; "frame", the attribute that refers to the dataframe; "df", the dataframe.

        Outcomes
        --------
        self.setup_transform_combo()
            Add widget from custom class CheckableComboBox to STAGG settings subGUI layout to serve as drop-down menu for data transformation options.
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
            button.clicked.connect(self.reference_event)
    

    def populate_variable_table(self, variable_table_df):
        """
        Assign delegates to self.variable_table and self.loop_table
        Set self.buttonDict_variable as an empty dictionary
        Repopulate it with text and widgets based on items listed in self.variable_names (list)
        Assign the RadioButton widgets of each row to a ButtonGroup
        Populate self.variable_table (TableWidget) with the contents of self.buttonDict_variable
        Assign toggled signals slotted for self.update_graph_config() to the RadioButtons in
          self.buttonDict_variable that correspond to those in the "Independent"
          and "Covariate" columns of the TableWidget
        Adjust the size of the cells of self.variable_table.

        Parameters
        --------
        AlignDelegate: class
            This class assigns delegates to Config.variable_table and Config.loop_table TableWidgets and and centers the delegate items.
        self.variable_table: QTableWidget
            This TableWidget is defined in the Config class, displayed in the STAGG settings subGUI, and populated with rows based on the list of variables (Plethysmography.variable_names).
        self.loop_table: QTableWidget
            This TableWidget is populated with the settings for additional models either via widgets or loading previously made other_config.csv with previous STAGG run's settings for additional models.
        self.variable_names: list
            This Plethysmography class attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        self.buttonDict_variable: dict
            This Plethysmography class attribute is a nested dictionary used to populate and save the text and RadioButton states of Config.variable_table (TableWidget) in the Config subGUI.
        
        Outputs
        --------
        self.variable_table: QTableWidget
            This TableWidget is populated with text and widgets stored in self.buttonDict_variable (dict).
        self.loop_table: QTableWidget
            This TableWidget is populated with one row. (why?)
        self.buttonDict_variable: dict
            This Plethysmography class attribute is set as an empty dictionary and repopulated with text and widgets based on items in the list self.variable_names.
        """
        # I've forgotten what this was specifically about, but I remember it had something to do with spacing or centering text or something.
        delegate = AlignDelegate(self.variable_table)
        delegate_loop = AlignDelegate(self.loop_table)
        self.variable_table.setItemDelegate(delegate)
        self.loop_table.setItemDelegate(delegate_loop)

        # Setting the number of rows in each table upon opening the window:
        self.variable_table.setRowCount(len(variable_table_df))

        self.variable_names = variable_table_df['Column'].tolist()
        self.aliases = variable_table_df['Alias']

        self.variable_table.blockSignals(True)
        
        # Grabbing every item in variable_names and making a row for each: 
        for row, record in enumerate(variable_table_df.to_dict('records')):
            var_name = record['Column']
            alias_name = record['Alias']

            # The first two columns are the text of the variable name. Alias should be text editable.
            orig_widget = QTableWidgetItem(var_name)
            self.variable_table.setItem(row, 0, orig_widget)
            
            alias_widget = QTableWidgetItem(alias_name)
            self.variable_table.setItem(row, 1, alias_widget)

            button_group = QButtonGroup(self)
            #button_group.idClicked.connect(self.cascade_variable_table_update)
            for i, label in enumerate(["Independent", "Dependent", "Covariate", "Ignore"]):
                new_radio_button = QRadioButton(label)
                new_radio_button.toggled.connect(self.cascade_variable_table_update)
                button_group.addButton(new_radio_button, id=i)
                self.variable_table.setCellWidget(row, 2 + i, new_radio_button)

        self.variable_table.resizeColumnsToContents()
        self.variable_table.resizeRowsToContents()

        self.variable_table.blockSignals(False)

    def cascade_variable_table_update(self):
        self.update_graph_config()
        self.update_loop()

    def update_custom_data(self, old_name, new_name):
        if self.custom_data is None:
            return

        # Update variable name with new alias
        for var_name in self.custom_data:
            if var_name == old_name:
                val = self.custom_data.pop(var_name)
                self.custom_data[new_name] = val
                break

    def get_all_dep_variables(self):
        return self.variable_table_df.loc[(self.variable_table_df["Dependent"] == 1)]["Alias"]

    def get_variable_table_df(self):
        """
        - Populate several list attributes and self.variable_table_df dataframe with text
           and widget statuses from self.buttonDict_variable (dict)
        - create columns for self.graph_config_df and self.other_config_df.

        Parameters
        --------
        self.buttonDict_variable: dict
            This Plethysmography class attribute is a nested dictionary used to populate and save the text and RadioButton states of Config.variable_table (TableWidget) in the Config subGUI.
        
        Outputs
        --------
        self.variable_table_df: Dataframe
            This attribute is populated with a dataframe that contains the states of the self.variable_table widgets for each variable as stored in self.buttonDict_variable (dict).
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
            variable_table_df["Poincare"] = 1
        elif self.Poincare_combo.currentText() == "None":
            variable_table_df["Poincare"] = 0
        elif self.Poincare_combo.currentText() == "Custom" and self.custom_data:
            custom_data_list = [[val['Poincare plot']] for val in self.custom_data.values()]
            variable_table_df.loc[variable_table_df.Alias.isin(self.custom_data.keys()), ["Poincare"]] = custom_data_list

        if self.Spectral_combo.currentText() == "All":
            variable_table_df["Spectral"] = 1
        elif self.Spectral_combo.currentText() == "None":
            variable_table_df["Spectral"] = 0
        elif self.Spectral_combo.currentText() == "Custom" and self.custom_data:
            custom_data_list = [[val['Spectral graph']] for val in self.custom_data.values()]
            variable_table_df.loc[variable_table_df.Alias.isin(self.custom_data.keys()), ["Spectral"]] = custom_data_list

        # Fill anything else missing with 0s
        variable_table_df[["Poincare", "Spectral"]] = variable_table_df[["Poincare","Spectral"]].fillna(0)
        
        variable_table_df["ymin"] = variable_table_df["ymin"].fillna(0)
        variable_table_df["ymax"] = variable_table_df["ymax"].fillna(0)

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

    def set_variable_table_df(self, new_data):
        if new_data is None:
            # TODO: this does weird things with widget placement...
            #self.reset_config()
            pass
        else:
            # Populate widgets
            self.load_variable_config(df=new_data)

    @property
    def dependent_vars(self):
        var_table_df = self.get_variable_table_df()
        dependent_vars = var_table_df.loc[(var_table_df["Dependent"] == 1)]["Alias"]
        return dependent_vars

    def show_custom(self):
        """
        Check self.variable_table Alias selections
        Update rows in Custom.custom_table accordingly
        Show the custom subGUI.

        Parameters
        --------
        self.dependent_vars: Series
            This attribute is a Series of the variables, specifically the "Alias" column of dataframe self.variable_table_df derived from self.variable_table.
        self.custom_dict: dict
            This attribute is either populated or updated to include newly-selected dependent variables.
        Custom: class
            This class inherits widgets and layouts of Ui_Custom and defines the subGUI within the STAGG settings subGUI that allows users to customize the settings for each dependent variable.
        
        Outputs
        --------
        self.old_deps: Series | list
            This attribute is a copy of self.dependent_vars before calling self.get_variable_table_df() to refresh self.dependent_vars with any recently selected dependent variables.
        self.dependent_vars: Series
            This attribute is set as the user-selected dependent variables defined by the self.variable_table_df dataframe after calling self.get_variable_table_df() and refreshing self.variable_table_df dataframe with any recently selected variables.
        self.custom_dict: dict
            Any items that are in self.old_deps but not in self.dependent_vars are popped from this dictionary.
        
        Outcomes
        --------
        self.get_variable_table_df()
            This method populates several list attributes and dataframe attributes with text and widget statuses from self.buttonDict_variable (dict).
        Custom.extract_variable()
            This Custom class method checks if self.dependent_vars (list) is empty. If it is, it prompts a MessageBox informing the user. If it isn't, it populates self.custom_table (TableWidget) using self.dependent_vars.
        Custom.show()
            This Custom class method shows the custom settings subGUI.
        """
        '''
        # If there is a change
        if set(self.dependent_vars) != set(self.old_deps):
            # remove anything that has been removed
            for c in self.custom_dict:
                if c not in self.dependent_vars:
                    self.custom_dict.pop(c, None)
        '''

        # Require at least 1 dependent variable assignment
        if self.dependent_vars.empty:
            notify_info(title='Choose variables', msg='Please select response variables to be modeled.')
            return

        # Get this from widgets
        variable_df = self.get_variable_table_df()

        # Open Custom window
        custom_window = Custom(variable_df, self.dependent_vars)
        reply = custom_window.exec()

        if reply:
            # Apply results back to widgets
            self.custom_data = custom_window.data
            self.load_custom()

    def load_custom(self): 
        # distribute updates to combo boxes
        for var_key, combo_box in {"Poincare plot": self.Poincare_combo, "Spectral graph": self.Spectral_combo}.items():

            all_options = [combo_box.itemText(i) for i in range(combo_box.count())]
            if "Custom" in all_options:
                combo_box.removeItem(all_options.index("Custom"))

            if all([data_row[var_key] == 1 for data_row in self.custom_data.values()]):
                combo_box.setCurrentText("All")

            elif any([data_row[var_key] == 1 for data_row in self.custom_data.values()]):
                combo_box.addItem("Custom")
                combo_box.setCurrentText("Custom")

            else:
                combo_box.setCurrentText("None")
            
        # Check if we can group them without customization
        all_selections = [tuple(data_row['Transformation']) for data_row in self.custom_data.values()]
        unique_selections = set(all_selections)
        
        # If the set has only one value, the selections are all the same
        if len(unique_selections) == 1:
            selected_options = list(unique_selections)[0]

            # None are selected
            if len(selected_options) == 0:
                self.transform_combo.loadCustom(["None"])

            # or some set is selected
            else:
                self.transform_combo.loadCustom(selected_options)

        # Otherwise we have a custom setup!
        else:
            self.transform_combo.loadCustom(["Custom"])

    def update_hierarchical_combos(self, valid_values, combos, default_value, renamed=None, enable_set=True, first_required=False):
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
            combo.setEnabled(prev_selected)

            # Immediately restore all following to defaults if previous not selected
            if not prev_selected:
                combo.blockSignals(True)
                combo.setCurrentText(default_value)
                combo.blockSignals(False)
                continue

            # Update value based on valid values and any renamed variables
            _default_value = None if (first_required and i==0) else default_value
            update_combo_values(combo, valid_values, renamed=renamed, default_value=_default_value)

            # Check if the curr_value was set back to default
            curr_value = combo.currentText()
            prev_selected = (curr_value != default_value)

            # remove this value from the options for the next boxes
            valid_values = valid_values[valid_values != curr_value]

    def update_graph_config(self, __checked=None, renamed=None):
        """
        Update the Xvar, Pointdodge, Facet1, and Facet2 comboBoxes whenever the user selects
          a new independent variable or covariate variable via RadioButton in the variable_table
    
        Parameters
        --------
        self.variable_table_df: Dataframe
            This attribute is a dataframe that contains the states of the self.variable_table widgets for each variable as stored in self.buttonDict_variable (dict).
        self.graph_config_combos: dict
            This attribute is a nested dictionary that relates the graph settings comboBoxes to their corresponding headers in self.graph_config_df.
        
        Outputs
        --------
        self.{role}_combo: QComboBox
            These ComboBoxes are populated with the aliases of user-selected independent and covariate variables as stored in self.variable_table_df after self.get_variable_table_df() is called and self.variable_table_df is refreshed.
        
        Outcomes
        --------
        self.get_variable_table_df()
            Populate several list attributes and dataframe attributes with text and widget statuses from self.buttonDict_variable (dict).
        """

        combos = self.graph_config_combos.values()
        default_value = "Select variable:"
        valid_values = self.get_independent_covariate_vars()

        self.update_hierarchical_combos(valid_values, combos, default_value, renamed=renamed)


    # TODO: group utilities together
    def get_independent_covariate_vars(self, df=None):
        """
        Get Aliases of all variables labeled as either Independent or Covariate
        """
        # Default to variable table
        if df is None:
            df = self.get_variable_table_df()
        return df.loc[(df["Independent"] == 1) | (df['Covariate'] == 1)]['Alias'].values

    @property
    def graph_config_df(self):
        """
        Populate self.graph_config_df with a dataframe containing the settings selected in the Xvar, Pointdodge, Facet1, and Facet2 comboBoxes.
        
        Parameters
        --------
        self.graph_config_combos: dict
            This attribute is a nested dictionary that relates the graph settings comboBoxes to their corresponding headers in self.graph_config_df.
        
        Outputs
        --------
        self.graph_config_df: Dataframe
            This attribute is a dataframe of two columns populated with the current text of the self.{role}_combo ComboBoxes.
        """
        clades_role_dict = {}
        for idx, (header_name, combo_box) in enumerate(self.graph_config_combos.items()):
            col_index = idx + 1  # (Role)?
            combo_text = combo_box.currentText()
            if combo_text == "Select variable:":
                combo_text = ""

            clades_role_dict.update({col_index: combo_text})

        graph_config_df = pd.DataFrame.from_dict(clades_role_dict,orient='index').reset_index()
        graph_config_df.columns = ['Role','Alias']
        return graph_config_df

    @graph_config_df.setter
    def graph_config_df(self, new_data):
        if new_data is None:
            # TODO: this does weird things with widget placement...
            #self.reset_config()
            pass
        else:
            # Populate widgets
            self.load_graph_config(df=new_data)

    def get_loop_widget_rows(self):
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
                int(self.loop_table.cellWidget(row, headers.index("Include all breaths")).currentText() == "Yes")
            ]

            yield loop_row

    def new_other_settings_combo_box(self):
        new_combo_box = QComboBox()
        new_combo_box.currentIndexChanged.connect(self.update_loop)
        return new_combo_box

    def new_inclusion_combo_box(self):
        inclusion_combo_box = QComboBox()
        inclusion_combo_box.addItems(["No", "Yes"])
        inclusion_combo_box.currentIndexChanged.connect(self.update_loop)
        return inclusion_combo_box

    def new_covariates_checkable_combo(self):
        covariates_checkable_combo = CheckableComboBox()
        covariates_checkable_combo.currentIndexChanged.connect(self.update_loop)
        return covariates_checkable_combo

    
    @property
    def other_config_df(self):
        """
        Populate self.other_config_df with a dataframe derived from the contents of self.clades_other_dict after the latter was updated with the current states of the widgets stored in self.loop_widgets (dict).

        Parameters
        --------
        self.loop_widgets: dict
            This Plethysmography class attribute is a nested dictionary used to populate and save the text, CheckBox, ComboBox, and CheckableComboBox states of Config.loop_table (TableWidget) in the Config subGUI.
        self.loop_table: QTableWidget
            This TableWidget is populated with the contents of self.loop_widgets.
        self.feature_combo: QComboBox
            This ComboBox is the drop-down menu that allows the user to choose whether or not to include plots of respiratory features (i.e. apneas, sighs) with STAGG output.
        
        Outputs
        --------
        self.clades_other_dict: dict
            This attribute is set as an empty dictionary and populated with the contents of self.loop_widgets which is populated with the current text of widgets in self.loop_table.
        self.other_config_df: Dataframe
            This attribute is set as a dataframe populated from self.clades_other_dict and the self.feature_combo selection.
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


        # TODO: what is this trying to do?
        if self.feature_combo.currentText() != "None":
            loop_table_rows = self.loop_table.rowCount()
            if self.feature_combo.currentText() == "All":
                other_config_df.at[loop_table_rows, "Graph"] = "Apneas"
                other_config_df.at[loop_table_rows+1, "Graph"] = "Sighs"
            else:
                other_config_df.at[loop_table_rows-1, "Graph"] = self.feature_combo.currentText()
        
        # TODO: notify user instead?
        # Drop anywhere with empty Graph or Variable columns
        if len(other_config_df):
            other_config_df.drop(
                other_config_df.loc[
                    (other_config_df["Graph"]=="") |
                    (other_config_df["Variable"]=="")].index, inplace=True)
        
        # Correcting some issue with filling nas on Apnea/Sighs stuff
        other_config_df['Inclusion'] = other_config_df['Inclusion'].fillna(0).astype(int)

        return other_config_df

    @other_config_df.setter
    def other_config_df(self, new_data):
        if new_data is None:
            # TODO: this does weird things with widget placement...
            #self.reset_config()
            pass
        else:
            # Populate widgets
            self.load_other_config(df=new_data)

    def save_as(self):
        """
        Save the dataframes
          - self.variable_table_df
          - self.graph_config_df
          - self.other_config_df
          as .csv files to the
           - default STAGG_config folder held in the user-selected
             output folder (self.workspace_dir)
        """
        # Ask user to pick a dir
        save_dir = QFileDialog.getExistingDirectory(self, 'Choose directory for STAGG configuration files', self.workspace_dir)

        # Catch cancel
        if not save_dir:
            return

        # Determine if there are any bad files
        for config_name, (config_df, settings_class) in self.configs.items():

            path = os.path.join(save_dir, f"{config_name}.csv")
            settings_class.save_file(config_df, path, self.workspace_dir)

        notify_info("All settings files have been saved")

    @property
    def configs(self):
        return {
            'variable_config': (self.get_variable_table_df(), VariableSettings),
            'graph_config': (self.graph_config_df, GraphSettings),
            'other_config': (self.other_config_df, OtherSettings)}

    def confirm(self):
        # set data to be retrieved by caller
        self.data = {
            'variable': self.get_variable_table_df(),
            'graph': self.graph_config_df,
            'other': self.other_config_df}
        self.accept()

    def add_loop(self):
        """
        - Update self.loop_widgets with another key corresponding to the additional row
        - add another row to self.loop_table
        ]- and populate the row with the text and widgets stored in self.loop_widgets.
        """

        loop_row = self.loop_table.rowCount()
        self.loop_table.insertRow(loop_row)

        self.loop_table.setCellWidget(loop_row, 0, QLineEdit())

        # Response Var, Xvar, Pointdodge, Facet1, Facet2
        for idx in range(6):
            new_combo_box = self.new_other_settings_combo_box()
            self.loop_table.setCellWidget(loop_row, idx+1, new_combo_box)

        covariates_checkable_combo = self.new_covariates_checkable_combo()
        self.loop_table.setCellWidget(loop_row, 6, covariates_checkable_combo)

        self.loop_table.setCellWidget(loop_row, 7, QLineEdit())
        self.loop_table.setCellWidget(loop_row, 8, QLineEdit())

        inclusion_combo_box = self.new_inclusion_combo_box()
        self.loop_table.setCellWidget(loop_row, 9, inclusion_combo_box)

        self.update_loop()

    def reset_config(self):
        """
        - Reset attributes
        - clear Xvar, Pointdodge, Facet1, and Facet2 comboBoxes
        - set Poincare, Spectral, feature, and Transformation
           comboBoxes to None
        - repopulate self.loop_table and self.variable_table with
           the updated (rebuilt) dictionaries self.loop_widgets
           and self.buttonDict_variable respectively.
        """
        variable_table_df = ConfigSettings.get_default_variable_df(self.variable_names)
        self.populate_variable_table(variable_table_df)

        for combo_box in self.graph_config_combos.values():
            combo_box.blockSignals(True)
            combo_box.clear()
            combo_box.addItem("Select variable:")
            combo_box.blockSignals(False)

        for combo in self.additional_dict.values():
            combo.blockSignals(True)
            if type(combo) is CheckableComboBox:
                combo.loadCustom(["None"])
            else:
                combo.setCurrentText("None")
            combo.blockSignals(False)

        self.clear_loops()

    def clear_loops(self):
        for _ in range(self.loop_table.rowCount()):
            # CheckableComboBox keeps emitting signal as it dies...
            # Blocking signals to prevent errors
            self.loop_table.cellWidget(0, 6).blockSignals(True)
            self.loop_table.removeRow(0)

    def load_configs(self, __checked, files=None):
        """
        Check the user-selected files to ensure they
          - exist
          - correct file format
          - begin with either
            > "variable_config"
            > "graph_config"
            > "other_config"

        Bad input triggers a MessageBox or dialog to inform the user

        If input is good, load the file as a dataframe

        """

        # if no paths passed in, let user pick
        if not files:
            files = ConfigSettings.open_file()
            if not files:
                return

            self.load_variable_config(files['variable'])
            self.load_graph_config(files['graph'])
            self.load_other_config(files['other'])

    def load_variable_config(self, var_config_path=None, df=None):
        """
        Load the variable_config file as a dataframe
        Populate self.variable_names with the list values in the "Column" column of the dataframe
        Populate self.variable_table (TableWidget) with a row for each variable in the variable_config dataframe
        Load the custom settings.
        """
        if df is None:
            df = VariableSettings.attempt_load(var_config_path)
        else:
            df = df.copy()

        # Convert dataframe...
        self.variable_names = df['Column'].tolist()
        self.aliases = df['Alias']

        self.populate_variable_table(df)

        #for a in self.variable_config_dict:
        # TODO: bad! use df iteration!
        for row_num, record in enumerate(df.to_dict('records')):
            var_name = record['Column']  # TODO: remove - unused
            alias_name = record['Alias']
            self.variable_table.item(row_num, 1).setText(alias_name)
            for i, k in enumerate(["Independent","Dependent","Covariate"]):
                if record[k] == 1:
                    widget = self.variable_table.cellWidget(row_num, i + 2)
                    widget.blockSignals(True)
                    widget.setChecked(True)
                    widget.blockSignals(False)
                    # we can break as there should be only one checked!
                    break

        # Load custom data
        all_custom = df[df["Dependent"] == 1].fillna("")
        self.custom_data = {}
        for record in all_custom.to_dict('records'):
            # Clean transform values and create list
            # Replace all 'non' with 'raw'
            transform = [t.replace("non","raw") for t in record['Transformation'].split('@')]
            # Replace all 'log' with 'ln', unless the text is 'log10'
            transform = [t.replace("log","ln") if t != "log10" else t for t in transform ]

            new_custom = {
                'Variable': record['Alias'],
                'Y axis minimum': record['ymin'],
                'Y axis maximum': record['ymax'],
                'Transformation': transform,
                'Poincare plot': record['Poincare'],
                'Spectral graph': record['Spectral']}
            self.custom_data[record['Alias']] = new_custom

        self.load_custom()

        #    alias: {
        #        'Variable': alias,
        #        'Y axis minimum': '0',
        #        'Y axis maximum': '0',
        #        'Transformation': [],
        #        'Poincare plot': 1,
        #        'Spectral graph': 0},
        #    }

    def order_items(self, combo_name):
        combo = self.graph_config_combos[combo_name]
        alias_name = combo.currentText()
        alias_idx, = np.where(self.aliases == alias_name)[0]
        print(np.where(self.aliases == alias_name))
        print(alias_idx)
        group_name = self.variable_names[alias_idx]

        # Skip anything set to default
        if group_name == "Select variable:":
            return

        items = self.col_vals[group_name]

        order_window = OrderingWindow(combo_name, group_name, items)
        reply = order_window.exec()
        if reply:
            # set new items
            self.col_vals[group_name] = order_window.get_items()

    def load_custom_config(self):
        """
        Populate Custom.custom_table based on the dependent variables
          selected by the user according to the dataframe derived from
          the variable config .csv file the user selected. 
        """
        for combo in self.additional_dict.values():
            combo.setCurrentText("None")

        self.custom_data = {}
        #for k, val in self.variable_config_dict.items():
        for k, val in self.get_variable_table_df().iterrows():
            new_custom_data = {
                'Poincare': 0,
                'Spectral': 0,
                'ymin': "",
                'ymax': "",
                'Transformation': []
            }

            if val['Poincare'] == "1":
                new_custom_data['Poincare'] = 1

            if val['Spectral'] == "1":
                new_custom_data['Spectral'] = 1

            for y in ['ymin','ymax']:
                if val[y] != "":
                    new_custom_data[y] = val[y]

            if val['Transformation'] != "":
                transform = [s.replace("non","raw") and s.replace("log","ln") for s in val['Transformation'].split('@')]
                transform = [z.replace("ln10","log10") for z in transform]
                self.transform_combo.loadCustom(transform)
                self.transform_combo.updateText()

    def load_graph_config(self, graph_config_file=None, df=None):
        """
        Populate the Xvar, Pointdodge, Facet1, and Facet2 comboBoxes
          with the variables selected as independent or covariate
          according to the variable_config .csv file

        If there is no variable_config file, then populate those comboBoxes
          with the variables in the dataframe read from the graph_config
          file and set the comboBoxes current text.
        """
        if df is None:
            gdf = GraphSettings.attempt_load(graph_config_file)
        else:
            gdf = df.copy()

        # Get only Independent/Covariate aliases
        # Try getting from variable_table first
        indep_covariate_vars = self.get_independent_covariate_vars()
        
        for idx, combo in enumerate(self.graph_config_combos.values()):
            combo.clear()
            combo.addItem("Select variable:")
            if len(indep_covariate_vars):
                combo.addItems(indep_covariate_vars)

                # Set each box to the value stored for it's Role
                combo_role = idx + 1
                curr_selection = gdf.loc[(gdf['Role'] == combo_role) & pd.notna(gdf['Alias'])]
                if len(curr_selection):
                    combo.setCurrentText(curr_selection["Alias"].values[0])

    def load_other_config(self, other_config_file=None, df=None):
        """
        Set the current text of the feature plots comboBox according to the other_config .csv file loaded
        Populate self.loop_table with the contents of the dataframe derived from the other_config .csv file.
        """

        if df is None:
            odf = OtherSettings.attempt_load(other_config_file)
        else:
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

        # Populate each row of loop_table
        for row_num in odf.index:
            self.add_loop()
            for table_idx, header in enumerate(self.loop_table_headers):
                if header == "Covariates":
                    # TODO: we care about having dependent variables?
                    covariates_str = odf.at[row_num, 'Covariates']
                    if covariates_str and len(self.dependent_vars):
                        covariate_combo = self.loop_table.cellWidget(row_num, table_idx)
                        covariate_combo.loadCustom(covariates_str.split('@'))
                        covariate_combo.updateText()
                    continue

                if header == "Include all breaths":
                    new_text = "Yes" if odf.at[row_num, "Inclusion"] else "No"
                elif header == "Graph name":
                    new_text = str(odf.at[row_num, "Graph"])
                elif header == "Response variable":
                    new_text = str(odf.at[row_num, "Variable"])
                else:
                    new_text = str(odf.at[row_num, header])

                write_widget(self.loop_table.cellWidget(row_num, table_idx), new_text)


    def checkable_ind(self):
        """
        Change the RadioButton status for every column in the selected rows so that only the "Independent" RadioButton is set as checked.
        """
        independent_col_idx = 2
        self.check_all(independent_col_idx)

    def checkable_dep(self):
        """
        Change the RadioButton status for every column in the selected rows so that only the "Dependent" RadioButton is set as checked.
        """
        dependent_col_idx = 3
        self.check_all(dependent_col_idx)
        
    def checkable_cov(self):
        """
        Change the RadioButton status for every column in the selected rows so that only the "Covariate" RadioButton is set as checked.
        """
        covariate_col_index = 4
        self.check_all(covariate_col_index)

    def checkable_ign(self):
        """
        Change the RadioButton status for every column in the selected rows so that only the "Ignore" RadioButton is set as checked.
        """
        ignore_col_index = 5
        self.check_all(ignore_col_index)

    def check_all(self, checked_idx):
        for selected_rows in self.variable_table.selectedRanges():
            first_row = selected_rows.topRow()
            last_row = selected_rows.bottomRow()
            for row in range(first_row, last_row+1):
                self.variable_table.cellWidget(row, checked_idx).setChecked(True)


# TODO: this is kinda gross -- split these out!
class ConfigSettings(Settings):
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
    def open_file(cls, workspace_dir=""):
        while True:
            files, filter = QFileDialog.getOpenFileNames(None, cls.file_chooser_message, workspace_dir)

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
    def _save_file(filepath, df):
        # Write df to csv at `path`
        df.to_csv(filepath, index=False)

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

    default_filename = 'variable_config.csv'

    @staticmethod
    def _right_filename(filepath):
        file_basename = os.path.basename(filepath) 
        return "variable" in file_basename and "config" in file_basename

    def attempt_load(filepath):
        if filepath.endswith(".xlsx"):
            df = pd.read_excel(filepath)

        elif filepath.endswith(".csv"):
            df = pd.read_csv(filepath)

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

    default_filename = 'graph_config.csv'

    @staticmethod
    def _right_filename(filepath):
        file_basename = os.path.basename(filepath) 
        return "graph" in file_basename and "config" in file_basename

    def attempt_load(filepath):
        gdf = pd.read_csv(filepath, index_col=False)
        return gdf


class OtherSettings(ConfigSettings):

    default_filename = 'other_config.csv'

    @staticmethod
    def _right_filename(filepath):
        file_basename = os.path.basename(filepath) 
        return "other" in file_basename and "config" in file_basename

    def attempt_load(filepath):
        odf = pd.read_csv(filepath, index_col=False, keep_default_na=False)
        return odf

    @staticmethod
    def _save_file(filepath, df):
        # If there are covariates, join them into a string with sep='@'
        #func = lambda x : '@'.join(x) if x else x
        #df['Covariates'] = df['Covariates'].apply(func)

        df = df.fillna("")

        # Rename transform labels
        for i, record in df.iterrows():
            covariates = record['Covariates']
            if covariates:
                df.at[i, 'Covariates'] = '@'.join(covariates)

        df.to_csv(filepath, index=False)