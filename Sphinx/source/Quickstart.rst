Quickstart
===========
There are a number of steps to preparing to run Breathe Easy. Below is a brief outline of 
the steps to set everything up within the GUI. Detailed instructions are linked within the 
outline and in the following sections of this guide. 

#. :ref:`Set input and output <Initialize: Input and Output for BASSPRO>`. 

    * Set output folder for all processes in Breathe Easy. Individual folders will be automatically generated for each run within the selected folder.
    * Select input signal files that you would like analyzed. :ref:`Help preparing data for analysis <Prepping Data>`.

#. :ref:`Review data for appropriate comments <Optional Data Validation>`. 

    * You may need to make corrections or adjustments based on the results of this check:

        * :ref:`Missing Timestamp <Missing timestamps>`
        * :ref:`Duplicate Timestamp <Duplicate timestamps>`
        * :ref:`Novel Timestamp <Novel timestamps>`

#. :ref:`Configure and load metadata for each animal and experiment <Metadata Generation>`. 
#. Next you will need to configure settings for BASSPRO’s selection of breaths from your recordings. 
   There are 3 different ways you can run BASSPRO, and each has a different type of configuration/ settings file associated with it. 

    * Automated run: BASSPRO will select breaths using your settings. 
      You will need 1) :ref:`Basic Settings <Basic Settings subGUI>` and 2) :ref:`Automated Settings <Automated Settings subGUI>`. 
    * Manual run: BASSPRO will select breaths that were manually selected by the user. 
      This will also require an additional export from your recording software that includes timestamps for your manual selections. 
      You will need 1) :ref:`Basic Settings <Basic Settings subGUI>` and 2) a :ref:`Manual Selections File <Manual Settings Configuration>`.
    * Automated and Manual run: BASSPRO will perform two iterations of breath selection where one set of breaths will be 
      those selected manually by the user and the other will be breaths that were selected by an automated run of BASSPRO 
      with the same files. You will need 1) :ref:`Basic Settings <Basic Settings subGUI>`, 2) :ref:`Automated Settings <Automated Settings subGUI>`, 
      and 3) a :ref:`Manual Selections File <Manual Settings Configuration>`.

        .. note::
           If you have existing configuration files for any or all of these settings, then you can click the 
           Select BASSPRO settings files button (9) to select those files and load them in without using the subGUIs.
   
#. From this point you can continue on to establish STAGG settings to allow a :ref:`full run of the program <Full Run of BASSPRO-STAGG>`. 
   Or you can :ref:`run BASSPRO <Running BASSPRO>`, then :ref:`run STAGG <Running STAGG>` separately. 

    * Running BASSPRO independently allows you to interrogate whether the data produced enough “quality” breaths 
      to allow for an accurate comparison between your groups. We recommend this kind of run if it is your first 
      time running your data through the pipeline. 


