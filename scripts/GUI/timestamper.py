#region Libraries

# from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
# from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5 import uic
import resource
from form import Ui_Plethysmography as pleth
from thorbass import Ui_Thorbass
from thumbass import Ui_Thumbass
from thinbass import Ui_Thinbass
from config_form import Ui_Config
from custom_config import Ui_Custom
from manual_form import Ui_Manual
from auto_form import Ui_Auto
from basic_form import Ui_Basic
from stagg_form import Ui_Stagg
from auto_simp_form import Ui_Auto_simp
import MainGUImain
import traceback
from pathlib import Path, PurePath
import subprocess
from subprocess import PIPE, Popen
import datetime
import time
import os
import sys
import copy
import json
import pyodbc
import tkinter
import tkinter.filedialog
import tkinter as tk 
from tkinter import N, ttk
import shutil
import pandas as pd
import threading
import re
# import asyncio
import multiprocessing
import MainGUIworker_thready
import AnnotGUI
from bs4 import BeautifulSoup as bs
import argparse

#endregion

#region Timestamper...

def grabTimeStamps(kwargs={}):
    """
    iterates through files in filepathlist to gather unique timestamps 
    contained in the files - this is useful for building AutoCriteria Files
    """
    errors = []
    timestamps = []
    tsbyfile = {}
    
    # for args.s in pleth.signals:
    tsbyfile[args.s]=[]
    print(args.s)
    # try:
    with open(args.s,'r') as opfi:
        i=0
        # l=0
        for line in opfi:
            if '#' in line:
                # pleth.hangar.append('{} TS AT LINE: {} - {}'.format(os.path.basename(args.s),i,line.split('#')[1][2:]))
                print('{} TS AT LINE: {} - {}'.format(os.path.basename(args.s),i,line.split('#')[1][2:]))
                timestamps.append(line.split('#')[1][2:])
                # pleth.tsbyfile[args.s].append(line.split('#* ')[1].split(' \n')[0])
                c = line.split('#')[1][2:].split(' \n')[0]
                tsbyfile[args.s].append(f"{c}")
                # l+=1
            i+=1
    # pleth.tsbyfile[args.s]=[i.split(' \n')[0] for i in pleth.tsbyfile[args.s]]
    # pleth.cur = [i.split(' \n')[0] for i in pleth.tsbyfile[args.s]]
    # pleth.tsbyfile[args.s] = dict(zip(pleth.cur,[num for num in range(len(pleth.tsbyfile[args.s]))]))
    tsbyfile[args.s] = [i for i in tsbyfile[args.s]]
    print(f"{os.path.basename(args.s)}: {tsbyfile[args.s]}")
        # except:
        #     print('error')
        #     errors.append(args.s)
    #trim timestamps
    timestamps=list(set(timestamps))
    timestamps=[i.split(' \n')[0] for i in timestamps]
    timestamps.sort()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s',help='Signal file path')
    parser.add_argument('-o',help='Output folder path')
    args, others = parser.parse_known_args()
    grabTimeStamps()
    checkFileTimeStamps()
# %%       
if __name__ == '__main__':
    main()