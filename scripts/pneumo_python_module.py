# -*- coding: utf-8 -*-
"""
BASSPRO
Breathing Analysis Selection and Segmentation 
for Plethysmography and Respiratory Observations

built as part of the Russell Ray Lab Breathing And Physiology Analysis Pipeline

***
Plethysmography Analysis Pipeline in R with
Python Launcher and Analysis Interface Node
"PAPR PLAIN"

***
Automated Breathcaller created by Christopher S Ward (C) 2020
updates include contributions from Avery Twitchell-Heyne and feedback from
Russell Ray, Savannah Lusk, and Andersen Chang

'Breathcaller' function adapted from prior efforts by Christopher S Ward
'WardBreathcaller' for python 3 (C) 2015,
'Breath Caller' for python 2 (C) 2014
'Breathing Analysis' for Matlab (C) 2011

***
Command Line Arguments
    '-i', help='Path containing signal files for input'
    '-f', action='append', help='names of signal files,\
            declare multiple times to build a list of files'
    '-o', help='Path to directory for output files'
    '-p', help='Path to Analysis Parameters File'
    '-a', help='Path to Animal MetaData File'
    '-m', help='Path to Manual Selection File'
        *optional, to explicitly indicate none provided, use NONE as the value
    '-c', help='Path to Automated Criteria File'
        *optional, to explicitly indicate none provided, use NONE as the value

***
"""
__version__ = '36.0.4'

"""
# v36.0.0 README
    v36 is a revision that updates a few areas, versioning moving forward
    will implement a modified nomenclature X.Y.Z
        X = Major Release Update - major feature/bugfix/workflow update
        Y = Minor Release Update - feature update
        Z = Micro Release Update - bug fix
        
    
# v35 README
    v35 is a major revision that aims to refactor to improve readability
    style of functions/variable naming as well as address structural issues
    for the workflow of the script. It should incorporate several of the
    updates from prior versions as well as the feature/fix goals from v34

    *Fixed offset being applied to PIF/PEF calculations (previous version
     offset values by 1 sampling interval - should be correct, minimal
     effective change compared to prior calculations though)
    *Fixed calculation of rolling averages for apnea and sigh scoring
     (previous version used an inclusive rolling average, update uses a sliding
     window that ommits the centered breath - which is the intended
     calculation)
    *logging now uses the python logging library - which should provide more
     informative logging files including timestamped information
    *updated temperature repair cutoffs, two stage repair now performed and
     toggled by the user. enhanced repair uses - median +/- 2x 25-75 range
     to generate candidate samples for repair

    *Done - add breathcaller version as an output parameter
    *Done - update output saving options - specify encoding of csv
    *Done - revised how the manual selections are imported - warning should be
        provided now if shared aliases lead to over_writing of the settings
    *jamboree updates...
        *Done - if manual selections include calibration info - those override 
            auto for calculations
        *Done - update analysis parameters to be a file rather than a series of
            arguments - this also permits greater flexibility for future 
            addition of new parameters
        *Done - if a signal file includes doesn't include a cal condition 
            in an auto-criteria file analysis will move on to the next one
            (this permits use of a generic auto-criteria file for multiple
             experiments)
        *Done - improve error logging using python logging module, traceback 
            should be provided if a catastrophic error occurs
        *Done - detection of common suboptimal settings and inclusion in log
            (i.e. bad gas calibration settings)
        Done - *create setting to allow user to specify if multi outputs needed
            (i.e. all breath, and aggregate are optional)
        *Done - refactored code to help clean out old unused code, improve variable
            naming, get closer to PEP8 guidelines
        *Done - add body temperature vs chamber temperature filter -
            bad breath if chamber temp > body temp
    *VO2 - consider quality measures (VO2 slope, VO2 variation,
                                      VO2 becoming negative?)
    



!!!
Style Suggestions

CONSTANT
name_of_function(local_variable_1, local_variable_2)
Main_Variable_1 = ...
ClassName()


!!!
Automated Selection of Breaths for Analysis - Heirarchy
Timestamp_Intervals
Blocks
Sections
Breaths
Segments


!!!
List of Expected Output Columns

<BREATHCALLER_OUTPUTS>
    <p>Mouse_And_Session_ID</p>
    <p>Breath_Inclusion_Filter</p>
    <p>Auto_Condition</p>
    <p>Man_Condition</p>
    <p>Exp_Condition</p>
    <p>Breath Number</p>
    <p>Timestamp_Inspiration</p>
    <p>Timestamp_Expiration</p>
    <p>Inspiratory_Duration</p>
    <p>Irreg_Score_Inspiratory_Duration</p>
    <p>Expiratory_Duration</p>
    <p>Irreg_Score_Expiratory_Duration</p>
    <p>Tidal_Volume_uncorrected</p>
    <p>Irreg_Score_Tidal_Volume_uncorrected</p>
    <p>Tidal_Volume_exhale_uncorrected</p>
    <p>Irreg_Score_Tidal_Volume_exhale_uncorrected</p>
    <p>VT__Tidal_Volume_corrected</p>
    <p>Irreg_Score_VT__Tidal_Volume_corrected</p>
    <p>VTpg__Tidal_Volume_per_gram_corrected</p>
    <p>Irreg_Score_VTpg__Tidal_Volume_per_gram_corrected</p>
    <p>Peak_Inspiratory_Flow</p>
    <p>Irreg_Score_Peak_Inspiratory_Flow</p>
    <p>Peak_Inspiratory_Flow_corrected</p>
    <p>Irreg_Score_Peak_Inspiratory_Flow_corrected</p>
    <p>Peak_Expiratory_Flow</p>
    <p>Irreg_Score_Peak_Expiratory_Flow</p>
    <p>Peak_Expiratory_Flow_corrected</p>
    <p>Irreg_Score_Peak_Expiratory_Flow_corrected</p>
    <p>Breath_Cycle_Duration</p>
    <p>Irreg_Score_Breath_Cycle_Duration</p>
    <p>VE__Ventilation</p>
    <p>Irreg_Score_VE__Ventilation</p>
    <p>VEpg__Ventilation_per_gram</p>
    <p>Irreg_Score_VEpg__Ventilation_per_gram</p>
    <p>VO2</p>
    <p>Irreg_Score_VO2</p>
    <p>VO2pg</p>
    <p>Irreg_Score_VO2pg</p>
    <p>VCO2</p>
    <p>Irreg_Score_VCO2</p>
    <p>VCO2pg</p>
    <p>Irreg_Score_VCO2pg</p>
    <p>VEVO2</p>
    <p>Irreg_Score_VEVO2</p>
    <p>VF</p>
    <p>Irreg_Score_VF</p>
    <p>TT_per_TV</p>
    <p>Irreg_Score_TT_per_TV</p>
    <p>TT_per_TVpg</p>
    <p>Irreg_Score_TT_per_TVpg</p>
    <p>O2_per_Air__VO2_x_TT_per_TV_</p>
    <p>Irreg_Score_O2_per_Air__VO2_x_TT_per_TV_</p>
    <p>Apnea</p>
    <p>Irreg_Score_Apnea</p>
    <p>Sigh</p>
    <p>Irreg_Score_Sigh</p>
    <p>DVTV</p>
    <p>Irreg_Score_DVTV</p>
    <p>per500</p>
    <p>Irreg_Score_per500</p>
    <p>mav</p>
    <p>Irreg_Score_mav</p>
    <p>O2_concentration</p>
    <p>Irreg_Score_O2_concentration</p>
    <p>CO2_concentration</p>
    <p>Irreg_Score_CO2_concentration</p>
    <p>Chamber_Temperature</p>
    <p>Irreg_Score_Chamber_Temperature</p>
    <p>O2_uncalibrated</p>
    <p>Irreg_Score_O2_uncalibrated</p>
    <p>CO2_uncalibrated</p>
    <p>Irreg_Score_CO2_uncalibrated</p>
    <p>Chamber_Temp_uncalibrated</p>
    <p>Irreg_Score_Chamber_Temp_uncalibrated</p>
    <p>Body_Temperature_Linear</p>
    <p>Irreg_Score_Body_Temperature_Linear</p>
</BREATHCALLER_OUTPUTS>

"""

# %% import libraries
import logging
import re
import datetime
import numpy
import pandas
import argparse
from scipy import stats
from scipy import signal
import tkinter.filedialog
import tkinter
import math
import statistics
import os
import csv
import sys

# %% define functions

def gui_open_filename(kwargs={}):
    """
    

    Parameters
    ----------
    kwargs : Dict, optional
        The default is {}.
        *Function calls on tkFileDialog and uses those arguments
      ......
      (declare as a dictionairy)
      {"defaultextension":'',"filetypes":'',"initialdir":'',...
      "initialfile":'',"multiple":'',"message":'',"parent":'',"title":''}
      ......

    Returns
    -------
    output_text : String
        String describing the path to the file selected by the GUI.
        
    """

    root = tkinter.Tk()
    output_text = tkinter.filedialog.askopenfilename(
        **kwargs)
    root.destroy()
    return output_text


def gui_open_filenames(kwargs={}):
    """
    

    Parameters
    ----------
    kwargs : Dict, optional
        The default is {}.
        *Function calls on tkFileDialog and uses those arguments
      ......
      (declare as a dictionairy)
      {"defaultextension":'',"filetypes":'',"initialdir":'',...
      "initialfile":'',"multiple":'',"message":'',"parent":'',"title":''}
      ......

    Returns
    -------
    output_text : List of Strings
        List of Strings describing the paths to the files selected by the GUI.
    
    """

    root = tkinter.Tk()
    output_text_raw = tkinter.filedialog.askopenfilenames(
        **kwargs)
    output_text = root.tk.splitlist(output_text_raw)
    root.destroy()
    return output_text


def gui_directory(kwargs={}):
    """
        Parameters
    ----------
    kwargs : Dict, optional
        The default is {}.
        *Function calls on tkFileDialog and uses those arguments
          ......
          (declare as a dictionairy)
          {"defaultextension":'',"filetypes":'',"initialdir":'',...
          "initialfile":'',"multiple":'',"message":'',"parent":'',"title":''}
          ......

    Returns
    -------
    output_text : String
        Returns the directory path selected by the GUI.

    """

    root = tkinter.Tk()
    output_text = tkinter.filedialog.askdirectory(
        **kwargs)
    root.destroy()
    return output_text


def get_avg(input_list):
    """
    returns the average of the values in a list

    Parameters
    ----------
    input_list : list of numerical values (i.e. int, float)

    Returns
    -------
    TYPE
    arithmatic average of the values in a list
    """

    try:
        return sum(input_list)/len(input_list)
    except:
        return 'NAN'


def get_med(inputlist):
    """
    returns the median of the values in a list

    Parameters
    ----------
    inputlist : list of numerical values (i.e. int, float)


    Returns
    -------
    numeric value if median can be calculated, otherwise NAN

    """

    try:
        return statistics.median(inputlist)
    except:
        return 'NAN'


def log_info_from_dict(local_logger, input_dict, log_prefix=''):
    """
    creates log entries from dict input

    Parameters
    ----------
    local_logger : instance of a logging.logger

    input_dict : dict {k:message,...}
        dict contents will be used to populate log entries

    log_prefix : string, optional
        The default is ''. string is placed ahead of dict values in the
        log entry

    Returns
    -------
    None.

    """

    for k in input_dict:
        local_logger.info('{}{} : {}'.format(log_prefix, k, input_dict[k]))


def convert_seconds_to_time_text(seconds):
    """
    creates a string summarizing the time provides in hrs, mins, secs

    Parameters
    ----------
    seconds : datetime.timedelta
        an interval of time

    Returns
    -------
    string
        string summarizing the time in hrs, mins, secs.

    """

    hrs = int(seconds.total_seconds()/3600)
    mins = int((seconds.total_seconds() % 3600)/60)
    secs = int(seconds.total_seconds() % 60)
    return '{} hrs {} mins {} secs'.format(hrs, mins, secs)


def get_animal_metadata(csvpath):
    """
    returns a dictionary extracted from an 'Animal Metadata' csv file
    note, PlyUID is a CASE-SENSITIVE REQUIRED column

    Parameters
    ----------
    csvpath : string
        path to file containing Animal_Metadata

    Returns
    -------
    animal_metadata : dict
        dict containing metadata associated with animal (indexed by PlyUID)

    """

    animal_metadata = {}
    text_list = []
    if csvpath == "" or csvpath == None:
        return animal_metadata
    else:
        with open(csvpath, 'r', encoding='UTF-8') as file:
            data = csv.DictReader(file, delimiter=",")
            for row in data:
                text_list.append(row)
        for row in text_list:
            animal_metadata[row['PlyUID']] = {}
            for k in row:
                try:
                    animal_metadata[row['PlyUID']][k] = float(row[k])
                except:
                    animal_metadata[row['PlyUID']][k] = row[k]
    return animal_metadata


def calculate_time_remaining(
        cur_file_num,
        tot_file_num,
        first_file_start,
        cur_file_start
        ):
    """
    estimates time remaining based on time used to complete analyses so far

    Parameters
    ----------
    cur_file_num : int
        iteration number for the current file
    tot_file_num : int
        total number of files submitted for analysis
    first_file_start : datetime
        timestamp at the start of analysis of the first file
    cur_file_start : datetime
        timestamp at the start of analysis for the current file

    Returns
    -------
    datetime.timedelta
        estimated time remaining to complete analysis of all files

    """
    
    time_elapsed = cur_file_start-first_file_start
    estimated_total_time = time_elapsed / cur_file_num * tot_file_num
    estimated_time_remaining = estimated_total_time - time_elapsed
    return estimated_time_remaining


def extract_muid_plyuid(
        filename,
        animal_metadata,
        extension='txt',
        local_logger=None):
    """
    extracts muid and plyuid information from a filename provided in
    MUID_PLYUID.txt format

    Parameters
    ----------
    filename : string
        filename, expected as MUID_PLYUID.txt format

    animal_metadata : dict
        dict indexed by 'PlyUID' containing animal metadata

    extension : string
        extension of the file, default is txt

    Returns
    -------
    muid : string

    plyuid : string

    """

    muid_plyuid_re = re.compile(
        '(?P<muid>.+?(?=_|\.txt))_?(?P<plyuid>.*).{}'.format(
            extension
            )
        )
    parsed_filename = re.search(muid_plyuid_re, os.path.basename(filename))
    muid = parsed_filename['muid']
    plyuid = parsed_filename['plyuid']

    if plyuid == '':
        plyuid = resolve_plyuid(muid, animal_metadata,
                                local_logger=local_logger)

    return muid, plyuid


def resolve_plyuid(muid, animal_metadata, local_logger=None):
    """
    

    Parameters
    ----------
    muid : string
        serial identifier for mouse/subject
    animal_metadata : dict
        dict indexed by 'PlyUID' containing animal metadata
    local_logger : instance of logging.logger

    Raises
    ------
    Exception
        exceptions raised if insufficient information to 
        link a file to a plyuid. (no entry in metadata, ambiguous entries)

    Returns
    -------
    plyuid : string
        serial identifier for data collection event 
        (plethysmography session id)
    """
    
    # create muid dict
    muid_dict = {}
    for k in animal_metadata:
        if k in muid_dict:
            muid_dict[animal_metadata[k]['MUID']].append(k)
        else:
            muid_dict[animal_metadata[k]['MUID']] = [k]

    # check if 1 and only 1 entry can be found
    if muid not in muid_dict:
        local_logger.error(
            'No entry for animal in Metadata',
            )
        raise Exception(
            '!!! No entry for animal in Metadata !!!'
            )
    elif len(muid_dict[muid]) != 1:
        local_logger.error(
            'muid is ambiguous without plyuid'
            )
        raise Exception(
            '!!! MUID is ambiguous without PLYUID !!!'
            )
    plyuid = muid_dict[muid][0]
    return plyuid


def load_signal_data(filename, local_logger):
    """
    creates a dataframe containing plethysmography signal data
    includes calls to several other functions that are required for proper
    parsing of an exported lab chart signal file

    Parameters
    ----------
    filename : string
        path to file containing signal data
    local_logger : instance of logging.logger


    Returns
    -------
    signal_data_assembled : pandas.DataFrame
        dataframe containing contents of signal file (merged into a single
        dataframe if multiple blocks are present)

    """
    Header_Tuples = extract_header_type(filename)
    header_locations = extract_header_locations(
        filename,
        local_logger=local_logger
        )
    signal_data_pieces = read_exported_labchart_file(
        filename,
        header_locations,
        header_tuples=Header_Tuples
        )
    signal_data_assembled = merge_signal_data_pieces(signal_data_pieces)
    return signal_data_assembled


def extract_header_type(filename,rows_to_check = 20):
    """
    gathers information regarding the header format/column contents present
    in an exported lab chart signal file (assumes set-up is in line with
    Ray Lab specifications)

    Parameters
    ----------
    filename : string
        path for file containing signal data

    Returns
    -------
    header_tuples : list of tuples
        list of tuples specifying ([column name],[datatype])

    """
    
    with open(filename,'r') as opfi:
        # check 1st [rows_to_check] rows to see if header is expected to 
        # include date column with data as well as data containing columns
    
        ts_columns = ['ts']
        for i in range(rows_to_check):
            cur_line = opfi.readline()
            if "DateFormat=	M/d/yyyy" in cur_line:
                ts_columns = ['ts','date']
            else:
                pass
                
            if "ChannelTitle=" in cur_line:
                header_columns = \
                    cur_line.lower().replace('\n','').split('\t')[1:]
                while '' in header_columns:
                    header_columns.remove('')
            else:
                pass
            
    # special_columns describe columns that should not be 
    # processed as float
    special_columns = {'date':str,'comment':str}
    
    # rename_columns describe columns that use a different alias when
    # handled by this script in subsequent steps
    rename_columns = {
        'breathing':'vol',
        'oxygen':'o2',
        'oxygen ':'o2',
        'co2':'co2',
        'tchamber':'temp',
        'channel 5':'ch5',
        'channel 6':'ch6',
        'channel 7':'ch7',
        'channel 8':'ch8',
        'vent flow':'flow'
        }
    
    combined_columns = ts_columns+\
        [
            rename_columns[j] if j in rename_columns else j \
            for j in header_columns
        ]+\
        ['comment']
    
    header_tuples = [
                (j.lower(),str) \
                if j in special_columns \
                else (j.lower(),float) \
                for j in combined_columns
                ]

    return header_tuples


