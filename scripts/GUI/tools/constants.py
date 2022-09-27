# -*- coding: utf-8 -*-
"""
CONSTANTS for use with BASSPRO-STAGG
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

Current contents include the list of anticipated BASSPRO_OUTPUT columns and 
the list of known continuous variables (a.k.a. BASSPRO_CONTINUOUS)

"""

BASSPRO_OUTPUT = [    
    'Mouse_And_Session_ID',
    'Breath_Inclusion_Filter',
    'Auto_Condition',
    'Man_Condition',
    'Exp_Condition',
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
    'Irreg_Score_Body_Temperature_Linear'
    ]

BASSPRO_CONTINUOUS = [
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
