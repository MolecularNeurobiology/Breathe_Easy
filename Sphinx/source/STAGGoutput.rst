STAGG Output
=================
The expected output of STAGG includes one of each per folder: 

1. the figures for each dependent variable,
2. the figures for any optional graphs or additional models,
3. the environments pre- and post-model creation as .RData files (the smaller file will be pre-model creation and can be used as input to STAGG),
4. copies of the STAGG settings files,
5. a .html file that concatenates all generated figures into a single .html page,

one “StatResults” folder containing:

6. a stat_basic.xlsx file that contains summary statistics for each dependent variable,
7. a stat_res.xlsx file that contains degrees of freedom, standard error, etc. that is used in the primary LMEM test,
8. a tukey_res.xlsx file that contains all comparisons in the Tukey post-hoc and associated p-values and standard errors for those comparisons and
9. residual and QQ plots for each dependent variable and any transformation chosen for those variables. 

and one "OptionalStatResults" folder containing:

10. a stat_res.xlsx file that contains degrees of freedom, standard error, etc. that is used in testing for optional graphs,
11. a tukey_res.xlsx file that contains all comparisons in the Tukey post-hoc and associated p-values and standard errors for those comparisons and
12. residual and QQ plots for each dependent variable and any transformation chosen for those variables.

All of these outputs are saved in a single folder for each run of STAGG. Each of these folders is automatically named with the 
format “STAGG_output_CurrentDate_CurrentTime” to allow the user to keep track of each different run they perform with different settings. 
In addition to the timestamps in the folder name, the inclusion of the STAGG settings files allows direct confirmation of the settings 
used to generate the files for each run. 
 
We recommend that users rename the folders with more distinct names based on the purpose of each run to make referencing and finding figures
and results easier later.