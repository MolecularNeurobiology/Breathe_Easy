
import sys
import os
from queue import Queue
import subprocess
import threading
from PyQt5.QtCore import QRunnable


class Worker(QRunnable):
    """
    Chris Ward got the threading to work!

    The Worker class handles the threading and parallel processing for the main GUI.

    Parameters
    --------
    QRunnable: class
        The Worker class inherits the properties and methods from teh QRunnable class.
    """
    def __init__(self, path_to_script: str, worker_id: int, worker_queue: Queue):
        """
        Instantiate the Worker Class.

        Parameters
        ---------
        path_to_script: str
            The string yielded by get_jobs_py() or get_jobs_r() that is given to the command line to launch either BASSPRO or STAGG respectively.
        worker_id: int
            The worker's number, determined by Plethysmography.counter.
        worker_queue: Queue
            A first-in, first-out queue constructor for safely exchanging information between threads.
        pleth: Class
            The Plethysmography Class.
        """
        super(Worker, self).__init__()
        self.path_to_script = path_to_script
        self.worker_id = worker_id
        self.worker_queue = worker_queue
    
    def run(self):
        """
        Use subprocess.Popen to run a seperate program in a new process.
        stdout will be captured by the variable proc.stdout and extracted below.
        
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


#region get_jobs
def get_jobs_py(signal_files, module, output, metadata, manual, auto, basic):
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
    for file_py in signal_files:
        breathcaller_cmd = [
            #'python',
            sys.executable,  # TODO: change this back to just 'python'
            '-u',
            module,  # path to basspro script
            '-i', os.path.dirname(file_py),  # signal dir
            '-f', os.path.basename(file_py),  # signal file
            '-o', output,
            '-a', metadata,
            '-m', manual if manual else "",
            '-c', auto if auto else "",
            '-p', basic,
        ]
        '''
        breathcaller_cmd = 'python -u "{module}" -i "{id}" -f "{signal}" -o "{output}" -a "{metadata}" -m "{manual}" -c "{auto}" -p "{basic}"'.format(
            # The path to the BASSPRO script:
            module=module,
            # The path of the signal file's directory:
            id=os.path.dirname(file_py),
            # The path of the BASSPRO output directory as chosen by the user previously:
            output=output,
            # The basename of the signal file:
            signal=os.path.basename(file_py),
            # The path of the metadata file:
            metadata=metadata,
            # The path of the manual settings file - if not selected, it's an empty string "":
            manual=manual if manual else "",
            # The path of the automated settings file - if not selected, it's an empty string "":
            auto=auto if auto else "",
            # The path of the basic settings file:
            basic=basic
        )
        '''
        yield breathcaller_cmd


def get_jobs_r(rscript, pipeline, papr_dir, workspace_dir, input_dir_r, variable_config, graph_config, other_config, output_dir, image_format):
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
    papr_cmd=[
        # The path to the local R executable file
        rscript,
        # The path to the STAGG script
        pipeline,
        # The path to the output directory chosen by the user
        '-d', workspace_dir,
        # This variable is either a list of JSON file paths produced as BASSPRO output, a list of JSON file paths produced as BASSPRO output and an .RData file path produced as STAGG output, a list containing a single path of an .RData file, or a string that is the path to a single directory containing JSON files produced as BASSPRO output.
        '-J', input_dir_r,
        # The path to the variable_config.csv file
        '-R', variable_config,
        # The path to the graph_config.csv file
        '-G', graph_config,
        # The path to the other_config.csv file
        '-F', other_config,
        # The path to the directory for STAGG output
        '-O', output_dir,
        # The paths to the STAGG scripts
        '-T', os.path.join(papr_dir, "Data_import_multi.R"),
        '-S', os.path.join(papr_dir, "Statistical_analysis.R"),
        '-M', os.path.join(papr_dir, "Graph_generator.R"),
        '-B', os.path.join(papr_dir, "Optional_graphs.R"),
        # A string, either ".jpeg" or ".svg", indicating the format of the image output from STAGG
        '-I', image_format,
        # The path to the STAGG scripts directory
        '--Sum', papr_dir
    ]
    print(' '.join([f'"{i}"' if i[0]!='-' else i for i in papr_cmd]))
    
    yield papr_cmd


#endregion
