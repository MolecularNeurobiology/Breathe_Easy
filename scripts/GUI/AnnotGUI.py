#%%
#region Libraries

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5 import uic
import sys
import csv
from pathlib import Path, PurePath
import subprocess
from subprocess import PIPE, Popen
import datetime
import time
import os
import json
import pyodbc
import datetime
import tkinter
import tkinter.filedialog
import tkinter as tk 
from tkinter import ttk
import shutil
import threading
import re
import importlib
from form import Ui_Plethysmography
from thumbass import Ui_Thumbass
from annot_form import Ui_Annot
# from MainGUI import *
import pandas as pd
import numpy as np

#endregion
#region Thumbass
class Thumbass(QWidget, Ui_Thumbass):
    """
    Standard dialog to help protect people from themselves.
    """
    def __init__(self):
        super(Thumbass, self).__init__()
        # self.label = QLabel("Another Window % d" % randint(0,100))
        self.setupUi(self)
        self.setWindowTitle("Nailed it.")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.label.setOpenExternalLinks(True)
        # self.pleth = Plethysmography
        # self.message_received()
    
    def message_received(self,title,words):
        self.setWindowTitle(title)
        self.label.setText(words)
#endregion

# #region Thorbass
# class Thorbass(QWidget, Ui_Thorbass):
#     """
#     Standard dialog to help protect people from themselves.
#     """
#     def __init__(self):
#         super(Thorbass, self).__init__()
#         self.annot = Annot
#         # self.label = QLabel("Another Window % d" % randint(0,100))
#         self.setupUi(self)
#         self.setWindowTitle("Nailed it.")
#         # self.pleth = Plethysmography
#         # self.message_received()
    
#     def message_received(self,words):
#         self.browser.setPlainText(words)
#         # self.browser.setPlainText(words)
#endregion

class Annot(QMainWindow, Ui_Annot):
    def __init__(self,Plethysmography):
        super(Annot, self).__init__()

#region class attributes

        self.GUIpath=os.path.realpath(__file__)
        self.setupUi(self)
        self.pleth = Plethysmography
        self.setWindowTitle("BASSPRO Variable Annotation")
        # Window opens and is brought to the front as the active window.
        # Window opens in maximized resolution.
        # self.showMaximized()
        self.isActiveWindow()
        self.ETTC=""

        # self.metadata = pd.read_csv('C:/Users/atwit/Documents/BCM/ETL/Alz_metadata.csv', sep=",",encoding='cp1252',header=0)
        self.metadata = None
        # self.megameta = self.metadata.copy()
        self.column=""
        self.new_column=""
        self.selected_values=[]
        self.groups=[]
        self.kids={}
        self.changes=[]

#endregion

