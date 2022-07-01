
from PyQt5.QtCore import QTimer
from datetime import datetime, timedelta
from util.tools import generate_unique_id
from util.ui.dialogs import nonblocking_msg


class ThreadManager:
    def __init__(self):
        self.monitors = {}  # store callback loops used to monitor processes

    def cancel_monitor(self, monitor_id, exec_after_cancel=None):
        self.monitors[monitor_id]['status'] = 'cancelled'
        if exec_after_cancel:
            exec_after_cancel()

    def add_monitor(self, workers, msg_queue, execute_after=None, exec_after_cancel=None, proc_name=None, print_funcs=[]):
        new_id = generate_unique_id(self.monitors.keys())
        cancel_func = lambda : self.cancel_monitor(new_id, exec_after_cancel=exec_after_cancel)
        no_cancel_func = lambda : self._reset_last_msg_time(new_id)
        self.monitors[new_id] = {
            'status': 'running',
            'execute_after': execute_after,
            'workers': workers,
            'msg_queue': msg_queue,
            'dialog_window': None,
            'last_heard': datetime.now(),
            'proc_name': proc_name if proc_name else f"Process {new_id}",
            'cancel_func': cancel_func,
            'no_cancel_func': no_cancel_func,
        }

        # monitor worker to execute next function
        self.monitor_workers(new_id)
        
        # monitor status messages (faster interval)
        self.print_queue_status(new_id, print_funcs)

    def print_queue_status(self, monitor_id, print_funcs=[], interval=200):
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

        QTimer.singleShot(interval, lambda : self.print_queue_status(monitor_id, interval=interval, print_funcs=print_funcs))

    def _reset_last_msg_time(self, monitor_id):
        """
        Reset the time we last heard from a monitored process
        Also, unset the dialog window for cancelling since we're getting a heartbeat
        """
        self.monitors[monitor_id]['last_heard'] = datetime.now()
        self.monitors[monitor_id]['dialog_window'] = None

    def monitor_workers(self, monitor_id, interval=1000):
        """
        Use this function to monitor a longrunning process and pick up afterwards
          with some arbitrary function
        Data about each monitoring instance is stored in `self.monitors`
        """
        monitor = self.monitors[monitor_id]

        # TODO: make sure we kill/wait any still running processes
        # Check if this monitor has been cancelled
        if monitor['status'] == 'cancelled':
            self.monitors.pop(monitor_id)
            return

        # If any of our workers are still working
        if len(monitor['workers']) > 0:
            last_heard = monitor['last_heard']

            # Unset dialog window if it was hidden (user made a selection)
            if monitor['dialog_window'] and monitor['dialog_window'].isHidden():
                self.monitors[monitor_id]['dialog_window'] = None

            # TODO: implement BASSPRO cancel, not just STAGG continuation
            # If it's been longer than 1 minute since we've heard from the threads
            if datetime.now() - last_heard > timedelta(minutes=2) and \
                not monitor['dialog_window']:
                msg = f"{monitor['proc_name']} is taking a while, would you like to cancel checking for STAGG autostart?"
                yes_func = monitor['cancel_func']
                no_func = monitor['no_cancel_func']
                msg_box = nonblocking_msg(msg, (yes_func, no_func), title="Longrunning Process", msg_type='yes')
                self.monitors[monitor_id]['dialog_window'] = msg_box
            
            # Check again in a second
            # TODO: make this a timer on interval, not singleshot
            QTimer.singleShot(interval, lambda : self.monitor_workers(monitor_id, interval=interval))
            return
        
        execute_after = monitor['execute_after']
        
        # Run next function
        if execute_after:
            self.monitors.pop(monitor_id)
            execute_after()
