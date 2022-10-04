STAGG Settings subGUI
===============================
The STAGG settings subGUI lets you define variable roles (independent, dependent, and covariate) for the statistical model, 
and how your dependent variables will be graphed by your independent and covariate variables. 

If you need a refresher on statistics, see our :ref:`resource page about statistics <Basic Statistics>`.

1. The STAGG settings subGUI will not open without one of the following sets of input: 

    * A metadata file, a basic BASSPRO settings file, and an automated and/or manual BASSPRO settings file
    * JSON files that were produced by BASSPRO and are selected using the Select STAGG input files button (14) and displayed in window (F).

2. Click the ``Select STAGG settings`` button (13) to open the subGUI (Figure 13).

    * If you have no input, then a file dialogue will appear for you to select existing csv files to start from.
    * If you have settings files that you’ve configured in the GUI, an option will appear to use those settings files to populate the subGUI.
    * If you have JSON file(s) selected in window (F), an option will appear to populate the subGUI using columns and variables from those files.
    * More than one option can appear if you have more than one of the above.

3. Use the below subsections to help in the selection of your settings.
4. Once you have finished selecting your variables, save your settings.

    * Click ``Ok`` to save your settings in local memory – the actual csv files detailing the settings won’t be created until STAGG is launched.
    * Click ``Export`` to open a file dialog to save your settings in a particular location for access later.
    * Either option of saving will result in a copy of these settings saved in the STAGG output folder for this run once launched.

5. If you want to clear all of your STAGG settings selections and start over, click the ``Cancel`` button at the bottom.

Primary Model Configuration - *REQUIRED*
------------------------------------------
The settings described in this section will assign all variables and settings for the primary loop of analysis. This primary loop
will analyze all variables that are selected as dependent variables. If you are unsure of any statistics terms, or need further explanation
on some of the verbiage used in the below instructions, see the HELP with STATS section.

If you need a refresher on statistics, see our :ref:`resource page about statistics <Basic Statistics>`.

Assign Variable Roles
^^^^^^^^^^^^^^^^^^^^^^^^
Following are instructions to designate settings for the statistical modeling using a linear mixed effects model with a Tukey post-hoc.

1. You can set variables as independent, dependent, or covariate in the left-hand table by clicking the corresponding bubble next to the appropriate variables in the list. Rules for each of the variable types:
    .. note::
       Independent variables MUST be categorical. Dependent variables MUST be continuous. 

    * Continuous variables that aren’t the response variable can be included in the model as covariates. 
    * You can select multiple rows and assign them the same role by clicking the corresponding button above the table.

2. The Variable column cannot be edited. 
3. The Alias column is editable – these labels are what will appear on the graph. 

    * For example, you can change ‘Experimental_Date’ to ‘Experimental Date’ so the awkward underscore doesn’t show up in your graph. 
    * If you save your images as .svg files, you can also make adjustments to names and other visual settings in an editing 
      software following generation if you forget to make those changes here. 

Assign Graph Roles
^^^^^^^^^^^^^^^^^^^^^^^
Following are instructions for telling STAGG how you would like your dependent variables graphed. STAGG utilizes 4 different 
arguments for graphing variables: xvar, pointdodge, facet1, and facet2. These arguments determine which of the independent 
variables in the model from the statistical analysis are plotted in the graphical output. 

1. Drop-down menus in the Graph Settings section of the subGUI are populated with the independent and covariate variables you selected in the left-hand table. Figure 14 shows what each graph role indicates: 

    * The Xvar variable determines which variable is shown on the x-axis of the plot. The points of the dependent variable are divided 
      into columns based on the categories of the variable selected for xvar.
    * The Pointdodge variable subdivides the xvar variable by the categories of the variable selected for pointdodge. Each of the 
      categories for this variable is shown as a different color on the plot and are labeled using a legend on the right-hand side of the plot. The points on the plot are dispersed into separate columns around the location of the corresponding xvar variable.
    * The Facet1 variable divides the overall plot into separate vertical panels with each panel column containing data from exactly 
      one of the categories selected as facet1.
    * The Facet2 variable divides the overall plot into separate horizontal panels with each panel row containing data from exactly one of 
      the categories selected as facet2. The combination of facet1 and facet2 can be used to create a grid of panels where each panel contains 
      the subset of data corresponding to one category from both the facet1 and facet2 variables.

2. Rules that must be followed:

    * STAGG requires an Xvar variable. All other graph settings are optional.
    * Each of the graphing variables are dependent on a variable being assigned to the higher variable. For example, you cannot 
      select a facet1 without having both xvar and pointdodge selected. Similarly, you cannot select a facet2 without have 
      xvar, pointdodge, and facet1 selected.

3. Once the variable(s) are assigned as desired, you have the ability to order the variables the way you would like them to appear on the graph. 
   For example, if you have two groups, control and experimental, and you want control animals to appear to the left of experimental animals, 
   you can order those in this subGUI. 

    * Click the ``…`` button to the right of the variable you would like to order. 
    * The popup in Figure 15 will appear and populate with all the values of that variable. With the value selected that you would 
      like to move, use the ``Up`` and ``Down`` navigation buttons to order your variable. 
    * Click ``OK`` to save that order. 
    
Additional Settings for Primary Model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Settings from the Graph Settings section will plot the primary model, but descriptive plots of the chosen dependent variables and 
feature plots of featured breathing are also available. These graphs are possible using the instructions below.