def extract_header_locations(
        filename,
        header_text_fragment='Interval=',
        local_logger=None):
    """
    gathers information regarding the locations of header information
    throughout a signal file - needed if files may contain multiple recording
    blocks

    Parameters
    ----------
    filename : string
        path to file containing signal data
    header_text_fragment : string, optional
        string that is present in header lines. The default is 'Interval='.
    local_logger : instance of logging.logger, optional
        The default is None (i.e. no logging)

    Returns
    -------
    headers : list
        list of rows in the datafile that indicate header content present
    """
    
    headers = []
    i = 0
    with open(filename, 'r') as opfi:
        for line in opfi:
            if header_text_fragment in line:
                if local_logger != None:
                    local_logger.info(
                        'Signal File has HEADER AT LINE: {}'.format(i)
                        )
                headers.append(i)
            i += 1
    return headers


def read_exported_labchart_file(
        lc_filepath,
        header_locations,
        header_tuples,
        delim='\t',
        rows_to_skip=6
        ):
    """
    collects data from an exported lab chart file and returns a list of
    dataframes (in order) containing the extracted contents of the signal file

    Parameters
    ----------
    lc_filepath : string
        path to file containing signal data
    header_locations : list of integers
        list describing the locations of headers throughout a signal file
    header_tuples : list of tuples
        list of tuples specifying ([column name],[datatype])
    delim : string, optional
        delimiter used. The default is '\t'.
    rows_to_skip : integer, optional
        the number of rows present in the header that should be skipped
        to get to the location containing data. The default is 6.

    Returns
    -------
    df_list : list of pandas.DataFrames
        list of dataframes containing signal data

    """
    df_list = []

    for i in range(len(header_locations)):
        # case if only one header
        if len(header_locations) == 1:
            df_list.append(
                pandas.read_csv(
                    lc_filepath,
                    sep=delim,
                    names=[i[0] for i in header_tuples],
                    skiprows=rows_to_skip+header_locations[i],
                    dtype=dict(header_tuples)
                    )
                )
        else:
            # case if not last section
            if i+1 < len(header_locations):
                df_list.append(
                    pandas.read_csv(
                        lc_filepath,
                        sep=delim,
                        names=[i[0] for i in header_tuples],
                        skiprows=rows_to_skip+header_locations[i],
                        nrows=header_locations[i+1]-header_locations[i]-6,
                        dtype=dict(header_tuples)
                        )
                    )
            # case if last section of multisection file
            else:
                df_list.append(
                    pandas.read_csv(
                        lc_filepath,
                        sep=delim,
                        names=[i[0] for i in header_tuples],
                        skiprows=rows_to_skip+header_locations[i],
                        dtype=dict(header_tuples)
                        )
                    )
    return df_list


def merge_signal_data_pieces(df_list):
    """
    merges multiple blocks contained in a list of dataframes into a single
    dataframe (current behavior will override timestamp information to
    place subsequent blocks of data using the next sequential timestamp)

    Parameters
    ----------
    df_list : list of pandas.DataFrames
        list of dataframes containing signal data

    Returns
    -------
    merged_data : pandas.DataFrame
        dataframe containing signal data

    """
    # merge into single dataframe
    merged_data = pandas.DataFrame()
    for piece_number in range(len(df_list)):
        if piece_number != 0:
            # revise timestamp so that multiblock data fit into the next
            # consecutive timestamp - labchart file may reset each block to 0
            # or each block may track time relative to experiment start
            ts_minus = df_list[piece_number]['ts'].min()
            ts_add = df_list[piece_number-1]['ts'].max() + \
                df_list[0]['ts'][2]-df_list[0]['ts'][1]
        else:
            ts_minus = 0
            ts_add = 0
        df_list[piece_number].loc[:, 'ts'] = df_list[piece_number]['ts'] + \
            ts_add - ts_minus
        merged_data = merged_data.append(
            df_list[piece_number], ignore_index=True
            )
    return merged_data


def apply_voltage_corrections(
        input_df, 
        factor_dict, 
        column_tuples,
        local_logger=None
        ):
    """

    Parameters
    ----------
    input_df : pandas.DataFrame
        dataframe to modify by appending new columns
    factor_dict : dict
        simple dict containing factors to use for modification
    column_tuples : list of tuples, each tuple containing 3 strings
        [(
            [source column in input_df],
            [destination column in input_df],
            [key in factor_dict for factor]
             )]
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    df : dataframe that can be used to replace input_df

    """
    df = input_df.copy()

    for source_column, dest_column, factor_key in column_tuples:
        if source_column in df:
            df[dest_column] = df[source_column] * \
                float(factor_dict[factor_key])
        else:
            if local_logger is not None:
                local_logger.info(
                    f'{source_column} not present in signal data '+\
                    '- no voltage correction applied'
                    )
    return df


def check_animal_metadata_and_analysis_parameters(
        animal_metadata,
        plyuid,
        analysis_parameters,
        parameter,
        default,
        local_logger=None):
    """
    

    Parameters
    ----------
    
    animal_metadata : dict
        dict indexed by 'PlyUID' containing animal metadata
    plyuid : string
        serial identifier for data collection event 
        (plethysmography session id)

    analysis_parameters : dict
        dictionary containing settings for analysis
    parameter : string
        name of the parameter being checked
    default : string
        default value for parameter
    local_logger : instance of logging.logger (optional)
    
    Returns
    -------
    checked_value : string

    """

    if animal_metadata[plyuid].get(parameter) is not None and \
        animal_metadata[plyuid].get(parameter) != '':
            checked_value = animal_metadata[plyuid][parameter]
            if analysis_parameters.get(parameter) is not None and \
                analysis_parameters.get(parameter) != '' and \
                local_logger is not None:
                    local_logger.warning(
                        'animal specific setting for parameter {} used'.format(
                            parameter
                            )
                        )
    elif analysis_parameters.get(parameter) is not None and \
        analysis_parameters.get(parameter) != '':
            checked_value = analysis_parameters[parameter]
    else: checked_value = default

    return checked_value


def repair_temperature(
        signal_data,
        plyuid,
        animal_metadata,
        analysis_parameters,
        local_logger=None
        ):
    """
    

    Parameters
    ----------
    signal_data : pandas.DataFrame
        dataframe containing signal data (including corrected_temp column)
    plyuid : string
        serial identifier for plethysmography recording session
    animal_metadata : dict
        dict indexed by 'PlyUID' containing animal metadata
    analysis_parameters : dict
        dictionary containing settings for analysis
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    pandas.Series
        series containing corrected temperature values

    """
    
    if 'corrected_temp' not in signal_data:
        if local_logger is not None:
            local_logger.warning(
                'corrected_temp not in signal data, replacing with default'
                )
        df = signal_data.copy()
        df['corrected_temp'] = float(
            check_animal_metadata_and_analysis_parameters(
                animal_metadata,
                plyuid,
                analysis_parameters,
                'corrected_temp_default',
                '35',
                local_logger=local_logger
                )
            )
        
        return df['corrected_temp']
    df = pandas.DataFrame()
    df['corrected_temp'] = signal_data['corrected_temp'].copy()

    cutoffs_raw = check_animal_metadata_and_analysis_parameters(
        animal_metadata,
        plyuid,
        analysis_parameters,
        'chamber_temp_cutoffs',
        '18 35',
        local_logger=local_logger
        )

    cutoffs = [float(i) for i in cutoffs_raw.split(' ')]

    temp_units = check_animal_metadata_and_analysis_parameters(
        animal_metadata,
        plyuid,
        analysis_parameters,
        'chamber_temperature_units',
        'C',
        local_logger=local_logger
        )

    default_temp = float(
        check_animal_metadata_and_analysis_parameters(
            animal_metadata,
            plyuid,
            analysis_parameters,
            'chamber_temperature_default',
            28,
            local_logger=local_logger
            )
        )

    temperature_trim_size = int(
        check_animal_metadata_and_analysis_parameters(
            animal_metadata,
            plyuid,
            analysis_parameters,
            'chamber_temperature_trim_size',
            1000,
            local_logger=local_logger
            )
        )

    temperature_narrow_fix = check_animal_metadata_and_analysis_parameters(
        animal_metadata,
        plyuid,
        analysis_parameters,
        'chamber_temperature_narrow_fix',
        'T',
        local_logger=local_logger
        )

    if temp_units == 'F':
        if local_logger is not None:
            local_logger.info('chamber temperature converted from F to C')
        df.loc[:, 'corrected_temp'] = \
            (df['corrected_temp'] - 32) * (5 / 9)

    try:
        unrepaired_median = numpy.median(df['corrected_temp'])
    except:
        unrepaired_median = 'nan'

    if unrepaired_median > 55:
        if local_logger is not None:
            local_logger.warning(
                'anomolous chamber temperature ' +
                'appears to be in F - converted to C'
                )
        df.loc[:, 'corrected_temp'] = \
            (df['corrected_temp'] - 32) * (5 / 9)

    df.loc[:, 'corrected_temp'] = filter_and_replace_temperature(
        df['corrected_temp'],
        cutoffs=cutoffs,
        default=default_temp,
        trim_size=temperature_trim_size,
        local_logger=local_logger
        )

    if temperature_narrow_fix == 'T':
        local_logger.info('applying enhanced chamber temperature check')
        median_temp = numpy.percentile(df['corrected_temp'], 50)
        iqr = numpy.percentile(df['corrected_temp'], 75) - \
            numpy.percentile(df['corrected_temp'], 25)
        df.loc[:, 'corrected_temp'] = filter_and_replace_temperature(
            df['corrected_temp'],
            cutoffs=[median_temp-iqr, median_temp+iqr],
            default=default_temp,
            trim_size=temperature_trim_size,
            local_logger=local_logger
            )

    return df['corrected_temp']


def filter_and_replace_temperature(
        input_series,
        cutoffs=(10, 100),
        default=26,
        trim_size=1000,
        local_logger=None
        ):
    """
    

    Parameters
    ----------
    input_series : DataSeries of Floats
        list of temperature values being screened for filtering/replacement
    cutoffs : tuple of Floats
        Boundary temperatures to use, values outside of this range are 
        identified and replaced
    default : Float, optional
        Temperature Value to use if temperature cannot be imputed from 
        neighboring measurements. The default is 26.
    trim_size : int, optional
        Number of samples to trim the data from the regio with the out of range
        value. The default is 1000.
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    temperature_series : DataSeries of Floats
        list of 'repaired' temperatures

    """

    temperature_series = input_series.copy()
    orig_series = input_series.copy()
    # create series to store filter for identification of out of range values
    filter_series = pandas.Series(numpy.zeros(len(temperature_series)))
    # identify values above the maximum cutoff
    filter_series.loc[temperature_series > cutoffs[1]] = 1
    # identify values below the minimum cutoff
    filter_series.loc[temperature_series < cutoffs[0]] = 1
    # trem edges around artifacts
    filter_series_expanded = filter_series.rolling(
        trim_size*2, center=True, min_periods=1).max()
    filter_series_expanded.fillna(1, inplace=True)
    # convert out of range values and the trimmed edges to NAN
    temperature_series.loc[filter_series_expanded == 1] = numpy.nan
    # fill in NAN based on surrounding values
    temperature_series.interpolate(method='linear', inplace=True)
    temperature_series.fillna(method='backfill', inplace=True)
    temperature_series.fillna(method='ffill', inplace=True)
    # if gaps still present, use default temp
    temperature_series.fillna(default, inplace=True)

    if orig_series.equals(temperature_series):
        if local_logger is not None:
            local_logger.info('no changes made to chamber temperature data')

        return temperature_series
    else:
        if local_logger is not None:
            local_logger.warning(
                'Chamber Temperature contains out of range data, fixes applied'
                )

        return temperature_series


def calculate_body_temperature(
        signal_data,
        plyuid,
        timestamp_dict,
        animal_metadata,
        manual_selection,
        auto_criteria,
        local_logger
        ):
    """
    

    Parameters
    ----------
    signal_data : Pandas.DataFrame
        DataFrame containing signal data
    plyuid : string
        serial identifier for data collection event 
    timestamp_dict : Dict
        Dictionairy containing timestamps and text used to describe them. 
        Captured from the commends in the signal_data
    animal_metadata : dict
        dict indexed by 'PlyUID' containing animal metadata
    manual_selection : TYPE
        DESCRIPTION.
    auto_criteria : TYPE
        DESCRIPTION.
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    DataSeries of Floats
        Series of Floats describing body temperature

    """

    start_body_temp, \
        mid_body_temp, \
        end_body_temp = extract_body_temperature_from_metadata(
            animal_metadata,
            plyuid,
            local_logger
            )

    startpoint, \
        midpoint, \
        endpoint = extract_body_temperature_timings(
            plyuid,
            manual_selection,
            auto_criteria,
            timestamp_dict,
            local_logger
            )

    if startpoint is None:
        startpoint = signal_data['ts'].min()
    if endpoint is None:
        endpoint = signal_data['ts'].max()
    if midpoint is None:
        midpoint = startpoint + endpoint / 2

    df = pandas.DataFrame()
    df['ts'] = signal_data['ts']
    df['body_temperature'] = start_body_temp
    # first half
    df.loc[
        (df['ts'] >= startpoint) & (df['ts'] <= midpoint),
        'body_temperature'
        ] = numpy.interp(
            [
                i for i in range(
                    len(
                        df[(df['ts'] >= startpoint) & (df['ts'] <= midpoint)]
                        )
                    )
                ],
            [0, len(df[(df['ts'] >= startpoint) & (df['ts'] <= midpoint)])],
            [start_body_temp, mid_body_temp]
            )
    # second half
    df.loc[
        (df['ts'] >= midpoint) & (df['ts'] <= endpoint),
        'body_temperature'
        ] = numpy.interp(
            [
                i for i in range(
                    len(
                        df[(df['ts'] >= midpoint) & (df['ts'] <= endpoint)]
                        )
                    )
                ],
            [0, len(df[(df['ts'] >= midpoint) & (df['ts'] <= endpoint)])],
            [mid_body_temp, end_body_temp]
            )
    # fill in the end
    df.loc[df['ts'] >= endpoint, 'body_temperature'] = end_body_temp

    return df['body_temperature']


def extract_body_temperature_from_metadata(
        animal_metadata,
        plyuid,
        local_logger,
        default=37.5):
    """
    

    Parameters
    ----------
    animal_metadata : dict
        dict indexed by 'PlyUID' containing animal metadata
    plyuid : string
        serial identifier for data collection event 
        (plethysmography session id)
    local_logger : instance of logging.logger (optional)
    default : Float, optional
        Default body temperature to use if no data available. 
        The default is 37.5.

    Returns
    -------
    start_body_temp : Float
        Body Temperature of the animal at the beginning of the recording
    mid_body_temp : Float
        Body Temperature of the animal at the 'middle' of the recording
    end_body_temp : Fload
        Body Temperature of the animal at the end of the recording

    """
    try:
        start_body_temp = float(
            animal_metadata[plyuid]['Start_body_temperature']
            )
    except:
        local_logger.warning(
            'no starting body temperature present in metadata'
            )
        start_body_temp = None

    try:
        mid_body_temp = float(
            animal_metadata[plyuid]['Mid_body_temperature']
            )
    except:
        local_logger.info(
            'no midpoint body temperature present in metadata')
        mid_body_temp = None

    try:
        end_body_temp = float(
            animal_metadata[plyuid]['End_body_temperature']
            )
    except:
        local_logger.warning(
            'no ending body temperature present in metadata')
        end_body_temp = None

    if start_body_temp is None and \
        mid_body_temp is None and \
        end_body_temp is None:
            start_body_temp = default
            mid_body_temp = default
            end_body_temp = default
            local_logger.warning(
              'no body temp data present, default value ({}) used'.format(
                    default
                    )
              )
    elif start_body_temp is not None and \
        end_body_temp is not None and \
        mid_body_temp is None:
            mid_body_temp = (start_body_temp + end_body_temp) / 2
            local_logger.info('midpoint body temp filled in with average')
    elif start_body_temp is not None and \
        mid_body_temp is None and \
        end_body_temp is None:
            mid_body_temp = start_body_temp
            end_body_temp = start_body_temp
            local_logger.info('only starting body temperature available')
    elif start_body_temp is None and \
        mid_body_temp is None and \
        end_body_temp is not None:
            start_body_temp = end_body_temp
            mid_body_temp = end_body_temp
            local_logger.info('only ending body temperature available')
    elif start_body_temp is None and \
        mid_body_temp is not None and \
        end_body_temp is None:
            start_body_temp = mid_body_temp
            end_body_temp = mid_body_temp
            local_logger.info('only midpoint body temperature available')
    elif start_body_temp is None and \
        mid_body_temp is not None and \
        end_body_temp is not None:
            start_body_temp = mid_body_temp
            local_logger.info('missing starting body temperature filled with' +
                              ' midpoint body temperature')
    elif start_body_temp is not None and \
        mid_body_temp is not None and \
        end_body_temp is None:
            end_body_temp = mid_body_temp
            local_logger.info('missing ending body temperature filled with' +
                              ' midpoint body temperature')
    else:
        pass
    return start_body_temp, mid_body_temp, end_body_temp


