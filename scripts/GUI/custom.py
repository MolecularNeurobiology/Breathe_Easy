
from PyQt5.QtWidgets import QWidget, QTableWidget, QMessageBox, QTableWidgetItem, QCheckBox
from PyQt5.QtCore import Qt
from checkable_combo_box import CheckableComboBox
from ui.custom_config import Ui_Custom

class Custom(QWidget, Ui_Custom):
    """
    The Custom class inherits widgets and layouts of Ui_Custom and defines the subGUI within the STAGG settings subGUI that allows users to customize the settings for each dependent variable.

    Parameters
    --------
    QWidget: class
        The Custom class inherits properties and methods from the QWidget class. 
    Ui_Custom: class
        The Custom class inherits widgets and layouts defined in the Ui_Custom class.
    """
    def __init__(self,Config):
        """
        Instantiate the Custom class.

        Parameters
        --------
        Config: class
            The Custom class inherits properties, attributes, and methods from the Config class.
        
        Outputs
        --------
        self.config: class
            Shorthand for the Config class.
        self.custom_alias: list
            This attribute is set as an empty list.
        self.ymin: list
            This attribute is set as an empty list.
        self.ymax: list
            This attribute is set as an empty list.
        self.custom_transform: list
            This attribute is set as an empty list.
        self.custom_poincare: list
            This attribute is set as an empty list.
        self.custom_spectral: list
            This attribute is set as an empty list.
        self.custom_irreg: list
            This attribute is set as an empty list.
        """
        super(Custom, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("Custom graph settings configuration")
        self.config = Config
        self.isMaximized()
        self.custom_alias = []
        self.ymin = []
        self.ymax = []
        self.custom_transform = []
        self.custom_poincare = []
        self.custom_spectral = []
        self.custom_irreg = []

    def extract_variable(self):
        """
        Check if Config.deps (list) is empty. If it is, prompt a MessageBox informing the user. If it isn't, populate self.custom_table (TableWidget) using Config.deps.

        Parameters
        --------
        self.config.deps: list
            This list contains the Aliases of the dependent variables the user has selected in Config.variable_table (TableWidget).
        self.custom_table: QTableWidget
            This TableWidget displays the text and widgets that allows the user to customize the STAGG settings for each dependent variable on the main model.

        Outputs
        --------
        reply: QMessageBox
            This specialized dialog communicates information to the user.
        self.custom_table: QTableWidget
            This TableWidget is populated based on the number of dependent variables selected by the user in Config.variable_table.
        
        Outcomes
        --------
        self.populate_table(self.config.deps, self.custom_table)
            This method populates self.custom_table TableWidget with rows corresponding to the items in the self.config.deps list.
        self.show()
            This method displays the STAGG settings subGUI.
        """
        print("custom.extract_variable()")
        if self.config.deps.empty:
            reply = QMessageBox.information(self, 'Choose variables', 'Please select response variables to be modeled.', QMessageBox.Ok)
        else:
            self.populate_table(self.config.deps,self.custom_table)
            self.adjustSize()
            self.show()

    def populate_table(self,frame: list,table: QTableWidget):
        """
        Populate an empty self.config.custom_dict as a nested dictionary based on the items in self.config.deps (list) or update an existing self.config.custom_dict by appending keys and establishing widgets, update self.config.custom_port if it's populated, and populate self.custom_table with the contents of self.config.custom_dict, with the number of rows corresponding to the number of items in self.config.deps.

        Parameters
        --------
        frame: list
            This argument passes self.config.deps, a list of user-selected dependent variables.
        table: QTableWidget
            This argument passes self.custom_table TableWidget.
        self.config.custom_dict: dict
            This attribute inherited from the Config class is either empty or a nested dictionary defining widgets.
        self.config.custom_port: dict
            This attribute inherited from the Config class is either empty or a deep copy of self.config.custom_dict.
        
        Outputs
        --------
        self.config.custom_dict: dict
            This attribute inherited from the Config class is either populated or updated to include newly-selected dependent variables.
        self.custom_table: QTableWidget
            This TableWidget is populated with the text and widgets stored in self.config.custom_dict.
        """
        print("custom started populating table")
        # Populate tablewidgets with dictionary holding widgets. 
        table.setRowCount(len(frame))
        row = 0
        if self.config.custom_dict == {}:
            for item in frame:
                self.config.custom_dict[item] = {}
                # The first two columns are the name of the dependent variables selected and empty strings for ymin and ymax:
                self.config.custom_dict[item]["Alias"]=QTableWidgetItem(item)
                self.config.custom_dict[item]["ymin"]=QTableWidgetItem("")
                self.config.custom_dict[item]["ymax"]=QTableWidgetItem("")
                # Creating the radio buttons that will populate the cells in each row:
                self.config.custom_dict[item]["Poincare"]=QCheckBox()
                self.config.custom_dict[item]["Spectral"]=QCheckBox()
                # Creating the combo boxes that will populate the cells in each row:
                self.config.custom_dict[item]["Transformation"]=CheckableComboBox()
                self.config.custom_dict[item]["Transformation"].addItems(["raw","log10","ln","sqrt"])
        else:
            diff = list(set(self.deps) - set(self.old_deps))
            for item_1 in diff:
                self.config.custom_dict[item_1] = {}
                # The first two columns are the name of the dependent variables selected and empty strings for ymin and ymax:
                self.config.custom_dict[item_1]["Alias"]=QTableWidgetItem(item_1)
                self.config.custom_dict[item_1]["ymin"]=QTableWidgetItem("")
                self.config.custom_dict[item_1]["ymax"]=QTableWidgetItem("")
                # Creating the radio buttons that will populate the cells in each row:
                self.config.custom_dict[item_1]["Poincare"]=QCheckBox()
                self.config.custom_dict[item_1]["Spectral"]=QCheckBox()
                # Creating the combo boxes that will populate the cells in each row:
                self.config.custom_dict[item_1]["Transformation"]=CheckableComboBox()
                self.config.custom_dict[item_1]["Transformation"].addItems(["raw","log10","ln","sqrt"])
        for entry in self.config.custom_dict:    
            print("setting widgets in table")
            table.setItem(row,0,self.config.custom_dict[entry]["Alias"])
            table.item(row,0).setFlags(table.item(row,0).flags() ^ Qt.ItemIsEditable)
            table.setItem(row,1,self.config.custom_dict[entry]["ymin"])
            table.setItem(row,2,self.config.custom_dict[entry]["ymax"])
            
            table.setCellWidget(row,3,self.config.custom_dict[entry]["Transformation"])
            table.setCellWidget(row,4,self.config.custom_dict[entry]["Poincare"])
            table.setCellWidget(row,5,self.config.custom_dict[entry]["Spectral"])
            if entry in self.config.custom_port:
                if self.config.custom_port[entry]["Poincare"] == 1:
                    self.config.custom_dict[entry]["Poincare"].setChecked(True)
                if self.config.custom_port[entry]["Spectral"] == 1:
                    self.config.custom_dict[entry]["Spectral"].setChecked(True)
                for y in ['ymin','ymax']:
                    if self.config.custom_port[entry][y] != "":
                        self.config.custom_dict[entry][y].setText(self.config.custom_port[entry][y])
                if self.config.custom_port[entry]["Transformation"] != []:
                    self.config.custom_dict[entry]["Transformation"].loadCustom(self.config.custom_port[entry]["Transformation"])
                    self.config.custom_dict[entry]["Transformation"].updateText()
            else:
                if list(self.config.clades.loc[(self.config.clades["Alias"] == entry)]["Column"])[0] in self.config.custom_port:
                    self.config.custom_port[entry] = self.config.custom_port.pop(list(self.config.clades.loc[(self.config.clades["Alias"] == entry)]["Column"])[0])
                    if self.config.custom_port[entry]["Poincare"] == 1:
                        self.config.custom_dict[entry]["Poincare"].setChecked(True)
                    if self.config.custom_port[entry]["Spectral"] == 1:
                        self.config.custom_dict[entry]["Spectral"].setChecked(True)
                    for y in ['ymin','ymax']:
                        if self.config.custom_port[entry][y] != "":
                            self.config.custom_dict[entry][y].setText(self.config.custom_port[entry][y])
                    if self.config.custom_port[entry]["Transformation"] != []:
                        self.config.custom_dict[entry]["Transformation"].loadCustom(self.config.custom_port[entry]["Transformation"])
                        self.config.custom_dict[entry]["Transformation"].updateText()
            row += 1
        table.resizeColumnsToContents()
        table.resizeRowsToContents()

    def save_custom(self):
        """
        Save the contents of Config.custom_dict to Config.custom_port. Update the status of the comboBoxes corresponding to Poincare, Spectral, and Transformation settings made in the Custom subGUI.

        Parameters
        --------
        self.config.custom_dict: dict
            This attribute inherited from the Config class is either empty or a nested dictionary defining rows and corresponding widgets that will populate self.custom_table TableWidget.
        self.config.Poincare_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to produce Poincare plots for all or none of the selected dependent variables.
        self.config.Spectral_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to produce Spectral plots for all or none of the selected dependent variables.
        self.config.transform_combo: CheckableComboBox
            This CheckableComboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to run STAGG on different model transformations.
        
        Outputs
        --------
        self.config.custom_port: dict
            This nested dictionary is a deep copy of self.config.custom_port.
        self.config.Poincare_combo: QComboBox
            The comboBox in the STAGG settings subGUI that allows the user to choose to produce Poincare plots for all or none of the selected dependent variables is set to "Custom" to indicate customized settings regarding Poincare plots.
        self.config.Spectral_combo: QComboBox
            The comboBox in the STAGG settings subGUI that allows the user to choose to produce Spectral plots for all or none of the selected dependent variables is set to "Custom" to indicate customized settings regarding Poincare plots.
        
        self.
        """
        print("custom.save_custom()")
        self.config.custom_port = {item: {col: None for col in self.config.custom_dict[item]} for item in self.config.custom_dict}
        try:
            for item in self.config.custom_dict:
                for col in self.config.custom_dict[item]:
                    if "QTableWidgetItem" in str(type(self.config.custom_dict[item][col])):
                        self.config.custom_port[item].update({col:self.config.custom_dict[item][col].text()})
                    elif "QCheckBox" in str(type(self.config.custom_dict[item][col])):
                        self.config.custom_port[item].update({col:int(self.config.custom_dict[item][col].isChecked())})
                    elif "QComboBox" in str(type(self.config.custom_dict[item][col])):
                        self.config.custom_port[item].update({col:self.config.custom_dict[item][col].currentText()})
                    elif "CheckableComboBox" in str(type(self.config.custom_dict[item][col])):
                        self.config.custom_port[item].update({col:self.config.custom_dict[item][col].currentData()})
            for key,value in {self.config.Poincare_combo:"Poincare",self.config.Spectral_combo:"Spectral"}.items():
                if all([self.config.custom_port[var][value] == 1 for var in self.config.custom_port]):
                    key.setCurrentText("All")
                if any([self.config.custom_port[var][value] == 1 for var in self.config.custom_port]):
                    key.setCurrentText("Custom")
                else:
                    key.setCurrentText("None")
                
            if any(th for th in [self.config.custom_port[t]["Transformation"] for t in self.config.custom_port])==True:
                self.config.transform_combo.setCurrentText("Custom")
            else:
                self.config.transform_combo.setCurrentText("None")
        except Exception as e:
            pass
        try:
            self.hide()
        except Exception as e:
            pass
        print(f"save_custom: {self.config.custom_port}")
            