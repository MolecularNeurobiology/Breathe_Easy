
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QCheckBox
from PyQt5.QtCore import Qt
from checkable_combo_box import CheckableComboBox
from util.ui.tools import read_widget
from ui.custom_config import Ui_Custom

class Custom(QDialog, Ui_Custom):
    """
    The Custom class inherits widgets and layouts of Ui_Custom and defines the subGUI within the STAGG settings subGUI that allows users to customize the settings for each dependent variable.

    Parameters
    --------
    QWidget: class
        The Custom class inherits properties and methods from the QWidget class. 
    Ui_Custom: class
        The Custom class inherits widgets and layouts defined in the Ui_Custom class.
    """
    def __init__(self, custom_data, dependent_vars):
        """
        Instantiate the Custom class.

        Parameters
        --------
        Config: class
            The Custom class inherits properties, attributes, and methods from the Config class.
        
        Outputs
        --------
        self: class
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
        self.isMaximized()
        self.dependent_vars = dependent_vars
        self.custom_alias = []
        self.ymin = []
        self.ymax = []
        self.custom_transform = []
        self.custom_poincare = []
        self.custom_spectral = []
        self.custom_irreg = []

        self.populate_table(custom_data)
        self.adjustSize()

    def extract_variable(self):
        """
        Check if Config.dependent_vars (list) is empty. If it is, prompt a MessageBox informing the user. If it isn't, populate self.custom_table (TableWidget) using Config.dependent_vars.

        Parameters
        --------
        self.dependent_vars: list
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
        self.populate_table(self.dependent_vars, self.custom_table)
            This method populates self.custom_table TableWidget with rows corresponding to the items in the self.dependent_vars list.
        self.show()
            This method displays the STAGG settings subGUI.
        """
        raise NotImplemented

    def populate_table(self, custom_data):
        """
        Populate an empty self.custom_dict as a nested dictionary
          based on the items in self.dependent_vars (list) OR
          Update an existing self.custom_dict by appending keys and establishing widgets
        Update self.custom_port if it's populated
        Populate self.custom_table with the contents of self.custom_dict, with the number of rows corresponding to the number of items in self.dependent_vars.

        Parameters
        --------
        dependent_vars: list
            This argument passes self.dependent_vars, a list of user-selected dependent variables.
        table: QTableWidget
            This argument passes self.custom_table TableWidget.
        self.custom_dict: dict
            This attribute inherited from the Config class is either empty or a nested dictionary defining widgets.
        self.custom_port: dict
            This attribute inherited from the Config class is either empty or a deep copy of self.custom_dict.
        
        Outputs
        --------
        self.custom_dict: dict
            This attribute inherited from the Config class is either populated or updated to include newly-selected dependent variables.
        self.custom_table: QTableWidget
            This TableWidget is populated with the text and widgets stored in self.custom_dict.
        """
        # Populate tablewidgets with dictionary holding widgets. 
        table = self.custom_table
        table.setRowCount(len(self.dependent_vars))

        default_vals = {
            'ymin': "",
            'ymax': "",
            'Poincare': 0,
            'Spectral': 0,
            'Transformation': ""
        }

        for row, var_name in enumerate(self.dependent_vars):
            vals = custom_data[custom_data.Alias == var_name]
            if len(vals):
                vals = vals.to_dict('records')[0]
            else:
                vals = default_vals


            # The first three columns are the name of the dependent variables selected and empty strings for ymin and ymax:
            # alias
            alias_item = QTableWidgetItem(var_name)
            alias_item.setFlags(alias_item.flags() ^ Qt.ItemIsEditable)
            table.setItem(row, 0, alias_item)

            # ymin
            table.setItem(row, 1, QTableWidgetItem(str(vals['ymin'])))

            # ymax
            table.setItem(row, 2, QTableWidgetItem(str(vals['ymax'])))

            # Creating the radio buttons that will populate the cells in each row:
            # Poincare
            poincare_checkbox = QCheckBox()
            poincare_checkbox.setChecked(vals['Poincare'] == 1)
            table.setCellWidget(row, 4, poincare_checkbox)

            # Spectral 
            spectral_checkbox = QCheckBox()
            spectral_checkbox.setChecked(vals['Spectral'] == 1)
            table.setCellWidget(row, 5, spectral_checkbox)

            # Creating the combo boxes that will populate the cells in each row:
            transformation_combo = CheckableComboBox()
            transformation_combo.addItems(["raw","log10","ln","sqrt"])
            transformation_combo.loadCustom(vals['Transformation'])
            transformation_combo.updateText()
            table.setCellWidget(row, 3, transformation_combo)

        table.resizeColumnsToContents()
        table.resizeRowsToContents()

    def confirm(self):
        """
        Save the contents of Config.custom_dict to Config.custom_port. Update the status of the comboBoxes corresponding to Poincare, Spectral, and Transformation settings made in the Custom subGUI.

        Parameters
        --------
        self.custom_dict: dict
            This attribute inherited from the Config class is either empty or a nested dictionary defining rows and corresponding widgets that will populate self.custom_table TableWidget.
        self.Poincare_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to produce Poincare plots for all or none of the selected dependent variables.
        self.Spectral_combo: QComboBox
            The comboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to produce Spectral plots for all or none of the selected dependent variables.
        self.transform_combo: CheckableComboBox
            This CheckableComboBox provides a drop-down menu in the STAGG settings subGUI that allows the user to choose to run STAGG on different model transformations.
        
        Outputs
        --------
        self.custom_port: dict
            This nested dictionary is a deep copy of self.custom_port.
        self.Poincare_combo: QComboBox
            The comboBox in the STAGG settings subGUI that allows the user to choose to produce Poincare plots for all or none of the selected dependent variables is set to "Custom" to indicate customized settings regarding Poincare plots.
        self.Spectral_combo: QComboBox
            The comboBox in the STAGG settings subGUI that allows the user to choose to produce Spectral plots for all or none of the selected dependent variables is set to "Custom" to indicate customized settings regarding Poincare plots.
        """
        custom_data = {}
        # Loop through each row in the table
        for row_idx in range(self.custom_table.rowCount()):
            row_data = {}

            # Pull data from each widget in this row
            for col_idx in range(self.custom_table.columnCount()):
                col_name = self.custom_table.horizontalHeaderItem(col_idx).text()
                widget = self.custom_table.item(row_idx, col_idx)

                # Any widgets that we put in the cell will be stored as cellWidget
                if widget is None:
                    widget = self.custom_table.cellWidget(row_idx, col_idx)

                row_data[col_name] = read_widget(widget)

            var_alias = row_data['Variable']
            custom_data[var_alias] = row_data

        # Set to self.data for access to outside caller
        self.data = custom_data
        self.accept()
            