def extract_body_temperature_timings(
        plyuid,
        manual_selection,
        auto_criteria,
        timestamp_dict,
        local_logger
        ):
    """


    Parameters
    ----------
    plyuid : string
        serial identifier for data collection event
    manual_selection : TYPE
        DESCRIPTION.
    auto_criteria : TYPE
        DESCRIPTION.
    timestamp_dict : Dict
        Dictionairy containing timestamps and text used to describe them. 
        Captured from the commends in the signal_data
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    startpoint : float of None
        timestamp key associated startpoint in autoc_criteria or start time
        associated with startpoint in manual_selection
    midpoint : float or None
        timestamp key associated midpoint in autoc_criteria or start time
        associated with midpoint in manual_selection
    endpoint : float or None
        timestamp key associated endpoint in autoc_criteria or stop time
        associated with endpoint in manual_selection

    """
    startpoint_auto = None
    midpoint_auto = None
    endpoint_auto = None
    if auto_criteria is not None:
        for ts in timestamp_dict:
            try:
                if (auto_criteria[
                        auto_criteria['Key'] == timestamp_dict[ts][3:-1]
                        ]['Startpoint'] == 1).bool():
                    startpoint_auto = ts
                    local_logger.info('startpoint found in auto_criteria')
            except:
                pass
            try:
                if (auto_criteria[
                        auto_criteria['Key'] == timestamp_dict[ts][3:-1]
                        ]['Midpoint'] == 1).bool():
                    midpoint_auto = ts
                    local_logger.info('midpoint found in auto_criteria')
            except:
                pass
            try:
                if (auto_criteria[
                        auto_criteria['Key'] == timestamp_dict[ts][3:-1]
                        ]['Endpoint'] == 1).bool():
                    endpoint_auto = ts
                    local_logger.info('endpoint found in auto_criteria')
            except:
                pass

    startpoint_manual = None
    midpoint_manual = None
    endpoint_manual = None
    if manual_selection is not None:
        try:
            startpoint_manual = manual_selection[
                (manual_selection['PLYUID'].astype(str) == plyuid) &
                (manual_selection['Startpoint'] == 1)
                ].start.values[0]
        except:
            pass
        try:
            midpoint_manual = manual_selection[
                (manual_selection['PLYUID'].astype(str) == plyuid) &
                (manual_selection['Midpoint'] == 1)
                ].start.values[0]
        except:
            pass
        try:
            endpoint_manual = manual_selection[
                (manual_selection['PLYUID'].astype(str) == plyuid) &
                (manual_selection['Endpoint'] == 1)
                ].stop.values[0]
        except:
            pass

    startpoint = startpoint_auto
    midpoint = midpoint_auto
    endpoint = endpoint_auto

    if startpoint_manual is not None:
        startpoint = startpoint_manual
    if midpoint_manual is not None:
        midpoint = midpoint_manual
    if endpoint_manual is not None:
        endpoint = endpoint_manual

    return startpoint, midpoint, endpoint


def apply_smoothing_filter(signal_data,
                           column,
                           high_pass=0.1,
                           high_pass_order=2,
                           low_pass=50,
                           low_pass_order=10,
                           ):
    """
    Parameters
    ----------
    signal_data : pandas.DataFrame
        data to be smoothed
    column : 'String'
        The name of the 
    high_pass : Float, optional
        Frequency cutoff (Hz) for the highpass filter. The default is 0.1.
    high_pass_order : Integer, optional
        order value for the high pass filter. The default is 2.
    low_pass : Float, optional
        Frequency cutoff (Hz) for the low_pass filter. The default is 50.
    low_pass_order : Integer, optional
        order value for the low pass filter. The default is 10.
     
    Returns
    -------
    lpf_hpf_signal : List, DataSeries of Floats
        smoothed data

    """
    sampleHz = round(
        1 / (list(signal_data['ts'])[2] - list(signal_data['ts'])[1])
        )

    hpf_b, hpf_a = signal.butter(
        high_pass_order, high_pass/(sampleHz/2), 'high')
    
    hpf_signal = signal.filtfilt(hpf_b, hpf_a, signal_data[column])

    lpf_b, lpf_a = signal.bessel(low_pass_order, low_pass/(sampleHz/2), 'low')
    
    lpf_hpf_signal = signal.filtfilt(lpf_b, lpf_a, hpf_signal)

    return lpf_hpf_signal


def getmaxbyindex(inputlist, indexlist):
    """
    inputlist : list
        list to extract average from
    indexlist : int
        list of index values specifying start of unit to screen within, n+1 
        specifies ent of unit

    Returns
    -------
    maxbyindexlist : Float
        min of the values specified by the index boundaries


    can get PIF calcs using flow data and transition times
    note that cross ref of indexlist with Ti vs Te timestamps
    is needed for segregation of the data
    """
    maxbyindexlist = [max(inputlist[indexlist[i]:indexlist[i+1]])
                    for i in range(len(indexlist)-1)]
    return numpy.array(maxbyindexlist)


def getminbyindex(inputlist, indexlist):
    """
    inputlist : list
        list to extract average from
    indexlist : int
        list of index values specifying start of unit to screen within, n+1 
        specifies ent of unit

    Returns
    -------
    minbyindexlist : Float
        min of the values specified by the index boundaries

    can get calcs using signal and transition times
    note that cross ref of indexlist with timestamps
    is needed for segregation of the data

    can get PEF calcs using flow data and transition times
    note that cross ref of indexlist with Ti vs Te timestamps
    is needed for segregation of the data
    """
    minbyindexlist = [min(inputlist[indexlist[i]:indexlist[i+1]])
                    for i in range(len(indexlist)-1)]
    return numpy.array(minbyindexlist)


def getsumby2index(inputlist, index1, index2):
    """
    inputlist : list
        list to extract average from
    index1 : int
        lower bound of index for range of entries to average
    index2 : int
        upper bound of index for range of entries to average

    Returns
    -------
    sumbyindexlist : Float
        sum of the values specified by the index boundaries

    
    can get TV calcs using flow data and transition times
    note that cross ref of indexlist with Ti vs Te timestamps
    is needed for segregation of the data
    """
    sumbyindexlist = [sum(
        inputlist[index1[i]:index2[i]]
                        )
                    for i in range(len(index1))]
    return sumbyindexlist


def getmaxby2index(inputlist, index1, index2):
    """
    

    Parameters
    ----------
    inputlist : list
        list to extract average from
    index1 : int
        lower bound of index for range of entries to average
    index2 : int
        upper bound of index for range of entries to average

    Returns
    -------
    maxbyindexlist : Float
        maximum of the values specified by the index boundaries

    can get calcs using signal and transition times
    note that cross ref of indexlist with timestamps
    is needed for segregation of the data. Useful for PIF/PEF calculations.
    """
    maxbyindexlist = [max(
        inputlist[index1[i]:index2[i]]
                        )
                    for i in range(len(index1))]
    return maxbyindexlist


def get_avg_by_2_index(inputlist, index1, index2):
    """
    Parameters
    ----------
    inputlist : list
        list to extract average from
    index1 : int
        lower bound of index for range of entries to average
    index2 : int
        upper bound of index for range of entries to average

    Returns
    -------
    avgbyindexlist : Float
        average of the values specified by the index boundaries

    can get calcs using signal and transition times
    note that cross ref of indexlist with timestamps
    is needed for segregation of the data
    """
    avgbyindexlist = [numpy.mean(
        inputlist[index1[i]:index2[i]]
                        )
                    for i in range(len(index1))]
    return avgbyindexlist


def extract_candidate_breath_transitions(signal_data):
    """
    

    Parameters
    ----------
    signal_data : Pandas.DataFrame
        DataFrame containing signal data

    Returns
    -------
    candidate_breath_transitions : Pandas.DataFrame
        DataFrame with additional columns describing candidate breath 
        parameters

    """
    candidate_breath_transitions = pandas.DataFrame()
    signal_above_zero = numpy.greater(signal_data['flow'], 0)
    dif_signal_above_zero = numpy.diff(signal_above_zero.astype(int))
    index_list = numpy.array(dif_signal_above_zero.nonzero())[0]
    candidate_breath_transitions['ts'] = numpy.take(
        signal_data['ts'], index_list
        )
    candidate_breath_transitions['inhale vs exhale'] = numpy.take(
        dif_signal_above_zero, index_list
        )
    candidate_breath_transitions['pif'] = numpy.append(
        getmaxbyindex(signal_data['flow'], index_list),
        0
        )
    candidate_breath_transitions['pef'] = numpy.append(
        getminbyindex(signal_data['flow'], index_list),
        0
        )
    candidate_breath_transitions['index_list'] = index_list
    return candidate_breath_transitions


def extract_filtered_breaths_from_candidates(
        candidate_breath_transitions,
        analysis_parameters,
        local_logger
        ):
    """
    Parameters
    ----------
    candidate_breath_transitions : Pandas.DataFrame
        DataFrame containing annotated transitions between breaths
    analysis_parameters : Dict
        Dict of settings to use for analysis
    local_logger : instance of logging.logger (optional)

    Raises
    ------
    Exception
        Raised is fewer than 30 breaths meet PIF PEF and TI criteria

    Returns
    -------
    filtered_breaths : Pandas.DataFrame
        DataFrame describing, per breath, the parameters of the filtered 
        breaths

    """

    # filter based on minimum PIF and PEF
    filtered_transitions = candidate_breath_transitions[
        (candidate_breath_transitions['pif'] >
         float(analysis_parameters['minimum_PIF'])) |
        (candidate_breath_transitions['pef'] <
         float(analysis_parameters['minimum_PEF']))
        ]

    toggle_inhale = 0
    toggle_exhale = 1

    ts_list = list(filtered_transitions['ts'])
    ie_list = list(filtered_transitions['inhale vs exhale'])
    pif_list = list(filtered_transitions['pif'])
    pef_list = list(filtered_transitions['pef'])
    index_list = list(filtered_transitions['index_list'])
    inhale_filter = [0 for i in ts_list]
    exhale_filter = [0 for i in ts_list]

    # collect breaths based on toggle between inhale/exhale
    for i in range(len(ts_list)):
        if \
                ie_list[i] == 1 and \
                toggle_exhale == 1 and \
                pif_list[i] > float(analysis_parameters['minimum_PIF']):
            toggle_inhale = 1
            toggle_exhale = 0
            inhale_filter[i] = 1
        if \
                ie_list[i] == -1 and \
                toggle_inhale == 1 and \
                pef_list[i] < float(analysis_parameters['minimum_PEF']):
            toggle_inhale = 0
            toggle_exhale = 1
            exhale_filter[i] = 1

    number_of_full_breaths = min(sum(inhale_filter), sum(exhale_filter))
    ts_inhale = numpy.take(ts_list, numpy.nonzero(inhale_filter)[0])
    ts_exhale = numpy.take(ts_list, numpy.nonzero(exhale_filter)[0])
    il_inhale = numpy.take(index_list, numpy.nonzero(inhale_filter)[0])
    il_exhale = numpy.take(index_list, numpy.nonzero(exhale_filter)[0])
    duration_list = ts_exhale[:number_of_full_breaths] - \
        ts_inhale[:number_of_full_breaths]
    # filter based on minimum TI from Analysis Parameters
    ti_filter = numpy.array(
        duration_list > float(analysis_parameters['minimum_TI'])
        ).astype(int)
    filtered_breath_index_list = numpy.nonzero(ti_filter)[0]
    if len(filtered_breath_index_list) < 30:
        local_logger.error('insufficient breaths to score')
        raise Exception('fewer than 30 breaths meet PIF PEF and TI criteria')

    filtered_breaths = pandas.DataFrame()
    filtered_breaths['ts_inhale'] = numpy.take(
        ts_inhale, filtered_breath_index_list[:-1]
        )
    filtered_breaths['ts_exhale'] = numpy.take(
        ts_exhale, filtered_breath_index_list[:-1]
        )
    filtered_breaths['ts_end'] = numpy.take(
        ts_inhale, filtered_breath_index_list[1:]
        )
    filtered_breaths['il_inhale'] = numpy.take(
        il_inhale, filtered_breath_index_list[:-1]
        )
    filtered_breaths['il_exhale'] = numpy.take(
        il_exhale, filtered_breath_index_list[:-1]
        )
    filtered_breaths['il_end'] = numpy.take(
        il_inhale, filtered_breath_index_list[1:]
        )
    local_logger.info('{} breaths found'.format(len(filtered_breaths)))

    return filtered_breaths


def calculate_irreg_score(input_series):
    """
    Parameters
    ----------
    input_series : Pandas.DataSeries of Floats
        Data to use for Irreg Score Calculation

    Returns
    -------
    output_series : Pandas.DataSeries of Floats
        Series of Irreg Scores, paired to input_series

        ...
        takes a numpy compatible series and calculates an irregularity score
        using the formula |x[n]-X[n-1]| / X[n-1]
    
        first value will be zero as it has no comparison to change from
    
        a series of the irregularity scores will be returned
    """
    output_series = numpy.insert(
        numpy.divide(
            numpy.abs(
                numpy.subtract(
                    list(input_series[1:]), list(input_series[:-1])
                    )
                ),
            list(input_series[:-1])
            ), 0, numpy.nan)
    return output_series


def calculate_moving_average(input_series, window, include_current=True):
    """
    Parameters
    ----------
    input_series : Pandas.DataSeries of Floats
        Data to use for moving average calculation
    window : Int
        number of samples to use for moving average
    include_current : Boolean, optional
        include the 'middle' breath in the moving average True/False. 
        The default is True.

    Returns
    -------
    moving_average : Pandas.DataSeries of Floats
        moving average smoothed series paired to the input_series

    """
    if include_current == False:
        moving_average = (
            input_series.rolling(
                window, center=True,
                min_periods=0
                ).sum() - input_series
            ) / (
                input_series.rolling(
                    window, center=True,
                    min_periods=0
                    ).count() - 1
                )
    else:
        moving_average = (
            input_series.rolling(
                window, center=True,
                min_periods=0
                ).sum()
            ) / (
                input_series.rolling(
                    window, center=True,
                    min_periods=0
                    ).count()
                )
    return moving_average


def basicRR(
        CT,
        TS,
        noisecutoff = 75,
        threshfactor = 4,
        absthresh = 0.3,
        minRR = 0.05):
    """
    

    Parameters
    ----------
    CT : Pandas.DataSeries or List of Floats
        Series of voltage data
    TS : Pandas.DataSeries or List of Floats
        Series of timestamps paired to voltage data
    noisecutoff : Float, optional
        percentile of signal amplitude to use to set the 'noise level'. 
        The default is 75.
    threshfactor : Float, optional
        fold change above noisecutoff to use for peak detection. 
        The default is 4.
    absthresh : Float, optional
        absolute minimum voltage to use for peak detection. The default is 0.3.
    minRR : Float, optional
        minimum duration of heartbeat to be considered a valid beat. 
        The default is 0.05.

    Returns
    -------
    beat_df : Pandas.DataFrame
        DataFrame containing baseg heart beat parameters (timestamp, 'RR')

    """
    """
    simple RR peak caller based on relative signal to noise thresholding
    CT = signal
    noisecutoff = perrcentile within signal to consider as noise
    threshfactor = multiple of the noisecutoff to use for beat detaction
    minRR = minimum RR in samples (1000BPM ~ 60 ms RR, minRR ~60 @1000Hz)
    **CV and Rvolt to thresh ratios may help for QC
    signal filtering is helpful (recommend butter highpass and notch filters)
    """
    
    # get above thresh
    noise_level=numpy.percentile(CT,noisecutoff)
    thresh=max(noise_level*threshfactor,absthresh)
    beats={}
    index_crosses=[]
    for i in range(len(CT)-1):
        if CT[i+1]>=thresh and CT[i]<thresh:
            index_crosses.append(i+1)
    
    if len(index_crosses)==0:
    
        return beats #pass no beats
    
    prevJ=0
    
    for i in index_crosses[:-1]:
        maxR=CT[i]
        
        TS_R=TS[i]
        for j in range(i,len(CT),1):
            if CT[j]<thresh:
                break
            if j>=index_crosses[-1]:
                break
            elif CT[j]>maxR:
                maxR=CT[j]
        
        if j-prevJ>=minRR:
            beats[TS_R]={'RR':TS[j]-TS[prevJ]}
            if prevJ==0: 
                beats[TS_R]['first']=True
            else: beats[TS_R]['first']=False
            prevJ=j
            
    beat_df = pandas.DataFrame(beats).transpose()
    beat_df.index.name = 'ts'
    beat_df.reset_index()
    return beat_df


