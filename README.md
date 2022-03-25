# BASSPRO-STAGG
# REFACTOR README

resources folder for  gui refactor and code review projects
Ray Lab Project: <br/>
PM154_PJ_GUI_Refactoring

Project Schemas: <br/>
*general user experience workflow <br/>
...
X:\Projects\PM154_PJ_GUI_Refactoring\Schema
<br/>
*architecture (named components of the GUI)<br/>
...
<br/>
Datasets for Testing: <br/>
X:\Projects\PM154_PJ_GUI_Refactoring\Testing Datasets
<br/>


Class locations:
------------------
=============
 .py file
...
Class (Class object type) found in the .py file
Class-less functions found in the .py file
GUI or subGUI that the Class is associated with
...
=============

MainGUImain.py
...
def main()
...


MainGui.py
...
Class Plethysmography (QMainWindow)
Primary Class for Main GUI
...
Class Auto (QWidget)
Primary Class for Automated BASSPRO Settings subGUI
...
Class Basic (QWidget)
Primary Class for Basic BASSPRO Settings subGUI
...
Class Manual (QWidget)
Primary Class for Manual BASSPRO Settings subGUI
...
Class Config (QWidget)
Primary Class for STAGG Settings subGUI
...
Class Custom (QWidget)
Primary Class for Custom STAGG Settings subsubGUI
Secondary Class for STAGG Settings subGUI
...
Class Thumbass (QDialog)
Supplementary Class for User Messaging
...
Class Thinbass (QDialog)
Supplementary Class for User Messaging when opening STAGG Settings subGUI with multiple possible variable list sources
...
Class Thorbass (QDialog)
Supplementary Class for User Messaging when merging in Manual BASSPRO Settings subGUI or when opening STAGG Settings subGUI with no possible variable list sources
...
Class AlignDelegate (QStyledItemDelegate)
Supplementary Class to align headers in STAGG Settings subGUI Config.variable_table
...
Class CheckableComboBox (QComboBox)
Supplementary Class to make checkable comboBox for transformation drop-down menus in STAGG Settings subGUI
...


AnnotGUI.py
...
Class Annot (QMainWindow)
Primary Class for Variable Configuration subGUI
...
Class Thumbass (QDialog)
Supplementary Class for User Messaging
...


MainGUIworker.py
...
Class WorkerSignals (QObject)
Secondary Class for Main GUI to support parallel processing
...
Class Worker (QRunnable)
Secondary Class for Main GUI to support parallel processing
...
def get_jobs_py()
def get_jobs_r()
def get_jobs_stamp()
...

GUI design files
--------------------------
==========
GUI Name
...
Initialized in: the .py file in which the GUI is initialized and defined
The .ui file produced by Qt Creator
The .py file produced by converting the .ui file with pyuic5
...
==========

MainGUI
...
Initialized in: MainGuimain.py | window.show()
form.ui
form.py
...

Variable configuration subGUI
...
Initialized in: MainGui.py | Main.show_annot()
annot_form.ui
annot_form.py
...

Basic BASSPRO settings subGUI
...
Initialized in: MainGui.py | Main.show_basic()
basic_form.ui
basic_form.py
...

Automated BASSPRO settings subGUI
...
Initialized in: MainGui.py | Main.show_auto()
auto_form.ui
auto_form.py
...

Manual BASSPRO settings subGUI
...
Initialized in: MainGui.py | Main.show_manual()
manual_form.ui
manual_form.py
...

STAGG settings subGUI
...
Initialized in: MainGui.py | Main.show_variable_config()
config_form.ui
config_form.py
...

Custom STAGG settings subsubGUI | Config.show_custom()
...
Initialized in: MainGui.py
custom_config.ui
custom_config.py
...

Thumbass dialog
...
Initialized in: MainGui.py | Main.Thumbass.show()
		AnnotGUI.py | Annot.Thumbass.show()
thumbass.ui
thumbass.py
...

Thinbass dialog
...
Initialized in: MainGui.py | Main.Thinbass.show()
thinbass.ui
thinbass.py
...

Thorbass dialog
...
Initialized in: MainGui.py | Main.Thorbass.show()
thorbass.ui
thorbass.py
...


