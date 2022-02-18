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


def grabTimeStamps(CurFile):
    errors = []
    # timestamps = []
    tsbyfile = {}
    
    tsbyfile[CurFile]=[]
    # try:
    with open(CurFile,'r') as opfi:
        i=0
        for line in opfi:
            if '#* ' in line:
                print("{} TS AT LINE: {} - {}".format(os.path.basename(CurFile),i,line.split('#* ')[1]))
                # timestamps.append(line.split('#* ')[1])
                tsbyfile[CurFile].append(line.split('#* ')[1].strip(' \n'))
            i+=1
            # tsbyfile[CurFile]=[i.split(' \n')[0] for i in tsbyfile[CurFile]]
        print(tsbyfile)

    for t in tsbyfile[CurFile]:
        if t not in necessary_timestamps:
            print(f"New ts: {os.path.basename(CurFile)}, {t}")
        else:
            continue
            # if t in necessary_timestamps[k]:
            #     nt_found+=1
            #     ts_found+=1
            # if ts_found!=1:
            #     print(f"New ts: {os.path.basename(tsbyfile[0])}, {t}")
            # if nt_found==1:
            #     continue
            # elif nt_found>1:
            #     print(f"Extra ts: {os.path.basename(tsbyfile[0])}, {k}")
            # #     filesextrats.append((f,k))
            # #     error=1
            # else:
            #     print(f"Missing ts: {os.path.basename(tsbyfile[0])}, {k}")
        #     filesmissingts.append((f,k))
        #     error=1
    # for t in tsbyfile[f]:
    #     ts_found=0
    #     for k in necessary_timestamps:
    #         if t in necessary_timestamps[k]:
    #             ts_found=1
    #     if ts_found!=1:
    #         new_ts.append((os.path.basename(f),t))
    #         error=1
    # except:
        # print(f'Error with {os.path.basename(CurFile)}')
        # errors.append(CurFile)
    #trim timestamps
    # timestamps=list(set(timestamps))
    # timestamps=[i.split(' \n')[0] for i in timestamps]
    # timestamps.sort()
    # return tsbyfile


#%%
# def checkFileTimeStamps(tsbyfile,necessary_timestamps):
#     new_ts=[]
#     # filesmissingts=[]
#     # filesextrats=[]
#     # goodfiles=[]
#     for f in tsbyfile:
#         error=0
#         for k in necessary_timestamps:  
#             nt_found=0
#             for t in tsbyfile[f]:
#                 if t in necessary_timestamps[k]:
#                     nt_found+=1
#             if nt_found==1:
#                 continue
#             # elif nt_found>1:
#             #     filesextrats.append((f,k))
#             #     error=1
#             # else:
#             #     filesmissingts.append((f,k))
#             #     error=1
#         for t in tsbyfile[f]:
#             ts_found=0
#             for k in necessary_timestamps:
#                 if t in necessary_timestamps[k]:
#                     ts_found=1
#             if ts_found!=1:
#                 new_ts.append((os.path.basename(f),t))
#                 error=1
#         # if error==0:
#         #     goodfiles.append(f)
#         # check = {'good_files':goodfiles,'files_missing_a_ts':filesmissingts,
#         #     'files_with_dup_ts':filesextrats,'new_ts':new_ts}
#     return new_ts
def timestamp_dict(self):
    combo_need = self.necessary_timestamp_box.currentText()
    if self.signals == []:
        self.hangar.append("Please choose signal files to check for timestamps.")
        # self.setAnimated(self.signal_files)
    elif combo_need == "Choose dataset:":
        self.hangar.append("Please choose a set of timestamps.")
    else:
        epoch = [os.path.basename(Path(self.signals[0]).parent.parent)]
        condition = [os.path.basename(Path(self.signals[0]).parent)]
        
        for f in self.signals:
            # epoch = os.path.basename(Path(f).parent)
            if os.path.basename(Path(f).parent.parent) in epoch:
                continue
            else:
                epoch.append(os.path.basename(Path(f).parent.parent))
                if os.path.basename(Path(f).parent) in condition:
                    continue
                else:
                    condition.append(os.path.basename(Path(f).parent))

        for c in condition:
            for e in epoch:
                if e in self.stamp['Dictionaries']['Data']:
                    if c in self.stamp['Dictionaries']['Data'][e]:
                        continue
                    else:
                        self.stamp['Dictionaries']['Data'][e][c] = {}
                else:
                    self.stamp['Dictionaries']['Data'][e] = {}
                    self.stamp['Dictionaries']['Data'][e][c] = {}
        print(self.stamp['Dictionaries']['Data'])

        self.need = self.stamp['Dictionaries']['Necessary_Timestamps'][combo_need]
        print(self.need)

        self.grabTimeStamps()
        self.checkFileTimeStamps()

        for notable in self.check:
            for e in epoch:
                for c in condition:
                    self.stamp['Dictionaries']['Data'][e][c][notable] = self.check[notable]
        print(self.stamp['Dictionaries']['Data'])