def calculate_basic_breath_parameters(
    signal_data,
    filtered_breaths,
    analysis_parameters,
    local_logger
    ):
    """
    

    Parameters
    ----------
    signal_data : Pandas.DataFrame
        DataFrame containing signal data
    filtered_breaths : Pandas.DataFrame
        DataFrame containing filtered list of candidate breaths
    analysis_parameters : dict
        dictionary containing settings for analysis
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    breath_parameters : Pandas.DataFrame
        DataFrame containing annotated paramters for candidate breaths

    """

    breath_parameters = filtered_breaths.copy()
    breath_parameters['TI'] = filtered_breaths['ts_exhale'] - \
        filtered_breaths['ts_inhale']
    breath_parameters['TE'] = filtered_breaths['ts_end'] - \
        filtered_breaths['ts_exhale']
    breath_parameters['TT'] = filtered_breaths['ts_end'] - \
        filtered_breaths['ts_inhale']
    breath_parameters['IS_TT'] = calculate_irreg_score(breath_parameters['TT'])
    breath_parameters['BPM'] = 60 / breath_parameters['TT']

    sample_interval = signal_data['ts'][2] - signal_data['ts'][1]

    breath_parameters['iTV'] = numpy.multiply(
        getsumby2index(
            signal_data['flow'],
            filtered_breaths['il_inhale'],
            filtered_breaths['il_exhale']
            ),
        sample_interval
        )
    breath_parameters['eTV'] = numpy.multiply(
        getsumby2index(
            signal_data['flow']*-1,
            filtered_breaths['il_exhale'],
            filtered_breaths['il_end']
            ),
        sample_interval
        )
    breath_parameters['IS_iTV'] = calculate_irreg_score(
        breath_parameters['iTV']
        )
    breath_parameters['PIF'] = getmaxby2index(
        signal_data['flow'],
        breath_parameters['il_inhale'],
        breath_parameters['il_exhale']
        )
    breath_parameters['PEF'] = getmaxby2index(
        signal_data['flow']*-1,
        breath_parameters['il_exhale'],
        breath_parameters['il_end']
        )
    breath_parameters['DVTV'] = numpy.divide(
        numpy.abs(
            numpy.subtract(
                numpy.abs(breath_parameters['iTV']),
                numpy.abs(breath_parameters['eTV'])
                )
            ),
        numpy.divide(
            numpy.add(
                numpy.abs(breath_parameters['iTV']),
                numpy.abs(breath_parameters['eTV'])
                ), 2
            )
        )

    breath_parameters['apnea_local_threshold'] = calculate_moving_average(
        breath_parameters['TT'],
        int(analysis_parameters['apnea_window']),
        include_current=False
        )

    breath_parameters['sigh_local_threshold'] = calculate_moving_average(
        breath_parameters['iTV'],
        int(analysis_parameters['sigh_window']),
        include_current=False
        )

    breath_parameters['per_X_calculation'] = calculate_moving_average(
        (
            breath_parameters['BPM'] >
            float(analysis_parameters['percent_X_value'])
            ).astype(int),
        int(analysis_parameters['percent_X_window']),
        include_current=True
        )

    breath_parameters['apnea'] = (
        breath_parameters['TT'] > (
            breath_parameters['apnea_local_threshold'] *
            float(analysis_parameters['minimum_apnea_duration_x_local_TT'])
            )
        ).astype(int)

    breath_parameters['sigh'] = (
        breath_parameters['iTV'] > (
            breath_parameters['sigh_local_threshold'] *
            float(analysis_parameters['minimum_sigh_amplitude_x_local_VT'])
            )
        ).astype(int)
    

    breath_parameters['o2'] = get_avg_by_2_index(
        signal_data['o2'],
        filtered_breaths['il_inhale'],
        filtered_breaths['il_end']
        )

    breath_parameters['co2'] = get_avg_by_2_index(
        signal_data['co2'],
        filtered_breaths['il_inhale'],
        filtered_breaths['il_end']
        )

    breath_parameters['corrected_o2'] = get_avg_by_2_index(
        signal_data['corrected_o2'],
        filtered_breaths['il_inhale'],
        filtered_breaths['il_end']
        )

    breath_parameters['corrected_co2'] = get_avg_by_2_index(
        signal_data['corrected_co2'],
        filtered_breaths['il_inhale'],
        filtered_breaths['il_end']
        )        
        
    breath_parameters['temp'] = get_avg_by_2_index(
        signal_data['temp'],
        filtered_breaths['il_inhale'],
        filtered_breaths['il_end']
        )    

    breath_parameters['corrected_temp'] = get_avg_by_2_index(
        signal_data['corrected_temp'],
        filtered_breaths['il_inhale'],
        filtered_breaths['il_end']
        )


    breath_parameters['Body_Temperature'] = get_avg_by_2_index(
        signal_data['Body_Temperature'],
        filtered_breaths['il_inhale'],
        filtered_breaths['il_end']
        )

    breath_parameters['mov_avg_vol'] = get_avg_by_2_index(
        signal_data['mov_avg_vol'],
        filtered_breaths['il_inhale'],
        filtered_breaths['il_end']
        )

    breaths_removed = len(breath_parameters) - \
        len(
            breath_parameters[
            (
                breath_parameters['DVTV'] <
                float(analysis_parameters['maximum_DVTV'])
                ) &
            (
                breath_parameters['per_X_calculation'] <
                float(analysis_parameters['maximum_percent_X'])
                )
                ]
            )

    local_logger.info(
        '{} breaths removed from initial quality filter'.format(
            breaths_removed
            )
        )

    return breath_parameters[
                (
                    breath_parameters['DVTV'] <
                    float(analysis_parameters['maximum_DVTV'])
                    ) &
                (
                    breath_parameters['per_X_calculation'] <
                    float(analysis_parameters['maximum_percent_X'])
                    )
                ]


def breath_caller(
        signal_data, analysis_parameters, local_logger
        ):
    """


    Parameters
    ----------
    signal_data : Pandas.DataFrame
        DataFrame containing signal data
    analysis_parameters : dict
        dictionary containing settings for analysis
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    basic_breath_parameters : Pandas.DataFrame
        DataFrame containing annotated breaths

    """
    local_logger.info('detection of breaths started')

    candidate_breath_transitions = extract_candidate_breath_transitions(
        signal_data
        )

    filtered_breaths = extract_filtered_breaths_from_candidates(
        candidate_breath_transitions,
        analysis_parameters,
        local_logger
        )

    basic_breath_parameters = calculate_basic_breath_parameters(
        signal_data,
        filtered_breaths,
        analysis_parameters,
        local_logger
        )

    return basic_breath_parameters


def create_auto_calibration_dict(
        signal_data,
        breath_list,
        auto_criteria,
        timestamp_dict,
        local_logger
        ):
    """
    

    Parameters
    ----------
    signal_data : Pandas.DataFrame
        DataFrame containing signal data
    breath_list : Pandas.DataFrame
        DataFrame containing annotated breaths
    auto_criteria : Dict
        Dict with info describing criteria for automated selection of breathing
        for 'calm quiet' breathing
    timestamp_dict : Dict
        Dictionairy containing timestamps and text used to describe them. 
        Captured from the commends in the signal_data
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    auto_calibration_dict : Dict
        Dict describing baseline measures and parameters for calibration

    """
    if auto_criteria is None:
        return None

    auto_calibration_dict = {
        'o2': {
            'nom': [],
            'voltage': []
            },
        'co2': {
            'nom': [],
            'voltage': []
            }
        }
    cal_list = breath_list.copy()
    all_keys = auto_criteria['Key'].unique()

    cal_keys = auto_criteria[
        auto_criteria['AUTO_IND_GAS_CAL'] == 1
        ][['Key', 'Alias', 'CAL_O2', 'CAL_CO2']]
    cal_keys['Key_and_Alias'] = \
        cal_keys['Key'].astype(str)+cal_keys['Alias'].astype(str)

    reverse_timestamp_dict = {}
    for k in timestamp_dict:
        if timestamp_dict[k][3:-1] in all_keys:
            reverse_timestamp_dict[timestamp_dict[k][3:-1]] = k

    for key_and_alias in cal_keys['Key_and_Alias']:

        key = cal_keys[
            cal_keys['Key_and_Alias'] == key_and_alias
            ]['Key'].values[0]
        alias = cal_keys[
            cal_keys['Key_and_Alias'] == key_and_alias
            ]['Alias'].values[0]
        if key not in reverse_timestamp_dict:
            continue

        current_auto_criteria = \
            auto_criteria[
                (auto_criteria['Key'] == key) & (
                    auto_criteria['Alias'] == alias)
                ].to_dict('records')[0]

        block_start, block_stop = extract_block_bounds(
            signal_data, reverse_timestamp_dict, all_keys, key
            )
        verified_block_start = max(
            block_start + float(current_auto_criteria['after_start']),
            block_stop - float(current_auto_criteria['within_end'])
            )
        verified_block_stop = min(
            block_stop - float(current_auto_criteria['before_end']),
            block_start + float(current_auto_criteria['within_start'])
            )

        try:
            nom_o2, min_v_o2, max_v_o2 = cal_keys[
                cal_keys['Key_and_Alias'] == key_and_alias
                ]['CAL_O2'].values[0].split(',')
            o2_filter = \
                (cal_list['o2'] >= float(min_v_o2)) & \
                (cal_list['o2'] <= float(max_v_o2))

        except:
            nom_o2, min_v_o2, max_v_o2 = None, None, None
            o2_filter = cal_list['o2'] == cal_list['o2']
        try:
            nom_co2, min_v_co2, max_v_co2 = cal_keys[
                cal_keys['Key_and_Alias'] == key_and_alias
                ]['CAL_CO2'].values[0].split(',')
            co2_filter = \
                (cal_list['co2'] >= float(min_v_co2)) & \
                (cal_list['co2'] <= float(max_v_co2))

        except:
            nom_co2, min_v_co2, max_v_co2 = None, None, None
            co2_filter = cal_list['co2'] == cal_list['co2']

        cal_list['filter_{}'.format(key_and_alias)] = 0
        cal_list.loc[
            (cal_list['TT'] >= float(current_auto_criteria['min_TT'])) &
            (cal_list['TT'] <= float(current_auto_criteria['max_TT'])) &
            (cal_list['DVTV'] <= float(current_auto_criteria['max_DVTV'])) &
            (cal_list['per_X_calculation'] <=
             float(current_auto_criteria['max_pX'])) &
            (cal_list['iTV'] >= float(current_auto_criteria['min_TV'])) &
            (cal_list['eTV'] >= float(current_auto_criteria['min_TV'])) &
            (o2_filter) &
            (co2_filter) &
            (cal_list['mov_avg_vol'] <=
             float(current_auto_criteria['vol_mov_avg_drift'])) &
            (cal_list['ts_inhale'] >= verified_block_start) &
            (cal_list['ts_end'] <= verified_block_stop),
            'filter_{}'.format(key_and_alias)
            ] = 1
        
        if sum(cal_list['filter_{}'.format(key_and_alias)]) == 0:
            if sum(
                    (cal_list['ts_inhale'] >= verified_block_start) & \
                    (cal_list['ts_end'] <= verified_block_stop) & \
                    (o2_filter)
                    ) < int(current_auto_criteria['min_bout']):
                local_logger.warning(
                    'insufficient gas calibration breaths satisfying O2 filter'
                    )
            if sum(
                    (cal_list['ts_inhale'] >= verified_block_start) & \
                    (cal_list['ts_end'] <= verified_block_stop) & \
                    (co2_filter)
                    ) < int(current_auto_criteria['min_bout']):
                local_logger.warning(
                    'insufficient gas calibration breaths satisfying CO2 filter'
                    )
            if sum(
                    (cal_list['ts_inhale'] >= verified_block_start) & \
                    (cal_list['ts_end'] <= verified_block_stop) & \
                    (cal_list['mov_avg_vol'] <=
                     float(current_auto_criteria['vol_mov_avg_drift']))
                    ) < int(current_auto_criteria['min_bout']):
                local_logger.warning(
                    'insufficient gas calibration breaths satisfying MAV filter'
                    )
            
        biggest_chunk = get_the_biggest_chunk(
            get_the_chunks(
                cal_list['filter_{}'.format(key_and_alias)],
                1,
                int(current_auto_criteria['min_bout'])
                )
            )
        if biggest_chunk is None or biggest_chunk == []:
            local_logger.warning(
                'expected gas calibration data in ' + \
                'AUTO {} | {} - '.format(key, alias) + \
                'no suitable data found'
                )
            continue
        else:
            chunk_filter = \
                (cal_list['ts_inhale'] >=
                 cal_list.iloc[biggest_chunk[0][0]]['ts_inhale']) & \
                (cal_list['ts_end'] <=
                 cal_list.iloc[biggest_chunk[0][1]]['ts_end'])

        if nom_o2 is not None:
            auto_calibration_dict['o2']['nom'].append(float(nom_o2))
            auto_calibration_dict['o2']['voltage'].append(
                sum(
                    cal_list[chunk_filter]['o2'] *
                    cal_list[chunk_filter]['TT']
                    ) / cal_list[chunk_filter]['TT'].sum()
                )
        if nom_co2 is not None:
            auto_calibration_dict['co2']['nom'].append(float(nom_co2))
            # create weighted average (TT) to generate average over sampling
            # time rather than per breath
            auto_calibration_dict['co2']['voltage'].append(
                sum(
                    cal_list[chunk_filter]['co2'] *
                    cal_list[chunk_filter]['TT']
                    ) / cal_list[chunk_filter]['TT'].sum()
                )
    return auto_calibration_dict


def extract_block_bounds(signal_data, reverse_timestamp_dict, all_keys, key):
    """
    Parameters
    ----------
    signal_data : Pandas.DataFrame
        DataFrame containing signal data
    reverse_timestamp_dict : Dict
        Dictionairy containing text used to describe timstamps and the 
        acutal timestamps themselvs. Built from timestamp_dict. 
    all_keys : List
        keys from reverse_timestamp_dict (not used)
    key : ...
        key to test in reverse_timestamp_dict

    Returns
    -------
    block_start : TYPE
        DESCRIPTION.
    block_end : TYPE
        DESCRIPTION.

    """

    block_start = reverse_timestamp_dict[key]
    block_end = min(
        [
            reverse_timestamp_dict[k]
            for k in reverse_timestamp_dict
            if reverse_timestamp_dict[k] > block_start
            ]+[signal_data['ts'].max()]
        )
    return block_start, block_end


def create_man_calibration_dict(
        signal_data,
        manual_selection,
        plyuid
        ):
    """
    

    Parameters
    ----------
    signal_data : Pandas.DataFrame
        DataFrame containing signal data
    manual_selection : Dict
        Dict with info describing manually selected start and stop points for
        breathing of interest
    plyuid : string
        serial identifier for data collection event

    Returns
    -------
    man_calibration_dict : Dict
        Dict describing baseline measures and parameters for calibration from
        manual selection

    """
    if manual_selection is None:
        return None

    man_calibration_dict = {
        'o2': {
            'nom': [],
            'voltage': []
            },
        'co2': {
            'nom': [],
            'voltage': []
            }
        }

    for segment_index in \
        manual_selection[
            (manual_selection['MAN_IND_GAS_CAL'] == 1) &
            (manual_selection['PLYUID'].astype(str) == plyuid)
            ].index:

        try:
            nom_o2 = float(manual_selection.iloc[segment_index]['CAL_O2'])

        except:
            nom_o2 = None

        try:
            nom_co2 = float(manual_selection.iloc[segment_index]['CAL_CO2'])

        except:
            nom_co2 = None

        if nom_o2 is not None and math.isnan(nom_o2) == False:
            man_calibration_dict['o2']['nom'].append(
                nom_o2
                )
            man_calibration_dict['o2']['voltage'].append(
                signal_data[
                    (signal_data['ts'] >=
                     manual_selection.iloc[segment_index]['start']) &
                    (signal_data['ts'] <=
                     manual_selection.iloc[segment_index]['stop'])
                    ]['o2'].mean()
                )

        if nom_co2 is not None and math.isnan(nom_co2) == False:
            man_calibration_dict['co2']['nom'].append(
                nom_co2
                )
            man_calibration_dict['co2']['voltage'].append(
                signal_data[
                    (signal_data['ts'] >=
                     manual_selection.iloc[segment_index]['start']) &
                    (signal_data['ts'] <=
                     manual_selection.iloc[segment_index]['stop'])
                    ]['co2'].mean()
                )
    return man_calibration_dict


def get_the_chunks(chunkable_list, value, min_chunk):
    """
    Parameters
    ----------
    chunkable_list : List
        List containing values to search through
    value : ...
        value that is being searched for in the chunkable list
    min_chunk : Int
        Integer minimum chunk size (consecutive list entries matching value)

    Returns
    -------
    chunks : List of tuples
        returns a list of tuples describing the indexes of chunks with the 
        value that meet the minumum chunk size

    """
    status = 0
    chunks = []
    chunk_start = 0
    chunk_stop = 1
    if len(chunkable_list) < min_chunk:
        return chunks

    for i in range(len(chunkable_list)):
        if chunkable_list[i] == value:
            if status == 0:
                chunk_start = i
                status = 1
            else:
                chunk_stop = i
        else:
            if status == 1:
                if chunk_stop-chunk_start >= min_chunk:
                    chunks.append((chunk_start, chunk_stop))
                status = 0
    if len(chunks) == 0 and status == 1:
        chunks.append((chunk_start, chunk_stop))
    return chunks


def get_the_biggest_chunk(chunk_list):
    """
        Parameters
    ----------
    chunk_list : list of tuples of Ints (or Floats)
        list of Tuples of Ints describing indexes of selections

    Returns
    -------
    biggest_chunk : Tuple of Ints (or Floats)
        Tuple describing the boundary of the largest 'chunk' in the chunk_list

    """
    biggest_chunk = []
    if len(chunk_list) == 0:
        return biggest_chunk

    biggest_chunk_size = 0

    for c in chunk_list:
        if c[1]-c[0] > biggest_chunk_size:
            biggest_chunk = [c]
            biggest_chunk_size = c[1]-c[0]
    return biggest_chunk


