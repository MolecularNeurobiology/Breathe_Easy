# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 14:57:06 2022

@author: wardc
"""
#%% import libraries
import pandas
import traceback
import difflib


#%% define functions
def convert_timestamps_to_autosections(list_of_files):
    """
    function will scan through files in the [list_of_files] to collect 
    timestamps. 

    Parameters
    ----------
    list_of_files : list of filepaths (signal files)
        list of files (1 or more entries)

    Returns
    -------
    Pandas DataFrame that provides a suggested template for creation of an 
    AutoSections File
    
    if no timestamps found or no files provided then None is returned

    """
    # return None if no files provided
    if len(list_of_files) == 0:
        return None
    
    try:
        # initialize timestamps list
        timestamps = []   
        # iterate through list of files
        for filepath in list_of_files:
            # print(f'checking file for timestamps: {filepath})
            # extract timestamps that are present in the file
            with open(filepath,'r') as openfile:
                for line in openfile:
                    # timestamp indicator is '#* ' substring
                    if '#* ' in line:
                        # generate timestamp substring (trim leading '#* ' and ...
                        # trailing ' \n')
                        candidate_timestamp = line.split('#* ')[1].split(' \n')[0]
                        if candidate_timestamp not in timestamps:
                            # print(
                            #   f'found new timestamp: {candidate_timestamp}
                            #   )
                            timestamps.append(candidate_timestamp)
    except Exception as e:
        print(f'{type(e).__name__}: {e}')
        print(traceback.format_exc())
        return None
      
    
    # populate a template dataframe in the AutoSections style
    try:
        autosections_dict = {
            'Alias': [i for i in timestamps],
            'Cal Seg': ['' for i in timestamps],
            'AUTO_IND_INCLUDE': [1 for i in timestamps],
            'AUTO_IND_CAL': [0 for i in timestamps],
            'AUTO_IND_GAS_CAL': [0 for i in timestamps],
            'AUTO_IND_GAS': ['' for i in timestamps],
            'AUTO_IND_INJECTION':['' for i in timestamps],
            'CAL_O2': ['' for i in timestamps],
            'CAL_CO2': ['' for i in timestamps],
            'Midpoint': [0 for i in timestamps],
            'min_TT': [0.1 for i in timestamps],
            'max_TT': [5 for i in timestamps],
            'max_DVTV': [0.25 for i in timestamps],
            'Startpoint': [0 for i in timestamps],
            'Endpoint': [0 for i in timestamps],
            'max_pX': [0.1 for i in timestamps],
            'X': [500 for i in timestamps],
            'max_calibrated_TV': ['off' for i in timestamps],
            'max_VEVO2': ['off' for i in timestamps],
            'include_apnea': [0 for i in timestamps],
            'include_sigh': [0 for i in timestamps],
            'include_high_chamber_temp': [0 for i in timestamps],
            'vol_mov_avg_drift': [1 for i in timestamps],
            'min_TV': [0 for i in timestamps],
            'min_CO2': [-1 for i in timestamps],
            'max_CO2': [110 for i in timestamps], 
            'min_O2': [-1 for i in timestamps],
            'max_O2': [110 for i in timestamps],
            'min_bout': [10 for i in timestamps],
            'within_start': [43200 for i in timestamps],
            'within_end': [43200 for i in timestamps],
            'after_start': [0 for i in timestamps],
            'before_end': [0 for i in timestamps],
            'Key': [i for i in timestamps]
            }
        autosections_df = pandas.DataFrame(data = autosections_dict)
    
        #%% try to detect if calibration information can be inferred and update
        volume_calibration_timestamps = [
            i for i in timestamps if 'cal' in i.lower()
            ]
        cal_seg = {}
        for i in timestamps:
            cal_seg[i] = difflib.get_close_matches(
                i.lower(),
                volume_calibration_timestamps,
                1,
                0.1
                )[0]
            
        for i in cal_seg:
            autosections_df.loc[
                autosections_df.Alias == i,
                'Cal Seg'
                ] = cal_seg[i]
        
        for i in volume_calibration_timestamps:
            autosections_df.loc[
                autosections_df.Alias == i,
                [
                    'AUTO_IND_INCLUDE',
                     'AUTO_IND_CAL',
                     'min_TT',
                     'max_TT',
                     'max_DVTV',
                     'max_pX',
                     'X',
                     'vol_mov_avg_drift'
                     ]
                ] = [
                    0,
                    1,
                    0.2,
                    1,
                    0.2,
                    1,
                    500,
                    0.5
                    ]
                    
    #%%
    except Exception as e:
        print(f'{type(e).__name__}: {e}')
        print(traceback.format_exc())
        return None
    
    # return the pandas dataframe
    return autosections_df
    

    
    
    
    
    
    