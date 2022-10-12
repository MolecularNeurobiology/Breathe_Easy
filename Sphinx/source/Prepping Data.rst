Prepping Data
===============

.. note::
   The required file format for the respiratory recordings is ``.txt``. It is possible to use recording software other than LabChart 
   as long as comments are included that indicate which timestamps belong to which experimental conditions, i.e., room air, 5% CO2, etc.. 
   We use LabChart for all of our recordings, so instructions to convert those recordings are below. For the software you use, 
   please visit the appropriate help website for information on converting the recordings into text files.

For manual selections to be run through BASSPRO-STAGG, you must convert the signal files AND the DataPad. 
This requires the running of two different Macros. If you only intend to run automated selections, then you 
need only complete signal file export below. If you intend to run manual selections, then you must run both 
the :ref:`signal file export<LabChart Signal File Export>` and the :ref:`DataPad export <LabChart DataPad Export>`.

Before running your data for the first time, we recommend completing the optional step of timestamp review
to give you a chance to address formatting issues that would cause errors later in BASSPRO. This can potentially save 
hours of program run time for unexpected results. See :ref:`Timestamp Review <Timestamp Review>` for more
information.

LabChart Signal File Export
------------------------------
Download LabChart `here <https://www.adinstruments.com/support/downloads/windows/labchart/>`_.

The required input for BASSPRO is text file-formatted recording files. If recordings are performed using 
LabChart, the default saving format is .adicht rather than .txt. Therefore, all of your .adicht files will 
need to be converted to .txt files before proceeding with BASSPRO-STAGG analysis. To do this, complete the 
below steps for batch conversion of all .adicht files within a folder. You can also convert a single file if 
you have that file open in LabChart and click File > Export… This will open a file dialog where you choose the 
folder in which you want your text file saved. Then click “Save”. 

.. figure:: Figures/Figure_1.png
  :scale: 100%
  :alt: Alternative Text
  
  *Figure 1* Settings to batch export .adicht files from LabChart as .txt files.

.. note::
   Your settings must match the settings indicated in the screenshot in Figure 1. These should be default settings on PC, but they might not be defaults on the Mac version of LabChart. Ensure these settings are correct for both single file conversion above and batch export below.

.. note::
   You MUST save the filename of your recordings with the Mouse Unique Identifier (MUID) of the animal in the recording and the Plethysmography Unique Identifier (PlyUID) of the specific recording for that animal, e.g., M35068_Ply340. 
   
#. Open LabChart.
#. Click ``New`` to create a new, blank LabChart file that has no data.
     .. note:: 
        This Macro will not work if you have any of the files open that you wish to convert.
#. Click on ``Macro`` on the top navigation bar.
    * Click ``Manage…`` from the dropdown menu.
#. Select the ``Example Macros`` tab from the top navigation of the popup.
#. Select ``ExportFolder`` from the options.
#. Click ``Run`` on the top right hand of the popup.
#. In the next popup, you will be in a file navigation window. Navigate to the folder that contains all of the LabChart files you wish to export. Click ``OK``.
#. The prompt at the top of the window will now change to say select the folder where you wish to save the exported files. Navigate to your desired output folder. Click ``OK``. 
#. After clicking ``OK`` in step 7, the script will automatically export all LabChart files from the folder selected in Step 6 and save those exported text files to the folder in Step 7.
     .. note:: 
        There may be points during the conversion where an error message informs you that 
        “LabChart is unable to read all the settings in this file.” This will halt conversion 
        and require user input to click ``OK`` and continue. Despite this error, all files will still 
        be converted. However, if you set up batch export and walk away, it may be halted until 
        you click ``OK`` each time this message appears. 
        
LabChart DataPad Export
-----------------------
#. Open LabChart.
#. Click ``New`` to create a new, blank LabChart file that has no data.
     .. note:: 
        This Macro will not work if you have any of the files open that you wish to convert.
#. Click on ``Macro`` on the top navigation bar.
    * Click ``Manage…`` from the dropdown menu.
#. Select the ``Example Macros`` tab from the top navigation of the popup.
#. Select ``ExportFolder`` from the options.
#. With that macro highlighted, click ``Copy to Library`` in the menu to the right.
#. Click the ``Library Macros`` tab at the top of the popup.
    * You should now see the ExportFolder(1) script, which is a copy of the ExportFolder default macro.
#. Highlight ``ExportFolder(1)`` and click the ``Edit`` button on the right-hand side of the popup.
#. In the bottom of the script you will see a line that says: 
     ``Call currentDoc.SaveAs (saveName, false, suppressOptionsDialog)``
#. Replace this line with the following:
     ``Call currentDoc.SaveAsAdvanced (saveName, "class DataPad::DataPadDataSaveAsText", 0)``
#. Click ``Run`` at the top of the popup. 
     .. note::
        You can also save this version of the macro for later use. You will just access it from your macro library instead of going to example macros
        and making the above changes each time.
#. In the next popup, you will be in a file navigation window. Navigate to the folder that contains all of the LabChart files you wish to export. Click ``OK``.
#. The prompt at the top of the window will now change to say select the folder where you wish to save the exported files. Navigate to your desired output folder. Click ``OK``. 
#. The script will automatically export all LabChart DataPad selections from the LabChart files in the folder selected and save those as exported text files in the selected output folder.