def reconcile_calibration_selections(
        auto_calibration_dict,
        man_calibration_dict,
        local_logger
        ):
    """
    Parameters
    ----------
    auto_calibration_dict : Dict
        Dict describing baseline measures and parameters to use for calibration
        from autmated selection
    man_calibration_dict : Dict
        Dict describing baseline measures and parameters to use for calibration
        from manual selection
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    o2_cal_dict : Dict
        Dict describing baseline measures and parameters to use for calibration
    co2_cal_dict : Dict
        Dict describing baseline measures and parameters to use for calibration

    """
    o2_cal_dict = {}
    temp_o2_cal_dict = {}
    co2_cal_dict = {}
    temp_co2_cal_dict = {}

    if auto_calibration_dict is not None and man_calibration_dict is not None:
        local_logger.warning('gas calibration data present in both ' +
            'automated and manual selections - manual selections ' +
            'will override automated selections if they correscpond ' +
            'to the same nominal concentrations')

    if auto_calibration_dict is not None:

        for i in range(len(auto_calibration_dict['o2']['nom'])):
            if auto_calibration_dict['o2']['nom'][i] not in o2_cal_dict:
                o2_cal_dict[auto_calibration_dict['o2']['nom'][i]] = [
                    auto_calibration_dict['o2']['voltage'][i]]
            else:
                o2_cal_dict[auto_calibration_dict['o2']['nom'][i]].append(
                    auto_calibration_dict['o2']['voltage'][i]
                    )
        for i in range(len(auto_calibration_dict['co2']['nom'])):
            if auto_calibration_dict['co2']['nom'][i] not in co2_cal_dict:
                co2_cal_dict[auto_calibration_dict['co2']['nom'][i]] = [
                    auto_calibration_dict['co2']['voltage'][i]]
            else:
                co2_cal_dict[auto_calibration_dict['co2']['nom'][i]].append(
                    auto_calibration_dict['co2']['voltage'][i]
                    )

    if man_calibration_dict is not None:

        for i in range(len(man_calibration_dict['o2']['nom'])):
            if man_calibration_dict['o2']['nom'][i] not in temp_o2_cal_dict:
                temp_o2_cal_dict[man_calibration_dict['o2']['nom'][i]] = [
                    man_calibration_dict['o2']['voltage'][i]]
            else:

                temp_o2_cal_dict[man_calibration_dict['o2']['nom'][i]].append(
                    man_calibration_dict['o2']['voltage'][i]
                    )
        for i in range(len(man_calibration_dict['co2']['nom'])):
            if man_calibration_dict['co2']['nom'][i] not in temp_co2_cal_dict:
                temp_co2_cal_dict[man_calibration_dict['co2']['nom'][i]] = [
                    man_calibration_dict['co2']['voltage'][i]]
            else:

                temp_co2_cal_dict[man_calibration_dict['co2']['nom'][i]].append(
                    man_calibration_dict['co2']['voltage'][i]
                    )
        for k in temp_o2_cal_dict:
            o2_cal_dict[k] = temp_o2_cal_dict[k]
        for k in temp_co2_cal_dict:
            co2_cal_dict[k] = temp_co2_cal_dict[k]

    o2_cal_dict['avg'] = {}
    co2_cal_dict['avg'] = {}

    for k in o2_cal_dict:
        if k != 'avg':

            o2_cal_dict['avg'][k] = (sum(o2_cal_dict[k]) /
                len(o2_cal_dict[k]))
    for k in co2_cal_dict:
        if k != 'avg':
            co2_cal_dict['avg'][k] = (sum(co2_cal_dict[k]) /
                len(co2_cal_dict[k]))

    return o2_cal_dict, co2_cal_dict


def apply_gas_calibration(
        signal_data,
        breath_list,
        o2_cal_dict,
        co2_cal_dict,
        local_logger
        ):
    """
    

    Parameters
    ----------
    signal_data : Pandas.DataFrame
        DataFrame containing signal data
    breath_list : Pandas.DataFrame
        DataFrame containing annotated breaths
    o2_cal_dict : Dict
        Dict describing O2 Calibration Parameters
    co2_cal_dict : Dict
        Dict describing CO2 Calbration Parameters
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    signal_calibrated_o2 : Pandas.DataSeries
        Calibrated O2 matched to signal_data
    signal_calibrated_co2 : Pandas.DataSeries
        Calibrated CO2 matched to signal_data
    breath_list_calibrated_o2 : Pandas.DataSeries
        Calibrated O2 matched to breath_list
    breath_list_calibrated_co2 : Pandas.DataSeries
        Calibrated CO2 matched to breath_list

    """

    if 0 not in o2_cal_dict and 0 < len(o2_cal_dict) < 2:
        local_logger.warning(
            'only one O2 calibration data point present - ' +
            '2 point curve will be created with assumption of 0 volts = 0%'
            )
        O2_curve = {0: 0}
    else: O2_curve = {}
    if 0 not in co2_cal_dict and 0 < len(co2_cal_dict) < 2:
        local_logger.warning(
            'only one CO2 calibration data point present - ' +
            '2 point curve will be created with assumption of 0 volts = 0%'
            )
        CO2_curve = {0: 0}
    else: CO2_curve = {}

    for k in o2_cal_dict:
        O2_curve[k] = o2_cal_dict[k]
    for k in co2_cal_dict:
        CO2_curve[k] = co2_cal_dict[k]

    O2_standards = list(O2_curve['avg'].keys())
    CO2_standards = list(CO2_curve['avg'].keys())

    if len(O2_standards) > 1:
        O2_slope, O2_intercept, r, p, s = stats.linregress(
            O2_standards, [O2_curve['avg'][k] for k in O2_standards]
            )
        signal_calibrated_o2 = (signal_data['o2']-O2_intercept)/O2_slope
        breath_list_calibrated_o2 = (breath_list['o2']-O2_intercept)/O2_slope
    else:
        signal_calibrated_o2 = signal_data['corrected_o2']
        breath_list_calibrated_o2 = breath_list['corrected_o2']
        local_logger.warning(
            'unable to calibrate O2 - insufficient data - ' +
            'correction factor multiplier provided in analysis paramters used'
            )

    if len(CO2_standards) > 1:
        CO2_slope, CO2_intercept, r, p, s = stats.linregress(
            CO2_standards, [CO2_curve['avg'][k] for k in CO2_standards]
            )
        signal_calibrated_co2 = (signal_data['co2']-CO2_intercept)/CO2_slope
        breath_list_calibrated_co2 = \
            (breath_list['co2']-CO2_intercept)/CO2_slope
    else:
        signal_calibrated_co2 = signal_data['corrected_co2']
        breath_list_calibrated_co2 = breath_list['corrected_co2']
        local_logger.warning(
            'unable to calibrate CO2 - insufficient data - ' +
            'correction factor multiplier provided in analysis paramters used'
            )

    return signal_calibrated_o2, signal_calibrated_co2, \
        breath_list_calibrated_o2, breath_list_calibrated_co2


def calibrate_gas(
        signal_data,
        breath_list,
        auto_criteria,
        manual_selection,
        plyuid,
        timestamp_dict,
        local_logger
        ):
    """
    

    Parameters
    ----------
    signal_data : Pandas.DataFrame
        DataFrame containing signal data
    breath_list : Pandas.DataFrame
        DataFrame containing annotated breaths
    auto_criteria : Dict
        Dict with info describing criteria for automated selection of breathing
        for 'calm quiet' breathing
    manual_selection : Dict
        Dict with info describing manually selected start and stop points for
        breathing of interest
    plyuid : string
        serial identifier for data collection event
    timestamp_dict : Dict
        Dictionairy containing timestamps and text used to describe them. 
        Captured from the commends in the signal_data
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    signal_calibrated_o2 : Pandas.DataSeries
        Calibrated O2 matched to signal_data
    signal_calibrated_co2 : Pandas.DataSeries
        Calibrated CO2 matched to signal_data
    breath_list_calibrated_o2 : Pandas.DataSeries
        Calibrated O2 matched to breath_list
    breath_list_calibrated_co2 : Pandas.DataSeries
        Calibrated CO2 matched to breath_list

    """

    auto_calibration_dict = create_auto_calibration_dict(
        signal_data,
        breath_list,
        auto_criteria,
        timestamp_dict,
        local_logger
        )

    man_calibration_dict = create_man_calibration_dict(
        signal_data,
        manual_selection,
        plyuid
        )

    o2_cal_dict, co2_cal_dict = reconcile_calibration_selections(
        auto_calibration_dict,
        man_calibration_dict,
        local_logger
        )

    signal_calibrated_o2, signal_calibrated_co2, \
    breath_list_calibrated_o2, breath_list_calibrated_co2 = \
        apply_gas_calibration(
        signal_data,
        breath_list,
        o2_cal_dict,
        co2_cal_dict,
        local_logger
        )

    return signal_calibrated_o2, signal_calibrated_co2, \
        breath_list_calibrated_o2, breath_list_calibrated_co2


def make_filter_from_chunk_list(ts_inhale_and_ts_end, chunk_list):
    """
    

    Parameters
    ----------
    ts_inhale_and_ts_end : Pandas.DataFrame
        DataFrame describing transition times for inhalation and end of breath
    chunk_list : List of tuples of Ints
        List of Tuples of Floats describing Indexes that should be included 
        in the filter

    Returns
    -------
    df_inhale_and_end['filter'] : Pandas.DataSeries
        Binary filter based on the input timelist
    
    df_inhale_and_end['selection_id'] : Pandas.DataSeries
        Selection ID metadata for the input timelist

    """
    df_inhale_and_end = pandas.DataFrame(ts_inhale_and_ts_end.copy())
    df_inhale_and_end['filter'] = 0
    df_inhale_and_end['selection_id'] = ""
    for chunk in chunk_list:
        df_inhale_and_end.loc[
            (df_inhale_and_end['ts_inhale'] >=
                 df_inhale_and_end.iloc[chunk[0]]['ts_inhale']) &
            (df_inhale_and_end['ts_end'] <=
                 df_inhale_and_end.iloc[chunk[1]]['ts_end']),
            'filter'
            ] = 1
        df_inhale_and_end.loc[
            (df_inhale_and_end['ts_inhale'] >=
                 df_inhale_and_end.iloc[chunk[0]]['ts_inhale']) &
            (df_inhale_and_end['ts_end'] <=
                 df_inhale_and_end.iloc[chunk[1]]['ts_end']),
            'selection_id'
            ] = chunk[0]
    return df_inhale_and_end['filter'],df_inhale_and_end['selection_id']


def make_filter_from_time_list(ts_inhale_and_ts_end, time_list):
    """
    

    Parameters
    ----------
    ts_inhale_and_ts_end : Pandas.DataFrame
        DataFrame describing transition times for inhalation and end of breath
    time_list : List of tuples of Floats
        List of Tuples of Floats describing beginning and ending of timestamps
        that should be included in the filter

    Returns
    -------
    df_inhale_and_end['filter'] : Pandas.DataSeries
        Binary filter based on the input timelist
    
    df_inhale_and_end['selection_id'] : Pandas.DataSeries
        Selection ID metadata for the input timelist
    

    """
    df_inhale_and_end = pandas.DataFrame(ts_inhale_and_ts_end.copy())
    df_inhale_and_end['filter'] = 0
    df_inhale_and_end['selection_id'] = ""
    for timestamps in time_list:
        df_inhale_and_end.loc[
            (df_inhale_and_end['ts_inhale'] >= timestamps[0]) &
            (df_inhale_and_end['ts_end'] <= timestamps[1]),
            'filter'
            ] = 1
        df_inhale_and_end.loc[
            (df_inhale_and_end['ts_inhale'] >= timestamps[0]) &
            (df_inhale_and_end['ts_end'] <= timestamps[1]),
            'selection_id'
            ] = timestamps[0]
    return df_inhale_and_end['filter'],df_inhale_and_end['selection_id']


def create_filters_for_automated_selections(
        signal_data,
        breath_list,
        auto_criteria,
        timestamp_dict,
        analysis_parameters,
        local_logger
        ):
    """
    

    Parameters
    ----------
    signal_data : Pandas.DataFrame
        DataFrame containing signal data
    breath_list : Pandas.DataFrame
        DataFrame containing annotated breaths
    auto_criteria : Dict
        Dict with info describing criteria for automated selection of breathing
        for 'calm quiet' breathing
    timestamp_dict : Dict
        Dictionairy containing timestamps and text used to describe them. 
        Captured from the commends in the signal_data
    analysis_parameters : Dict
        Dict of settings to use for analysis
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    block_dict : Nested Dict
        Nested Dict describing boundaries of selected blocks and related 
        information such as a filter indicating member breaths, timestamp 
        boundaries, etc.

    """
    block_dict = {}
    if auto_criteria is None:
        return block_dict
    
    automated_block = pandas.DataFrame(breath_list['ts_inhale'].copy())
    automated_selection = pandas.DataFrame(breath_list['ts_inhale'].copy())
    automated_biggest_block = pandas.DataFrame(breath_list['ts_inhale'].copy())

    all_keys = auto_criteria['Key'].unique()

    auto_keys = auto_criteria[['Key', 'Alias']]
    auto_keys.loc[:, 'key_and_alias'] = \
        auto_keys['Key'].copy().astype(
            str)+auto_keys['Alias'].copy().astype(str)

    reverse_timestamp_dict = {}
    
    if analysis_parameters.get('Pneumo_Mode') == '1':
        for k in timestamp_dict:
            if timestamp_dict[k][3:] in all_keys:
                reverse_timestamp_dict[timestamp_dict[k][3:]] = k

    else:
        
        for k in timestamp_dict:
            if timestamp_dict[k][3:-1] in all_keys:
                reverse_timestamp_dict[timestamp_dict[k][3:-1]] = k
    

    for key_and_alias in auto_keys['key_and_alias']:

        key = auto_keys[
            auto_keys['key_and_alias'] == key_and_alias
            ]['Key'].values[0]
        alias = auto_keys[
            auto_keys['key_and_alias'] == key_and_alias
            ]['Alias'].values[0]
        if key not in reverse_timestamp_dict:
            continue

        block_dict[key_and_alias] = {}

        current_auto_criteria = \
            auto_criteria[
                (auto_criteria['Key'] == key) & (
                    auto_criteria['Alias'] == alias)
                ].to_dict('records')[0]

        block_start, block_stop = extract_block_bounds(
            signal_data, reverse_timestamp_dict, all_keys, key
            )
        verified_block_start = max(
            block_start + float(current_auto_criteria['after_start']),
            block_stop - float(current_auto_criteria['within_end'])
            )
        verified_block_stop = min(
            block_stop - float(current_auto_criteria['before_end']),
            block_start + float(current_auto_criteria['within_start'])
            )

        
        high_chamber_temp_filter = breath_list['Body_Temperature'] < \
            breath_list['corrected_temp']
        
        if 'calibrated_TV' in breath_list.columns and \
                current_auto_criteria['max_calibrated_TV'] != 'off':
            high_TV_filter = breath_list['calibrated_TV'] < \
                float(current_auto_criteria['max_calibrated_TV'])
        else:
            high_TV_filter = \
                breath_list['ts_inhale'] == breath_list['ts_inhale']
        
        if 'VE_per_VO2' in breath_list.columns and \
                current_auto_criteria['max_VEVO2'] != 'off':
            high_VEVO2_filter = breath_list['VE_per_VO2'] < \
                float(current_auto_criteria['max_VEVO2'])
        else:
            high_VEVO2_filter = \
                breath_list['ts_inhale'] == breath_list['ts_inhale']
            


        automated_block[key_and_alias] = 0
        automated_selection[key_and_alias] = 0
        automated_biggest_block[key_and_alias] = 0

        automated_block.loc[
            (current_auto_criteria['min_CO2'] <= breath_list['calibrated_co2']) &
            (current_auto_criteria['max_CO2'] >= breath_list['calibrated_co2']) &
            (current_auto_criteria['min_O2'] <= breath_list['calibrated_o2']) &
            (current_auto_criteria['max_O2'] >= breath_list['calibrated_o2']) &
            (breath_list['ts_inhale'] >= verified_block_start) &
            (breath_list['ts_end'] <= verified_block_stop),
            key_and_alias
            ] = 1
        automated_selection.loc[
            (current_auto_criteria['min_CO2'] <= breath_list['calibrated_co2']) &
            (current_auto_criteria['max_CO2'] >= breath_list['calibrated_co2']) &
            (current_auto_criteria['min_O2'] <= breath_list['calibrated_o2']) &
            (current_auto_criteria['max_O2'] >= breath_list['calibrated_o2']) &
            (breath_list['ts_inhale'] >= verified_block_start) &
            (breath_list['ts_end'] <= verified_block_stop) &
            (current_auto_criteria['min_TT'] <= breath_list['TT']) &
            (current_auto_criteria['max_TT'] >= breath_list['TT']) &
            (current_auto_criteria['max_DVTV'] >= breath_list['DVTV']) &
            (current_auto_criteria['max_pX'] >=
             breath_list['per_X_calculation']) &
            (current_auto_criteria['min_TV'] <= breath_list['iTV']) &
            (current_auto_criteria['min_TV'] <= breath_list['eTV']) &
            (current_auto_criteria['include_apnea'] >= breath_list['apnea']) &
            (current_auto_criteria['include_sigh'] >= breath_list['sigh']) &
            (current_auto_criteria['include_high_chamber_temp'] >=
             high_chamber_temp_filter) &
            (current_auto_criteria['vol_mov_avg_drift'] >=
             breath_list['mov_avg_vol']) &
            (high_VEVO2_filter == 1) &
            (high_TV_filter == 1),
            key_and_alias
            ] = 1

        blocks = get_the_chunks(
            automated_block[key_and_alias],
            1,
            int(current_auto_criteria['min_bout'])
            )
        biggest_block = get_the_biggest_chunk(blocks)
        selection_list = get_the_chunks(
            automated_selection[key_and_alias],
            1,
            int(current_auto_criteria['min_bout'])
            )
        if biggest_block is []:
            local_logger.warning(
                'AUTO {} | {} - '.format(key, alias) +
                'no suitable data found'
            )
            continue
        else:
            block_dict[key_and_alias]['biggest_block'], \
            block_dict[key_and_alias]['block_id'] = \
                make_filter_from_chunk_list(
                    breath_list[['ts_inhale', 'ts_end']],
                    biggest_block
                    )

            block_dict[key_and_alias]['selection_filter'], \
            block_dict[key_and_alias]['selection_id'] = \
                make_filter_from_chunk_list(
                    breath_list[['ts_inhale', 'ts_end']],
                    selection_list
                    )

    return block_dict


