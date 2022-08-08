
from typing import Callable, List, Optional
from datetime import datetime, timedelta
from threading import Thread
from queue import Queue

from PyQt5.QtCore import QTimer
from util.tools import generate_unique_id
from util.ui.dialogs import nonblocking_msg


class ThreadManager:
    """
    Manage start/stop and output of running threads

    Attributes
    ---------
    monitors (dict): all currently maintained threads
    """
    def __init__(self):
        self.monitors = {}  # store callback loops used to monitor processes

    def is_process_named(self, search_name: str):
        """
        Search for a running thread with given name

        Returns
        ------
        bool: whether the name is found
        """
        for monitor in self.monitors.values():
            if monitor['proc_name'] == search_name:
                return True
        return False

    def cancel_monitor(self, monitor_id: int, exec_after_cancel: Optional[Callable] = None):
        """
        Cancel monitoring for a process and run a given function
        """
        self.monitors[monitor_id]['status'] = 'cancelled'
        if exec_after_cancel:
            exec_after_cancel()

    def add_monitor(self, workers: List[Thread], msg_queue: Queue,
                    execute_after: Optional[Callable] = None,
                    exec_after_cancel: Optional[Callable] = None,
                    proc_name: str = None, print_funcs: List[Callable] = [],
                    cancel_msg: str = None):
        """
        Add a new monitor for a process.

        Parameters
        ---------
        workers: list of all the running threads for this process
        msg_queue: shared message queue for communication with threads
        execute_after: function to execute on process completion
        exec_after_cancel: function to execute on monitor cancellation
        proc_name: optional process name
        print_funcs:
            list of functions intended to receive string output from
            the shared message queue
        cancel_msg:
            cancel message to display when the process hangs for too long
        """
        new_id = generate_unique_id(self.monitors.keys())
        cancel_func = lambda : self.cancel_monitor(new_id, exec_after_cancel=exec_after_cancel)
        no_cancel_func = lambda : self._reset_last_msg_time(new_id)
        default_cancel_message = "would you like to cancel waiting for followup processing?"
        self.monitors[new_id] = {
            'status': 'running',
            'execute_after': execute_after,
            'workers': workers,
            'msg_queue': msg_queue,
            'dialog_window': None,
            'last_heard': datetime.now(),
            'proc_name': proc_name or f"Process {new_id}",
            'cancel_func': cancel_func,
            'no_cancel_func': no_cancel_func,
            'cancel_msg': cancel_msg or default_cancel_message
        }

        # monitor worker to execute next function
        self.monitor_workers(new_id)
        
        # monitor status messages (faster interval)
        self.print_queue_status(new_id, print_funcs)

    def print_queue_status(self, monitor_id: int, print_funcs: List[Callable] = [], interval: int = 200):
        """
        Print queue messages to a set of `print_funcs` on a given interval

        Parameters
        ---------
        monitor_id: id of monitor
        print_funcs: list of print functions to pass string messages to
        interval: [ms] delay until calling this function again
        """
        # Check if proc is completed or cancelled
        if monitor_id not in self.monitors or self.monitors[monitor_id]['status'] == 'cancelled':
            return

        monitor = self.monitors[monitor_id]

        # TODO: search - "pyqt multiprocessing signals vs queue messages"
        queue = monitor['msg_queue']
        while not queue.empty():
            worker_id, new_msg = queue.get_nowait()
            if new_msg == 'DONE':
                # Remove worker from monitor
                self.monitors[monitor_id]['workers'].pop(worker_id)
            else:
                self._reset_last_msg_time(monitor_id)

            # Print message to all message funcs
            for print_func in print_funcs:
                print_func(f'{worker_id} : {new_msg}')

        # Call this function again after the given [ms] interval
        QTimer.singleShot(interval, lambda : self.print_queue_status(monitor_id, interval=interval, print_funcs=print_funcs))

    def _reset_last_msg_time(self, monitor_id):
        """
        Reset the time we last heard from a monitored process, and
        unset the dialog window for cancelling since we're getting a heartbeat
        """
        self.monitors[monitor_id]['last_heard'] = datetime.now()
        self.monitors[monitor_id]['dialog_window'] = None

    def monitor_workers(self, monitor_id: int, interval: int = 1000):
        """
        Monitor process status and execute a function after completion

        Parameters
        ---------
        monitor_id: id of process monitor
        interval: [ms] delay between subsequent calls of this method
        """
        monitor = self.monitors[monitor_id]

        # TODO: make sure we kill/wait any still running processes
        # Check if this monitor has been cancelled
        if monitor['status'] == 'cancelled':
            self.monitors.pop(monitor_id)
            return

        # If any of our workers are still working
        if len(monitor['workers']) > 0:

            # Check again in `interval` milliseconds
            # TODO: make this a timer on interval, not singleshot
            QTimer.singleShot(interval, lambda : self.monitor_workers(monitor_id, interval=interval))
            return
        
        execute_after = monitor['execute_after']
        
        # Run next function
        if execute_after:
            self.monitors.pop(monitor_id)
            execute_after()
