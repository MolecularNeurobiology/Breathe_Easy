Troubleshooting
=================
No breaths, but recordings look good
------------------------------------------

Missing calibration values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you think that you should have breaths selected from a particular period in your experiment, but do not have any refined variables, i.e., 
variables that require calibration information to calculate, then you may have an issue with your calibration period. The most common 
reason for this is that the gas concentration settings for the calibration period may be too stringent for your particular recording environment. 
Check the actual voltage and concentration that you record during calibration and adjust your automated settings accordingly.

Incorrect settings in automated settings file derived from signal files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you use the Deriving Settings from Signal Files – with and without modifications function, then the settings for each gas 
condition may not be correct. Unfortunately, suggested settings for each gas condition are not auto populated when using this function. 
Therefore, you will need to manually interrogate the settings in each column and assign appropriate values using the table provided. 

Common errors in GUI
-------------------------------

Non-numeric data identification in variable configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
During automated binning you may find some variables produce an error that states the variable is non-numeric. 
Automated binning only works on numeric data. This error may be produced for variables that are numeric if there 
is an issue with the formatting of that particular column in the metadata file. If you feel this is the cause of 
the error for your data, simply open your metadata file, force the data type to numeric for the column in question, 
save, then re-upload the metadata into the GUI. 

What the screen?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This error will only occur if you have multiple monitors.

In a very rare case you may experience resizing issues due to inconsistent resolution settings. This error has only been seen 
one time, but makes using the subGUIs very difficult. Essentially, the subGUI will open and appear spread over multiple monitors with
portions of the subGUI appearing on each screen. This is caused by having your display set to extend display AND setting one of the monitors
where the display is extended as the primary monitor. Both of these must be true for this error to occur. To fix this issue, simply change the 
display settings.
