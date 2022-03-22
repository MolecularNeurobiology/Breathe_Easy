#%%
#region Libraries

from PyQt5.QtCore import *
import subprocess
import os
import threading

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
    # Building the string that will be delivered to the command line to start BASSPRO
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

def get_jobs_r(Plethysmography):
    print('R env route')
    print('get_jobs_r thread id',threading.get_ident())
    print("get_jobs_r process id",os.getpid())
    papr_cmd='"{rscript}" "{pipeline}" -d "{d}" -J "{j}" -R "{r}" -G "{g}" -F "{f}" -O "{o}" -T "{t}" -S "{s}" -M "{m}" -B "{b}" -I "{i}"'.format(
            # The path to the local R executable file:
            rscript = Plethysmography.rscript_des,
            # The path to the STAGG script:
            pipeline = Plethysmography.pipeline_des,
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
    
def get_jobs_stamp(Plethysmography):
    print('get_jobs_stamp thread id',threading.get_ident())
    print("get_jobs_stamp process id",os.getpid())
    for file_st in Plethysmography.signals:
        print(file_st)
        stamp_cmd = 'python -u "{stamper}" --s "{signal}" --n "{need}"'.format(
            # The path to the timestamper python script:
            stamper = Plethysmography.gui_config['Dictionaries']['Paths']['timestamper'],
            # The basename of the signal file:
            signal = file_st,
            # The series of timestamps to the timestamps of the signal file will be compared to:
            need = Plethysmography.gui_config['Dictionaries']['Timestamps'][1])
        yield stamp_cmd

#endregion
