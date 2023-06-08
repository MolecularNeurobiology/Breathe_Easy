SASSI Output
=================
There are a number of steps to preparing to run Breathe Easy. Below is a brief outline of 
the steps to set everything up within the GUI. Detailed instructions are linked within the 
outline and in the following sections of this guide. 

*The expected output of SASSI includes one of each per folder:*
1. the settings files you generated in the SASSI configuration settings (“autosections.csv”, “basics.csv”, and/ or “manual.csv”), 
2. the “metadata.csv” file associated with the data, 

and one of each per recording/ signal file:

3. a log file describing the signal file’s performance through SASSI,

    * The log file will record any errors encountered when analyzing a signal file – any log file without accompanying JSON 
      files means that SASSI was not able to analyze that particular signal file.

4. a csv file of all the breaths identified by SASSI concatenated with the relevant metadata,
5. a json file that holds the same data as the csv file in #4, but only for breaths that were selected as “good breaths”, and
6. another csv file that summarizes the breath selections and calculates averages for each section of the run for both “good breaths” and 
   all other breaths.
   
    .. note::
       To help understand some of the variables produced in SASSI, you can download :download:`this excel sheet <Docs/BASSPRO_output_descriptions.xlsx>`.
       This resource has units and brief descriptions for the variables generated within SASSI.

All of these outputs are saved in a single folder for each run of SASSI. Each of these folders is automatically named with the format 
“SASSI_output_CurrentDate_CurrentTime” to allow the user to keep track of each different run they perform with different settings. 
In addition to the timestamps in the folder name, the inclusion of the “autosections.csv”, “metadata.csv”, and/ or “manual.csv” files 
allows direct confirmation of the settings used to generate the files for each run. 

The JSON files that are generated will be the input for the STAGG component of the pipeline. If you complete an independent run of SASSI, 
you will need to select these JSON files as input for your STAGG run. If you complete a full run, then this selection is automatically done. 