
import os
from pathlib import Path
import datetime
import csv
import pandas as pd
from PyQt5.QtWidgets import QWidget, QSpacerItem, QSizePolicy, QButtonGroup, QTableWidgetItem, QRadioButton, QLineEdit, QComboBox, QFileDialog
from PyQt5.QtCore import QObject, Qt
from checkable_combo_box import CheckableComboBox
from align_delegate import AlignDelegate
from custom import Custom
from util import avert_name_collision, notify_error, notify_warning
from thumbass_controller import Thumbass
from ui.config_form import Ui_Config

class Config(QWidget, Ui_Config):
    """
    The Config class inherits widgets and layouts of Ui_Config and defines the STAGG settings subGUI that allows users to define the STAGG settings.
    
    Parameters
    --------
    QWidget: class
        The Config class inherits properties and methods from the QWidget class.
    Ui_Config: class
        The Config class inherits widgets and layouts defined in the Ui_Config class.
    """
    def __init__(self,Plethysmography):
        """
        Instantiate the Config class.

        Parameters 
        --------
        Plethysmography: class
            Config inherits the properties, attributes, and methods of the Plethysmography class.

        Outputs
        --------
        self.pleth: class
            Shorthand for Plethysmography class.
        self.deps: list
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

        # Add custom combo box
        self.setup_transform_combo()

        self.pleth = Plethysmography
        self.deps = []
        self.setup_variables_config()
        self.setup_table_config()
        self.show_loops(self.loop_table, 1)

        # Setup cell changed callbacks
        self.update_table_conn = self.variable_table.cellChanged.connect(self.no_duplicates)
    
    def minus_loop(self):
        """
        Remove the selected row from self.loop_table and its corresponding data from self.pleth.loop_menu (dict).

        Parameters
        --------
        self.loop_table: QTableWidget
            This TableWidget displays the settings for additional models either via widgets or loading previously made other_config.csv with previous STAGG run's settings for additional models.
        self.pleth.loop_menu: dict
            The nested dictionary used to populate and save the text, CheckBox, ComboBox, and CheckableComboBox states of Config.loop_table (TableWidget) in the Config subGUI.
        
        Outputs
        --------
        self.loop_table: QTableWidget
            The user-selected row is removed from this TableWidget.
        self.pleth.loop_menu: dict
            The item in this nested dictionary that corresponds to the removed row is popped from the dictionary.

        """
        self.pleth.loop_menu[self.loop_table].pop(self.loop_table.currentRow())
        for p in self.pleth.loop_menu[self.loop_table]:
            if p > self.loop_table.currentRow():
                self.pleth.loop_menu[self.loop_table][p-1] = self.pleth.loop_menu[self.loop_table].pop(p)
        self.loop_table.removeRow(self.loop_table.currentRow())
        
    def reference_event(self):
        """
        Respond to the signal emitted by the self.help_{setting} ToolButton clicked by the user by calling self.populate_reference(self.sender.objectName()) to populate the self.config_reference TextBrowser with the definition, description, and default value of corresponding setting.
        """
        sbutton = self.sender()
        self.populate_reference(sbutton.objectName())

    def populate_reference(self,buttoned: QObject.objectName):
        """
        Populate self.config_reference (TextBrowser) with the definition, description, and default values of the appropriate setting as indicated by the suffix of the ToolButton's objectName(), e.g. "help_{setting}" from Plethysmography.rc_config (reference_config.json).

        Parameters
        --------
        buttoned: QObject.objectName
            This variable is the objectName of the ToolButton that emitted the signal self.reference_event that called this method. Its suffix is used to identify the appropriate cell in self.view_tab (TableWidget).
        self.widgy: dict
            This attribute relates the self.help_{setting} ToolButtons to self.reference_config TableWidget.
        Plethysmography.rc_config: dict
            This attribute is a shallow dictionary loaded from reference_config.json. It contains definitions, descriptions, and recommended values for every basic, manual, and automated BASSPRO setting.

        Outputs
        --------
        self.config_reference: QTableWidget
            This TableWidget displays the definition, description, and default value of the user-selected setting.
        """
        for k,v in self.widgy.items():
            for vv in v:
                if vv.objectName() == str(buttoned):
                    k.setPlainText(self.pleth.rc_config['References']['Definitions'][buttoned.replace("help_","")])

    def no_duplicates(self):
        """
        Automatically rename the variable in the "Alias" column of self.variable_table (TableWidget) to avoid duplicate variable names.

        Parameters
        --------
        self.variable_table: QTableWidget
            This TableWidget displays the text and widgets needed to allow the user to indicate the type of a selected variable.
        """
        '''
        for row in range(self.variable_table.rowCount()):
            if row != self.variable_table.currentRow():
                item = self.variable_table.item(row, 1)
                if item is None:
                    pass

                elif item.text() == self.variable_table.currentItem().text():
                    self.n += 1
                    self.variable_table.item(row,1).setText(f"{self.variable_table.item(row,1).text()}_{self.n}")
        '''

        curr_item = self.variable_table.currentItem()
        if curr_item is None:
            return

        new_item_name = curr_item.text()
        
        curr_col = self.variable_table.currentColumn()
        if curr_col != 1:
            raise RuntimeError("Can only edit Alias column!")

        num_variables = self.variable_table.rowCount()
        curr_row = self.variable_table.currentRow()

        # Get all var names, skipping curr row
        existing_vars = [self.variable_table.item(row, 1).text() for row in range(num_variables) if row != curr_row]
        
        # Get unique name
        new_item_name = avert_name_collision(new_item_name, existing_vars)
        
        # Set text
        curr_item.setText(new_item_name)

        self.update_loop()
    
    def update_loop(self):
        """
        Update the contents of self.clades_other_dict with the contents of self.pleth.loop_menu and then update the contents of self.loop_table with the newly updated contents of self.clades_other_dict.
        
        Parameters
        --------
        self.variable_table_df: Dataframe
            This attribute is a dataframe that contains the states of the self.variable_table widgets for each variable.
        self.loop_table: QTableWidget
            This TableWidget displays the settings for additional models either via widgets or loading previously made other_config.csv with previous STAGG run's settings for additional models.
        self.pleth.loop_menu: dict
            The nested dictionary used to populate and save the text, CheckBox, ComboBox, and CheckableComboBox states of Config.loop_table (TableWidget) in the Config subGUI.
        self.clades_other_dict: dict
            This dictionary is populated and updated with the current states of the widgets stored in self.pleth.loop_menu.
        
        Outputs
        --------
        self.deps: Series
            This attribute is a Series of the variables, specifically the "Alias" column of dataframe self.variable_table_df derived from self.variable_table.
        self.loop_table: QTableWidget
            This TableWidget is populated with the settings for additional models either via widgets or loading previously made other_config.csv with previous STAGG run's settings for additional models.
        self.clades_other_dict: dict
            This dictionary is populated and updated with the current states of the widgets stored in self.pleth.loop_menu.
        
        Outcomes
        --------
        self.show_loops(self.loop_table, len(self.clades_other_dict))
            This method populates self.pleth.loop_menu with the appropriate widgets and populates self.loop_table with self.clades_other_dict.
        """
        #self.disconnect(self.update_table_conn)
        notify_warning("Blocking signals")
        self.blockSignals(True)

        self.update_variable_table_df()
        self.deps = self.variable_table_df["Alias"]
        for row in range(self.loop_table.rowCount()):
            self.clades_other_dict.update({row:{}})
            self.clades_other_dict[row].update({"Graph": self.pleth.loop_menu[self.loop_table][row]["Graph"].text()})
            self.clades_other_dict[row].update({"Variable": self.pleth.loop_menu[self.loop_table][row]["Variable"].currentText()})
            self.clades_other_dict[row].update({"Xvar": self.pleth.loop_menu[self.loop_table][row]["Xvar"].currentText()})
            self.clades_other_dict[row].update({"Pointdodge": self.pleth.loop_menu[self.loop_table][row]["Pointdodge"].currentText()})
            self.clades_other_dict[row].update({"Facet1": self.pleth.loop_menu[self.loop_table][row]["Facet1"].currentText()})
            self.clades_other_dict[row].update({"Facet2": self.pleth.loop_menu[self.loop_table][row]["Facet2"].currentText()})
            self.clades_other_dict[row].update({"Covariates": '@'.join(self.pleth.loop_menu[self.loop_table][row]["Covariates"].currentData())})
            self.clades_other_dict[row].update({"Inclusion": self.pleth.loop_menu[self.loop_table][row]["Inclusion"].currentText()}) 
            self.clades_other_dict[row].update({"Y axis minimum": self.pleth.loop_menu[self.loop_table][row]["Y axis minimum"].text()})
            self.clades_other_dict[row].update({"Y axis maximum": self.pleth.loop_menu[self.loop_table][row]["Y axis maximum"].text()})

        self.show_loops(self.loop_table,len(self.clades_other_dict))
        for row_1 in range(len(self.clades_other_dict)):
            self.loop_table.cellWidget(row_1,0).setText(self.clades_other_dict[row_1]['Graph'])
            self.loop_table.cellWidget(row_1,7).setText(self.clades_other_dict[row_1]['Y axis minimum'])
            self.loop_table.cellWidget(row_1,8).setText(self.clades_other_dict[row_1]['Y axis maximum'])
            self.loop_table.cellWidget(row_1,1).setCurrentText(self.clades_other_dict[row_1]['Variable'])
            self.loop_table.cellWidget(row_1,2).setCurrentText(self.clades_other_dict[row_1]['Xvar'])
            self.loop_table.cellWidget(row_1,3).setCurrentText(self.clades_other_dict[row_1]['Pointdodge'])
            self.loop_table.cellWidget(row_1,4).setCurrentText(self.clades_other_dict[row_1]['Facet1'])
            self.loop_table.cellWidget(row_1,5).setCurrentText(self.clades_other_dict[row_1]['Facet2'])
            if self.clades_other_dict[row_1]['Covariates'] != "":
                self.pleth.loop_menu[self.loop_table][row_1]['Covariates'].loadCustom([w for w in self.clades_other_dict[row_1]['Covariates'].split('@')])
                self.pleth.loop_menu[self.loop_table][row_1]['Covariates'].updateText()

        self.blockSignals(False)

    def setup_transform_combo(self):
        """
        Add widget from custom class CheckableComboBox to STAGG settings subGUI layout to serve as drop-down menu for data transformation options.
        """
        spacerItem64 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_25.addItem(spacerItem64)
        self.transform_combo = CheckableComboBox()
        self.transform_combo.addItems(["raw","log10","ln","sqrt","Custom","None"])
        self.verticalLayout_25.addWidget(self.transform_combo)
        spacerItem65 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_25.addItem(spacerItem65)

    def setup_variables_config(self): 
        """
        Add the CheckableComboBox to the STAGG settings subGUI layout
        Establish attributes
        Assign clicked signals and self.reference_event slots to each self.help_{setting} ToolButton.

        Parameters
        --------
        self.variable_table_df: Dataframe
            This attribute is a dataframe that containts the states of the self.variable_table widgets for each variable.
        self.clades_graph: Dataframe
            This attribute is a dataframe that containts the states of the many comboBoxes that define graph roles for selected variables.
        self.clades_other: Dataframe
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
        self.pleth.variable_config: str
            This Plethysmography class attribute is the file path to one of the STAGG settings files.
        self.plethg.graph_config: str
            This Plethysmography class attribute is the file path to one of the STAGG settings files.
        self.pleth.other_config: str
            This Plethysmography class attribute is the file path to one of the STAGG settings files.

        Outputs
        --------
        self.role_list: list
            This attribute is a list of strings that are the headers of the self.loop_table.
        self.additional_dict: dict
            This dictionary relates certain header strings to their corresponding comboBoxes.
        self.settings_dict: dict
            A nested dictionary that relates the graph settings comboBoxes to their headers.
        self.widgy: dict
            This dictionary relates the self.help_{setting} widgets to self.config_reference (TextBrowser).
        self.custom_dict: dict
            This attribue is set as an empty dictionary.
        self.custom_port: dict
            This attribute is set as an empty dictionary.
        self.clades_other_dict: dict
            This dictionary is populated and updated with the current states of the widgets stored in self.pleth.loop_menu.
        self.variable_table_df: Dataframe | list
            This attribute is set as an empty list.
        self.clades_graph: Dataframe | list
            This attribute is set as an empty list.
        self.clades_other: Dataframe | list
            This attribute is set as an empty list.
        self.configs: dict
            This attribute is populated with a nested dictionary in which each item contains a dictionary unique to each settings file - variable_config.csv, graph_config.csv, and other_config.csv. Each dictionary has the following key, value items: "variable", the Plethysmography class attribute that refers to the file path to the settings file; "path", the string file path to the settings file; "frame", the attribute that refers to the dataframe; "df", the dataframe.

        Outcomes
        --------
        self.setup_transform_combo()
            Add widget from custom class CheckableComboBox to STAGG settings subGUI layout to serve as drop-down menu for data transformation options.
        """
        self.role_list = ["Graph","Variable","Xvar","Pointdodge","Facet1","Facet2","Inclusion","Y axis minimum","Y axis maximum"]
        self.additional_dict = {self.feature_combo:"Feature",self.Poincare_combo:"Poincare",self.Spectral_combo:"Spectral",self.transform_combo:"Transformation"}
        self.settings_dict = {"role": {self.Xvar_combo:1,self.Pointdodge_combo:2,self.Facet1_combo:3,self.Facet2_combo:4}, 
                              "rel": {"Xvar":self.Xvar_combo,"Pointdodge":self.Pointdodge_combo,"Facet1":self.Facet1_combo,"Facet2":self.Facet2_combo}}
        self.widgy = {self.config_reference:[self.help_xvar,self.help_pointdodge,self.help_facet1,self.help_facet2,self.help_feature,self.help_poincare,self.help_spectral,self.help_transformation]}

        self.custom_dict = {}
        self.custom_port = {}
        self.clades_other_dict = {}
        self.variable_table_df = []
        self.clades_graph = []
        self.clades_other = []
        self.configs = {
            "variable_config":{
                "variable": self.pleth.variable_config,
                "path":"",
                "frame": self.variable_table_df,
                "df":[]
            },
            "graph_config": {
                "variable": self.pleth.graph_config,
                "path": "",
                "frame": self.clades_graph,
                "df":[]
            },
            "other_config": {
                "variable": self.pleth.other_config,
                "path": "",
                "frame": self.clades_other,
                "df": []
            }
        }

        for v in self.widgy.values():
            for vv in v:
                vv.clicked.connect(self.reference_event)
    
    def setup_table_config(self):
        """
        Assign delegates to self.variable_table and self.loop_table, set self.pleth.buttonDict_variable as an empty dictionary, repopulate it with text and widgets based on items listed in self.pleth.breath_df (list), assign the RadioButton widgets of each row to a ButtonGroup, populate self.variable_table (TableWidget) with the contents of self.pleth.buttonDict_variable, assign toggled signals slotted for self.add_combos() to the RadioButtons in self.pleth.buttonDict_variable that correspond to those in the "Independent" and "Covariate" columns of the TableWidget, and adjust the size of the cells of self.variable_table.

        Parameters
        --------
        AlignDelegate: class
            This class assigns delegates to Config.variable_table and Config.loop_table TableWidgets and and centers the delegate items.
        self.variable_table: QTableWidget
            This TableWidget is defined in the Config class, displayed in the STAGG settings subGUI, and populated with rows based on the list of variables (Plethysmography.breath_df).
        self.loop_table: QTableWidget
            This TableWidget is populated with the settings for additional models either via widgets or loading previously made other_config.csv with previous STAGG run's settings for additional models.
        self.pleth.breath_df: list
            This Plethysmography class attribute is a list of variables derived from one of the following sources: 1) the metadata csv file and the BASSPRO settings files, or 2) user-selected variable_config.csv file, or 3) user-selected BASSPRO JSON output file.
        self.pleth.buttonDict_variable: dict
            This Plethysmography class attribute is a nested dictionary used to populate and save the text and RadioButton states of Config.variable_table (TableWidget) in the Config subGUI.
        
        Outputs
        --------
        self.variable_table: QTableWidget
            This TableWidget is populated with text and widgets stored in self.pleth.buttonDict_variable (dict).
        self.loop_table: QTableWidget
            This TableWidget is populated with one row. (why?)
        self.pleth.buttonDict_variable: dict
            This Plethysmography class attribute is set as an empty dictionary and repopulated with text and widgets based on items in the list self.pleth.breath_df.
        """
        # I've forgotten what this was specifically about, but I remember it had something to do with spacing or centering text or something.
        delegate = AlignDelegate(self.variable_table)
        delegate_loop = AlignDelegate(self.loop_table)
        self.variable_table.setItemDelegate(delegate)
        self.loop_table.setItemDelegate(delegate_loop)

        # Setting the number of rows in each table upon opening the window:
        self.variable_table.setRowCount(len(self.pleth.breath_df))
        self.loop_table.setRowCount(1)
        
        # Establishing the dictionary in which the table contents will be stored for delivery to r_config.csv:
        self.pleth.buttonDict_variable = {}

        # Grabbing every item in breath_df and making a row for each: 
        row = 0
        for item in self.pleth.breath_df:
            # Establishing each row as its own group to ensure mutual exclusivity for each row within the table:
            self.pleth.buttonDict_variable[item]={"group": QButtonGroup()}
            # self.buttonDict_variable[item]["group"].buttonClicked.connect(self.check_buttons)

            # The first two columns are the text of the variable name. Alias should be text editable.
            self.pleth.buttonDict_variable[item]["orig"] = QTableWidgetItem(item)
            self.pleth.buttonDict_variable[item]["Alias"] = QTableWidgetItem(item)

            # Creating the radio buttons that will populate the cells in each row:
            self.pleth.buttonDict_variable[item]["Independent"] = QRadioButton("Independent")
            self.pleth.buttonDict_variable[item]["Dependent"] = QRadioButton("Dependent")
            self.pleth.buttonDict_variable[item]["Covariate"] = QRadioButton("Covariate")
            self.pleth.buttonDict_variable[item]["Ignore"] = QRadioButton("Ignore")
            self.pleth.buttonDict_variable[item]["Ignore"].setChecked(True)

            # Adding those radio buttons to the group to ensure mutual exclusivity across the row:
            self.pleth.buttonDict_variable[item]["group"].addButton(self.pleth.buttonDict_variable[item]["Independent"])
            self.pleth.buttonDict_variable[item]["group"].addButton(self.pleth.buttonDict_variable[item]["Dependent"])
            self.pleth.buttonDict_variable[item]["group"].addButton(self.pleth.buttonDict_variable[item]["Covariate"])
            self.pleth.buttonDict_variable[item]["group"].addButton(self.pleth.buttonDict_variable[item]["Ignore"])
            
            # Populating the table widget with the row:
            self.variable_table.setItem(row,0,self.pleth.buttonDict_variable[item]["orig"])
            self.variable_table.setItem(row,1,self.pleth.buttonDict_variable[item]["Alias"])

            self.variable_table.setCellWidget(row,2,self.pleth.buttonDict_variable[item]["Independent"])
            self.variable_table.setCellWidget(row,3,self.pleth.buttonDict_variable[item]["Dependent"])
            self.variable_table.setCellWidget(row,4,self.pleth.buttonDict_variable[item]["Covariate"])
            self.variable_table.setCellWidget(row,5,self.pleth.buttonDict_variable[item]["Ignore"])

            row += 1
            # you have to iteratively create the widgets for each row, not just iteratively
            # add the widgets for each row because it'll only do the last row
        for item_1 in self.pleth.breath_df:
            self.pleth.buttonDict_variable[item_1]["Independent"].toggled.connect(self.add_combos)
            self.pleth.buttonDict_variable[item_1]["Covariate"].toggled.connect(self.add_combos)
        
        self.variable_table.resizeColumnsToContents()
        self.variable_table.resizeRowsToContents()
        self.show_loops(self.loop_table, 1)
    
    def show_loops(self,table,r):
        """
        Set self.pleth.loop_menu as an empty dictionary, iteratively populate self.pleth.loop_menu with QLineEdits, QComboBoxes, and CheckableComboBox, populate the ComboBoxes with items from self.deps, populate self.loop_table with the contents of self.pleth.loop_menu, and adjust the cell sizes of self.loop_table.

        Parameters
        --------
        self.pleth.loop_menu: dict
            This Plethysmography class attribute is a nested dictionary used to populate and save the text, CheckBox, ComboBox, and CheckableComboBox states of Config.loop_table (TableWidget) in the Config subGUI.
        self.role_list: list
            This attribute is a list of strings that are the headers of the self.loop_table.
        self.deps:
            This attribute is a Series of the variables, specifically the "Alias" column of dataframe self.variable_table_df derived from self.variable_table.
        table: QTableWidget
            This argument refers to self.loop_table TableWidget - previously there was another loop table, so that's why we have the "table" argument instead of just used the attribute to refer to the widget.
        r: int
            This argument passes the number of rows self.loop_table should have.
        
        Outputs
        --------
        self.pleth.loop_menu: dict
            This Plethysmography class attribute is set as an empty dictionary and repopulated with widgets with a row count of "r". 
        self.loop_table: QTableWidget
            This TableWidget is populated with the contents of self.pleth.loop_menu.
        """
        # Almost redundant. See Main.show_loops().
        print("config.show_loops()")
        self.pleth.loop_menu = {}
        for row in range(r):
            self.pleth.loop_menu.update({table:{row:{}}})
            # Creating the widgets within the above dictionary that will populate the cells of each row:
            self.pleth.loop_menu[table][row]["Graph"] = QLineEdit()
            self.pleth.loop_menu[table][row]["Y axis minimum"] = QLineEdit()
            self.pleth.loop_menu[table][row]["Y axis maximum"] = QLineEdit()
            for role in self.role_list[1:6]:
                self.pleth.loop_menu[table][row][role] = QComboBox()
                self.pleth.loop_menu[table][row][role].addItems([""])
                self.pleth.loop_menu[table][row][role].addItems([x for x in self.deps])
            
            self.pleth.loop_menu[table][row]["Inclusion"] = QComboBox()
            self.pleth.loop_menu[table][row]["Inclusion"].addItems(["No","Yes"])
            self.pleth.loop_menu[table][row]["Covariates"] = CheckableComboBox()
            self.pleth.loop_menu[table][row]["Covariates"].addItems([b for b in self.deps])
        
            table.setCellWidget(row,0,self.pleth.loop_menu[table][row]["Graph"])
            table.setCellWidget(row,1,self.pleth.loop_menu[table][row]["Variable"])
            table.setCellWidget(row,2,self.pleth.loop_menu[table][row]["Xvar"])
            table.setCellWidget(row,3,self.pleth.loop_menu[table][row]["Pointdodge"])
            table.setCellWidget(row,4,self.pleth.loop_menu[table][row]["Facet1"])
            table.setCellWidget(row,5,self.pleth.loop_menu[table][row]["Facet2"])
            table.setCellWidget(row,6,self.pleth.loop_menu[table][row]["Covariates"])
            table.setCellWidget(row,7,self.pleth.loop_menu[table][row]["Y axis minimum"])
            table.setCellWidget(row,8,self.pleth.loop_menu[table][row]["Y axis maximum"])
            table.setCellWidget(row,9,self.pleth.loop_menu[table][row]["Inclusion"])
        
        table.resizeColumnsToContents()
        table.resizeRowsToContents()

    def show_custom(self):
        """
        Check self.variable_table Alias selections, update rows in Custom.custom_table accordingly, and show the custom subGUI.

        Parameters
        --------
        self.deps: Series
            This attribute is a Series of the variables, specifically the "Alias" column of dataframe self.variable_table_df derived from self.variable_table.
        self.custom_dict: dict
            This attribute is either populated or updated to include newly-selected dependent variables.
        Custom: class
            This class inherits widgets and layouts of Ui_Custom and defines the subGUI within the STAGG settings subGUI that allows users to customize the settings for each dependent variable.
        
        Outputs
        --------
        self.old_deps: Series | list
            This attribute is a copy of self.deps before calling self.update_variable_table_df() to refresh self.deps with any recently selected dependent variables.
        self.deps: Series
            This attribute is set as the user-selected dependent variables defined by the self.variable_table_df dataframe after calling self.update_variable_table_df() and refreshing self.variable_table_df dataframe with any recently selected variables.
        self.custom_dict: dict
            Any items that are in self.old_deps but not in self.deps are popped from this dictionary.
        
        Outcomes
        --------
        self.update_variable_table_df()
            This method populates several list attributes and dataframe attributes with text and widget statuses from self.pleth.buttonDict_variable (dict).
        Custom.extract_variable()
            This Custom class method checks if self.deps (list) is empty. If it is, it prompts a MessageBox informing the user. If it isn't, it populates self.custom_table (TableWidget) using self.deps.
        Custom.show()
            This Custom class method shows the custom settings subGUI.
        """
        print("config.show_custom()")
        self.old_deps = self.deps
        self.update_variable_table_df()
        self.deps = self.variable_table_df.loc[(self.variable_table_df["Dependent"] == 1)]["Alias"]
        if self.custom_dict == {}:
            self.pleth.c = Custom(self)
            self.pleth.c.extract_variable()
        elif set(self.deps) != set(self.old_deps):
            d = [c for c in self.custom_dict]
            for c in d:
                if c not in self.deps:
                    self.custom_dict.pop(c,None)
            self.pleth.c = Custom(self)
            self.pleth.c.extract_variable()
        else:
            self.pleth.c.show()

    def update_variable_table_df(self):
        """
        - Populate several list attributes and self.variable_table_df dataframe with text
           and widget statuses from self.pleth.buttonDict_variable (dict)
        - create columns for self.clades_graph and self.clades_other.

        Parameters
        --------
        self.pleth.buttonDict_variable: dict
            This Plethysmography class attribute is a nested dictionary used to populate and save the text and RadioButton states of Config.variable_table (TableWidget) in the Config subGUI.
        
        Outputs
        --------
        self.variable_table_df: Dataframe
            This attribute is populated with a dataframe that contains the states of the self.variable_table widgets for each variable as stored in self.pleth.buttonDict_variable (dict).
        """
        # Create base dataframe
        self.variable_table_df = pd.DataFrame(columns=["Column","Alias","Independent","Dependent","Covariate","ymin","ymax","Poincare","Spectral","Transformation"])
        origin = []
        alias = []
        independent = []
        dependent = []
        covariate = []

        # populate lists with user selections from all buttons
        for item in self.pleth.buttonDict_variable:
            origin.append(item)
            alias.append(self.pleth.buttonDict_variable[item]["Alias"].text())
            independent.append(self.pleth.buttonDict_variable[item]["Independent"].isChecked())
            dependent.append(self.pleth.buttonDict_variable[item]["Dependent"].isChecked())
            covariate.append(self.pleth.buttonDict_variable[item]["Covariate"].isChecked())
            
        # Update dataframe with user selections
        self.variable_table_df["Column"] = origin
        self.variable_table_df["Alias"] = alias
        self.variable_table_df["Independent"] = independent
        self.variable_table_df["Dependent"] = dependent
        self.variable_table_df["Covariate"] = covariate
        self.variable_table_df[["Independent","Dependent","Covariate"]] = self.variable_table_df[["Independent","Dependent","Covariate"]].astype(int)
        self.variable_table_df[["Poincare","Spectral"]] = self.variable_table_df[["Poincare","Spectral"]].fillna(0)

    def add_combos(self):
        """
        Update the Xvar, Pointdodge, Facet1, and Facet2 comboBoxes whenever the user selects a new independent variable or covariate variable via RadioButton in Config.variable_table (TableWidget).
    
        Parameters
        --------
        self.variable_table_df: Dataframe
            This attribute is a dataframe that contains the states of the self.variable_table widgets for each variable as stored in self.pleth.buttonDict_variable (dict).
        self.settings_dict: dict
            This attribute is a nested dictionary that relates the graph settings comboBoxes to their corresponding headers in self.clades_graph.
        
        Outputs
        --------
        self.{role}_combo: QComboBox
            These ComboBoxes are populated with the aliases of user-selected independent and covariate variables as stored in self.variable_table_df after self.update_variable_table_df() is called and self.variable_table_df is refreshed.
        
        Outcomes
        --------
        self.update_variable_table_df()
            Populate several list attributes and dataframe attributes with text and widget statuses from self.pleth.buttonDict_variable (dict).
        """
        print("add_combos()")
        self.update_variable_table_df()
        for c in self.settings_dict['role'].keys():
            c.clear()
            c.addItem("Select variable:")
            c.addItems([x for x in self.variable_table_df.loc[(self.variable_table_df["Independent"] == 1) | (self.variable_table_df['Covariate'] == 1)]['Alias']])

    def graphy(self):
        """
        Populate self.clades_graph with a dataframe containing the settings selected in the Xvar, Pointdodge, Facet1, and Facet2 comboBoxes.
        
        Parameters
        --------
        self.role_list: list
            This attribute is a list of strings that are the headers of the self.loop_table.
        self.settings_dict: dict
            This attribute is a nested dictionary that relates the graph settings comboBoxes to their corresponding headers in self.clades_graph.
        
        Outputs
        --------
        self.clades_graph: Dataframe
            This attribute is a dataframe of two columns populated with the current text of the self.{role}_combo ComboBoxes.
        """
        print("config.graphy()")
        clades_role_dict = {}
        for col in self.role_list[2:6]:
            if self.settings_dict["rel"][col].currentText() == "Select variable:":
                clades_role_dict.update({self.settings_dict["role"][self.settings_dict["rel"][col]]:""})
            else:
                clades_role_dict.update({self.settings_dict["role"][self.settings_dict["rel"][col]]: self.settings_dict["rel"][col].currentText()})
        self.clades_graph = pd.DataFrame.from_dict(clades_role_dict,orient='index').reset_index()
        self.clades_graph.columns = ['Role','Alias']
    
    def othery(self):
        """
        Populate self.clades_other with a dataframe derived from the contents of self.clades_other_dict after the latter was updated with the current states of the widgets stored in self.pleth.loop_menu (dict).

        Parameters
        --------
        self.pleth.loop_menu: dict
            This Plethysmography class attribute is a nested dictionary used to populate and save the text, CheckBox, ComboBox, and CheckableComboBox states of Config.loop_table (TableWidget) in the Config subGUI.
        self.loop_table: QTableWidget
            This TableWidget is populated with the contents of self.pleth.loop_menu.
        self.feature_combo: QComboBox
            This ComboBox is the drop-down menu that allows the user to choose whether or not to include plots of respiratory features (i.e. apneas, sighs) with STAGG output.
        
        Outputs
        --------
        self.clades_other_dict: dict
            This attribute is set as an empty dictionary and populated with the contents of self.pleth.loop_menu which is populated with the current text of widgets in self.loop_table.
        self.clades_other: Dataframe
            This attribute is set as a dataframe populated from self.clades_other_dict and the self.feature_combo selection.
        """
        print("config.othery()")
        self.clades_other_dict = {}
        for row in range(self.loop_table.rowCount()):
            self.clades_other_dict.update({row:{}})
            self.clades_other_dict[row].update({"Graph": self.pleth.loop_menu[self.loop_table][row]["Graph"].text()})
            self.clades_other_dict[row].update({"Variable": self.pleth.loop_menu[self.loop_table][row]["Variable"].currentText()})
            self.clades_other_dict[row].update({"Xvar": self.pleth.loop_menu[self.loop_table][row]["Xvar"].currentText()})
            self.clades_other_dict[row].update({"Pointdodge": self.pleth.loop_menu[self.loop_table][row]["Pointdodge"].currentText()})
            self.clades_other_dict[row].update({"Facet1": self.pleth.loop_menu[self.loop_table][row]["Facet1"].currentText()})
            self.clades_other_dict[row].update({"Facet2": self.pleth.loop_menu[self.loop_table][row]["Facet2"].currentText()})
            self.clades_other_dict[row].update({"Covariates": '@'.join(self.pleth.loop_menu[self.loop_table][row]["Covariates"].currentData())})
            self.clades_other_dict[row].update({"Inclusion": self.pleth.loop_menu[self.loop_table][row]["Inclusion"].currentText()})
            if self.clades_other_dict[row]['Inclusion'] == 'Yes':
                self.clades_other_dict[row]['Inclusion'] = 1
            else:
                self.clades_other_dict[row]['Inclusion'] = 0  
            self.clades_other_dict[row].update({"Y axis minimum": self.pleth.loop_menu[self.loop_table][row]["Y axis minimum"].text()})
            self.clades_other_dict[row].update({"Y axis maximum": self.pleth.loop_menu[self.loop_table][row]["Y axis maximum"].text()})
            
        self.clades_other = pd.DataFrame.from_dict(self.clades_other_dict)
        self.clades_other = self.clades_other.transpose()

        if self.feature_combo.currentText() != "None":
            if self.feature_combo.currentText() == "All":
                self.clades_other.at[self.loop_table.rowCount(),"Graph"] = "Apneas"
                self.clades_other.at[self.loop_table.rowCount()+1,"Graph"] = "Sighs"
            else:
                self.clades_other.at[self.loop_table.rowCount()-1,"Graph"] = self.feature_combo.currentText()
        self.clades_other.drop(self.clades_other.loc[(self.clades_other["Graph"]=="") & (self.clades_other["Variable"]=="")].index, inplace=True)
     
    def classy_save(self):
        """
        Call self.update_variable_table_df() to update self.variable_table_df with the latest user selections from self.variable_table TableWidget
        Update the relevant cells in self.variable_table_df with any custom settings stored in self.custom_port
        Update the self.configs dictionary with the new dataframe for "variable_config", "graph_config", and "other_config"
        Call self.graphy() and self.othery() to populate self.clades_graph and self.clades_other.

        Parameters
        --------
        Custom: class
            The Custom class inherits widgets and layouts of Ui_Custom and defines the subGUI within the STAGG settings subGUI that allows users to customize the settings for each dependent variable.
        self.custom_port: dict
            This attribute is either empty or a deep copy of self.custom_dict, which stores the text and widgets that populate Custom.custom_table.
        self.variable_table_df: Dataframe
            This attribute is populated with a dataframe that contains the states of the self.variable_table widgets for each variable as stored in self.pleth.buttonDict_variable (dict).
        self.configs: dict
            This attribute is populated with a nested dictionary in which each item contains a dictionary unique to each settings file - variable_config.csv, graph_config.csv, and other_config.csv.
        
        Outputs
        --------
        self.variable_table_df: Dataframe
            This attribute's dataframe is updated to include the user-selected custom settings stored in self.custom_port.
        self.configs: dict
            The "df" key is updated with the updated dataframes for "variable_config", "graph_config", and "other_config".

        Outcomes
        --------
        self.update_variable_table_df()
            This method populates several list attributes and dataframe attributes with text and widget statuses from self.pleth.buttonDict_variable (dict).
        self.graphy()
            Populate self.clades_graph with a dataframe containing the settings selected in the Xvar, Pointdodge, Facet1, and Facet2 comboBoxes.
        self.othery()
            Populate self.clades_other with a dataframe derived from the contents of self.clades_other_dict after the latter was updated with the current states of the widgets stored in self.pleth.loop_menu (dict).
        """
        # Grabbing the user's selections from the widgets and storing them in dataframes:
        self.update_variable_table_df()
        if self.custom_port == {}:
            self.pleth.c = Custom(self)
            self.pleth.c.save_custom()

        for cladcol in self.variable_table_df:
            for item in self.custom_port:
                for col in self.custom_port[item]:
                    if self.custom_port[item][col] != None:
                        if col == "Transformation":
                            self.custom_port[item][col] = [x.replace("raw","non") for x in self.custom_port[item][col]]
                            self.custom_port[item][col] = [x.replace("ln","log") for x in self.custom_port[item][col]]
                            self.variable_table_df.loc[(self.variable_table_df["Alias"] == self.custom_port[item]["Alias"]) & (cladcol == col),cladcol] = "@".join(self.custom_port[item][col])
                        else:
                            self.variable_table_df.loc[(self.variable_table_df["Alias"] == self.custom_port[item]["Alias"]),col] = self.custom_port[item][col]
        
        self.configs["variable_config"].update({"df":self.variable_table_df})

        self.graphy()
        self.configs["graph_config"].update({"df":self.clades_graph})

        self.othery()
        self.configs["other_config"].update({"df":self.clades_other})
        
    def save_config(self, save_dir=None):
        """
        Save the dataframes
          - self.variable_table_df
          - self.clades_graph
          - self.clades_other
          as .csv files to the
           - default STAGG_config folder held in the user-selected
             output folder (self.pleth.workspace_dir)
           - timestamped .csv files to the timestamped
             STAGG output folder (self.pleth.output_dir_r)
             in the STAGG_output folder (self.pleth.r_output_folder)
             in the user-selected output folder (self.pleth.workspace_dir).
        """
        # TODO: save only when starting run?
        self.classy_save()
        if not save_dir:
            #self.pleth.dir_checker(self.pleth.output_dir_r,self.pleth.r_output_folder,"STAGG")
            #if self.pleth.output_folder != "":
            #    self.pleth.output_dir_r = self.pleth.output_folder
            save_dir = self.pleth.create_output_folder(toolname="STAGG")

        # TODO: can I get rid of this attribute?
        #self.pleth.output_dir_r = save_dir

        error_files = []
        for config_name, config in self.configs.items():
            path = config["path"]

            # Fill any blank paths
            if path == "":
                #path = os.path.join(self.pleth.output_dir_r,
                #                    f"{config_name}_{os.path.basename(self.pleth.output_dir_r).lstrip('STAGG_output')}.csv")
                notify_error(f"Path was blank, check save function to see why: config '{config_name}'")
                path = os.path.join(save_dir, f"{config_name}.csv")
            # Write df to csv at `path`
            config["df"].to_csv(path, index=False)

            # Try to save df to csv also at workspace dir
            try:
                # Make folder if it doesn't exist
                if not Path(os.path.join(self.pleth.workspace_dir,'STAGG_config')).exists():
                    Path(os.path.join(self.pleth.workspace_dir,'STAGG_config')).mkdir()

                config["df"].to_csv(os.path.join(self.pleth.workspace_dir, f'STAGG_config/{config_name}.csv'),index=False)
            except PermissionError as e:
                error_files.append(path)
    
        # Notify user of any errors
        if len(error_files) > 0:
            notify_error("File in use",f"One or more of the files selected is open in another program:\n{os.linesep.join([os.path.basename(thumb) for thumb in set(error_files)])}")

        # Update MainGUI with config paths
        for f in self.configs:
            for item in self.pleth.variable_list.findItems(f,Qt.MatchContains):
                self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
            self.pleth.variable_list.addItem(self.configs[f]['path'])
    
    def saveas_config(self):
        """
        Save the settings stored in
          - self.variable_table_df
          - self.clades_graph
          - and/or self.clades_other
          to .csv files at the
            - paths selected by the user
            - default paths in the STAGG_config folder in the user-selected output folder (self.pleth.workspace_dir)
        Populate the display widget self.pleth.variable_list (ListWidget) in the Main GUI with the timestamped file paths
        Update self.configs (dict) with the timestamped file paths
        Assign self.pleth.output_folder_r and self.pleth.input_dir_r according to the user-selected location of the STAGG settings files.
        """
        # TODO: this is done is save_config(). Still need to do before the other things here?
        #self.classy_save()

        # Ask user to pick a dir
        save_dir = QFileDialog.getExistingDirectory(self, 'Choose directory for STAGG configuration files', self.pleth.workspace_dir)

        # Catch cancel
        if not save_dir:
            return

        self.configs['variable_config']['path'] = os.path.join(save_dir, 'variable_config_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')
        self.configs['graph_config']['path'] = os.path.join(save_dir, 'graph_config_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')
        self.configs['other_config']['path'] = os.path.join(save_dir, 'other_config_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')

        self.save_config(save_dir)

    def add_loop(self):
        """
        - Update self.pleth.loop_menu with another key corresponding to the additional row
        - add another row to self.loop_table
        - and populate the row with the text and widgets stored in self.pleth.loop_menu.
        """
        loop_row = self.loop_table.rowCount()
        self.loop_table.insertRow(loop_row)

        self.pleth.loop_menu[self.loop_table].update({loop_row: {"Graph": QLineEdit()}})
        self.loop_table.setCellWidget(loop_row, 0, self.pleth.loop_menu[self.loop_table][loop_row]["Graph"])

        self.pleth.loop_menu[self.loop_table][loop_row].update({"Y axis minimum": QLineEdit()})
        self.loop_table.setCellWidget(loop_row, 7, self.pleth.loop_menu[self.loop_table][loop_row]["Y axis minimum"])

        self.pleth.loop_menu[self.loop_table][loop_row].update({"Y axis maximum": QLineEdit()})
        self.loop_table.setCellWidget(loop_row, 8, self.pleth.loop_menu[self.loop_table][loop_row]["Y axis maximum"])

        self.pleth.loop_menu[self.loop_table][loop_row].update({"Inclusion": QComboBox()})
        self.pleth.loop_menu[self.loop_table][loop_row]["Inclusion"].addItems(["No", "Yes"])
        self.loop_table.setCellWidget(loop_row, 9, self.pleth.loop_menu[self.loop_table][loop_row]["Inclusion"])

        self.pleth.loop_menu[self.loop_table][loop_row].update({"Covariates": CheckableComboBox()})
        self.pleth.loop_menu[self.loop_table][loop_row]["Covariates"].addItems([b for b in self.pleth.breath_df])
        self.loop_table.setCellWidget(loop_row, 6, self.pleth.loop_menu[self.loop_table][loop_row]["Covariates"])

        for role in self.role_list[1:6]:
            self.pleth.loop_menu[self.loop_table][loop_row][role] = QComboBox()
            self.pleth.loop_menu[self.loop_table][loop_row][role].addItems([""])
            self.pleth.loop_menu[self.loop_table][loop_row][role].addItems([x for x in self.pleth.breath_df])
        
        self.loop_table.setCellWidget(loop_row,1,self.pleth.loop_menu[self.loop_table][loop_row]["Variable"])
        self.loop_table.setCellWidget(loop_row,2,self.pleth.loop_menu[self.loop_table][loop_row]["Xvar"])
        self.loop_table.setCellWidget(loop_row,3,self.pleth.loop_menu[self.loop_table][loop_row]["Pointdodge"])
        self.loop_table.setCellWidget(loop_row,4,self.pleth.loop_menu[self.loop_table][loop_row]["Facet1"])
        self.loop_table.setCellWidget(loop_row,5,self.pleth.loop_menu[self.loop_table][loop_row]["Facet2"])

    def reset_config(self):
        """
        - Reset attributes
        - clear Xvar, Pointdode, Facet1, and Facet2 comboBoxes
        - set Poincare, Spectral, feature, and Transformation
           comboBoxes to None
        - repopulate self.loop_table and self.variable_table with
           the updated (rebuilt) dictionaries self.pleth.loop_menu
           and self.pleth.buttonDict_variable respectively.
        """
        #self.setup_variables_config()
        #self.setup_table_config()
        #self.show_loops(self.loop_table,1)

        for s in self.settings_dict['role']:
            s.clear()
            s.addItem("Select variable:")

        for p in self.additional_dict:
            p.setCurrentText("None")

        self.deps = []
        self.update_variable_table_df()
        self.deps = self.variable_table_df.loc[(self.variable_table_df["Dependent"] == 1)]["Alias"]

    def check_load_variable_config(self, __checked, open_file=True):
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
        paths = []

        # let user select a path
        if open_file:
            # Opens open file dialog
            paths, filter = QFileDialog.getOpenFileNames(self, 'Select files', str(os.path.join(Path(__file__).parent.parent.parent,"PAPR Output/STAGG_config")))

        # pull paths from configs dict
        else:
            paths = [self.configs[p]["path"] for p in self.configs]

        # Return if no paths
        if not paths:
            return

        baddies = []
        goodies = []

        # Take each path
        for path in paths:
            # Each key in the configs
            for config_name in self.configs:
                # Skip anything not in path
                if config_name not in path:
                    continue

                # path is a real file, right file format, and starts with config_name
                if Path(path).is_file() and \
                    path.endswith('.csv') or path.endswith('.xlsx') and \
                    os.path.basename(path).startswith(config_name):

                    if path in goodies:
                        goodies.remove(path)
                    if path in baddies:
                        baddies.remove(path)
                    if config_name in goodies:
                        goodies.remove(config_name)
                    if config_name in baddies:
                        baddies.remove(config_name)

                    self.configs[config_name]["path"] = path

                    for item in self.pleth.variable_list.findItems(config_name, Qt.MatchContains):
                        self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                    self.pleth.variable_list.addItem(self.configs[config_name]["path"])
                    goodies.append(config_name)

                else:
                    # Catch any errors
                    if path not in baddies:
                        baddies.append(path)

                    if not Path(path).is_file():
                        print(f'baddies got {path} cause it is not a real file')
                        notify_error(title="Files not found", msg=f"One or more of the files selected cannot be found:\n{os.linesep.join([b for b in baddies])}")
                    elif not (path.endswith('.csv') or path.endswith('.xlsx')):
                        notify_error(title="Incorrect file format", msg=f"One or more of the files selected is not in the correct file format:\n{os.linesep.join([b for b in baddies])}\nOnly .csv or .xlsx are accepted.")
                    elif not os.path.basename(path).startswith(config_name):
                        notify_error("Wrong file name", msg=f"""One or more of the files selected is cannot be recognized:\n{os.linesep.join([b for b in baddies])}\nPlease rename the file(s) as described in the <a href="https://github.com/">documentation</a> or select a different file.""")

        if "variable_config" in goodies:
            try:
                self.load_variable_config()
                for item in self.pleth.variable_list.findItems("variable_config",Qt.MatchContains):
                    self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                self.pleth.variable_list.addItem(self.configs["variable_config"]['path'])
            except KeyError as e:
                goodies.remove("variable_config")
                baddies.append("variable_config")

        if "graph_config" in goodies:
            try:
                self.load_graph_config()
                for item in self.pleth.variable_list.findItems("graph_config",Qt.MatchContains):
                    self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                self.pleth.variable_list.addItem(self.configs["graph_config"]['path'])
            except KeyError as e:
                goodies.remove("graph_config")
                baddies.append("graph_config")

        if "other_config" in goodies:
            try:
                self.load_other_config()
                for item in self.pleth.variable_list.findItems("other_config",Qt.MatchContains):
                    self.pleth.variable_list.takeItem(self.pleth.variable_list.row(item))
                self.pleth.variable_list.addItem(self.configs["other_config"]['path'])
            except KeyError as e:
                goodies.remove("other_config")
                baddies.append("other_config")

        if len(baddies) > 0:
            self.thumb = Thumbass(self.pleth)
            self.thumb.show()
            documentation = '<a href="https://github.com/">documentation</a>'
            self.thumb.message_received("Error reading file",f"""One or more of the files selected is not formatted correctly:<br><br>{os.linesep.join([self.configs[b]['path'] for b in baddies])}<br><br>Please refer to the <a href="https://github.com/">documentation</a> for structuring your data.""") 

    def load_variable_config(self):
        """
        Load the variable_config file as a dataframe
        Populate self.pleth.breath_df with the list values in the "Column" column of the dataframe
        Populate self.variable_table (TableWidget) with a row for each variable in the variable_config dataframe
        Load the custom settings.
        """
        var_config_path = self.configs["variable_config"]["path"]

        # Convert Excel file to csv
        if var_config_path.endswith(".xlsx"):
            df = pd.read_excel(var_config_path)

            # TODO: Can we do without this or do we need the csv version?
            #xl.to_csv(csv_filename)

        # CSV
        elif var_config_path.endswith(".csv"):
            df = pd.read_csv(var_config_path)

        else:
            notify_error(f"Bad variable config file: {var_config_path}")
            return

        # Convert dataframe...
        self.pleth.breath_df = df['Column'].tolist()

        self.setup_table_config()
        self.variable_dataframe = {}

        with open(var_config_path,'r') as f:
            r = csv.DictReader(f)
            for row in r:
                for k in dict(row):
                    if dict(row)[k] == "1":
                        self.variable_dataframe.update({dict(row)['Column']:dict(row)})

        for a in self.variable_dataframe:
            self.pleth.buttonDict_variable[a]['Alias'].setText(self.variable_dataframe[a]['Alias'])
            for k in ["Independent","Dependent","Covariate"]:
                if self.variable_dataframe[a][k] == '1':
                    self.pleth.buttonDict_variable[a][k].setChecked(True)

        self.load_custom_config()

    def load_custom_config(self):
        """
        Populate Custom.custom_table based on the dependent variables
          selected by the user according to the dataframe derived from
          the variable config .csv file the user selected. 
        """
        for p in self.additional_dict:
            p.setCurrentText("None")

        self.deps = [self.variable_dataframe[a]['Alias'] for a in self.variable_dataframe if self.variable_dataframe[a]['Dependent'] == '1']
        self.custom_dict = {}

        # Create custom 
        self.pleth.c = Custom(self)
        self.pleth.c.populate_table(self.deps,self.pleth.c.custom_table)

        for k in self.variable_dataframe:
            if self.variable_dataframe[k]['Poincare'] == "1":
                self.custom_dict[k]['Poincare'].setChecked(True)

            if self.variable_dataframe[k]['Spectral'] == "1":
                self.custom_dict[k]['Spectral'].setChecked(True)

            for y in ['ymin','ymax']:
                if self.variable_dataframe[k][y] != "":
                    self.custom_dict[k][y].setText(self.variable_dataframe[k][y])

            if self.variable_dataframe[k]['Transformation'] != "":
                transform = [s.replace("non","raw") and s.replace("log","ln") for s in self.variable_dataframe[k]['Transformation'].split('@')]
                transform = [z.replace("ln10","log10") for z in transform]
                self.custom_dict[k]['Transformation'].loadCustom(transform)
                self.custom_dict[k]['Transformation'].updateText()

        self.pleth.c.save_custom()
        
    def load_graph_config(self):
        """
        Populate the Xvar, Pointdodge, Facet1, and Facet2 comboBoxes
          with the variables selected as independent or covariate
          according to the variable_config .csv file

        If there is no variable_config file, then populate those comboBoxes
          with the variables in the dataframe read from the graph_config
          file and set the comboBoxes current text.
        """
        gdf = pd.read_csv(self.configs["graph_config"]["path"], index_col=False)

        # TODO: why are we checking goodies?
        # If variable config is good
        goodies = ['variable_config']
        if "variable_config" in goodies:
            variable_df = self.variable_dataframe
            # TODO: "valid_values?" -- better name?? what are these?
            valid_values = [[variable_df[k]["Alias"] for k in variable_df if variable_df[k][v] == "1"] for v in ["Independent","Covariate"]][0]
        else:
            valid_values = [x for x in gdf['Alias'] if pd.notna(x)]

        for c in self.settings_dict['role']:
            c.clear()
            c.addItem("Select variable:")
            c.addItems(valid_values)
            #c.setCurrentText([x for x in gdf.loc[(gdf['Role'] == self.settings_dict['role'][c])]['Alias'] if pd.notna(x)][0])
            
    def load_other_config(self):
        """
        Set the current text of the feature plots comboBox according to the other_config .csv file loaded
        Populate self.loop_table with the contents of the dataframe derived from the other_config .csv file.
        """
        # Load other config from csv
        odf = pd.read_csv(self.configs["other_config"]['path'], index_col=False)

        # Reset feature comboBox
        self.feature_combo.setCurrentText("None")

        if "Apneas" in set(odf["Graph"]):
            self.feature_combo.setCurrentText("Apneas")

        if "Sighs" in set(odf["Graph"]):
            self.feature_combo.setCurrentText("Sighs") 

        if ("Apneas" and "Sighs") in set(odf["Graph"]):
            self.feature_combo.setCurrentText("All")

        odf.drop(odf.loc[(odf["Graph"]=="Apneas") | (odf["Graph"]=="Sighs")].index, inplace = True)
        self.show_loops(self.loop_table, len(odf))

        # Skip processing if df is empty
        if len(odf)==0:
            return

        # Update each row of loop_table
        for row_1 in range(len(odf)):
            self.loop_table.cellWidget(row_1,0).setText(str(odf.at[row_1,'Graph']))
            self.loop_table.cellWidget(row_1,7).setText(str(odf.at[row_1,'Y axis minimum']))
            self.loop_table.cellWidget(row_1,8).setText(str(odf.at[row_1,'Y axis maximum']))
            self.loop_table.cellWidget(row_1,1).setCurrentText(str(odf.at[row_1,'Variable']))
            self.loop_table.cellWidget(row_1,2).setCurrentText(str(odf.at[row_1,'Xvar']))
            self.loop_table.cellWidget(row_1,3).setCurrentText(str(odf.at[row_1,'Pointdodge']))
            self.loop_table.cellWidget(row_1,4).setCurrentText(str(odf.at[row_1,'Facet1']))
            self.loop_table.cellWidget(row_1,5).setCurrentText(str(odf.at[row_1,'Facet2']))

            if odf.at[row_1,'Inclusion'] == 1:
                self.loop_table.cellWidget(row_1, 9).setCurrentText("Yes")
            else:
                self.loop_table.cellWidget(row_1, 9).setCurrentText("No")

            if odf.at[row_1, 'Covariates'] != "":
                if self.deps != []:
                    self.pleth.loop_menu[self.loop_table][row_1]['Covariates'].loadCustom([w for w in odf.at[row_1, 'Covariates'].split('@')])
                    self.pleth.loop_menu[self.loop_table][row_1]['Covariates'].updateText()
                    
            # If row is not last row
            if row_1 < (len(odf)-1):
                self.add_loop()

    def checkable_ind(self,state):
        """
        Change the RadioButton status for every column in the selected rows so that only the "Independent" RadioButton is set as checked.
        """
        try:
            print("true")
            for selected_rows in self.variable_table.selectedRanges():
                for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
                    self.variable_table.cellWidget(row,2).setChecked(True)
        except:
            print("nope")
        # 
    def checkable_dep(self):
        """
        Change the RadioButton status for every column in the selected rows so that only the "Dependent" RadioButton is set as checked.
        """
        try:
            for selected_rows in self.variable_table.selectedRanges():
                for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
                    self.variable_table.cellWidget(row,3).setChecked(True)
        except:
            print("nope")
        
    def checkable_cov(self):
        """
        Change the RadioButton status for every column in the selected rows so that only the "Covariate" RadioButton is set as checked.
        """
        try:
            for selected_rows in self.variable_table.selectedRanges():
                for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
                    self.variable_table.cellWidget(row,4).setChecked(True)
        except:
            print("nope")

    def checkable_ign(self):
        """
        Change the RadioButton status for every column in the selected rows so that only the "Ignore" RadioButton is set as checked.
        """
        try:
            for selected_rows in self.variable_table.selectedRanges():
                for row in range(selected_rows.topRow(),selected_rows.bottomRow()+1):
                    self.variable_table.cellWidget(row,5).setChecked(True)
        except:
            print("nope")