def create_filters_for_manual_selections(
        breath_list,
        manual_selection,
        plyuid,
        logger
        ):
    """
    

    Parameters
    ----------
    breath_list : Pandas.DataFrame
        DataFrame containing annotated breaths
    manual_selection : Dict
        Dict with info describing manually selected start and stop points for
        breathing of interest
    plyuid : string
        serial identifier for data collection event 
        (plethysmography session id)
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    block_dict : Nested Dict
        Nested Dict describing boundaries of selected blocks and related 
        information such as a filter indicating member breaths, timestamp 
        boundaries, etc.

    """

    block_dict = {}
    if manual_selection is None:
        return block_dict
    
    alias_dict = {}
    for segment_index in \
        manual_selection[
            (manual_selection['PLYUID'].astype(str) == plyuid)
            ].index:
        chunk_start = manual_selection.iloc[segment_index]['start']
        chunk_stop = manual_selection.iloc[segment_index]['stop']

        if manual_selection.iloc[segment_index]['Alias'] not in block_dict:
            alias_dict[manual_selection.iloc[segment_index]['Alias']] = []

        alias_dict[manual_selection.iloc[segment_index]
            ['Alias']].append([chunk_start, chunk_stop])

    for alias in alias_dict:
        selection_filter,selection_id = make_filter_from_time_list(
            breath_list[['ts_inhale', 'ts_end']],
            alias_dict[alias])
        
        block_dict[alias] = {
            'selection_filter':selection_filter,
            'selection_id':selection_id
            }
    return block_dict


def collect_calibration_parameters(
        breath_list,
        analysis_parameters,
        animal_metadata,
        plyuid,
        auto_criteria,
        manual_selection,
        automated_selections_filters,
        manual_selections_filters,
        local_logger
        ):
    """

    Parameters
    ----------
    breath_list : Pandas.DataFrame
        DataFrame containing annotated breaths
    analysis_parameters : dict
        dictionary containing settings for analysis
    animal_metadata : dict
        dict indexed by 'PlyUID' containing animal metadata
    plyuid : string
        serial identifier for data collection event 
        (plethysmography session id)
    auto_criteria : Dict
        Dict with info describing criteria for automated selection of breathing
        for 'calm quiet' breathing
    manual_selection : Dict
        Dict with info describing manually selected start and stop points for
        breathing of interest
    automated_selections_filters : Nested Dict with Lists
        Nested Dict with binary lists describing which breaths are associated
        with passing/failing particular filters
    manual_selections_filters : Nested Dict with Lists
        Nested Dict with binary lists describing which breaths are associated 
        with passing/failing particular filters
    local_logger : instance of logging.logger

    Returns
    -------
    calibration_dict : Nested Dict
        Nested Dict containing calibration parameters to be applied to 
        automated of manually selected breaths

    """
    
    calibration_dict = {}

    if 'Bar_Pres' in animal_metadata[plyuid]:
        calibration_dict['room_baro_mmHg'] = \
            animal_metadata[plyuid]['Bar_Pres']*25.4
        local_logger.info('Barometric Pressure field found [Bar_Pres] ' +
                          'units assumed to be inHg')
    elif 'Room Baro mmHg' in animal_metadata[plyuid]:
        calibration_dict['room_baro_mmHg'] = \
            animal_metadata[plyuid]['Room Baro mmHg']
        local_logger.info('Barometric Pressure field found [Room Baro mmHg] ' +
                          'units assumed to be mmHg')
    else:
        calibration_dict['room_baro_mmHg'] = 760
        local_logger.warning('No Barometric Pressure field found, set at ' +
                             'default of 760 mmHg')

    if 'Calibration_Volume' in animal_metadata[plyuid]:
        calibration_dict['cal_vol_mL'] = \
            animal_metadata[plyuid]['Calibration_Volume'] / 1000
        local_logger.info('Calibration Volume field found ' +
                          '[Calibration_Volume] units assumed to be uL')
    elif 'Cal vol mL' in animal_metadata[plyuid]:
        calibration_dict['cal_vol_mL'] = \
            animal_metadata[plyuid]['Cal vol mL']
        local_logger.info('Calibration Volume field found ' +
                          '[Cal vol mL] units assumed to be mL')
    else:
        calibration_dict['cal_vol_mL'] = 0.02
        local_logger.warning('No Calibration Volume field found, set at ' +
                             'default of 0.02 mL')

    if 'Rotometer_Flowrate' in animal_metadata[plyuid]:
        calibration_dict['Flowrate (SLPM)'] = \
            numpy.interp(
                animal_metadata[plyuid]['Rotometer_Flowrate'],
                [float(i) for i in
                 analysis_parameters[
                     'rotometer_standard_curve_readings'
                     ].split(' ')
                 ],
                [float(i) for i in
                 analysis_parameters[
                     'rotometer_standard_curve_flowrates'
                     ].split(' ')
                 ]
                )
        local_logger.info('Flowrate field found [Rotometer_Flowrate] ' +
                          'units converted to SLPM using std curve')
    elif 'Flowrate (SLPM)' in animal_metadata[plyuid]:
        calibration_dict['Flowrate (SLPM)'] = animal_metadata[plyuid][
            'Flowrate (SLPM)'
            ]
        local_logger.info('Flowrate field found [Flowrate (SLPM)] ' +
                          'units assumed to be SLPM')
    else:
        calibration_dict['Flowrate (SLPM)'] = 0.5
        local_logger.warning('No Flowrate field fount, set at ' +
                             'default of 0.5 SLPM')

    if 'Weight' in animal_metadata[plyuid]:
        calibration_dict['Weight'] = animal_metadata[plyuid]['Weight']
        local_logger.info('Body Weight field found [Weight] ' +
                          'units assumed to be g')
    else:
        calibration_dict['Weight'] = 1
        local_logger.warning('No Body Weight field found, set at ' +
                             'default of 20g')

    if auto_criteria is not None or manual_selection is not None:
        calibration_dict['Cal_Segs'] = {}

    if auto_criteria is not None:
        calibration_dict['Auto_Cal_Match'] = {}
        for row in auto_criteria.index:
            key_and_seg = '{}{}'.format(
                auto_criteria.iloc[row]['Key'],
                auto_criteria.iloc[row]['Alias']
                )
            if key_and_seg not in automated_selections_filters:
                continue
            calibration_dict['Auto_Cal_Match'][
                '{}{}'.format(
                    auto_criteria.iloc[row]['Key'],
                    auto_criteria.iloc[row]['Alias']
                    )
                ] = {
                    'Key': auto_criteria.iloc[row]['Key'],
                    'Alias': auto_criteria.iloc[row]['Alias'],
                    'Cal Seg': auto_criteria.iloc[row]['Cal Seg']
                    }
        for row in auto_criteria[auto_criteria['AUTO_IND_CAL'] == 1].index:
            key_and_seg = '{}{}'.format(
                auto_criteria.iloc[row]['Key'],
                auto_criteria.iloc[row]['Alias']
                )
            if key_and_seg not in automated_selections_filters:
                continue
            calibration_dict['Cal_Segs'][
                auto_criteria.iloc[row]['Alias']] = {
                    'Key or segment': auto_criteria.iloc[row]['Key'],
                    'Alias': auto_criteria.iloc[row]['Alias'],
                    'Auto_or_Man': 'Auto',
                    'o2': breath_list[
                        (automated_selections_filters[key_and_seg]\
                         ['biggest_block'] == 1) &
                        (automated_selections_filters[key_and_seg]
                         ['selection_filter'] == 1)
                        ]['calibrated_o2'].mean(),
                    'co2': breath_list[
                        (automated_selections_filters[key_and_seg]\
                         ['biggest_block'] == 1) &
                        (automated_selections_filters[key_and_seg]
                         ['selection_filter'] == 1)
                        ]['calibrated_co2'].mean(),
                    'tv': breath_list[
                        (automated_selections_filters[key_and_seg]\
                         ['biggest_block'] == 1) &
                        (automated_selections_filters[key_and_seg]
                         ['selection_filter'] == 1)
                        ]['iTV'].mean()
                    }

    if manual_selection is not None:
        calibration_dict['Man_Cal_Match'] = {}
        for row in manual_selection[
                manual_selection['PLYUID'].astype(str) == plyuid
                ].index:
            calibration_dict['Man_Cal_Match'][
                manual_selection.iloc[row]['Alias']
                ] = {
                    'segment': manual_selection.iloc[row]['segment'],
                    'Alias': manual_selection.iloc[row]['Alias'],
                    'Cal Seg': manual_selection.iloc[row]['Cal Seg']
                    }
        for row in manual_selection[
                (manual_selection['PLYUID'].astype(str) == plyuid) &
                (manual_selection['MAN_IND_CAL'] == 1)
                ].index:
            if manual_selection.iloc[row]['Alias'] in \
                    calibration_dict['Cal_Segs']:
                local_logger.warning(
                    'Manual Selection defines a calibration segment ' +
                    'that was already added, settings may be overwritten'
                    )
            calibration_dict['Cal_Segs'][
                manual_selection.iloc[row]['Alias']] = {
                    'Key or segment': manual_selection.iloc[row]['segment'],
                    'Alias': manual_selection.iloc[row]['Alias'],
                    'Auto_or_Man': 'Man',
                    'o2': breath_list[
                        manual_selections_filters['{}'.format(
                            manual_selection.iloc[row]['Alias']
                            )]['selection_filter'] == 1
                        ]['calibrated_o2'].mean(),
                    'co2': breath_list[
                        manual_selections_filters['{}'.format(
                            manual_selection.iloc[row]['Alias']
                            )]['selection_filter'] == 1
                        ]['calibrated_co2'].mean(),
                    'tv': breath_list[
                        manual_selections_filters['{}'.format(
                            manual_selection.iloc[row]['Alias']
                            )]['selection_filter'] == 1
                        ]['iTV'].mean()
                    }

    return calibration_dict



def getvaporpressure(temperature):
    """
    Parameters
    ----------
    temperature : Float
        Temperature in degrees Celsius

    Returns
    -------
    Float
        Vapor Pressure of Water

    """
    return \
        (
            1.142 + (0.8017 * temperature) -
            (0.012 * temperature ** 2) + (0.0006468 * temperature ** 3)
            )


def getK(C):
    """
    Parameters
    ----------
    C : Float
        Temperature in degrees Celsius

    Returns
    -------
    Float
        Temperature in Kelvin

    """
    return (C+273.15)


def get_BT_TV_K(tv, calv, act_calv, t_body, t_chamb, room_pressure):
    """
    Parameters
    ----------
    tv : Float
        uncorrected tidal volume (V)
    calv : Float
        uncorrected tidal volume from calibration period (V)
    act_calv : Float
        nominal calibration volume (mL)
    t_body : Float
        Body Temperature (Celsius)
    t_chamb : Float
        Chamber Temperature (Celsius)
    room_pressure : Float
        Room Barometric Pressure (mmHg)

    Returns
    -------
    Float
        corrected tidal volume (mL)

    """
    return \
        (tv/calv) * (act_calv) * \
        (getK(t_body) * (room_pressure-getvaporpressure(t_chamb))) / \
        (
            (
                getK(t_body) * (room_pressure - getvaporpressure(t_chamb))
                ) -
                getK(t_chamb) * (room_pressure - getvaporpressure(t_body)))


def get_pneumo_TV(tv,calv,act_calv):
    """
    Parameters
    ----------
    tv : Float
        uncorrected tidal volume (V)
    calv : Float
        uncorrected tidal volume from calibration period (V)
    act_calv : Float
        nominal calibration volume (mL)

    Returns
    -------
    Float
        corrected tidal volume (mL)

    """
    
    return tv / calv * act_calv


def get_VO2(o2_in, o2_out, flowrate):
    """
    calculates Volume of O2 (mL) consumed per minute

    Parameters
    ----------
    o2_in : Float
        O2 concentration (%) into the chamber
    o2_out : Float
        O2 concentration (%) out of the chamber
    flowrate : Float
        flowrate (mL) of air through the chamber

    Returns
    -------
    Float
        Volume of O2 (mL) consumed per minute.

    """
    
    return (flowrate*1000*o2_in/100-flowrate*1000*o2_out/100)


def get_VCO2(co2_in, co2_out, flowrate):
    """
    calculates Volume of CO2 (mL) produced per minute

    Parameters
    ----------
    co2_in : Float
        CO2 concentration (%) into the chamber
    co2_out : Float
        CO2 concentration (%) out of the chamber
    flowrate : Float
        flowrate (mL) of air through the chamber

    Returns
    -------
    Float
        Volume of CO2 (mL) produced per minute.    
    """
    
    return (flowrate*1000*co2_out/100-flowrate*1000*co2_in/100)


def apply_volumetric_and_respiratory_calculations(
        breath_list,
        calibration_parameters,
        automated_selections_filters,
        manual_selections_filters,
        analysis_parameters,
        local_logger
        ):
    local_logger.info('Applying volumetric and respiratory calculations')
    basic_volume_list = populate_baseline_values_for_calibration_calculations(
        breath_list, 
        calibration_parameters, 
        automated_selections_filters, 
        manual_selections_filters, 
        local_logger
        )
    if analysis_parameters.get('Pneumo_Mode') == '1':
        enhanced_volume_list = \
            calculate_calibrated_pneumo_volume_and_respiration(
                breath_list,
                basic_volume_list,
                calibration_parameters
                )
    else:
        enhanced_volume_list = calculate_calibrated_volume_and_respiration(
            breath_list,
            basic_volume_list,
            calibration_parameters
            )
    return enhanced_volume_list

def calculate_calibrated_pneumo_volume_and_respiration(
        breath_list,
        volume_list,
        calibration_parameters
        ):
    """
    

    Parameters
    ----------
    breath_list : Pandas.DataFrame
        DataFrame containing annotated breaths
    volume_list : Pandas.DataFrame
        DataFrame related to breath_list, but with baseline volume data placed
        for later use in calculations
    calibration_parameters : Dict
        Dict containing parameters needed for calculating calibrated volumes

    Returns
    -------
    enhanced_volume_list : Pandas.DataFrame
        DataFrame describing calibrated volume and respiratory data

    """

    enhanced_volume_list = volume_list.copy()
    
    enhanced_volume_list['calibrated_TV'] = get_pneumo_TV(
        breath_list['iTV'],
        volume_list['base_tv'],
        calibration_parameters['cal_vol_mL'],
        )

    enhanced_volume_list['calibrated_PIF'] = get_pneumo_TV(
        breath_list['PIF'],
        volume_list['base_tv'],
        calibration_parameters['cal_vol_mL'],
        )

    enhanced_volume_list['calibrated_PEF'] = get_pneumo_TV(
        breath_list['PEF'],
        volume_list['base_tv'],
        calibration_parameters['cal_vol_mL'],
        )

    enhanced_volume_list['VO2'] = get_VO2(
        volume_list['base_o2'],
        breath_list['o2'],
        calibration_parameters['Flowrate (SLPM)']
        )

    enhanced_volume_list['VCO2'] = get_VCO2(
        volume_list['base_co2'],
        breath_list['co2'],
        calibration_parameters['Flowrate (SLPM)']
        )
    
    enhanced_volume_list['VE'] = breath_list['BPM'] * \
        enhanced_volume_list['calibrated_TV']
    enhanced_volume_list['VE_per_VO2'] = enhanced_volume_list['VE'] / \
        enhanced_volume_list['VO2']
    enhanced_volume_list['RER'] = enhanced_volume_list['VCO2'] / \
        enhanced_volume_list['VO2']
    enhanced_volume_list['calibrated_TV_per_gram'] = enhanced_volume_list[
        'calibrated_TV'] / calibration_parameters['Weight']
    enhanced_volume_list['VE_per_gram'] = enhanced_volume_list[
        'VE'] / calibration_parameters['Weight']
    enhanced_volume_list['VO2_per_gram'] = enhanced_volume_list[
        'VO2'] / calibration_parameters['Weight']
    enhanced_volume_list['VCO2_per_gram'] = enhanced_volume_list[
        'VCO2'] / calibration_parameters['Weight']
    enhanced_volume_list['TT_per_TV'] = breath_list['TT'] / \
        enhanced_volume_list['calibrated_TV']
    enhanced_volume_list['TT_per_TVpg'] = breath_list['TT'] / \
        enhanced_volume_list['calibrated_TV_per_gram']
    enhanced_volume_list['O2_per_Air'] = enhanced_volume_list[
        'VO2'] * breath_list['TT'] / 60 / enhanced_volume_list['calibrated_TV']

    return enhanced_volume_list

