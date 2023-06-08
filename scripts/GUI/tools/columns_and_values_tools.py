# -*- coding: utf-8 -*-
"""
columns_and_values_tools
Copyright (C) 2022  Christopher Scott Ward

created as a component of Breathe Easy

***
Breathe Easy - an automated waveform analysis pipeline
Copyright (C) 2022  
Savannah Lusk, Andersen Chang, 
Avery Twitchell-Heyne, Shaun Fattig, 
Christopher Scott Ward, Russell Ray.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
***



functions contained are intended to assist with identifying column names and 
unique values contained within.

3 functions are included:
1) --function to prepare column_names and values starting from SASSI output
    --JSON files--
    
    columns_and_values_from_jsons(
            paths_to_jsons,
            known_continuous = __SASSI_CONTINUOUS__,
            truncate_to = 10,
            truncate_all = False
            ):
2) --funtion to prepare column_names and values starting from SASSI input
    --metadata, auto_settings, manual_settings (all as pandas.DataFrames)--
    
    columns_and_values_from_settings(
            metadata,
            auto_settings = None,
            manual_settings = None,
            known_continuous = __SASSI_CONTINUOUS__,
            truncate_to = 10,
            truncate_all = False
            ):
3) --function to assist with truncating the list of unique values if the 
    initial extraction of values was larger than needed for subsequent uses
    
    truncate_values_from_columns(
            input_dict,
            known_continuous = __SASSI_CONTINUOUS__,
            truncate_to = 10,
            truncate_all = True
            ):



"""

import pandas

#%% CONSTANTS

__SASSI_CONTINUOUS__ = [
    'Breath Number',
    'Timestamp_Inspiration',
    'Timestamp_Expiration',
    'Inspiratory_Duration',
    'Irreg_Score_Inspiratory_Duration',
    'Expiratory_Duration',
    'Irreg_Score_Expiratory_Duration',
    'Tidal_Volume_uncorrected',
    'Irreg_Score_Tidal_Volume_uncorrected',
    'Tidal_Volume_exhale_uncorrected',
    'Irreg_Score_Tidal_Volume_exhale_uncorrected',
    'VT__Tidal_Volume_corrected',
    'Irreg_Score_VT__Tidal_Volume_corrected',
    'VTpg__Tidal_Volume_per_gram_corrected',
    'Irreg_Score_VTpg__Tidal_Volume_per_gram_corrected',
    'Peak_Inspiratory_Flow',
    'Irreg_Score_Peak_Inspiratory_Flow',
    'Peak_Inspiratory_Flow_corrected',
    'Irreg_Score_Peak_Inspiratory_Flow_corrected',
    'Peak_Expiratory_Flow',
    'Irreg_Score_Peak_Expiratory_Flow',
    'Peak_Expiratory_Flow_corrected',
    'Irreg_Score_Peak_Expiratory_Flow_corrected',
    'Breath_Cycle_Duration',
    'Irreg_Score_Breath_Cycle_Duration',
    'VE__Ventilation',
    'Irreg_Score_VE__Ventilation',
    'VEpg__Ventilation_per_gram',
    'Irreg_Score_VEpg__Ventilation_per_gram',
    'VO2',
    'Irreg_Score_VO2',
    'VO2pg',
    'Irreg_Score_VO2pg',
    'VCO2',
    'Irreg_Score_VCO2',
    'VCO2pg',
    'Irreg_Score_VCO2pg',
    'VEVO2',
    'Irreg_Score_VEVO2',
    'VF',
    'Irreg_Score_VF',
    'TT_per_TV',
    'Irreg_Score_TT_per_TV',
    'TT_per_TVpg',
    'Irreg_Score_TT_per_TVpg',
    'O2_per_Air__VO2_x_TT_per_TV_',
    'Irreg_Score_O2_per_Air__VO2_x_TT_per_TV_',
    'Apnea',
    'Irreg_Score_Apnea',
    'Sigh',
    'Irreg_Score_Sigh',
    'DVTV',
    'Irreg_Score_DVTV',
    'per500',
    'Irreg_Score_per500',
    'mav',
    'Irreg_Score_mav',
    'O2_concentration',
    'Irreg_Score_O2_concentration',
    'CO2_concentration',
    'Irreg_Score_CO2_concentration',
    'Chamber_Temperature',
    'Irreg_Score_Chamber_Temperature',
    'O2_uncalibrated',
    'Irreg_Score_O2_uncalibrated',
    'CO2_uncalibrated',
    'Irreg_Score_CO2_uncalibrated',
    'Chamber_Temp_uncalibrated',
    'Irreg_Score_Chamber_Temp_uncalibrated',
    'Body_Temperature_Linear',
    'Irreg_Score_Body_Temperature_Linear',
    ]



#%%

def columns_and_values_from_jsons(
        paths_to_jsons,
        known_continuous = __SASSI_CONTINUOUS__,
        truncate_to = 10,
        truncate_all = False
        ):
    
    yield 'loading jsons...'

    # load jsons
    main_df = pandas.concat(
        [pandas.read_json(i) for i in paths_to_jsons]
        )
    
    yield 'reading cols...'

    # initialize output dict
    output = {}
    # iterate through columns
    for col in main_df.columns:
        output[col] = list(main_df[col].unique())


    i = 1
    for col in output:
        yield f"Column {col} ({i}/{len(output)})"
        i += 1
        
        if col in known_continuous:
        
            output[col] = output[col][0:min(truncate_to,len(output[col]))]
        elif truncate_all == True:
        
            output[col] = output[col][0:min(truncate_to,len(output[col]))]

    return output


def columns_and_values_from_settings(
        metadata,
        auto_settings = None,
        manual_settings = None,
        known_continuous = __SASSI_CONTINUOUS__,
        truncate_to = 10,
        truncate_all = False
        ):

    output = {}

    if auto_settings is not None:
        for col in auto_settings:
            if 'AUTO_IND_' in col:
                output[col] = list(auto_settings[col].unique())
    if manual_settings is not None:
        for col in manual_settings:
            if 'MAN_IND_' in col:
                output[col] = list(manual_settings[col].unique())
    for col in metadata:
        output[col] = list(metadata[col].unique())
    for col in known_continuous:
        output[col] = ['?float?',1.1,2,2,3.3,4.4,5.5]
    for col in output:
        
        if truncate_all == True:
        
            output[col] = output[col][0:min(truncate_to,len(output[col]))]
    return output
    

def truncate_values_from_columns(
        input_dict,
        known_continuous = __SASSI_CONTINUOUS__,
        truncate_to = 10,
        truncate_all = True
        ):
    
    output = {}
    
    for col in input_dict:
        
        if col in known_continuous:
            
            output[col] = input_dict[col][
                0:min(truncate_to,len(input_dict[col]))
                ]
        
        elif truncate_all == True:
        
            output[col] = input_dict[col][
                0:min(truncate_to,len(input_dict[col]))
                ]
    return output