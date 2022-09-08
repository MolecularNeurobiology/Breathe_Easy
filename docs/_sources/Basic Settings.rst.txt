Basic Settings subGUI
*****************************
The basic settings are quantitative descriptors that define what a breath is throughout a plethysmography recording. 
We do not recommend using basic settings to perform any real filtering for “good” vs. “bad” breaths as this is done 
with the automated settings, or with user-selected breaths is performing a manual run. 

Also included in basic settings are details about your specific equipment that are necessary to ensure the refined 
variable calculations are accurate. Be sure to review these settings and compare to your respective equipment. 

1. Click the ``Basic Settings`` button (8). 
2. Upon opening, the subGUI will already be populated with default settings that should apply to all adult mouse whole 
   body plethysmography experiments conducted in the Ray lab (Figure 8). 
   
        .. figure:: Figures/Figure_8.png
           :width: 100%
        
           *Figure 8* Summary tab view of Basic Settings subGUI.

    * You can use the subGUI to make desired changes. 
    * The settings are divided among four tabs, including a summary table. In each tab the settings are displayed to the 
      left of a Reference panel. The ? button to the left of each setting’s label will populate the Reference panel with a 
      description of the setting and recommended default values. The Reset button to the right of the setting deletes any 
      changes the user made and reverts the value of that setting to its default value. 
    * We do not recommend the user adjust the settings in the Basic Settings Configuration subGUI EXCEPT to verify that the 
      Rig Specifications match those of the equipment used during the plethysmography recordings being analyzed (Figure 9).
       
         .. figure:: Figures/Figure_9.png
            :width: 100%
            
            *Figure 9* Rig specifications tab in Basic Settings subGUI with help menu displayed.

3. Save your settings.

     * Click ``Ok`` to save your settings in local memory – the actual csv files detailing the settings won’t be created until BASSPRO is launched.
     * Click ``Save As`` to open a file dialog to save your settings in a particular location for access later.
     * Either option of saving will result in a copy of these settings saved in the BASSPRO output folder for this run once launched.