def grabTimeStamps(self):
    """
    iterates through files in filepathlist to gather unique timestamps 
    contained in the files - this is useful for building AutoCriteria Files
    """
    errors = []
    timestamps = []
    
    for CurFile in self.signals:
        self.tsbyfile[CurFile]=[]
        print(CurFile)
        try:
            with open(CurFile,'r') as opfi:
                i=0
                for line in opfi:
                    if '#* ' in line:
                        self.hangar.append('{} TS AT LINE: {} - {}'.format(CurFile,i,line.split('#* ')[1]))
                        timestamps.append(line.split('#* ')[1])
                        self.tsbyfile[CurFile].append(line.split('#* ')[1])
                    i+=1
            self.tsbyfile[CurFile]=[i.split(' \n')[0] for i in self.tsbyfile[CurFile]]
            print(f"{CurFile}: {self.tsbyfile[CurFile]}")
        except:
            print('error')
            errors.append(CurFile)
    #trim timestamps
    timestamps=list(set(timestamps))
    timestamps=[i.split(' \n')[0] for i in timestamps]
    timestamps.sort()

def checkFileTimeStamps(self):
    new_ts={}
    filesmissingts={}
    filesextrats={}
    goodfiles=[]
    for f in self.tsbyfile:
        error=0
        for k in self.need: 
            nt_found=0
            for t in self.tsbyfile[f]:
                if t in self.need[k]:
                    nt_found+=1
            if nt_found==1:
                continue
            elif nt_found>1:
                if k in filesextrats.keys():
                    filesextrats[k].append(os.path.basename(f))
                else:
                    filesextrats[k] = [os.path.basename(f)]
                error=1
            else:
                if k in filesmissingts.keys():
                    filesmissingts[k].append(os.path.basename(f))
                else:
                    filesmissingts[k] = [os.path.basename(f)]
                # filesmissingts.append((f,k))
                error=1
        for t in self.tsbyfile[f]:
            ts_found=0
            for k in self.need:
                if t in self.need[k]:
                    ts_found=1
            if ts_found!=1:
                if t in new_ts.keys():
                    new_ts[t].append(os.path.basename(f))
                else:
                    new_ts[t] = [os.path.basename(f)]
                # new_ts.append((os.path.basename(f),t))
                error=1
        if error==0:
            goodfiles.append(f)
        self.check = {'good_files':goodfiles,'files_missing_a_ts':filesmissingts,
            'files_with_dup_ts':filesextrats,'new_ts':new_ts}
#%%
need = {
    "Necessary_Timestamps_CNO_Hypercapnia":{
        "Cal 20 Room Air":["Cal 20 Room Air"],
        "Cal 20 5% CO2":["Cal 20 5% CO2"],
        "Pre-CNO Room Air":["Pre-CNO Room Air", "Room Air"],
        "Pre-CNO 5% CO2":["Pre-CNO 5% CO2", "5% CO2"],
        "Pre-CNO Room Air 2":["Pre-CNO Room Air 2","Pre-CNO Room AIr 2","Pre-CNO Post-CO2 Recovery", "Room Air 2"],
        "Post-CNO Room Air":["Post-CNO Room Air","Post-CNO Room Air "],
        "Post-CNO 5% CO2":["Post-CNO 5% CO2","Post-CNO 5% CO2 "],
        "Post-CNO Room Air 2":["Post-CNO Room Air 2","Post-CNO Post-CO2 Recovery"]
    },
    "Necessary_Timestamps_Alz_Hypercapnia":{
        "Cal 20 Room Air":["Cal 20 Room Air","Cal 20 Room Air ","Cal 20 Room AIr"],
        "Cal 20 5% CO2":["Cal 20 5% CO2","Cal 20 5%CO2","Cal 30 5% CO2"],
        "Room Air":["Room Air", "Rooom Air", "Room Air ","Room AIr"],
        "5% CO2":["5% CO2", "5%CO2","5% Co2","Cal 20 5% Co2"],
        "Room Air 2":["Room Air 2","Room AIr 2"]
    },
    "Necessary_Timestamps_Alz_Hypoxia":{
        "Cal 20 Room Air":["Cal 20 Room Air","Cal 20 ROom Air","Cal 20 Room Air "],
        "Cal 20 10% O2":["Cal 20 10% O2","Cal  20 10% O2","Cal 20 10% O2 ","cal 20 10% O2","Cal 20 1-% O2","cAl 20 10% O2","Cal 20 10% o2","CAl 20 10% O2","Cal 20 10& O2"],
        "Room Air":["Room Air","Rooom Air","Room Air ","Roomo Air","Room Ai","Room AIr"],
        "10% O2":["10% O2","10% O2\\10% O2","10% O2 "," 10% O2","10 O2","10% O@"],
        "Room Air 2":["Room Air 2","Cal 20 Room Air 2","CAl 20 Room Air 2","room Air 2","room air 2","Room Air 2 ","Room AIr 2"]
    }
}                
#%% 
parser = argparse.ArgumentParser(description='Automated Timestamper')
parser.add_argument('--s', help = 'Signal file we are checking for timestamps')
parser.add_argument('--n', help = 'Dictionary of necessary timestamps')
args = parser.parse_args()
CurFile = args.s
for nd in need:
    if args.n == nd:
        necessary_timestamps = need[nd]
grabTimeStamps(CurFile)
# print(bob)
# sue = checkFileTimeStamps(bob, necessary_timestamps)
# print(sue)
# print(f"sue: {sue}")
# print(set([i[1] for i in sue]))    
# %%
# 4 cap, 5 cap, 6 cap, 7 cap, 3 cap