1. In the Additional Plots section of the subGUI you can choose to produce certain common variations of graphs for respiratory outcomes.

    * Our Feature Plots currently includes the option to plot apneas and sighs using your currently selected graph settings. 
       
        * From the dropdown menu, you can select Apneas, Sighs, All, or None. 

            #. None is the default setting and will result in no graphs of apneas or sighs. 
            #. Apneas or Sighs will result in a plot of either Apneas or Sighs using the xvar, pointdodge, facet1, and facet2 settings 
               from the Graph Settings section.
            #. All will result in both Apneas and Sighs graphs using the xvar, pointdodge, facet1, and facet2 settings from the Graph Settings section.

    * Poincare plots allow for visualization of variability within your data. Our Poincare plots currently includes options for Custom, All, or None. Poincare plots requires a pointdodge setting in the Graph Settings section.

        * None is the default and will result in no Poincare plots.
        * All will result in Poincare plots for all dependent variables where the pointdodge setting will label data points in 
          different colors based on the categories present in the pointdodge variable.
        * Custom will require the use of the Custom Settings pop-up box, which is outlined below.

    * Spectral plots allow for visualization of the frequency of different values in your data. Our Spectral plots currently includes options for Custom, All, or None. Poincare plots requires a pointdodge setting in the Graph Settings section.

        * None is the default and will result in no Spectral plots.
        * All will result in Spectral plots for all dependent variables where the pointdodge setting will label data points in 
          different colors based on the categories present in the pointdodge variable.
        * Custom will require the use of the Custom Settings pop-up box, which is outlined below.

2. In the Additional Models section of the subGUI you can choose to produce various transformations on your data to adjust as needed for 
   failed assumptions in the initial statistical test.

    * Transformations of your data might be required if the resulting QQ plots and residual plots from the linear mixed effects model 
      indicate that your data do not abide by the assumptions of the test. QQ plots and residuals are automatically generated for each 
      run of STAGG so you, or your statistician, can make these determinations after running the non-transformed values.

        * Our Transformations section currently allows for log (log10), natural log (ln), square root (sqrt), and Custom transformations (a combination
          of the listed transformations).

            #. Log10 will perform a log10 calculation on all dependent variable values in your dataset, re-run the linear mixed effects 
               model with Tukey post-hoc, and then re-graph these transformed data with the new statistical results.
            #. Ln will perform a natural log calculation on all dependent variable values in your dataset, re-run the linear mixed 
               effects model with Tukey post-hoc, and then re-graph these transformed data with the new statistical results.
            #. Sqrt will perform a square root calculation on all dependent variable values in your dataset, re-run the linear 
               mixed effects model with Tukey post-hoc, and then re-graph these transformed data with the new statistical results.
            #. Custom will require the use of the Custom Settings pop-up box, which is outlined below.

3. Poincare plots, spectral plots, and transformations settings can be assigned for all selected dependent variables via the drop-down menus. 
   However, custom settings is a pop-up within this subGUI that allows for custom configuration of optional plots and models for each dependent variable. 

    * If you want to assign different settings for different dependent variables, click Custom Settings to open a table where you 
      can define settings for each dependent variable.
        
        * Once inside the pop-up, you can use the check boxes to assign Poincaré and/ or spectral plots to the desired dependent variables.
        * You can use the dropdown menus in the Transformation column to assign specific transformations for each of your dependent variables.

    * You can also assign minimum and maximum y-axis values in the custom settings subGUI.

        * Note that if you choose a y axis minimum or maximum that data may be cut off on the resulting plot. Be sure to know the 
          range of your data before manually assigning these values as there is no messaging that will tell you if data is missing.
    
Additional Plots Configuration - *OPTIONAL*
------------------------------------------------
You can model data differently from your primary model using the bottom panel. These plots can include data from your primary model or 
be comprised entirely of different data. Following are instructions on creating optional graphs that will be in addition to all of the 
dependent graphs created by the primary model. For example, you may want to graph the weights of animals in each of your groups.

1. To create additional graphs, begin by entering your desired values into the first line in this table.

    * *Graph name* is the figure title. It is optional.
    * *Response variable* is the dependent variable. It is required.
    * *Xvar, Pointdodge, Facet1, and Facet2* follow the same rules here as they do for the main model. 
    * *Filter breaths?* asks whether or not you want to include data from all breaths (No), as opposed to just “good breaths” (Yes). 

        * It is important to note here that featured breathing, like apneas and sighs, does not always pass the breathing filters of BASSPRO. 
          If you want to include featured breathing that might not typically be considered “good” you may want to include all breaths rather 
          than applying the filter.

    * Y axis minimum and Y axis maximum let you set the min and max values for the response variable that will be shown in the figure.

        * Note that if you choose a y axis minimum or maximum that you might be missing data on the resulting plot. Be sure to know the 
          range of your data before manually assigning these values.

2. Click the  +  button to add a row to define another model.
3. To delete an additional model, select the row and click the  -  button to the right of the panel.
4. Save your settings.

    * Click ``Ok`` to save your settings in local memory – the actual csv files detailing the settings won’t be created until STAGG is launched.
    * Click ``Save As`` to open a file dialog to save your settings in a particular location for access later.
    * Either option of saving will result in a copy of these settings saved in the BASSPRO output folder for this run once launched.
