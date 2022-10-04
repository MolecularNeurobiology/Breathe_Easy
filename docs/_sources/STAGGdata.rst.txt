Initialize: Input for STAGG
==============================
There are a number of ways that STAGG input may be populated in the corresponding box on the GUI. Whichever way it is populated 
(all are described below), ensure that the STAGG settings you’ve just generated correspond to the files that will be used in the STAGG modeling. 

The output folder for STAGG will automatically be the folder selected for BASSPRO output (the path to this folder can be found in window A).

1. Automatic addition of STAGG input from current BASSPRO run

    * If you just finished running BASSPRO, then the JSON files produced as BASSPRO output will automatically appear in window (F) as the STAGG input.

2. If you want to select STAGG input manually, click Select STAGG input files to open a file dialog to navigate to the desired STAGG input. 

    * STAGG accepts three types of input:

        #. JSON files produced by BASSPRO. 
            
            * If you want to select files from different directories, complete the selection of files from the first folder and click Open. 

            * Then, click Select STAGG input files again, navigate to a different directory, and make your selections. You will be asked if you want to keep your previously selected STAGG input files – if you do, click Yes. 

        #. RData files produced by STAGG.

            * Only available if this dataset has been previously run through STAGG.
            * You can only select one RData file at a time.
            * STAGG produces two RData files for each run. You can use either one but using the smaller one will be faster.

        #. A single RData file and any number of JSON files.

            * RData file is only available if this dataset has been previously run through STAGG.

3. Important use notes:

    * If you haven’t run a particular dataset through STAGG, then you need to provide the JSON files as input.
    * If you have run a particular dataset through STAGG, then we recommend providing the RData file as input – 
      STAGG runs significantly faster with the RData file.
