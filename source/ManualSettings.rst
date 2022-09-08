.. Breathe Easy documentation master file, created by
   sphinx-quickstart on Tue Sep  6 13:46:52 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Manual Settings Configuration
#################################
Manual settings are unique in that you must load experimental settings and additional LabChart input from the DataPad. 
For help on DataPad export, see :ref:`DataPad Export <LabChart DataPad Export>`.

You can either create a new manual selection settings file or open an existing one. With both options you can edit the table 
manually within the subGUI.

New Settings File
**********************
1. Click the ``Manual Settings`` button (7) to open the Manual Settings subGUI (Figure 12). 

    * This subGUI consists of three tables that populate with the appropriate settings from your input. 

2. Click ``Select default settings:`` and choose an experimental design from the dropdown menu that best fits your experiment.

    * Make necessary changes in the table of the subGUI that reflect your experiment exactly. 

3. Click ``Load LabChart selections`` to navigate a file dialog and select the .txt files that are the exported LabChart DataPad views. 
    .. note::
       This is the DataPad export, NOT the text file export of the whole signal file.

4. After confirming your choices, click ``Merge`` to create your Manual Settings configuration file. 

Existing Manual Settings Files
********************************
1. Click the ``Manual Settings`` button (7) to open the Manual Settings subGUI (Figure 12). 
    
    * This subGUI consists of three tables that populate with the appropriate settings from your input. 

2. Click ``Load previous settings`` to navigate a file dialog and select an existing manual settings file. 

    * Make necessary changes in the table of the subGUI that reflect your experiment exactly.

3. Click ``Load LabChart selections`` to navigate a file dialog and select the .txt files that are the exported LabChart DataPad views. 
    .. note::
       This is the DataPad export, NOT the text file export of the whole signal file.

4. After confirming your choices, click ``Merge`` to create your Manual Settings configuration file. 
