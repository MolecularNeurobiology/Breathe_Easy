# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 13:43:36 2021

@author: wardc
"""
import os
#%%
#import libraries
import os
import pandas
import json
import tkinter
import tkinter.filedialog
import argparse

#%%
import datetime
import time
import subprocess
from subprocess import PIPE, Popen
import threading
import multiprocessing
import concurrent.futures

# needs = {
#             "CNO_cap": {
#                 'Cal 20 Room Air':['Cal 20 Room Air'],
#                 'Cal 20 5% CO2':['Cal 20 5% CO2'],
#                 'Pre-CNO Room Air':['Pre-CNO Room Air', 'Room Air'],
#                 'Pre-CNO 5% CO2':['Pre-CNO 5% CO2', '5% CO2'],
#                 'Pre-CNO Room Air 2':['Pre-CNO Room Air 2','Pre-CNO Room AIr 2','Pre-CNO Post-CO2 Recovery', 'Room Air 2'],
#                 'Post-CNO Room Air':['Post-CNO Room Air','Post-CNO Room Air '],
#                 'Post-CNO 5% CO2':['Post-CNO 5% CO2','Post-CNO 5% CO2 '],
#                 'Post-CNO Room Air 2':['Post-CNO Room Air 2','Post-CNO Post-CO2 Recovery']
#             },
#             "Alz_cap": {
#                 'Cal 20 Room Air':['Cal 20 Room Air','Cal 20 Room Air ','Cal 30 Room Air ','Cal20 Room Air','Cal 20 Room AIr '],
#                 'Cal 20 5% CO2':['Cal 20 5% CO2','Cal 30 5% CO2','Cal 20 5%CO2','Cal 20 5% CO2 ','Cal 20% CO2 ','Cal 5% CO2'],
#                 'Room Air':['Room Air', 'Rooom Air', 'Room Air ','Room AIr','Room Air \\'],
#                 '5% CO2':['5% CO2', '5%CO2','5% CO2 ','5%  CO2','5%CO2 ','5'],
#                 'Room Air 2':['Room Air 2','Room Air 4','room air 2','room Air 2']
#             },
#             "Alz_ox": {
#                 'Cal 20 Room Air':['Cal 20 Room Air'],
#                 'Cal 20 10% O2':['Cal 20 10% O2'],
#                 'Room Air':['Room Air'],
#                 '10% O2':['10% O2'],
#                 'Room Air 2':['Room Air 2']
#             }
#         }

parser = argparse.ArgumentParser(description='Automated Timestamper')
parser.add_argument('--signal', help = 'Signal file we are checking for timestamps')
parser.add_argument('--n', help = 'Dictionary of necessary timestamps')
args, others = parser.parse_known_args()
signals = []
print(args.signal)

# errors = []
# timestamps = []
# tsbyfile = {}
# tsbyfile[CurFile]=[]
# print(CurFile)
# # try:
# with open(CurFile,'r') as opfi:
#     i=0
#     for line in opfi:
#         if '#* ' in line:
#             print('TS AT LINE: {} - {}'.format(i,line.split('#* ')[1]))
#             timestamps.append(line.split('#* ')[1])
#             tsbyfile[CurFile].append(line.split('#* ')[1])
#         i+=1
# tsbyfile[CurFile]=[i.split(' \n')[0] for i in tsbyfile[CurFile]]
# # except:
# #     print('error')
# #     errors.append(CurFile)
# #trim timestamps
# timestamps=list(set(timestamps))
# timestamps=[i.split(' \n')[0] for i in timestamps]
# timestamps.sort()
# # return timestamps, tsbyfile, errors


# #%%
# new_ts=[]
# filesmissingts=[]
# filesextrats=[]
# goodfiles=[]
# for f in tsbyfile:
# error=0
# for k in necessary_timestamps:    
#     nt_found=0
#     for t in tsbyfile[f]:
#         if t in necessary_timestamps[k]:
#             nt_found+=1
#     if nt_found==1:
#         continue
#     elif nt_found>1:
#         filesextrats.append((f,k))
#         error=1
#     else:
#         filesmissingts.append((f,k))
#         error=1
# for t in tsbyfile[f]:
#     ts_found=0
#     for k in necessary_timestamps:
#         if t in necessary_timestamps[k]:
#             ts_found=1
#     if ts_found!=1:
#         new_ts.append((f,t))
#         error=1
# if error==0:
#     goodfiles.append(f)
# check = {'good_files':goodfiles,'files_missing_a_ts':filesmissingts,
#     'files_with_dup_ts':filesextrats,'new_ts':new_ts}

#%%
# def timestamp_dict():
#     with open('C:/Users/atwit/Documents/BCM/timestamps.json') as config_file:
#             td = json.load(config_file)

#     for epoch in os.scandir("D:/BCM/PM101"):
#         # print(epoch)
#         for condition in os.scandir(epoch.path):
#             if condition.is_dir():
#                 if str(condition.path).endswith("capnia"):
#                     needs = td['Dictionaries']['Necessary_Timestamps']['Alz_Hypercapnia']
#                 if str(condition.path).endswith("oxia"):
#                     needs = td['Dictionaries']['Necessary_Timestamps']['Alz_Hypoxia']
#                 filepathlist = os.listdir(condition)
#                 print(os.path.basename(epoch))
#                 grab_errors = td['Dictionaries']['returns'][os.path.basename(epoch)][os.path.basename(condition)]['errors']
#                 # timestamps = td['Dictionaries']['returns'][epoch][condition]['timestamps']
#                 # tsbyfile = td['Dictionaries']['returns'][epoch][condition]['tsbyfile']

#                 for signal in filepathlist:
#                     # tsbyfile[signal]=[]
#                     print(signal)

    # for CurFile in filepathlist:
    #     tsbyfile[CurFile]=[]
    #     print(CurFile)
    #     try:
    #         with open(CurFile,'r') as opfi:
    #             i=0
    #             for line in opfi:
    #                 if '#* ' in line:
    #                     print('TS AT LINE: {} - {}'.format(i,line.split('#* ')[1]))
    #                     timestamps.append(line.split('#* ')[1])
    #                     tsbyfile[CurFile].append(line.split('#* ')[1])
    #                 i+=1
    #         tsbyfile[CurFile]=[i.split(' \n')[0] for i in tsbyfile[CurFile]]
    #     except:
    #         print('error')
    #         errors.append(CurFile)
    # #trim timestamps
    # timestamps=list(set(timestamps))
    # timestamps=[i.split(' \n')[0] for i in timestamps]
    # timestamps.sort()
    # return timestamps, tsbyfile, errors
                    
#%% create a list for storing errors
# with open('C:/Users/atwit/Documents/BCM/timestamps.json') as config_file:
#             td = json.load(config_file)

# bob = grabTimeStamps(filepathlist)
# sue = checkFileTimeStamps(bob[1], Necessary_Timestamps_Alz_Hypercapnia)
# print(set([i[1] for i in sue["new_ts"]]))    
# %%
# 4 cap, 5 cap, 6 cap, 7 cap, 3 cap