#region actions
    def binning_value(self):
        print("annot.binning_value()")
        self.group_list.clear()
        self.variable_tree.clear()
        self.groups = []
        value_list = self.metadata[self.variable_list_columns.selectedItems()[0].text()]
        if value_list.dtypes == object:
            print("Selected variable has non-numeric values.")
            self.group_list.addItem("Selected variable has non-numeric values.")
        elif pd.isna(value_list).any() == True:
            print("Selected variable has missing values.")
            # self.thorb = Thorbass()
            # self.thorb.show()
            # self.thorb.message_received("The selected variable has missing values. Would you like to continue? Missing values will be relegated to their own bin.")
            # self.thorb.ok_button.clicked.connect(self.annot.binning_continued())
            reply = QMessageBox.question(self, 'Missing values', 'The selected variable has missing values.\n\nWould you like to continue?\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.binning_value_continued()
        else:
            self.binning_value_continued()

    def binning_value_continued(self):
        print("annot.binning_value_continued()")
        value_list = self.metadata[self.variable_list_columns.selectedItems()[0].text()]
        value_list = value_list.sort_values()
        self.bin_number = int(self.bin_edit.text())
        diff = value_list.max() - value_list.min()
        cutt_off = diff/self.bin_number
        for x in range(self.bin_number):
            # One is subtracted from the bin number because Python is left inclusive.
            if x == self.bin_number - 1:
                print(f'{x}: {x*cutt_off}')
                self.selected_values = value_list[(value_list>=(x*cutt_off)+value_list.min())]
            else:
                print(f'{x}: {x*cutt_off}')
                self.selected_values = value_list[(value_list>=(x*cutt_off)+value_list.min())&(value_list<value_list.min()+cutt_off*(x+1))]

            self.current_group = 'Group {}'.format(len(self.groups)+1)
            self.group_list.addItem(self.current_group)

            self.tree_group = QTreeWidgetItem(self.variable_tree)
            self.tree_group.setExpanded(True)
            self.tree_group.setText(0, self.current_group)

            for y in self.selected_values:
                print(f'value binning:{type(x)}')
                kid = QTreeWidgetItem(self.tree_group)
                kid.setText(0,str(y))
                self.tree_group.addChild(kid)
            self.groups.append({"alias": self.current_group,"kids":self.selected_values})

    def binning_count(self):
        print("annot.binning_count()")
        value_list = self.metadata[self.variable_list_columns.selectedItems()[0].text()]
        print(value_list.dtypes)
        if value_list.dtypes == object:
            print("Selected variable has non-numeric values.")
            self.group_list.addItem("Selected variable has non-numeric values.")
        elif pd.isna(value_list).any() == True:
            print("Selected variable has missing values.")
            # self.thorb = Thorbass()
            # self.thorb.show()
            # self.thorb.message_received("The selected variable has missing values. Would you like to continue? Missing values will be relegated to their own bin.")
            # self.thorb.ok_button.clicked.connect(self.annot.binning_continued())
            reply = QMessageBox.question(self, 'Missing values', 'The selected variable has missing values.\n\nWould you like to continue?\n', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.binning_count_continued()
        else:
            self.binning_count_continued()

    def binning_count_continued(self):
        print("annot.binning_count_continued()")
        self.group_list.clear()
        self.variable_tree.clear()
        self.selected_values = []
        self.groups = []
        value_list = self.metadata[self.variable_list_columns.selectedItems()[0].text()]
        print(f'before: {value_list}')
        value_list = value_list.sort_values()
        print(f'after sort:{value_list} : {len(value_list)}')
        # value_list_sort = value_list.reset_index()
        # if pd.isna(value_list).any() == True:
        value_list = [v for v in value_list if not(pd.isna(v))]
        value_list_int = [int(floater) for floater in value_list]
        # value_list = value_list.sort_values()
        self.bin_number = int(self.bin_edit.text())
        diff = len(value_list)
        cutt_off = int(diff/self.bin_number)
        for x in range(self.bin_number):
            self.selected_values = []
            # if x == self.bin_number - 1:
                # self.selected_values = value_list[]
            selected_column = self.variable_list_columns.selectedItems()[0].text()
            # if x == 0:
            #     cutt = 0
            # else:
            #     cutt = x*cutt_off-1
            # cutt_1 = (x+1)*cutt_off
            # for y in value_list:
            # print(f"cutt: {cutt} - {value_list_sort[selected_column][cutt]}")
            # print(f"cutt_1: {cutt_1} - {value_list_sort[selected_column][cutt_1]}")
            # print(f"cutt_1+1: {cutt_1+1} - {value_list_sort[selected_column][cutt_1+1]}")
            
            # print(value_list[cutt:cutt_1])
            # x*cutoff is inclusive
            # x+1*cutoff is exclusive except for last one
            # if value_list_sort[selected_column][cutt_1] == value_list_sort[selected_column][cutt_1+1]:
            #     self.selected_values = value_list_sort[selected_column][cutt:cutt_1+1]
            #     # cutt =+ 1
            #     print("vutt")
            # else:
            #     self.selected_values = value_list_sort[selected_column][cutt:cutt_1]
            #     print("vis")

            if x == self.bin_number - 1:
                # self.selected_values = value_list[(value_list>=value_list[x*cutt_off])]
                print(f'{x}: {value_list[x*cutt_off]}')
                self.selected_values = [v for v in value_list if v>=value_list[x*cutt_off]]
                print(f'{x} : {self.selected_values} : {len(self.selected_values)}')
            else:
                print(f'{x}: {value_list[x*cutt_off]}')
                # self.selected_values = value_list[(value_list>=value_list[x*cutt_off])&(value_list<value_list[cutt_off*(x+1)])]
                self.selected_values = [v for v in value_list if (v>=value_list[x*cutt_off]) and (v<value_list[(x+1)*cutt_off])]
                print(f'{x} : {self.selected_values} : {len(self.selected_values)}')
        

            # if x == self.bin_number - 1:
            #     self.selected_values = value_list[(value_list>=(x*cutt_off)+value_list.min())]
            # else:
            #     self.selected_values = value_list[(value_list>=(x*cutt_off)+value_list.min())&(value_list<value_list.min()+cutt_off*(x+1))]

            # self.selected_values.append(value_list_sort[selected_column][cutt:cutt_1])
            # print(self.selected_values)
                # self.selected_values = value_list[(value_list>=(x*cutt_off)+value_list.min())]
            # else:
            #     self.selected_values = value_list[(value_list>=(x*cutt_off))&(value_list<cutt_off*(x+1))]
            # print(self.selected_values)
            self.current_group = 'Group {}'.format(len(self.groups)+1)
            self.group_list.addItem(self.current_group)
            print(self.current_group)

            self.tree_group = QTreeWidgetItem(self.variable_tree)
            self.tree_group.setExpanded(True)
            self.tree_group.setText(0, self.current_group)

            # print(self.groups)
            # print(f'Group {len(self.groups)+1}: {self.selected_values}')
            for y in self.selected_values:
                print(f'count binning:{type(y)}')
                # print(y)
                kid = QTreeWidgetItem(self.tree_group)
                kid.setText(0,str(y))
                self.tree_group.addChild(kid)
            self.groups.append({"alias": self.current_group,"kids":self.selected_values})

    def recode(self):  
        print("annot.recode()") 
        self.selected_values=[]
        for value in list(self.variable_list_values.selectedItems()):
            self.selected_values.append(value.text())

        self.current_group = 'Group {}'.format(len(self.groups)+1)
        self.group_list.addItem(self.current_group)

        self.tree_group = QTreeWidgetItem(self.variable_tree)
        self.tree_group.setExpanded(True)
        self.tree_group.setText(0, self.current_group)
        for x in self.selected_values:
            print(f'manual binning:{type(x)}')
            kid = QTreeWidgetItem(self.tree_group)
            kid.setText(0,x)
            self.tree_group.addChild(kid)
        self.groups.append({"alias": self.current_group,"kids":self.selected_values})
        # self.groups.append({"alias": group.text(0),"kids":self.selected_values})
        for selected_value in self.variable_list_values.selectedItems():
            # selected_value.setHidden(True)
            # print(selected_value)
            self.variable_list_values.takeItem(self.variable_list_values.row(selected_value))
        
            # selected_value.setHidden(True)
        # print(self.groups)
        # print(self.selected_values)
        # self.tree_label()

    # def edit_label(self):
    #     self.variable_tree.editItem

    # def relabel(self):
    #     index = self.group_list.currentIndex()
    #     if index.isValid():
    #         item = self.group_list.itemFromIndex(index)
    #         item.setFlags(item.flags() | Qt.ItemIsEditable)
    #     self.group_list.edit(index)
    #     for x in range(len(self.groups)):
    #         if self.groups[x]["alias"] == item.text():
    #             self.groups[x]["alias"] == self.group_list.currentItem().text()
    #             self.tree_group.setText(x,self.group_list.currentItem().text())
    #     print(self.tree_group.text(0))
    #     print(self.group_list.currentItem().text())
    #     print(item.text())
    #     print(self.groups)

    def relabel_group(self):
        print("annot.relabel_group()")
        index = self.group_list.currentIndex()
        if index.isValid():
            item = self.group_list.itemFromIndex(index)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.group_list.edit(index)
    
    def relabel_column(self):
        print("annot.relabel_column()")
        index = self.variable_list_columns.currentIndex()
        item = self.variable_list_columns.itemFromIndex(index)
        if index.isValid():
            # item = self.variable_list_columns.itemFromIndex(index)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.variable_list_columns.edit(index)

    def column_label(self):
        print("annot.column_label()")
        index = self.variable_list_columns.currentIndex()
        item = self.variable_list_columns.itemFromIndex(index)
        self.metadata.rename(columns = {self.column:item.text()}, inplace=True)
        print(self.column)
        print(item.text())
        # self.megameta.loc[self.megameta[self.column]==value,
        #             [self.new_column]]=group["alias"]
        print(self.metadata.columns)

    def tree_label(self):
        print("annot.tree_label()")
        self.variable_tree.clear()
        index = self.group_list.currentIndex()
        item = self.group_list.itemFromIndex(index)
        self.groups[index.row()]["alias"] = item.text()

        for group in self.groups:
            self.tree_group = QTreeWidgetItem(self.variable_tree)
            self.tree_group.setText(0, group["alias"])
            for k in group["kids"]:
                kid = QTreeWidgetItem(self.tree_group)
                self.tree_group.addChild(kid)
                kid.setText(0,str(k))
            self.tree_group.setExpanded(True)

    def naming(self):
        print("annot.naming()")
        c=1
        if any(f"{self.column}_recode" in col for col in self.metadata.columns):
            c+=1
            self.new_column = f"{self.column}_recode_{c}"
        else:
            self.new_column = f"{self.column}_recode_1"

    def add_config(self):
        print("annot.add_config()")
        # self.metadata["{selected_column}_recode_{number}".format(
        #     selected_column=self.selected_column, number=1)]
        self.megameta = self.metadata.copy()
        # self.new_column="NEW"
        self.naming()
        # print([type(v) for v in self.megameta[self.column]])
        # for m in self.megameta[self.column]:
        #     print(f'column value type:{type(m)}')
        #     print(f'column converted to string:{type(str(m))}')
        for group in self.groups:
            print(f'group:{group}')
            for value in group["kids"]:
                # print(type(value))
                # # if any(self.megameta[self.column]) == value:
                # # if any([str(m) for m in self.megameta[self.column]]) == value:
                # for m in self.megameta[self.column]:
                #     if str(m)==value:
                #         print(f'value type:{type(value)}')
                #         print(f'str(m) type:{type(str(m))}')
                #         print(f'm type: {type(m)}')
                #         print("equals!")
                #     else:
                #         print("not equals")
                #         print(f'value type:{type(value)}')
                #         print(f'str(m) type:{type(str(m))}')
                #         print(f'm type: {type(m)}')
                self.megameta.loc[self.megameta[self.column].astype(str)==str(value),
                    [self.new_column]]=group["alias"]
        print([type(v) for v in self.megameta[self.new_column]])
        self.variable_list_columns.clear()
        self.variable_list_values.clear()
        self.group_list.clear()
        for x in self.megameta.columns:
            self.variable_list_columns.addItem(x)
        self.metadata=self.megameta.copy()
        self.groups=[]

    def save_config(self):
        print("annot.save_config()")
        # perhaps need a safe measure so that if the user didn't press add configuration and they hit save we prompt them to make sure they didn't forget
        # print(self.metadata)
        try:
            file = QFileDialog.getSaveFileName(self, 'Save File', '', ".csv(*.csv))")
            self.metadata.to_csv(file[0], index = False)
            self.pleth.metadata = file[0]
            self.pleth.metadata_list.clear()
            self.pleth.metadata_list.addItem(self.pleth.metadata)
            # print(self.pleth.metadata)
        except PermissionError:
            reply = QMessageBox.information(self, 'File in use', 'One or more of the files you are trying to save is open in another program.', QMessageBox.Ok)
        except Exception as e:
            print(f'{type(e).__name__}: {e}')
            print("no file chosen")
        if self.pleth.breath_df != []:
            self.pleth.update_breath_df()
        # self.Plethysmography.variable_list.addItem(file[0])

#endregion
    def cancel_annot(self):
        print("annot.cancel_annot()")
        self.metadata = None

    def show_metadata_file(self):
        print("annot.show_metadata_file()")
        # print(self.metadata)
        # print(self.pleth.metadata)
        if self.pleth.metadata == "" and self.metadata is None:
            print("metadata path and df are empty")
            reply = QMessageBox.information(self, 'Missing metadata file', 'Please select a metadata file.', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.load_metadata_file()
            if reply == QMessageBox.Cancel:
                self.close()
        elif self.pleth.metadata != "" and self.metadata is None:
            print("metadata path exists but df is empty")
            if Path(self.pleth.metadata).exists():
                if self.pleth.metadata.endswith('.xlsx'):
                    self.metadata = pd.read_excel(self.pleth.metadata)
                    self.populate_list_columns()
                elif self.pleth.metadata.endswith('.csv'):
                    self.metadata = pd.read_csv(self.pleth.metadata)
                    print(self.metadata.columns)
                    self.populate_list_columns()
                else:
                    reply = QMessageBox.information(self, 'Incorrect file format', 'Only .csv or .xlsx files are accepted.\nWould you like to select a different file?', QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
                    if reply == QMessageBox.Ok:
                        self.load_metadata_file()
        else:
            print("existing annot activity")
            

#region populate
    def load_metadata_file(self):
        print("loading metadata file for annot subGUI")
        self.variable_list_columns.clear()
        self.variable_list_values.clear()
        self.variable_tree.clear()
        self.group_list.clear()
        self.kids={}
        self.groups=[]
        # if Path(self.pleth.metadata).exists():
        #     self.metadata = pd.read_csv(self.pleth.metadata)
        # else:
        #     print("load")
        if self.pleth.mothership == "":
            load_path = str(os.path.join(Path(__file__).parent.parent.parent,"PAPR Output"))
            print(load_path)
        else:
            print("mothership exists")
            load_path = self.pleth.mothership
            

    # Opens open file dialog
        file = QFileDialog.getOpenFileName(self, 'Select metadata file', str(load_path))

    # If you the file you chose sucks, the GUI won't crap out.
        if not file[0]:
            print("that didn't work")
        elif Path(file[0]).suffix == ".xlsx":
            self.metadata = pd.read_excel(file[0])
            self.populate_list_columns()
        elif Path(file[0]).suffix == ".csv":
            self.metadata = pd.read_csv(file[0])
            self.populate_list_columns()
        else:
            self.thumb = self.pleth.Thumbass()
            self.thumb.show()
            self.thumb.message_received("Incorrect file format","The file you selected is neither an xlsx nor a csv. Please check the format of your file or choose another one.")

    def populate_list_columns(self):
        print("annot.populate_list_columns()")
        self.variable_list_columns.clear()
        self.variable_list_values.clear()
        self.variable_tree.clear()
        self.group_list.clear()
        self.kids={}
        self.groups=[]
        for x in self.metadata.columns:
            # if pd.isna(self.metadata[x]).any() == True:
            #     self.variable_list_columns.addItem(f'{x}*')
            # else:
            self.variable_list_columns.addItem(x)

    def populate_list_values(self):
        print("annot.populate_list_values()")
        self.variable_list_values.clear()
        self.variable_tree.clear()
        self.group_list.clear()
        self.kids={}
        self.groups=[]
        # self.column = self.variable_list_columns.selectedItems()
        # for x in list(self.column):
        #     print(x.text())
        #     self.selected_column = x.text()
        #     print(self.selected_column)
        #     for y in self.metadata[x.text()].unique():
        #         self.variable_list_values.addItem(str(y))
        #         self.kids[str(y)]=y
        self.column = self.variable_list_columns.currentItem().text()
        for y in sorted(set([m for m in self.metadata[self.column] if not(pd.isnull(m) == True)])):
            self.variable_list_values.addItem(str(y))
            self.kids[str(y)]=y
        # for x in list(self.column):
        #     print(x.text())
        #     self.selected_column = x.text()
        #     print(self.selected_column)
        #     for y in self.metadata[x.text()].unique():
        #         self.variable_list_values.addItem(str(y))
        #         self.kids[str(y)]=y
        # add functionality that either greys out items that have been included in a group or prompts
        # a warning when the user selects a value that's already been recoded.

#endregion

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = Variable_config()
#     window.show()
#     app.exec_()

# %%

