"""
Module for creating and executing SASSI and STAGG runs, asynchoronously

***
built as part of the Russell Ray Lab Breathing And Physiology Analysis Pipeline
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

"""

from typing import List
import sys
import os
import subprocess

from queue import Queue
from PyQt5.QtCore import QRunnable


class Worker(QRunnable):
    """
    Chris Ward got the threading to work!

    The Worker class handles the threading and parallel processing for the main GUI.

    Attributes
    ---------
    path_to_script: command arguments yielded by get_jobs_py() or get_jobs_r() to launch either SASSI or STAGG respectively.
    worker_id: unique identifier for this thread
    worker_queue: FIFO queue constructor for safely exchanging information between threads.
    """
    def __init__(self, path_to_script: List[str], worker_id: int, worker_queue: Queue):
        """
        Instantiate the Worker Class.

        Parameters
        ---------
        path_to_script: command arguments yielded by get_jobs_py() or get_jobs_r() to launch either SASSI or STAGG respectively.
        worker_id: unique identifier for this thread
        worker_queue: FIFO queue constructor for safely exchanging information between threads.
        """
        super(Worker, self).__init__()
        self.path_to_script = path_to_script
        self.worker_id = worker_id
        self.worker_queue = worker_queue
    
    def run(self):
        """
        Run external process and push output to shared worker queue
        """
        proc = subprocess.Popen(
            self.path_to_script,
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT
            )

        # Extract the stdout and feed it to the queue.
        # Emit signals whenever adding to the queue or finishing.
        running = True
        while running:
            line = proc.stdout.readline().decode('utf8')
            if proc.poll() is not None:
                running = False

            elif line != '':
                self.worker_queue.put((self.worker_id, line.strip()))

        self.worker_queue.put((self.worker_id, "DONE"))


def get_jobs_py(signal_files: List[str], module: str, output_folder: str,
                metadata: str, manual: str, auto: str, basic: str):
    """
    Return the list of arguments fed to the command line to launch
    the SASSI module.

    Parameters
    --------
    signal_files: collection of input breath files
    module: path to SASSI script
    output_folder: path to folder created for SASSI run output
    metadata: path to SASSI input metadata
    manual: path to manual SASSI settings
    auto: path to automated SASSI settings
    basic: path to basic SASSI settings
    NOTE: either mansections or autosections must be provided
    
    Returns
    ------
    list: Command line arguments to launch the SASSI module.
    """
    for file_py in signal_files:
        breathcaller_cmd = [
            sys.executable,  # path to the current python executable
            '-u', module,  # path to SASSI script
            '-i', os.path.dirname(file_py),  # signal dir
            '-f', os.path.basename(file_py),  # signal file
            '-o', output_folder,
            '-a', metadata,
            '-m', manual if manual else "",
            '-c', auto if auto else "",
            '-p', basic,
        ]
        yield breathcaller_cmd


def get_jobs_r(rscript: str, pipeline: str, papr_dir: str, output_dir: str,
               inputpaths_file: str, variable_config: str, graph_config: str,
               other_config: str, output_dir_r: str, image_format: str):
    """
    Return the list of arguments fed to the command line to launch
    the STAGG module.

    Parameters
    --------
    rscript: path to the Rscript.exe file
    pipeline: path to the appropriate .R script
    papr_dir: path to STAGG scripts directory
    output_dir: output directory selected by user
    inputpaths_file: path to the file containing STAGG input filepaths
    variable_config: path to variable config 
    graph_config: path to graph config 
    other_config: path to other config 
    output_dir_r: path to the STAGG output directory
    image_format: file format of STAGG output figures
        Either ".svg" or ".jpeg"

    Returns
    ------
    list: Command line arguments to launch the STAGG module.
    """
    papr_cmd = [
        # The path to the local R executable file
        rscript,
        # The path to the STAGG script
        pipeline,
        # The path to the output directory chosen by the user
        '-d', output_dir,
        # This variable is either a list of JSON file paths produced as SASSI output, a list of JSON file paths produced as SASSI output and an .RData file path produced as STAGG output, a list containing a single path of an .RData file, or a string that is the path to a single directory containing JSON files produced as SASSI output.
        '-J', inputpaths_file,
        # The path to the variable_config.csv file
        '-R', variable_config,
        # The path to the graph_config.csv file
        '-G', graph_config,
        # The path to the other_config.csv file
        '-F', other_config,
        # The path to the directory for STAGG output
        '-O', output_dir_r,
        # The paths to the STAGG scripts
        '-T', os.path.join(papr_dir, "Data_import.R"),
        '-S', os.path.join(papr_dir, "Statistical_analysis.R"),
        '-M', os.path.join(papr_dir, "Graph_generator.R"),
        '-B', os.path.join(papr_dir, "Optional_graphs.R"),
        # A string, either ".jpeg" or ".svg", indicating the format of the image output from STAGG
        '-I', image_format,
        # The path to the STAGG scripts directory
        '--Sum', papr_dir
    ]
    
    yield papr_cmd

