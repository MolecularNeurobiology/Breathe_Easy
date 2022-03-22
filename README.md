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
MainGui.py
form.ui
form.py
...

Variable configuration subGUI
...
AnnotGUI.py
annot_form.ui
annot_form.py
...

Basic BASSPRO settings subGUI
...
MainGui.py
basic_form.ui
basic_form.py
...

Automated BASSPRO settings subGUI
...
MainGui.py
auto_form.ui
auto_form.py
...

Manual BASSPRO settings subGUI
...
MainGui.py
manual_form.ui
manual_form.py
...

STAGG settings subGUI
...
MainGui.py
config_form.ui
config_form.py
...

Custom STAGG settings subsubGUI
...
MainGui.py
custom_config.ui
custom_config.py
...

Thumbass dialog
...
MainGui.py
thumbass.ui
thumbass.py
...

Thinbass dialog
...
MainGui.py
thinbass.ui
thinbass.py
...

Thorbass dialog
...
MainGui.py
thorbass.ui
thorbass.py
...


GUI settings files
-------------------
breathcaller_config.json
gui_config.json
timestamps.json
reference_config.json
resource.qrc
resource.py
resources>graphic.png


