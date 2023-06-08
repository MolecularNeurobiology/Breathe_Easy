.. Breathe Easy documentation master file, created by
   sphinx-quickstart on Tue Sep  6 13:46:52 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Running SASSI
=================
Once the signal files, the metadata, and the settings are selected, we can run SASSI. Follow the below steps to run 
SASSI independently without triggering STAGG to run immediately following completion. To run STAGG immediately after 
SASSI, see Full Run of SASSI-STAGG.

Parallel Processing
----------------------
The GUI can analyze multiple files at the same time, but this parallel processing can be resource intense. 
The alternative is to analyze each file sequentially, but it will take longer for SASSI to complete the analysis. 
To run SASSI without parallel processing, just click ``Launch BASSPRO`` (12) and skip all below instructions in this section.

You can choose how much of your computer should focus on SASSI by selecting the number of processors in your computer 
you’d like to devote to the program. Most computers have 8 processors. If you want to run SASSI and work in other applications, 
you should choose a lower number of cores to devote to SASSI. If you want to run a large dataset overnight, you should select 
the maximum number of cores to dedicate to SASSI. If your computer has fewer than 8 processors, we recommend you use a different machine. 
Complete the steps below to set up parallel processing. 

1. Click the # Cores drop-down menu (10) in the main window. 

    * The GUI will automatically detect how many cores your computer has, and you can select a number from that list to indicate how many cores you’d like to use. 
    * If you select the highest number, then all of your cores will be used for parallel processing, and you might notice some performance issues in other applications while it is running. 
    * If you choose the lowest number, you should not notice any performance issues in other applications, however, it will take longer for SASSI to run. 

2. Select the number of cores you would like to devote to running SASSI.
3. Click ``Launch BASSPRO`` (12). 
4. Window (G) will immediately begin to populate with each process occurring during the analysis and will continue to do so throughout the run until it is complete.