GUI settings files
-------------------
breathcaller_config.json
...
The breathcaller_config.json stores a nested dictionary containing default settings for BASSPRO for multiple experimental setups. The first level of the dictionary consists of three 
keys - "AP" holds the basic BASSPRO settings dictionaries, "Manual Settings" holds the manual BASSPRO settings dictionaries, and "Auto Settings" holds the automated BASSPRO settings
dictionaries. 

The "default" dictionaries for Manual Settings and Auto Settings should have eight keys, each for different experimental setups - CNO 5% Hypercapnia, CNO 7% Hypercapnia, CNO 10% 
Hypercapnia, CNO 10% Hypoxia, 5% Hypercapnia, 7% Hypercapnia, 10% Hypercapnia, and 10% Hypoxia. Currently, Auto Settings has all eight, but Manual Settings only has CNO 5% Hypercapnia, 
5% Hypercapnia, 7% Hypercapnia, 10% Hypercapnia, and 10% Hypoxia. The value of each of these experimental setup keys is a dictionary with keys corresponding to the timestamps of that 
experimental setup. The value of each of these timestamp keys is a dictionary of the settings and their values for each timestamp. 
The "default" dictionary for AP (basic settings) is shallower - each setting is a key and its value is the actual setting value. 

Auto Settings and AP (basic settings) have a second key "current" that stores the settings values saved from their respective subGUIs as a dictionary. If the user chooses to open a 
breathcaller_config.json file to load previous settings (as opposed to opening a previously-made .csv file), the subGUI will populate its widgets with values from the "current" dictionary.

AP (basic settings) has a third key, "nomenclature", that is not accessed by the GUI. It served as a reference when we changed the names of the basic settings to be more descriptive.

=================
gui_config.json
...
The gui_config.json is a nested dictionary containing three keys. The "Paths" key's value is a dictionary storing paths to the BASSPRO module,
the directory of the STAGG scripts, and the R executable file (Rscript.exe) on the user's device. 

The "metadata" key's value is a nested dictionary storing the names of the fields of the database that are accessed when building a metadata file using the database. Currently, these fields 
are written to accommodate the Ray Lab's database. Ideally, the user will be able to change these fields to suit their own database using something friendlier than a json file. 

The "Settings Names" key's value is a nested dictionary of two dictionaries, one for Auto and one for Basic settings, containing the labels of settings used in the subGUI and their corresponding 
labels used in BASSPRO, divided according to which table in the subGUI will be populated with those labels' settings. The basic settings labels dictionary is no longer used, and I anticipate the 
auto settings labels dictionary also retiring when we make the changes to the auto settings subGUI needed to relate the timestamp results and the auto settings subGUI.

================
timestamps.json
...
The timestamps.json stores a dictionary that has two main keys. One is a dictionary containing the expected timestamps for CNO 5% Hypercapnia, CNO 7% Hypercapnia, CNO 10% Hypercapnia, CNO 10% Hypoxia, 
5% Hypercapnia, 7% Hypercapnia, 10% Hypercapnia, and 10% Hypoxia. The other key is an empty dictionary where the contents of Main.tsbyfile, the dictionary created by the timestamper 
methods (Main.timestamp_dict(), Main.grabTimeStamps(), and Main.checkFileTimeStamps()) in MainGui.py, are dumped when the timestamper json is saved to the directory of the first 
signal file selected by the user. This json contains the timestamps for every signal file selected, as well as whether or not those timestamps matched the timestamps of the selected experimental
setup. The experimental setup used for comparison is selected by the user via a drop-down menu (Main.necessary_timestamp_box) with options sourced from the keys of 
Main.bc_config["Dictionaries"]["Auto Settings"]["default"], a dictionary stored in the breathcaller_config.json file. A summary of the comparison is presented on the main display
in the Main Gui as a list of files that were missing timestamps, had duplicate timestamps, and/or had novel timestamps.

================
reference_config.json
...
The reference_config.json is a shallow dictionary containing a key for every setting, beit basic, manual, or automated, with a corresponding value of a string defining and describing the setting and
its default values where appropriate.

===============
resource.qrc
resource.py
resources>graphic.png
...
The resource.qrc file (accessible to the GUI scripts by conversion to resource.py) stores the path to the image used in the STAGG settings subGUI. The image itself is saved to the resources folder 
within the scripts>GUI folder. 


