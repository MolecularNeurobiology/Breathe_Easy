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

MainGUImain.py
...
def main()
...


MainGui.py
...
Class Plethysmography (QMainWindow)
...
Class Auto (QWidget)
...
Class Basic (QWidget)
...
Class Manual (QWidget)
...
Class Config (QWidget)
...
Class Custom (QWidget)
...
Class Thumbass (QDialog)
...
Class Thinbass (QDialog)
...
Class Thorbass (QDialog)
...
Class AlignDelegate (QStyledItemDelegate)
...
Class CheckableComboBox (QComboBox)
...


AnnotGUI.py
...
Class Annot (QMainWindow)
...
Class Thumbass (QDialog)
...


MainGUIworker.py
...
Class WorkerSignals (QObject)
...
Class Worker (QRunnable)
...
def get_jobs_py()
def get_jobs_r()
def get_jobs_stamp()
...

GUI design files
--------------------------

MainGUI
...
Initialized in: MainGui.py
form.ui
form.py
...

Variable configuration subGUI
...
Initialized in: MainGui.py
annot_form.ui
annot_form.py
...

Basic BASSPRO settings subGUI
...
Initialized in: MainGui.py
basic_form.ui
basic_form.py
...

Automated BASSPRO settings subGUI
...
Initialized in: MainGui.py
auto_form.ui
auto_form.py
...

Manual BASSPRO settings subGUI
...
Initialized in: MainGui.py
manual_form.ui
manual_form.py
...

STAGG settings subGUI
...
Initialized in: MainGui.py
config_form.ui
config_form.py
...

Custom STAGG settings subsubGUI
...
Initialized in: MainGui.py
custom_config.ui
custom_config.py
...

Thumbass dialog
...
Initialized in: MainGui.py
thumbass.ui
thumbass.py
...

Thinbass dialog
...
Initialized in: MainGui.py
thinbass.ui
thinbass.py
...

Thorbass dialog
...
Initialized in: MainGui.py
thorbass.ui
thorbass.py
...


GUI settings files
-------------------
breathcaller_config.json
...
The breathcaller_config.json holds the dictionaries for 
gui_config.json
timestamps.json
...
The timestamps.json has two main keys. One is a dictionary containing the expected timestamps for CNO 5% Hypercapnia, CNO 7% Hypercapnia, CNO 10% Hypercapnia, CNO 10% Hypoxia, 
5% Hypercapnia, 7% Hypercapnia, 10% Hypercapnia, and 10% Hypoxia. The other key is an empty dictionary where the contents of Main.tsbyfile, the dictionary created by the timestamper 
methods (Main.timestamp_dict(), Main.grabTimeStamps(), and Main.checkFileTimeStamps()) in MainGui.py, are dumped when the timestamper json is saved to the directory of the first 
signal file selected by the user. This json contains the timestamps for every signal file selected, as well as whether or not those timestamps matched the timestamps of the selected experimental
setup. The experimental setup used for comparison is selected by the user via a drop-down menu (Main.necessary_timestamp_box) with options sourced from the keys of 
Main.bc_config["Dictionaries"]["Auto Settings"]["default"], a dictionary stored in the breathcaller_config.json file. A summary of the comparison is presented on the main display
in the Main Gui as a list of files that were missing timestamps, had duplicate timestamps, and/or had novel timestamps.
...
reference_config.json
resource.qrc
resource.py
resources>graphic.png


