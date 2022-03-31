#%%
#region Libraries

import os
from pyclbr import Class
from queue import Queue
import subprocess
import threading
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal

#endregion


class WorkerSignals(QObject):
    """
    Chris Ward got the threading to work!
    
    Create signals used by the worker.

    Parameters
    --------
    QObject: class
        The WorkerSignals class inherits properties and methods from the QObject class.
    """
    finished = pyqtSignal(int)
    progress = pyqtSignal(int)
    

class Worker(QRunnable):
    """
    Chris Ward got the threading to work!

    The Worker class handles the threading and parallel processing for the main GUI.

    Parameters
    --------
    QRunnable: class
        The Worker class inherits the properties and methods from teh QRunnable class.
    """
    def __init__(self, path_to_script: str, i: int, worker_queue: Queue, pleth: Class):
        """
        Instantiate the Worker Class.

        Parameters
        ---------
        path_to_script: str
            The string yielded by get_jobs_py() or get_jobs_r() that is given to the command line to launch either BASSPRO or STAGG respectively.
        i: int
            The worker's number, determined by Plethysmography.counter.
        worker_queue: Queue
            A first-in, first-out queue constructor for safely exchanging information between threads.
        pleth: Class
            The Plethysmography Class.
        """
        super(Worker, self).__init__()
        self.path_to_script = path_to_script
        self.i = i
        self.worker_queue = worker_queue
        self.pleth = pleth
        self.signals = WorkerSignals()
        self.finished = self.signals.finished
        self.progress = self.signals.progress
    
    def run(self):
        """
        Use subprocess.Popen to run a seperate program in a new process.
        stdout will be captured by the variable self.echo and extracted below.
        
        """
        self.echo = subprocess.Popen(
            self.path_to_script,
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT
            )
        # Extract the stdout and feed it to the queue.
        # Emit signals whenever adding to the queue or finishing.
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
def get_jobs_py(Plethysmography: Class):
    """
    Return the string fed to the command line to launch the BASSPRO module.

    Parameters
    --------
    Plethysmography: Class
        The Plethysmography Class.
    
    Returns
    --------
    output: breathcaller_cmd
        The string given to the command line to launch the BASSPRO module.
    """
    print('get_jobs_py thread id',threading.get_ident())
    print("get_jobs_py process id",os.getpid())
    for file_py in Plethysmography.signals:
        breathcaller_cmd = 'python -u "{module}" -i "{id}" -f "{signal}" -o "{output}" -a "{metadata}" -m "{manual}" -c "{auto}" -p "{basic}"'.format(
            # The path to the BASSPRO script:
            module = Plethysmography.breathcaller_path,
            # The path of the signal file's directory:
            id = os.path.dirname(file_py),
            # The path of the BASSPRO output directory as chosen by the user previously:
            output = Plethysmography.output_dir_py,
            # The basename of the signal file:
            signal = os.path.basename(file_py),
            # The path of the metadata file:
            metadata = Plethysmography.metadata,
            # The path of the manual settings file - if not selected, it's an empty string "":
            manual = Plethysmography.mansections,
            # The path of the automated settings file - if not selected, it's an empty string "":
            auto = Plethysmography.autosections,
            # The path of the basic settings file:
            basic = Plethysmography.basicap
        )
        yield breathcaller_cmd


def get_jobs_r(Plethysmography: Class):
    """
    Return the string fed to the command line to launch the STAGG module.

    Parameters
    --------
    Plethysmography: Class
        The Plethysmography Class.
    
    Returns
    --------
    output: papr_cmd
        The string given to the command line to launch the STAGG module.
    """
    print('get_jobs_r thread id',threading.get_ident())
    print("get_jobs_r process id",os.getpid())
    papr_cmd='"{rscript}" "{pipeline}" -d "{d}" -J "{j}" -R "{r}" -G "{g}" -F "{f}" -O "{o}" -T "{t}" -S "{s}" -M "{m}" -B "{b}" -I "{i}"'.format(
            # The path to the local R executable file:
            rscript = Plethysmography.rscript_des,
            # The path to the STAGG script:
            pipeline = Plethysmography.pipeline_des,
            # The path to the STAGG scripts directory:
            # summary = Plethysmography.papr_dir,
            # The path to the output directory chosen by the user:
            d = Plethysmography.mothership,
            # This variable is either a list of JSON file paths produced as BASSPRO output, a list of JSON file paths produced as BASSPRO output and an .RData file path produced as STAGG output, a list containing a single path of an .RData file, or a string that is the path to a single directory containing JSON files produced as BASSPRO output.
            j = Plethysmography.input_dir_r,
            # The path to the variable_config.csv file:
            r = Plethysmography.variable_config,
            # The path to the graph_config.csv file:
            g = Plethysmography.graph_config,
            # The path to the other_config.csv file:
            f = Plethysmography.other_config,
            # The path to the directory for STAGG output:
            o = Plethysmography.output_dir_r,
            # The paths to the STAGG scripts:
            t = os.path.join(Plethysmography.papr_dir, "Data_import_multi.R"),
            s = os.path.join(Plethysmography.papr_dir, "Statistical_analysis.R"),
            m = os.path.join(Plethysmography.papr_dir, "Graph_generator.R"),
            b = os.path.join(Plethysmography.papr_dir, "Optional_graphs.R"),
            # A string, either ".jpeg" or ".svg", indicating the format of the image output from STAGG:
            i = Plethysmography.image_format
    )
    yield papr_cmd


#endregion