def populate_baseline_values_for_calibration_calculations(
        breath_list,
        calibration_parameters,
        automated_selections_filters,
        manual_selections_filters,
        local_logger
        ):
    """

    Parameters
    ----------
    breath_list : Pandas.DataFrame
        DataFrame containing annotated breaths
    calibration_parameters : Dict
        Dict containing parameters needed for calculating calibrated volumes
    automated_selections_filters : Nested Dict with Lists
        Nested Dict with binary lists describing which breaths are associated
        with passing/failing particular filters
    manual_selections_filters : Nested Dict with Lists
        Nested Dict with binary lists describing which breaths are associated 
        with passing/failing particular filters
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    volume_list : Pandas.DataFrame
        DataFrame related to breath_list, but with baseline volume data placed
        for later use in calculations

    """
    
    volume_list = pandas.DataFrame(breath_list['ts_inhale'].copy())
    
    volume_list['base_selection'] = numpy.nan
    volume_list['base_o2'] = numpy.nan
    volume_list['base_co2'] = numpy.nan
    volume_list['base_tv'] = numpy.nan

    if 'Auto_Cal_Match' in calibration_parameters:
        if len(calibration_parameters['Auto_Cal_Match']) > 0:
            for key_and_alias in automated_selections_filters:
                volume_list.loc[
                    (automated_selections_filters[key_and_alias]
                         ['biggest_block'] == 1) &
                    (automated_selections_filters[key_and_alias]
                         ['selection_filter'] == 1),
                    'base_selection'] = calibration_parameters[
                        'Auto_Cal_Match'
                    ][key_and_alias]['Cal Seg']
                volume_list.loc[
                    (automated_selections_filters[key_and_alias]
                         ['biggest_block'] == 1) &
                    (automated_selections_filters[key_and_alias]
                         ['selection_filter'] == 1),
                    'base_o2'] = calibration_parameters[
                        'Cal_Segs'][calibration_parameters['Auto_Cal_Match']
                                    [key_and_alias]['Cal Seg']]['o2']
                volume_list.loc[
                    (automated_selections_filters[key_and_alias]
                         ['biggest_block'] == 1) &
                    (automated_selections_filters[key_and_alias]
                         ['selection_filter'] == 1),
                    'base_co2'] = calibration_parameters[
                        'Cal_Segs'][calibration_parameters['Auto_Cal_Match']
                                    [key_and_alias]['Cal Seg']]['co2']
                volume_list.loc[
                    (automated_selections_filters[key_and_alias]
                         ['biggest_block'] == 1) &
                    (automated_selections_filters[key_and_alias]
                         ['selection_filter'] == 1),
                    'base_tv'] = calibration_parameters[
                        'Cal_Segs'][calibration_parameters['Auto_Cal_Match']
                                    [key_and_alias]['Cal Seg']]['tv']

    if 'Man_Cal_Match' in calibration_parameters:
        if len(calibration_parameters['Man_Cal_Match']) > 0:
            for alias in manual_selections_filters:
                volume_list.loc[
                    manual_selections_filters[alias]
                         ['selection_filter'] == 1,
                         'base_selection'] = calibration_parameters[
                             'Man_Cal_Match'
                             ][alias]['Cal Seg']
                volume_list.loc[
                    manual_selections_filters[alias]
                        ['selection_filter'] == 1,
                        'base_o2'] = calibration_parameters[
                            'Cal_Segs'][calibration_parameters['Man_Cal_Match']
                                        [alias]['Cal Seg']]['o2']
                volume_list.loc[
                    manual_selections_filters[alias]
                        ['selection_filter'] == 1,
                        'base_co2'] = calibration_parameters[
                            'Cal_Segs'][calibration_parameters['Man_Cal_Match']
                                        [alias]['Cal Seg']]['co2']
                volume_list.loc[
                    manual_selections_filters[alias]
                        ['selection_filter'] == 1,
                        'base_tv'] = calibration_parameters[
                            'Cal_Segs'][calibration_parameters['Man_Cal_Match']
                                        [alias]['Cal Seg']]['tv']

    return volume_list



def calculate_calibrated_volume_and_respiration(
        breath_list,
        volume_list,
        calibration_parameters,
        analysis_parameters
        ):
    """
    

    Parameters
    ----------
    breath_list : Pandas.DataFrame
        DataFrame containing annotated breaths
    volume_list : Pandas.DataFrame
        DataFrame related to breath_list, but with baseline volume data placed
        for later use in calculations
    calibration_parameters : Dict
        Dict containing parameters needed for calculating calibrated volumes
    analysis_parameters : Dict
        Dict of settings to use for analysis

    Returns
    -------
    enhanced_volume_list : Pandas.DataFrame
        DataFrame describing calibrated volume and respiratory data

    """
    
    enhanced_volume_list = volume_list.copy()
    enhanced_volume_list['calibrated_TV'] = get_BT_TV_K(
        breath_list['iTV'],
        volume_list['base_tv'],
        calibration_parameters['cal_vol_mL'],
        breath_list['Body_Temperature'],
        breath_list['corrected_temp'],
        calibration_parameters['room_baro_mmHg']
        )

    enhanced_volume_list['calibrated_PIF'] = get_BT_TV_K(
        breath_list['PIF'],
        volume_list['base_tv'],
        calibration_parameters['cal_vol_mL'],
        breath_list['Body_Temperature'],
        breath_list['corrected_temp'],
        calibration_parameters['room_baro_mmHg']
        )

    enhanced_volume_list['calibrated_PEF'] = get_BT_TV_K(
        breath_list['PEF'],
        volume_list['base_tv'],
        calibration_parameters['cal_vol_mL'],
        breath_list['Body_Temperature'],
        breath_list['corrected_temp'],
        calibration_parameters['room_baro_mmHg']
        )

    enhanced_volume_list['VO2'] = get_VO2(
        volume_list['base_o2'],
        breath_list['o2'],
        calibration_parameters['Flowrate (SLPM)']
        )

    enhanced_volume_list['VCO2'] = get_VCO2(
        volume_list['base_co2'],
        breath_list['co2'],
        calibration_parameters['Flowrate (SLPM)']
        )
    
    enhanced_volume_list['VE'] = breath_list['BPM'] * \
        enhanced_volume_list['calibrated_TV']
    enhanced_volume_list['VE_per_VO2'] = enhanced_volume_list['VE'] / \
        enhanced_volume_list['VO2']
    enhanced_volume_list['RER'] = enhanced_volume_list['VCO2'] / \
        enhanced_volume_list['VO2']
    enhanced_volume_list['calibrated_TV_per_gram'] = enhanced_volume_list[
        'calibrated_TV'] / calibration_parameters['Weight']
    enhanced_volume_list['VE_per_gram'] = enhanced_volume_list[
        'VE'] / calibration_parameters['Weight']
    enhanced_volume_list['VO2_per_gram'] = enhanced_volume_list[
        'VO2'] / calibration_parameters['Weight']
    enhanced_volume_list['VCO2_per_gram'] = enhanced_volume_list[
        'VCO2'] / calibration_parameters['Weight']
    enhanced_volume_list['TT_per_TV'] = breath_list['TT'] / \
        enhanced_volume_list['calibrated_TV']
    enhanced_volume_list['TT_per_TVpg'] = breath_list['TT'] / \
        enhanced_volume_list['calibrated_TV_per_gram']
    enhanced_volume_list['O2_per_Air'] = enhanced_volume_list[
        'VO2'] * breath_list['TT'] / 60 / enhanced_volume_list['calibrated_TV']

    return enhanced_volume_list



def create_output(
        breath_list,
        analysis_parameters,
        animal_metadata,
        auto_criteria,
        manual_selection,
        plyuid,
        automated_selections_filters,
        manual_selections_filters,
        column_dictionary,
        local_logger
        ):                
    """
    

    Parameters
    ----------
    breath_list : Pandas.DataFrame
        DataFrame containing annotated breaths
    analysis_parameters : Dict
        Dict of settings to use for analysis
    animal_metadata : Dict
        Dict of metadata information for an animal
    auto_criteria : Dict
        Dict with info describing criteria for automated selection of breathing
        for 'calm quiet' breathing
    manual_selection : Dict
        Dict with info describing manually selected start and stop points for
        breathing of interest
    plyuid : string
        serial identifier for data collection event 
        (plethysmography session id)
    automated_selections_filters : Nested Dict with Lists
        Nested Dict with binary lists describing which breaths are associated
        with passing/failing particular filters
    manual_selections_filters : Nested Dict with Lists
        Nested Dict with binary lists describing which breaths are associated 
        with passing/failing particular filters
        DESCRIPTION.
    column_dictionary : Dict
        Dict that indicates translation of current 'column names' for output
        to match the current preferred style
    local_logger : instance of logging.logger (optional)

    Returns
    -------
    output_list : Pandas DataFrame
        STAGG ready output, contains a breathlist and associated parameters 
        and metadata for subsequent statistical analysis

    """
    
    output_list = breath_list.copy()
    
    output_list['Exp_Condition'] = ""
    output_list['Auto_Condition'] = ""
    output_list['Breath_Inclusion_Filter'] = 0
    output_list['AUTO_Inclusion_Filter'] = 0
    output_list['MAN_Inclusion_Filter'] = 0
    output_list['Man_Condition'] = ""
    output_list['Auto_Block_Id'] = ""
    output_list['Auto_Selection_Id'] = ""
    output_list['Man_Selection_Id'] = ""
    output_list['AUTO_IND_INCLUDE'] = 0
    output_list['MAN_IND_INCLUDE'] = 0
    
    if auto_criteria is not None:
        
        auto_criteria['key_and_alias'] = \
            auto_criteria.copy()['Key'].astype(str) + \
            auto_criteria.copy()['Alias'].astype(str)
        
                            
        for row in auto_criteria.index:
            if auto_criteria.iloc[row]['key_and_alias'] not in \
                    automated_selections_filters:
                continue
            for c in auto_criteria.columns:
                if 'AUTO_IND_' == c[0:9]:
                        
                    if c not in output_list.columns:
                        output_list[c] = ""
                        
                    if auto_criteria.groupby(['Alias',c]).ngroups > \
                            auto_criteria.groupby(['Alias']).ngroups:
                        local_logger.warning(
                            'Shared Aliases in autocriteria with variant ' +\
                            'entries for {}'.format(c)
                            )
        
                    output_list.loc[automated_selections_filters[
                        auto_criteria.iloc[row]['key_and_alias']][
                            'biggest_block']==1,c] = auto_criteria.iloc[
                                row][c]
                                
            if 'AUTO_Condition_{}'.format(
                    auto_criteria.iloc[row]['Alias']
                    ) not in output_list.columns:
                output_list[
                    'AUTO_Condition_{}'.format(
                        auto_criteria.iloc[row]['Alias']
                        )
                    ] = 0
                
            output_list.loc[automated_selections_filters[
                auto_criteria.iloc[row]['key_and_alias']][
                    'biggest_block']==1,
                    'AUTO_Condition_{}'.format(
                        auto_criteria.iloc[row]['Alias']
                        )
                    ] = 1
                    
            output_list.loc[automated_selections_filters[
                auto_criteria.iloc[row]['key_and_alias']][
                    'biggest_block']==1,
                    'Auto_Condition'] = \
                        auto_criteria.iloc[row]['Alias']
                        
            output_list.loc[automated_selections_filters[
                auto_criteria.iloc[row]['key_and_alias']][
                    'biggest_block']==1,
                    'Auto_Block_Id'] = \
                        automated_selections_filters[
                            auto_criteria.iloc[row]['key_and_alias']
                            ]['block_id'][automated_selections_filters[
                                auto_criteria.iloc[row]['key_and_alias']][
                                    'biggest_block']==1]
                                
            
            output_list.loc[automated_selections_filters[
                auto_criteria.iloc[row]['key_and_alias']][
                    'selection_filter']==1,
                    'Breath_Inclusion_Filter'] = 1
                    
            output_list.loc[automated_selections_filters[
                auto_criteria.iloc[row]['key_and_alias']][
                    'selection_filter']==1,
                    'AUTO_Inclusion_Filter'] = 1
            
            output_list.loc[automated_selections_filters[
                auto_criteria.iloc[row]['key_and_alias']][
                    'selection_filter']==1,
                    'Auto_Selection_Id'] = \
                        automated_selections_filters[
                            auto_criteria.iloc[row]['key_and_alias']
                            ]['selection_id'][automated_selections_filters[
                                auto_criteria.iloc[row]['key_and_alias']][
                                    'selection_filter']==1]
                    
            
                        
    if manual_selection is not None:
        for alias in manual_selections_filters:
            for c in manual_selection.columns:
                if 'MAN_IND_' == c[0:8]:
                    
                    if c not in output_list.columns:
                        breath_list[c] = ""
                        
                    if manual_selection[
                            manual_selection['PLYUID'].astype(str)==plyuid
                            ].groupby(['Alias',c]).ngroups > \
                            manual_selection[
                                manual_selection['PLYUID'].astype(str)==\
                                    plyuid].groupby(['Alias']).ngroups:
                        local_logger.warning(
                            'Shared Aliases in manual select with variant '+\
                            'entries for {}'.format(c)
                            )
                    output_list.loc[manual_selections_filters[alias][
                        'selection_filter'
                        ]==1,c] = manual_selection[
                            (manual_selection['Alias']==alias)&
                            (manual_selection['PLYUID'].astype(str)==plyuid)
                            ][c].values[0]
            output_list['MAN_Condition_{}'.format(alias)] = 0
            output_list.loc[manual_selections_filters[alias]\
                            ['selection_filter']==1,'MAN_Condition_{}'.format(
                                alias
                                )
                            ] = 1
            output_list.loc[:,'Man_Selection_Id'] = \
                manual_selections_filters[alias]['selection_id']
                
            output_list.loc[manual_selections_filters[alias]\
                            ['selection_filter']==1,
                            'Man_Condition'] = alias
            
            output_list.loc[manual_selections_filters[alias]\
                            ['selection_filter']==1,
                            'Breath_Inclusion_Filter'] = 1
            
            output_list.loc[manual_selections_filters[alias]\
                            ['selection_filter']==1,
                            'MAN_Inclusion_Filter'] = 1

    for m in animal_metadata[plyuid]:
        output_list[m] = animal_metadata[plyuid][m]
    
    output_list['Mouse_And_Session_ID'] = \
        output_list['MUID'].copy().astype(str) + '_' + \
        output_list['PlyUID'].copy().astype(str)
    
    for p in analysis_parameters:
        output_list[p] = analysis_parameters[p]
    
    reversed_column_dictionary = {}
    for k in column_dictionary:
        reversed_column_dictionary[column_dictionary[k]] = k
    
    output_list.rename(columns=reversed_column_dictionary, inplace = True)
    column_list = []
    for k in column_dictionary:
        column_list.append(k)
        if k in [
                'Mouse_And_Session_ID',
                'Breath_Inclusion_Filter',
                'Exp_Condition',
                'Auto_Condition',
                'Man_Condition',
                'Breath Number',
                'Auto_Block_Id',
                'Auto_Selection_Id',
                'Man_Selection_Id',
                'Timestamp_Inspiration',
                'Timestamp_Expiration',
                ]:
            continue
        output_list['Irreg_Score_{}'.format(k)] = calculate_irreg_score(
            output_list[k]
            )
        column_list.append('Irreg_Score_{}'.format(k))
    
    output_list.loc[:,'Exp_Condition'] = \
        output_list['Auto_Condition'].astype(str) + \
        output_list['Man_Condition'].astype(str)
    
    return output_list

