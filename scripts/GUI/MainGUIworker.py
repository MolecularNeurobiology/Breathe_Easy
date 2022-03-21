#%%
#region Libraries

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from form import Ui_Plethysmography
import csv
import subprocess
import datetime
import time
import os
import json
import pyodbc
import threading
import multiprocessing
import concurrent.futures
import MainGui

import sys
from pathlib import Path, PurePath
import shutil
import pandas
import re
import importlib
import logging
import asyncio

#endregion

class WorkerSignals(QObject):
    # create signals to be used by the worker
    finished = pyqtSignal(int)
    progress = pyqtSignal(int)
    
class Worker(QRunnable):
       
    def __init__(self,path_to_script,i,worker_queue,pleth):
        super(Worker, self).__init__()
        self.path_to_script = path_to_script
        self.i = i
        self.worker_queue = worker_queue
        self.pleth = pleth
        self.signals = WorkerSignals()
        self.finished = self.signals.finished
        self.progress = self.signals.progress
    
    def run(self):
        # use subprocess.Popen to run a seperate program in a new process
        # stdout will be captured by the variable self.echo and extracted below
        self.echo = subprocess.Popen(
            self.path_to_script,
            stdout= subprocess.PIPE, 
            stderr = subprocess.STDOUT
            )
    
        # extract the stdout and feed it to the queue
        # emit signals whenever adding to the queue or finishing
        running = 1
        while running == 1:
            line = self.echo.stdout.readline().decode('utf8')
            if self.echo.poll() is not None:
                running = 0
            elif line != '':
                self.worker_queue.put(line.strip())
                self.progress.emit(self.i)
        self.finished.emit(self.i)

#region get_jobs
def get_jobs_py(Plethysmography):
    print('get_jobs_py thread id',threading.get_ident())
    print("get_jobs_py process id",os.getpid())
    for file_py in Plethysmography.signals:
        print(file_py)
        breathcaller_cmd = 'python -u "{module}" -i "{id}" -f "{signal}" -o "{output}" -a "{metadata}" -m "{manual}" -c "{auto}" -p "{basic}"'.format(
            module = Plethysmography.breathcaller_path,
            id = os.path.dirname(file_py),
            output = Plethysmography.output_dir_py,
            signal = os.path.basename(file_py),
            metadata = Plethysmography.metadata,
            manual = Plethysmography.mansections,
            # manual = "NONE", 
            auto = Plethysmography.autosections,
            # auto = "NONE",
            basic = Plethysmography.basicap
        )
        yield breathcaller_cmd

def get_jobs_r(Plethysmography):
    print('R env route')
    print('get_jobs_r thread id',threading.get_ident())
    print("get_jobs_r process id",os.getpid())

    papr_cmd='"{rscript}" "{pipeline}" -d "{d}" -J "{j}" -R "{r}" -G "{g}" -F "{f}" -O "{o}" -T "{t}" -S "{s}" -M "{m}" -B "{b}" -I "{i}"'.format(
            rscript = Plethysmography.rscript_des,
            pipeline = Plethysmography.pipeline_des,
            d = Plethysmography.mothership,
            j = Plethysmography.input_dir_r,
            r = Plethysmography.variable_config,
            g = Plethysmography.graph_config,
            f = Plethysmography.other_config,
            o = Plethysmography.output_dir_r,
            t = os.path.join(Plethysmography.papr_dir, "Data_import_multi.R"),
            s = os.path.join(Plethysmography.papr_dir, "Statistical_analysis.R"),
            m = os.path.join(Plethysmography.papr_dir, "Graph_generator.R"),
            b = os.path.join(Plethysmography.papr_dir, "Optional_graphs.R"),
            i = Plethysmography.image_format
    )
    yield papr_cmd
    
def get_jobs_stamp(Plethysmography):
    print('get_jobs_stamp thread id',threading.get_ident())
    print("get_jobs_stamp process id",os.getpid())
    for file_st in Plethysmography.signals:
        print(file_st)
        stamp_cmd = 'python -u "{stamper}" --s "{signal}" --n "{need}"'.format(
            stamper = Plethysmography.gui_config['Dictionaries']['Paths']['timestamper'],
            signal = file_st,
            need = Plethysmography.gui_config['Dictionaries']['Timestamps'][1])
        yield stamp_cmd

#endregion