# %% main
def main():
    # %%
    try:
        Column_Dictionary = {
            'Mouse_And_Session_ID':'Mouse_And_Session_ID',
            'Breath_Inclusion_Filter':'Breath_Inclusion_Filter',
            'Auto_Condition':'Auto_Condition',
            'Man_Condition':'Man_Condition',
            'Exp_Condition':'Exp_Condition',
            'Auto_Block_Id':'Auto_Block_Id',
            'Auto_Selection_Id':'Auto_Selection_Id',
            'Man_Selection_Id':'Man_Selection_Id',
            'Breath Number':'il_inhale',
            'Timestamp_Inspiration':'ts_inhale',
            'Timestamp_Expiration':'ts_exhale',
            'Inspiratory_Duration':'TI',
            'Expiratory_Duration':'TE',
            'Tidal_Volume_uncorrected':'iTV',
            'Tidal_Volume_exhale_uncorrected':'eTV',
            'VT__Tidal_Volume_corrected':'calibrated_TV',
            'VTpg__Tidal_Volume_per_gram_corrected':'calibrated_TV_per_gram',
            'Peak_Inspiratory_Flow':'PIF',
            'Peak_Inspiratory_Flow_corrected':'calibrated_PIF',
            'Peak_Expiratory_Flow':'PEF',
            'Peak_Expiratory_Flow_corrected':'calibrated_PEF',
            'Breath_Cycle_Duration':'TT',
            'VE__Ventilation':'VE',
            'VEpg__Ventilation_per_gram':'VE_per_gram',
            'VO2':'VO2',
            'VO2pg':'VO2_per_gram',
            'VCO2':'VCO2',
            'VCO2pg':'VCO2_per_gram',
            'VEVO2':'VE_per_VO2',
            'VF':'BPM',
            'TT_per_TV':'TT_per_TV',
            'TT_per_TVpg':'TT_per_TVpg',
            'O2_per_Air__VO2_x_TT_per_TV_':'O2_per_Air',
            'Apnea':'apnea',
            'Sigh':'sigh',
            'DVTV':'DVTV',
            'per500':'per_X_calculation',
            'mav':'mov_avg_vol',
            'O2_concentration':'calibrated_o2',
            'CO2_concentration':'calibrated_co2',
            'Chamber_Temperature':'corrected_temp',
            'O2_uncalibrated':'o2',
            'CO2_uncalibrated':'co2',
            'Chamber_Temp_uncalibrated':'temp',
            'Body_Temperature_Linear':'Body_Temperature',
            }
        
        Launch_Time = datetime.datetime.now()
        # gather command line arguments
        parser = argparse.ArgumentParser(description='Automated Breath Caller')
        parser.add_argument(
            '-i', help='Path containing signal files for input'
            )
        parser.add_argument(
            '-f', action='append', help='names of signal files,\
                declare multiple times to build a list of files'
            )
        parser.add_argument('-o', help='Path to directory for output files')
        parser.add_argument('-m', help='Path to Manual Selection File')
        parser.add_argument('-a', help='Path to Animal MetaData File')
        parser.add_argument('-c', help='Path to Automated Criteria File')
        parser.add_argument('-p', help='Path to Analysis Parameters File')

        args, others = parser.parse_known_args()

        # if arguments are incomplete, then request from user
        if args.i is None or args.f is None:
            print('"i" or "f" is empty')
            Signal_Files = gui_open_filenames(
                {
                    'title': 'Load Ascii Files With Trace Data',
                    'filetypes': [('txt', '.txt'), ('all files', '.*')]
                    }
                )
        else:
            print(args.i)
            Signal_Files = []
            print(args.f)
            for file in args.f:
                Signal_Files.append(os.path.join(args.i, file))

        if args.o is None:
            print('"o" is empty')
            Output_Path = gui_directory(
                {'title': 'Choose Filename for Output Data'}
                )
        else:
            print(args.o)
            Output_Path = args.o

        if args.a is None:
            Animal_Metadata_Path = gui_open_filename(
                {'title': 'Select file containing Animal Metadata'}
                )
        else:
            print(args.a)
            Animal_Metadata_Path = args.a

        if args.m is None:
            print('"m" is empty')
            Manual_Selections_Path = gui_open_filename(
                {'title': 'Select file containing Manual Selections'}
                )
        else:
            print(args.m)
            Manual_Selections_Path = args.m

        if args.c is None:
            print('"c" is empty')
            Auto_Criteria_Path = gui_open_filename(
                {'title': 'Select file containing Autmated Selection Criteria'}
                )
        else:
            print(args.c)
            Auto_Criteria_Path = args.c

        if args.p is None:
            print('"p" is None')
            Analysis_Parameters_Path = gui_open_filename(
                {'title': 'Select file containing Analysis Parameters'}
                )
        else:
            print(args.p)
            Analysis_Parameters_Path = args.p

        # set-up logging
        # create logger
        logger = logging.getLogger('BreathCaller')
        logger.setLevel(logging.DEBUG)

        # create file and console handlers to receive logging
        console_handler = logging.StreamHandler(sys.stdout)
        if len(Signal_Files)>1:
            file_handler = logging.FileHandler(
                os.path.join(Output_Path, 'log.log'))
        else:
            file_handler = logging.FileHandler(
                os.path.join(Output_Path, os.path.basename(Signal_Files[0])+'.log'))
        console_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)

        # create format for log and apply to handlers
        log_format = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
                )
        console_handler.setFormatter(log_format)
        file_handler.setFormatter(log_format)

        # add handlers to the logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        # log initial inputs
        logger.info('Beginning Analysis')
        logger.info('{}'.format(Launch_Time.isoformat()))
        log_info_from_dict(
            logger,
            {'i': args.i,
             'f': args.f,
             'o': args.o,
             'p': args.p,
             'a': args.a,
             'm': args.m,
             'c': args.c
             },
            'command line argument : '
            )
        log_info_from_dict(
            logger,
            {
                'signal files': Signal_Files,
                'output path': Output_Path,
                'analysis parameters path': Analysis_Parameters_Path,
                'animal metadata path': Animal_Metadata_Path,
                'manual selections path': Manual_Selections_Path,
                'auto criteria path': Auto_Criteria_Path
                },
            'input paths : '
            )

        # collect data from input files - raise exception or warning if needed
        if Animal_Metadata_Path is not None and \
                Animal_Metadata_Path != '':
            Animal_Metadata = get_animal_metadata(Animal_Metadata_Path)
            if Animal_Metadata == {}:
                raise Exception('Empty or unparsable Animal Metadata')
        else: raise Exception('No Animal Metadata File Provided')

        if Manual_Selections_Path is not None and \
                Manual_Selections_Path != '' and \
                Manual_Selections_Path != 'NONE':
            Manual_Selection = pandas.read_csv(
                Manual_Selections_Path,
                sep=',',
                encoding='UTF-8')
        else: Manual_Selection = None

        if Auto_Criteria_Path is not None and \
                Auto_Criteria_Path != '' and \
                Auto_Criteria_Path != 'NONE':
            Auto_Criteria = pandas.read_csv(Auto_Criteria_Path, sep=',')
        else: Auto_Criteria = None

        if Analysis_Parameters_Path is not None and \
                Analysis_Parameters_Path != '':
            Analysis_Parameters = pandas.read_csv(
                Analysis_Parameters_Path,
                sep=',',
                encoding='UTF-8',
                index_col='Parameter'
                )['Setting'].to_dict()
        else: raise Exception('No Analysis Parameters File Provided')

        First_File_Time = datetime.datetime.now()
        # iterate through files and call breaths
        for file_number in range(len(Signal_Files)):
            try:
                Current_File_Start_Time = datetime.datetime.now()
                File = Signal_Files[file_number]
                # estimate time to completion
                if File != Signal_Files[0]:
                    logger.info(
                      'estimated time remaining - {}'.format(
                          convert_seconds_to_time_text(
                              calculate_time_remaining(
                                  file_number,
                                  len(Signal_Files),
                                  First_File_Time,
                                  Current_File_Start_Time
                                  )
                              )
                          )
                      )

                else:
                    pass
                logger.info('{}'.format(File))

                # confirm animal is present in metadata
                # extract MUID and PLYUID
                MUID, PLYUID = extract_muid_plyuid(
                    File,
                    Animal_Metadata,
                    local_logger=logger
                    )

                # load current signal file
                Signal_Data = load_signal_data(
                    File, 
                    logger
                    )

                # apply basic voltage corrections to gas and temperature values
                Signal_Data = apply_voltage_corrections(
                    Signal_Data,
                    Analysis_Parameters,
                    [
                        ('o2', 'corrected_o2', 'O2_calibration_factor'),
                        ('co2', 'corrected_co2', 'CO2_calibration_factor'),
                        (
                            'temp',
                            'corrected_temp',
                            'temperature_calibration_factor'
                            )
                        ],
                    logger
                    )

                # repair chamber temperature if needed
                Signal_Data.loc[:, 'corrected_temp'] = repair_temperature(
                    Signal_Data,
                    PLYUID,
                    Animal_Metadata,
                    Analysis_Parameters,
                    local_logger=logger
                    )
                
                if Analysis_Parameters.get('Pneumo_Mode') == '1':
                    purge_columns = []
                    if 'temp' not in Signal_Data:
                        Signal_Data['temp'] = Signal_Data['corrected_temp']
                        purge_columns.append('temp','corrected_temp')
                        
                    if 'corrected_co2' not in Signal_Data:
                        Signal_Data['corrected_co2'] = \
                          Analysis_Parameters.get('calibrated_co2_default') if\
                          Analysis_Parameters.get('calibrated_co2_default') \
                          else -1
                        Signal_Data['co2'] = \
                            Signal_Data['corrected_co2']
                        purge_columns.append('calibrated_co2_default')
                        logger.warning('CO2 data not in signal data')
                        
                    if 'corrected_o2' not in Signal_Data:
                        Signal_Data['corrected_o2'] = \
                          Analysis_Parameters.get('calibrated_o2_default') if\
                          Analysis_Parameters.get('calibrated_o2_default') \
                          else -1
                        Signal_Data['o2'] = \
                            Signal_Data['corrected_o2']
                        purge_columns.append('calibrated_o2_default')
                        logger.warning('O2 data not in signal data')

                # collect time stamps
                Timestamp_Dict = dict(
                    zip(
                        Signal_Data.ts[Signal_Data.comment.dropna().index],
                        Signal_Data.comment.dropna()
                        )
                    )

                Reverse_Timestamp_Dict = {}
                for k in Timestamp_Dict:
                    Reverse_Timestamp_Dict[Timestamp_Dict[k][3:-1]] = k

                # apply linear estimation of body temperature
                Signal_Data['Body_Temperature'] = calculate_body_temperature(
                    Signal_Data,
                    PLYUID,
                    Timestamp_Dict,
                    Animal_Metadata,
                    Manual_Selection,
                    Auto_Criteria,
                    logger
                    )

                # differentiate breathing signal to 'derived flow'
                if 'flow' not in Signal_Data:
                    Signal_Data['flow'] = Signal_Data['vol'].diff().fillna(1.0)
                    logger.info('calculating flow from vol data')
                else:
                    logger.info('flow data present in signal data')

                if 'vol' not in Signal_Data:
                    Signal_Data['vol'] = Signal_Data['flow'].cumsum()
                    Signal_Data['vol'] = apply_smoothing_filter(
                        Signal_Data,
                        'vol'
                        )
                    logger.info('calculating vol data from flow data')
                else:                
                    logger.info('vol data present in signal data')

                # calculate sampling rate (expected to be 1000Hz)
                sampleHz = round(1/(Signal_Data['ts'][2]-Signal_Data['ts'][1]))

                # calculate moving average of vol signal to use for QC
                # (1sec centered mov avg)
                    
                Signal_Data['mov_avg_vol'] = Signal_Data['vol'].rolling(
                    int(sampleHz), center=True
                    ).mean()

                # smooth data with high and low pass filter if option selected
                if int(Analysis_Parameters['apply_smoothing_filter']) == 1:
                    Signal_Data['original_flow'] = Signal_Data['flow'].copy()
                    Signal_Data['flow'] = apply_smoothing_filter(
                        Signal_Data,
                        'flow'
                        )

                # call breaths
                Breath_List = breath_caller(
                    Signal_Data,
                    Analysis_Parameters,
                    logger
                    )

                if 'ecg' in Signal_Data:
                    Beat_List = basicRR(Signal_Data['ecg'],Signal_Data['ts'])
                    if len(Beat_List)>0:
                        Beat_List.to_csv(
                            os.path.join(
                                Output_Path,'{}_{}_beats.csv'.format(
                                    MUID,PLYUID
                                    )
                                )
                            )
                else:
                    pass
                
                
                # recalibrate gas concentration
                Signal_Data['calibrated_o2'], Signal_Data['calibrated_co2'], \
                Breath_List['calibrated_o2'], Breath_List['calibrated_co2'] = \
                    calibrate_gas(
                        Signal_Data,
                        Breath_List,
                        Auto_Criteria,
                        Manual_Selection,
                        PLYUID,
                        Timestamp_Dict,
                        logger
                        )

                # assign breaths to blocks and selections
                Automated_Selections_Filters = \
                    create_filters_for_automated_selections(
                        Signal_Data,
                        Breath_List,
                        Auto_Criteria,
                        Timestamp_Dict,
                        Analysis_Parameters,
                        logger
                        )

                Manual_Selections_Filters = \
                    create_filters_for_manual_selections(
                        Breath_List,
                        Manual_Selection,
                        PLYUID,
                        logger
                        )

                # apply volumetric calibrations
                Calibration_Parameters = collect_calibration_parameters(
                    Breath_List,
                    Analysis_Parameters,
                    Animal_Metadata,
                    PLYUID,
                    Auto_Criteria,
                    Manual_Selection,
                    Automated_Selections_Filters,
                    Manual_Selections_Filters,
                    logger
                    )
                
                Advanced_Breath_Parameters = \
                    apply_volumetric_and_respiratory_calculations(
                        Breath_List, 
                        Calibration_Parameters, 
                        Automated_Selections_Filters, 
                        Manual_Selections_Filters,
                        Analysis_Parameters,
                        logger)
                
                # review/revise automated filters in case volumetric 
                # calibration changes inclusion                
                Revised_Automated_Selections_Filters = \
                    create_filters_for_automated_selections(
                        Signal_Data,
                        Breath_List.merge(
                            Advanced_Breath_Parameters, 
                            on = 'ts_inhale',
                            how = 'left',
                            ),
                        Auto_Criteria,
                        Timestamp_Dict,
                        Analysis_Parameters,
                        logger                        
                        )
                    
                Revised_Calibration_Parameters = collect_calibration_parameters(
                        Breath_List.merge(
                            Advanced_Breath_Parameters, 
                            on = 'ts_inhale',
                            how = 'left',
                            ),
                        Analysis_Parameters,
                        Animal_Metadata,
                        PLYUID,
                        Auto_Criteria,
                        Manual_Selection,
                        Revised_Automated_Selections_Filters,
                        Manual_Selections_Filters,
                        logger
                        )
                
                Revised_Advanced_Breath_Parameters = \
                    apply_volumetric_and_respiratory_calculations(
                        Breath_List.merge(
                            Advanced_Breath_Parameters, 
                            on = 'ts_inhale',
                            how = 'left',
                            ), 
                        Revised_Calibration_Parameters, 
                        Revised_Automated_Selections_Filters, 
                        Manual_Selections_Filters, 
                        Analysis_Parameters,
                        logger)

                # merge values for calibrated volumes into the Breath_List
                Breath_List = Breath_List.merge(
                    Revised_Advanced_Breath_Parameters, 
                    on = 'ts_inhale',
                    how = 'left',
                    )
                
                # Include the version of this script as an Analysis Parameter
                Analysis_Parameters['Version'] = __version__
                
                Output_List = create_output(
                    Breath_List, 
                    Analysis_Parameters, 
                    Animal_Metadata, 
                    Auto_Criteria, 
                    Manual_Selection, 
                    PLYUID, 
                    Revised_Automated_Selections_Filters, 
                    Manual_Selections_Filters, 
                    Column_Dictionary, 
                    logger
                    )
                
                # Prepare the output for STAGG - only generate if not empty
                if len(
                        Output_List[
                            (Output_List['AUTO_IND_INCLUDE'] == 1) |
                            (Output_List['MAN_IND_INCLUDE'] == 1)
                            ]
                        )<1:
                    logger.exception(
                        "{}_{} does not have any includable breaths ".format(
                            MUID,PLYUID
                            )+
                        "- no JSON file will be produced."+
                        "This is probably due to problems during "+
                        "sample collection or settings that are not "+
                        "appropriate for the current file"
                        )
                else:
                    logger.info(
                        "{}_{} has includable breaths {}".format(
                            MUID,PLYUID,len(Output_List)
                            )+
                        "- JSON file will be produced."
                        )
                    Output_List[
                        (Output_List['AUTO_IND_INCLUDE'] == 1) |
                        (Output_List['MAN_IND_INCLUDE'] == 1)
                        ].to_json(
                            os.path.join(
                                Output_Path,
                                '{}_{}.json'.format(MUID,PLYUID)
                                )
                            )
                
                # provide 'all breath' breathlist if requested
                if 'All_Breath_Output' in Analysis_Parameters:
                    if Analysis_Parameters['All_Breath_Output'] == '1':
                        Output_List.to_csv(
                            os.path.join(
                                Output_Path,'{}_{}_all.csv'.format(MUID,PLYUID)
                                )
                            )
                
                # provide 'aggregated breath data' output if requested
                if 'Aggregate_Output' in Analysis_Parameters:
                    if Auto_Criteria is not None:
                        if Analysis_Parameters['Aggregate_Output'] != '':
                            group_by_vars = \
                                Analysis_Parameters[
                                    'Aggregate_Output'
                                    ].split('@')
                            group_by_vars = [i for i in group_by_vars if i!=\
                                             'Man_Condition']
                            temp_df1 = Output_List.groupby(
                                group_by_vars
                                ).first()
                            temp_df2 = Output_List.groupby(
                                group_by_vars
                                ).mean()
                            temp_df3 = Output_List.groupby(
                                group_by_vars
                                ).count()
                        
                            for k in temp_df2.columns:
                                temp_df1.loc[:,k] = temp_df2[k]
                                
                            temp_df1['N'] = temp_df3['Mouse_And_Session_ID']
                            
                            temp_df1['AGG_VF'] = \
                                60/temp_df1['Breath_Cycle_Duration']
                            temp_df1['AGG_VE'] = \
                                temp_df1['AGG_VF'] * \
                                    temp_df1['VT__Tidal_Volume_corrected']
                            temp_df1['AGG_VEpg'] = \
                                temp_df1['AGG_VF'] * \
                                    temp_df1[
                                        'VTpg__Tidal_Volume_per_gram_corrected'
                                        ]
                            temp_df1['AGG_VEVO2'] = \
                                temp_df1['AGG_VE'] / temp_df1['VO2']
                            
                            temp_df1.to_csv(
                                os.path.join(
                                    Output_Path,
                                    '{}_{}_agg_auto.csv'.format(MUID,PLYUID)
                                    )
                                )
                    if Manual_Selection is not None:
                        if Analysis_Parameters['Aggregate_Output'] != '':
                            group_by_vars = \
                                Analysis_Parameters[
                                    'Aggregate_Output'
                                    ].split('@')
                            group_by_vars = [i for i in group_by_vars if i!=\
                                             'Auto_Condition']
                            temp_df1 = Output_List.groupby(
                                group_by_vars
                                ).first()
                            temp_df2 = Output_List.groupby(
                                group_by_vars
                                ).mean()
                            temp_df3 = Output_List.groupby(
                                group_by_vars
                                ).count()
                        
                            for k in temp_df2.columns:
                                temp_df1.loc[:,k] = temp_df2[k]
                                
                            temp_df1['N'] = temp_df3['Mouse_And_Session_ID']
                            
                            temp_df1['AGG_VF'] = \
                                60/temp_df1['Breath_Cycle_Duration']
                            temp_df1['AGG_VE'] = \
                                temp_df1['AGG_VF'] * \
                                    temp_df1['VT__Tidal_Volume_corrected']
                            temp_df1['AGG_VEpg'] = \
                                temp_df1['AGG_VF'] * \
                                    temp_df1[
                                        'VTpg__Tidal_Volume_per_gram_corrected'
                                        ]
                            temp_df1['AGG_VEVO2'] = \
                                temp_df1['AGG_VE'] / temp_df1['VO2']
                            
                            temp_df1.to_csv(
                                os.path.join(
                                    Output_Path,
                                    '{}_{}_agg_man.csv'.format(MUID,PLYUID)
                                    )
                                )
                    
                logger.info('completed file {}'.format(File))
                



                
                
            except Exception as e:
                logger.exception(
                    'Breathcaller was unable to process {} - {}'.format(
                        File,
                        e
                        ),
                    exc_info=True
                    )
                continue
            
            
    except Exception as e:
        logger.exception(
            'Breath Caller encountered an ERROR: {}'.format(e),
            exc_info=True
            )
    Finish_Time=datetime.datetime.now()
    logger.info(
        'Duration of Run : {}'.format(
            convert_seconds_to_time_text(
                Finish_Time-Launch_Time
                )
            )
        )
       
# %% Run the Main Program
if __name__ == '__main__':
    main()



